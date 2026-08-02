from __future__ import annotations

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
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
BODY_FONT = "IBM Plex Sans Arabic"
STATUS = "الشعار 02 معتمد، وبقية القرارات قيد المراجعة"
PROHIBITED = (r"\bA" + r"I\b", "Artificial " + "Intelligence", "الذكاء " + "الاصطناعي")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def xml(archive: zipfile.ZipFile, name: str):
    return etree.fromstring(archive.read(name))


def style_maps(styles_root):
    bidi: dict[str, bool] = {}
    font: dict[str, str | None] = {}
    based_on: dict[str, str | None] = {}
    for style in styles_root.findall(f"{{{W}}}style"):
        style_id = style.get(f"{{{W}}}styleId")
        p_pr = style.find(f"{{{W}}}pPr")
        r_pr = style.find(f"{{{W}}}rPr")
        based = style.find(f"{{{W}}}basedOn")
        based_on[style_id] = based.get(f"{{{W}}}val") if based is not None else None
        bidi[style_id] = p_pr is not None and p_pr.find(f"{{{W}}}bidi") is not None
        r_fonts = r_pr.find(f"{{{W}}}rFonts") if r_pr is not None else None
        font[style_id] = r_fonts.get(f"{{{W}}}cs") if r_fonts is not None else None

    def inherits(mapping, style_id, wanted):
        seen = set()
        current = style_id
        while current and current not in seen:
            seen.add(current)
            if mapping.get(current) == wanted:
                return True
            current = based_on.get(current)
        return False

    return bidi, font, based_on, inherits


def audit(path: Path) -> dict:
    with zipfile.ZipFile(path, "r") as archive:
        require(archive.testzip() is None, "ZIP CRC failure")
        names = archive.namelist()
        require(len(names) == len(set(names)), "Duplicate package entries")
        mandatory = {
            "[Content_Types].xml",
            "_rels/.rels",
            "word/document.xml",
            "word/styles.xml",
            "word/fontTable.xml",
            "docProps/core.xml",
        }
        require(mandatory.issubset(names), "Missing mandatory OOXML parts")
        for name in names:
            if name.endswith((".xml", ".rels")):
                etree.fromstring(archive.read(name))

        document = xml(archive, "word/document.xml")
        styles = xml(archive, "word/styles.xml")
        bidi_map, font_map, based_on, inherits = style_maps(styles)

        visible_parts = [
            name
            for name in names
            if name == "word/document.xml" or re.fullmatch(r"word/(header|footer)\d+\.xml", name)
        ]
        visible_text: list[str] = []
        paragraphs = 0
        rtl_paragraphs = 0
        arabic_runs = 0
        branded_font_runs = 0
        image_count = 0
        images_with_alt = 0

        for name in visible_parts:
            root = xml(archive, name)
            visible_text.extend(node.text or "" for node in root.findall(f".//{{{W}}}t"))
            for paragraph in root.findall(f".//{{{W}}}p"):
                text = "".join(node.text or "" for node in paragraph.findall(f".//{{{W}}}t")).strip()
                if not text:
                    continue
                paragraphs += 1
                p_pr = paragraph.find(f"{{{W}}}pPr")
                direct_bidi = p_pr is not None and p_pr.find(f"{{{W}}}bidi") is not None
                p_style = p_pr.find(f"{{{W}}}pStyle") if p_pr is not None else None
                style_id = p_style.get(f"{{{W}}}val") if p_style is not None else "Normal"
                if direct_bidi or inherits(bidi_map, style_id, True):
                    rtl_paragraphs += 1
                else:
                    raise AssertionError(f"Non-RTL visible paragraph in {name}: {text[:80]}")

                for run in paragraph.findall(f"{{{W}}}r"):
                    run_text = "".join(node.text or "" for node in run.findall(f".//{{{W}}}t"))
                    if not re.search(r"[\u0600-\u06FF]", run_text):
                        continue
                    arabic_runs += 1
                    r_pr = run.find(f"{{{W}}}rPr")
                    r_fonts = r_pr.find(f"{{{W}}}rFonts") if r_pr is not None else None
                    direct_font = r_fonts.get(f"{{{W}}}cs") if r_fonts is not None else None
                    if direct_font == BODY_FONT or inherits(font_map, style_id, BODY_FONT):
                        branded_font_runs += 1
                    else:
                        raise AssertionError(f"Arabic run without brand font in {name}: {run_text[:80]}")

            for node in root.iter():
                if etree.QName(node).localname != "docPr":
                    continue
                image_count += 1
                description = (node.get("descr") or "").strip()
                title = (node.get("title") or "").strip()
                if description and title:
                    images_with_alt += 1
                    visible_text.extend((description, title))

        joined_visible = "\n".join(visible_text)
        require(not re.search(r"[A-Za-z]", joined_visible), "Visible Latin text found outside the logo artwork")
        for pattern in PROHIBITED:
            require(not re.search(pattern, joined_visible, flags=re.IGNORECASE), f"Prohibited term found: {pattern}")
        require(STATUS in joined_visible, "Required approval-status statement is missing")
        require(image_count == images_with_alt, "One or more images lacks Arabic alt text and title")
        require(arabic_runs == branded_font_runs, "One or more Arabic runs lacks the brand font")

        core = xml(archive, "docProps/core.xml")
        title = (core.findtext(f"{{{DC}}}title") or "").strip()
        subject = (core.findtext(f"{{{DC}}}subject") or "").strip()
        creator = (core.findtext(f"{{{DC}}}creator") or "").strip()
        modified_by = (core.findtext(f"{{{CP}}}lastModifiedBy") or "").strip()
        require(title and subject, "Title or subject metadata is empty")
        require(not creator and not modified_by, "Personal creator metadata was not scrubbed")
        require("docProps/custom.xml" not in names, "Custom properties remain")
        metadata_text = title + "\n" + subject
        for pattern in PROHIBITED:
            require(not re.search(pattern, metadata_text, flags=re.IGNORECASE), f"Prohibited metadata term found: {pattern}")

        font_table = xml(archive, "word/fontTable.xml")
        font_node = font_table.find(f"{{{W}}}font[@{{{W}}}name='{BODY_FONT}']")
        require(font_node is not None, "Brand font is absent from fontTable.xml")
        embedded_targets = {
            "word/fonts/IBMPlexSansArabic-Regular.odttf",
            "word/fonts/IBMPlexSansArabic-Bold.odttf",
        }
        require(embedded_targets.issubset(names), "Embedded regular or bold font payload is missing")
        require(font_node.find(f"{{{W}}}embedRegular") is not None, "embedRegular is missing")
        require(font_node.find(f"{{{W}}}embedBold") is not None, "embedBold is missing")
        content_types = xml(archive, "[Content_Types].xml")
        odttf = content_types.find(f"{{{CT}}}Default[@Extension='odttf']")
        require(odttf is not None, "Embedded-font content type is missing")
        font_rels = xml(archive, "word/_rels/fontTable.xml.rels")
        rel_targets = {node.get("Target") for node in font_rels.findall(f"{{{REL}}}Relationship")}
        require(
            {"fonts/IBMPlexSansArabic-Regular.odttf", "fonts/IBMPlexSansArabic-Bold.odttf"}.issubset(rel_targets),
            "Embedded-font relationships are incomplete",
        )

        sect_prs = document.findall(f".//{{{W}}}sectPr")
        require(sect_prs, "No section properties found")
        for sect_pr in sect_prs:
            pg_sz = sect_pr.find(f"{{{W}}}pgSz")
            pg_mar = sect_pr.find(f"{{{W}}}pgMar")
            require(pg_sz is not None and pg_mar is not None, "Missing page geometry")
            width = int(pg_sz.get(f"{{{W}}}w"))
            height = int(pg_sz.get(f"{{{W}}}h"))
            left = int(pg_mar.get(f"{{{W}}}left"))
            right = int(pg_mar.get(f"{{{W}}}right"))
            require(abs(width - 11906) <= 2 and abs(height - 16838) <= 2, "Page is not A4 portrait")
            require(width - left - right == 9360, "Content width is not the required 9360 DXA")

        tables = document.findall(f".//{{{W}}}tbl")
        for index, table in enumerate(tables, start=1):
            tbl_pr = table.find(f"{{{W}}}tblPr")
            require(tbl_pr is not None and tbl_pr.find(f"{{{W}}}bidiVisual") is not None, f"Table {index} is not RTL")
            first_row = table.find(f"{{{W}}}tr")
            tr_pr = first_row.find(f"{{{W}}}trPr") if first_row is not None else None
            require(tr_pr is not None and tr_pr.find(f"{{{W}}}tblHeader") is not None, f"Table {index} header row is not marked")
            require(not table.findall(f".//{{{W}}}trHeight"), f"Table {index} uses fixed row heights")

        require(not document.findall(f".//{{{W}}}ins"), "Tracked insertions remain")
        require(not document.findall(f".//{{{W}}}del"), "Tracked deletions remain")
        require(not any(name.startswith("word/comments") for name in names), "Comment parts remain")

        return {
            "file": str(path),
            "status": "pass",
            "package_parts": len(names),
            "visible_paragraphs": paragraphs,
            "rtl_paragraphs": rtl_paragraphs,
            "arabic_runs": arabic_runs,
            "brand_font_runs": branded_font_runs,
            "images": image_count,
            "images_with_alt": images_with_alt,
            "tables": len(tables),
            "embedded_fonts": 2,
            "page_geometry": "A4 portrait; 9360 DXA content width",
            "metadata_title": title,
            "metadata_subject": subject,
        }


def main() -> int:
    if len(sys.argv) < 4:
        raise SystemExit("usage: audit_docx_v2.py REPORT.json FILE.docx FILE.docx [...]")
    report_path = Path(sys.argv[1])
    results = [audit(Path(value).resolve()) for value in sys.argv[2:]]
    report = {"status": "pass", "documents": results}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
