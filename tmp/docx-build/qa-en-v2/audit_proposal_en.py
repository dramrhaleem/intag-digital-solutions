from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
DC = "http://purl.org/dc/elements/1.1/"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
FONT_NAME = "Poppins"
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
STATUS = 'Logo 02 “Connected Frame” is approved.'
TECHNICAL_WORKSTREAM = "Technology & Digital Products"
PROHIBITED = (
    r"\bA" + r"I\b",
    "Artificial " + "Intelligence",
    "Open" + "AI",
    "Chat" + "GPT",
    "Code" + "x",
    "Gem" + "ini",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def xml(archive: zipfile.ZipFile, name: str) -> etree._Element:
    return etree.fromstring(archive.read(name))


def q(local: str) -> str:
    return f"{{{W}}}{local}"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(path: Path, reference: Path, render_dir: Path) -> dict:
    with zipfile.ZipFile(path, "r") as archive, zipfile.ZipFile(reference, "r") as source:
        require(archive.testzip() is None, "ZIP CRC failure")
        names = archive.namelist()
        require(len(names) == len(set(names)), "Duplicate package entries")
        for name in names:
            if name.endswith((".xml", ".rels")):
                etree.fromstring(archive.read(name))

        document = xml(archive, "word/document.xml")
        visible_parts = [
            name
            for name in names
            if name == "word/document.xml" or re.fullmatch(r"word/(header|footer)\d+\.xml", name)
        ]
        visible_text: list[str] = []
        visible_paragraphs = 0
        visible_runs = 0
        images = 0
        images_with_alt = 0

        for name in visible_parts:
            root = xml(archive, name)
            for paragraph in root.findall(f".//{{{W}}}p"):
                paragraph_text = "".join(
                    node.text or "" for node in paragraph.findall(f".//{{{W}}}t")
                ).strip()
                if not paragraph_text:
                    continue
                visible_paragraphs += 1
                visible_text.append(paragraph_text)
                p_pr = paragraph.find(q("pPr"))
                require(
                    p_pr is None or p_pr.find(q("bidi")) is None,
                    f"Visible paragraph is RTL in {name}: {paragraph_text[:80]}",
                )
                if p_pr is not None:
                    jc = p_pr.find(q("jc"))
                    if jc is not None:
                        require(jc.get(q("val")) != "right", f"Visible paragraph is right-aligned: {paragraph_text[:80]}")

                for run in paragraph.findall(q("r")):
                    run_text = "".join(node.text or "" for node in run.findall(f".//{{{W}}}t"))
                    if not run_text.strip():
                        continue
                    visible_runs += 1
                    r_pr = run.find(q("rPr"))
                    require(r_pr is not None, f"Visible run lacks rPr in {name}: {run_text[:80]}")
                    require(r_pr.find(q("rtl")) is None, f"Visible run is RTL in {name}: {run_text[:80]}")
                    fonts = r_pr.find(q("rFonts"))
                    require(fonts is not None, f"Visible run lacks explicit font in {name}: {run_text[:80]}")
                    for attribute in ("ascii", "hAnsi", "eastAsia", "cs"):
                        require(
                            fonts.get(q(attribute)) == FONT_NAME,
                            f"Visible run does not use Poppins ({attribute}) in {name}: {run_text[:80]}",
                        )
                    lang = r_pr.find(q("lang"))
                    require(
                        lang is not None and lang.get(q("val")) == "en-US",
                        f"Visible run language is not en-US in {name}: {run_text[:80]}",
                    )

            for node in root.iter():
                if etree.QName(node).localname != "docPr":
                    continue
                images += 1
                description = (node.get("descr") or "").strip()
                title = (node.get("title") or "").strip()
                if description and title:
                    images_with_alt += 1
                    visible_text.extend((description, title))

        joined_visible = "\n".join(visible_text)
        require(not ARABIC_RE.search(joined_visible), "Arabic remains in visible content")
        require(STATUS in joined_visible, "Approved Logo 02 statement is missing")
        require(TECHNICAL_WORKSTREAM in joined_visible, "Required technical workstream label is missing")
        require(images == images_with_alt, "An image lacks English alt text or title")

        core = xml(archive, "docProps/core.xml")
        title = (core.findtext(f"{{{DC}}}title") or "").strip()
        subject = (core.findtext(f"{{{DC}}}subject") or "").strip()
        creator = (core.findtext(f"{{{DC}}}creator") or "").strip()
        modified_by = (core.findtext(f"{{{CP}}}lastModifiedBy") or "").strip()
        require(title and subject, "Title or subject metadata is empty")
        require(not creator and not modified_by, "Creator metadata was not scrubbed")
        require(not ARABIC_RE.search(title + "\n" + subject), "Arabic remains in core metadata")
        require("docProps/custom.xml" not in names, "Custom properties remain")

        textual_package = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in names
            if name.endswith((".xml", ".rels"))
        )
        for pattern in PROHIBITED:
            require(
                not re.search(pattern, joined_visible + "\n" + textual_package, flags=re.IGNORECASE),
                f"Disallowed term or tool name remains: {pattern}",
            )

        require("IBM Plex Sans Arabic" not in textual_package, "Arabic reference font remains in OOXML")
        require(not any(name.startswith("word/fonts/IBMPlexSansArabic") for name in names), "Arabic font payload remains")
        expected_fonts = {
            "word/fonts/Poppins-Regular.odttf",
            "word/fonts/Poppins-Bold.odttf",
        }
        require(expected_fonts.issubset(names), "Embedded Poppins regular or bold payload is missing")
        font_table = xml(archive, "word/fontTable.xml")
        font_node = font_table.find(f"{{{W}}}font[@{{{W}}}name='{FONT_NAME}']")
        require(font_node is not None, "Poppins is absent from fontTable.xml")
        require(font_node.find(q("embedRegular")) is not None, "Poppins embedRegular is missing")
        require(font_node.find(q("embedBold")) is not None, "Poppins embedBold is missing")

        sections = document.findall(f".//{{{W}}}sectPr")
        require(len(sections) == 1, "Proposal must retain one A4 section")
        sect_pr = sections[0]
        pg_sz = sect_pr.find(q("pgSz"))
        pg_mar = sect_pr.find(q("pgMar"))
        require(pg_sz is not None and pg_mar is not None, "Page geometry is incomplete")
        width = int(pg_sz.get(q("w")))
        height = int(pg_sz.get(q("h")))
        left = int(pg_mar.get(q("left")))
        right = int(pg_mar.get(q("right")))
        require(abs(width - 11906) <= 2 and abs(height - 16838) <= 2, "Page is not A4 portrait")
        require(width - left - right == 9360, "Content width is not 9360 DXA")

        header_types = {node.get(q("type")) for node in sect_pr.findall(q("headerReference"))}
        footer_types = {node.get(q("type")) for node in sect_pr.findall(q("footerReference"))}
        require({"default", "even"}.issubset(header_types), "Default/even header references are incomplete")
        require({"default", "even"}.issubset(footer_types), "Default/even footer references are incomplete")
        require("word/header2.xml" in names and "word/footer2.xml" in names, "Even header/footer parts are missing")

        tables = document.findall(f".//{{{W}}}tbl")
        require(len(tables) == 7, f"Expected 7 tables, found {len(tables)}")
        for index, table in enumerate(tables, start=1):
            tbl_pr = table.find(q("tblPr"))
            require(tbl_pr is not None, f"Table {index} lacks tblPr")
            require(tbl_pr.find(q("bidiVisual")) is None, f"Table {index} remains RTL")
            jc = tbl_pr.find(q("jc"))
            require(jc is not None and jc.get(q("val")) == "left", f"Table {index} is not LTR-aligned")
            first_row = table.find(q("tr"))
            tr_pr = first_row.find(q("trPr")) if first_row is not None else None
            require(tr_pr is not None and tr_pr.find(q("tblHeader")) is not None, f"Table {index} header row is not marked")
            require(not table.findall(f".//{{{W}}}trHeight"), f"Table {index} uses fixed row heights")

        require(not document.findall(f".//{{{W}}}ins"), "Tracked insertions remain")
        require(not document.findall(f".//{{{W}}}del"), "Tracked deletions remain")
        require(not any(name.startswith("word/comments") for name in names), "Comment parts remain")

        page_images = sorted(render_dir.glob("page-*.png"))
        require(len(page_images) == 5, f"Word render must contain 5 pages, found {len(page_images)}")
        require((render_dir / "proposal-en.pdf").exists(), "Word-rendered PDF is missing")

        allowed_changed = {
            "[Content_Types].xml",
            "docProps/core.xml",
            "word/document.xml",
            "word/_rels/document.xml.rels",
            "word/styles.xml",
            "word/stylesWithEffects.xml",
            "word/settings.xml",
            "word/numbering.xml",
            "word/header1.xml",
            "word/footer1.xml",
            "word/fontTable.xml",
            "word/_rels/fontTable.xml.rels",
        }
        common = set(names).intersection(source.namelist())
        preserved_parts = []
        unexpected_changes = []
        for name in sorted(common - allowed_changed):
            if sha256(archive.read(name)) == sha256(source.read(name)):
                preserved_parts.append(name)
            else:
                unexpected_changes.append(name)
        require(not unexpected_changes, "Unexpected package changes: " + ", ".join(unexpected_changes))
        require(
            sha256(archive.read("word/media/image1.png")) == sha256(source.read("word/media/image1.png")),
            "Approved Logo 02 image payload changed",
        )

        source_hash = hashlib.sha256(reference.read_bytes()).hexdigest()
        target_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            "status": "pass",
            "file": str(path),
            "sha256": target_hash,
            "reference": str(reference),
            "reference_sha256": source_hash,
            "package_parts": len(names),
            "package_xml_integrity": "pass",
            "preserved_unmodified_parts": len(preserved_parts),
            "unexpected_package_changes": unexpected_changes,
            "visible_paragraphs": visible_paragraphs,
            "visible_runs": visible_runs,
            "visible_language": "English",
            "paragraph_direction": "LTR",
            "brand_font": FONT_NAME,
            "embedded_fonts": sorted(expected_fonts),
            "images": images,
            "images_with_alt_and_title": images_with_alt,
            "approved_logo_payload_preserved": True,
            "technical_workstream": TECHNICAL_WORKSTREAM,
            "forbidden_terms_and_tool_names": "none detected",
            "metadata_title": title,
            "metadata_subject": subject,
            "creator_metadata_scrubbed": True,
            "page_geometry": "A4 portrait; one section; 9360 DXA content width",
            "word_render_pages": len(page_images),
            "tables": len(tables),
            "even_header_footer_explicit": True,
            "tracked_changes": 0,
            "comments": 0,
            "custom_properties": 0,
        }


def main() -> int:
    if len(sys.argv) != 5:
        raise SystemExit("usage: audit_proposal_en.py OUTPUT.json FILE.docx REFERENCE.docx RENDER_DIR")
    report_path = Path(sys.argv[1]).resolve()
    result = audit(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve())
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
