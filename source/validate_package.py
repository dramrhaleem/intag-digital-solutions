from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"

EXPECTED = [
    ROOT / "README_AR.md",
    ROOT / "brandbook" / "index.html",
    OUTPUT / "pdf" / "INTAG_Brand_Guidelines_v2.0_Logo02_Approved_Working.pdf",
    OUTPUT / "pdf" / "INTAG_Brand_Quick_Reference_v2.0_Logo02_Approved_Working.pdf",
    ROOT / "assets" / "logo" / "svg" / "INTAG_Logo_Primary_Horizontal_RGB_v1.svg",
    ROOT / "assets" / "logo" / "svg" / "INTAG_Symbol_Color_RGB_v1.svg",
    ROOT / "assets" / "logo" / "png" / "INTAG_Logo_Primary_Horizontal_RGB_v1_1280w.png",
    ROOT / "assets" / "logo" / "png" / "favicon.ico",
    ROOT / "assets" / "tokens" / "INTAG_DesignTokens_v1.json",
    ROOT / "assets" / "tokens" / "INTAG_Palette_v1.ase",
    ROOT / "assets" / "fonts" / "Poppins" / "OFL.txt",
    ROOT / "assets" / "fonts" / "IBMPlexSansArabic" / "OFL.txt",
    ROOT / "requirements.txt",
    ROOT / "package.json",
    ROOT / "pnpm-lock.yaml",
    ROOT / "docs" / "TEMPLATE_PLACEHOLDERS_AR.md",
    ROOT / "docs" / "LAYOUT_AND_SPACING_SYSTEM_AR.md",
    ROOT / "docs" / "DISCOVERY_AND_APPROVAL_AR.md",
    OUTPUT / "VISUAL_QA_AR.md",
    ROOT / "templates" / "presentation" / "INTAG_Presentation_Starter_EN_v2.pptx",
    ROOT / "templates" / "proposal" / "INTAG_Proposal_Starter_EN_v2.docx",
    ROOT / "templates" / "stationery" / "INTAG_Letterhead_Template_AR_v2.docx",
    ROOT / "templates" / "stationery" / "INTAG_BusinessCard_Front_90x50mm_Bleed3mm_v2.svg",
    ROOT / "templates" / "stationery" / "INTAG_BusinessCard_Back_90x50mm_Bleed3mm_v2.svg",
    ROOT / "templates" / "large-format" / "INTAG_Rollup_85x200cm_Bleed3mm_v2.svg",
    ROOT / "templates" / "large-format" / "INTAG_Rollup_85x200cm_Bleed3mm_v2.pdf",
    ROOT / "templates" / "large-format" / "INTAG_Rollup_85x200cm_ProductionGuide_v2.svg",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_release_file(path: Path) -> bool:
    """Mirror the release builder's inclusion rules for package-level QA."""

    if not path.is_file():
        return False
    rel = path.relative_to(ROOT)
    if rel.parts and rel.parts[0] in {"tmp", "release"}:
        return False
    if "__pycache__" in rel.parts or path.suffix.lower() in {".pyc", ".pyo"}:
        return False
    return True


def forbidden_association_patterns() -> list[tuple[str, re.Pattern[str]]]:
    """Terms and visual shorthand excluded from the public-facing brand system.

    Split string literals keep the validator itself from becoming a false
    positive when source files are included in the technical handoff.
    """

    return [
        (
            "english_acronym",
            re.compile(r"(?<![A-Za-z])" + "A" + "I" + r"(?![A-Za-z])", re.IGNORECASE),
        ),
        (
            "english_long_form",
            re.compile("artificial" + r"[\s_-]+" + "intelligence", re.IGNORECASE),
        ),
        (
            "arabic_long_form",
            re.compile("الذكاء" + r"\s+" + "الاصطناعي"),
        ),
        (
            "arabic_short_form",
            re.compile("ذكاء" + r"\s+" + "اصطناعي"),
        ),
        (
            "visual_shorthand_en",
            re.compile(
                r"\b(?:"
                + "ro" + "bot"
                + r"|"
                + "chat" + "bot"
                + r"|"
                + "neural" + r"[\s_-]+" + "network"
                + r"|"
                + "machine" + r"[\s_-]+" + "learning"
                + r"|"
                + "deep" + r"[\s_-]+" + "learning"
                + r")\b",
                re.IGNORECASE,
            ),
        ),
        (
            "visual_shorthand_ar",
            re.compile(
                r"(?:"
                + "رو" + "بوت"
                + r"|"
                + "شبكات?" + r"\s+" + "عصبية"
                + r"|"
                + "تعلم" + r"\s+" + "آلي"
                + r"|"
                + "تعلّم" + r"\s+" + "آلي"
                + r")"
            ),
        ),
        (
            "model_or_tool_reference",
            re.compile(
                r"(?<![A-Za-z])(?:"
                + "Chat" + "G" + "PT"
                + r"|"
                + "Open" + "A" + "I"
                + r"|"
                + "G" + "PT" + r"(?:[-_ ]?\d+(?:\.\d+)?)?"
                + r"|"
                + "LL" + "M"
                + r"|"
                + "Mid" + "journey"
                + r"|"
                + "DALL" + r"[-_ ]?" + "E"
                + r"|"
                + "Stable" + r"[\s_-]+" + "Diffusion"
                + r")(?![A-Za-z])",
                re.IGNORECASE,
            ),
        ),
        (
            "arabic_model_reference",
            re.compile(r"(?:نماذج?\s+لغوية\s+كبيرة|نموذج\s+لغوي\s+كبير)"),
        ),
    ]


def scan_forbidden_associations() -> list[dict[str, str]]:
    """Scan release-facing names, text, Office XML, and PDF text/metadata."""

    patterns = forbidden_association_patterns()
    hits: list[dict[str, str]] = []
    text_suffixes = {
        ".md", ".html", ".htm", ".css", ".js", ".mjs", ".json", ".txt", ".xml", ".svg", ".py"
    }

    def check_text(path: Path, surface: str, text: str) -> None:
        # Embedded font binaries are long base64 data URIs, not language,
        # metadata, or visible brand content.
        if path.suffix.lower() == ".svg":
            text = re.sub(r"data:[^\"']+", "", text)
        for label, pattern in patterns:
            match = pattern.search(text)
            if match:
                snippet = re.sub(
                    r"\s+",
                    " ",
                    text[max(0, match.start() - 45): match.end() + 45],
                ).strip()
                hits.append(
                    {
                        "file": path.relative_to(ROOT).as_posix(),
                        "surface": surface,
                        "rule": label,
                        "snippet": snippet,
                    }
                )

    ignored_names = {"MANIFEST_SHA256.json", "QA_REPORT.json", "QA_REPORT_AR.md"}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel.parts and rel.parts[0] in {"tmp", "release"}:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.name in ignored_names:
            continue

        relative_name = rel.as_posix()
        for label, pattern in patterns:
            if pattern.search(relative_name):
                hits.append(
                    {
                        "file": relative_name,
                        "surface": "filename",
                        "rule": label,
                        "snippet": relative_name,
                    }
                )

        suffix = path.suffix.lower()
        if suffix in text_suffixes:
            check_text(path, "text", path.read_text(encoding="utf-8", errors="replace"))
        elif suffix in {".docx", ".pptx"}:
            try:
                with zipfile.ZipFile(path) as archive:
                    for member in archive.namelist():
                        if member.endswith((".xml", ".rels")):
                            check_text(
                                path,
                                f"ooxml:{member}",
                                archive.read(member).decode("utf-8", errors="replace"),
                            )
            except zipfile.BadZipFile:
                continue
        elif suffix == ".pdf":
            try:
                reader = PdfReader(path)
                metadata = " ".join(
                    f"{key} {value}" for key, value in (reader.metadata or {}).items()
                )
                check_text(path, "pdf_metadata", metadata)
                for index, page in enumerate(reader.pages, start=1):
                    check_text(path, f"pdf_page:{index}", page.extract_text() or "")
            except Exception:
                continue

    return hits


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, object] = {}

    missing = [str(path.relative_to(ROOT)) for path in EXPECTED if not path.exists()]
    checks["expected_files_missing"] = missing
    if missing:
        errors.append(f"Missing expected files: {missing}")

    # SVG well-formedness and raster-embedding check.
    svg_files = sorted(path for path in ROOT.rglob("*.svg") if is_release_file(path))
    svg_errors = []
    raster_embeds = []
    for path in svg_files:
        try:
            ET.parse(path)
        except Exception as exc:
            svg_errors.append({"file": str(path.relative_to(ROOT)), "error": str(exc)})
        text = path.read_text(encoding="utf-8", errors="replace")
        if "data:image/" in text:
            raster_embeds.append(str(path.relative_to(ROOT)))
    checks["svg_count"] = len(svg_files)
    checks["svg_parse_errors"] = svg_errors
    checks["svg_raster_embeds"] = raster_embeds
    if svg_errors:
        errors.append(f"Invalid SVG files: {svg_errors}")
    if raster_embeds:
        warnings.append(f"SVG files with embedded raster data: {raster_embeds}")

    # Physical print-master geometry.
    print_master_specs = {
        ROOT / "templates" / "large-format" / "INTAG_Rollup_85x200cm_Bleed3mm_v2.svg": {
            "width": "856mm", "height": "2006mm", "viewBox": "0 0 856 2006"
        },
        ROOT / "templates" / "stationery" / "INTAG_BusinessCard_Front_90x50mm_Bleed3mm_v2.svg": {
            "width": "96mm", "height": "56mm", "viewBox": "0 0 960 560"
        },
        ROOT / "templates" / "stationery" / "INTAG_BusinessCard_Back_90x50mm_Bleed3mm_v2.svg": {
            "width": "96mm", "height": "56mm", "viewBox": "0 0 960 560"
        },
    }
    print_master_geometry = []
    for path, wanted in print_master_specs.items():
        if not path.exists():
            continue
        root = ET.parse(path).getroot()
        actual = {key: root.attrib.get(key) for key in ("width", "height", "viewBox")}
        print_master_geometry.append({"file": str(path.relative_to(ROOT)), "actual": actual, "expected": wanted})
        if actual != wanted:
            errors.append(f"Print-master geometry mismatch for {path.name}: {actual} != {wanted}")
    checks["print_master_geometry"] = print_master_geometry

    # Approved Logo 02 must match the exact Connected Frame geometry preserved
    # in the pre-v2 backup: two separate right-angle corners, never diagonals.
    approved_symbol = ROOT / "assets" / "logo" / "svg" / "INTAG_Symbol_Color_RGB_v1.svg"
    if approved_symbol.exists():
        symbol_text = approved_symbol.read_text(encoding="utf-8", errors="replace")
        geometry_checks = {
            "blue_corner": bool(re.search(r'M20(?:\.0+)?\s+84(?:\.0+)?V28(?:\.0+)?H72(?:\.0+)?', symbol_text)),
            "green_corner": bool(re.search(r'M108(?:\.0+)?\s+44(?:\.0+)?V100(?:\.0+)?H56(?:\.0+)?', symbol_text)),
            "center_node": bool(re.search(r'<circle\b[^>]*\bcx="64(?:\.0+)?"[^>]*\bcy="64(?:\.0+)?"[^>]*\br="14(?:\.0+)?"', symbol_text)),
            "no_diagonal_commands": not bool(re.search(r'<path\b[^>]*\bd="[^"]*\bL\s*64(?:\.0+)?\s+64(?:\.0+)?', symbol_text)),
        }
        checks["approved_logo02_geometry"] = geometry_checks
        if not all(geometry_checks.values()):
            errors.append(f"Approved Logo 02 geometry mismatch: {geometry_checks}")

    # PNG and ICO integrity.
    image_files = sorted(
        path
        for path in (
            list(ROOT.rglob("*.png"))
            + list(ROOT.rglob("*.webp"))
            + list(ROOT.rglob("*.ico"))
        )
        if is_release_file(path)
    )
    image_errors = []
    image_meta = []
    for path in image_files:
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                image_meta.append({"file": str(path.relative_to(ROOT)), "size": list(image.size), "mode": image.mode})
        except Exception as exc:
            image_errors.append({"file": str(path.relative_to(ROOT)), "error": str(exc)})
    checks["image_count"] = len(image_files)
    checks["image_errors"] = image_errors
    if image_errors:
        errors.append(f"Invalid raster files: {image_errors}")

    primary_png = ROOT / "assets" / "logo" / "png" / "INTAG_Logo_Primary_Horizontal_RGB_v1_1280w.png"
    if primary_png.exists():
        with Image.open(primary_png).convert("RGBA") as image:
            alpha = image.getchannel("A")
            checks["primary_logo_has_transparency"] = alpha.getextrema()[0] == 0
            if alpha.getextrema()[0] != 0:
                warnings.append("Primary PNG logo has no fully transparent pixels.")

    # PDF integrity and page counts.
    pdf_meta = []
    expected_pages = {
        "INTAG_Brand_Guidelines_v2.0_Logo02_Approved_Working.pdf": 44,
        "INTAG_Brand_Quick_Reference_v2.0_Logo02_Approved_Working.pdf": 2,
    }
    for path in sorted(path for path in ROOT.rglob("*.pdf") if is_release_file(path)):
        try:
            reader = PdfReader(path)
            count = len(reader.pages)
            pdf_meta.append({"file": str(path.relative_to(ROOT)), "pages": count})
            wanted = expected_pages.get(path.name)
            if wanted is not None and count != wanted:
                errors.append(f"{path.name}: expected {wanted} pages, found {count}")
        except Exception as exc:
            errors.append(f"Unreadable PDF {path.relative_to(ROOT)}: {exc}")
    checks["pdfs"] = pdf_meta

    # Native Office templates: ZIP integrity and expected editable structures.
    office_meta = []
    office_errors = []
    office_specs = {
        ROOT / "templates" / "presentation" / "INTAG_Presentation_Starter_EN_v2.pptx": {
            "required": {"[Content_Types].xml", "ppt/presentation.xml"},
            "slide_count": 7,
        },
        ROOT / "templates" / "proposal" / "INTAG_Proposal_Starter_EN_v2.docx": {
            "required": {"[Content_Types].xml", "word/document.xml"},
        },
        ROOT / "templates" / "stationery" / "INTAG_Letterhead_Template_AR_v2.docx": {
            "required": {"[Content_Types].xml", "word/document.xml"},
        },
    }
    for path, spec in office_specs.items():
        if not path.exists():
            continue
        try:
            with zipfile.ZipFile(path) as archive:
                bad_member = archive.testzip()
                names = set(archive.namelist())
                missing_members = sorted(spec["required"] - names)
                slide_count = len(
                    [
                        name
                        for name in names
                        if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
                    ]
                )
                item = {
                    "file": str(path.relative_to(ROOT)),
                    "bytes": path.stat().st_size,
                    "zip_crc_error": bad_member,
                    "missing_members": missing_members,
                }
                if path.suffix.lower() == ".pptx":
                    item["slide_count"] = slide_count
                office_meta.append(item)
                if bad_member:
                    office_errors.append(f"{path.name}: CRC failure in {bad_member}")
                if missing_members:
                    office_errors.append(f"{path.name}: missing OOXML members {missing_members}")
                wanted_slides = spec.get("slide_count")
                if wanted_slides is not None and slide_count != wanted_slides:
                    office_errors.append(
                        f"{path.name}: expected {wanted_slides} slides, found {slide_count}"
                    )
                if path.stat().st_size < 10_000:
                    office_errors.append(f"{path.name}: unexpectedly small native template")
        except Exception as exc:
            office_errors.append(f"Unreadable Office template {path.relative_to(ROOT)}: {exc}")
    checks["native_office_templates"] = office_meta
    if office_errors:
        errors.extend(office_errors)

    # HTML local references.
    html_files = sorted(path for path in ROOT.rglob("*.html") if is_release_file(path))
    broken_refs = []
    ref_re = re.compile(r'''(?:src|href)=["']([^"'#]+)["']''', re.IGNORECASE)
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for ref in ref_re.findall(text):
            if ref.startswith("[") and ref.endswith("]"):
                continue
            if re.match(r"^(?:https?:|mailto:|tel:|data:|/)", ref):
                continue
            target = (path.parent / ref.split("?", 1)[0]).resolve()
            if not target.exists():
                broken_refs.append({"html": str(path.relative_to(ROOT)), "ref": ref})
    checks["html_count"] = len(html_files)
    checks["broken_html_refs"] = broken_refs
    if broken_refs:
        errors.append(f"Broken HTML references: {broken_refs}")

    # Token values and accessibility audit presence.
    token_path = ROOT / "assets" / "tokens" / "INTAG_DesignTokens_v1.json"
    if token_path.exists():
        data = json.loads(token_path.read_text(encoding="utf-8"))
        checks["core_token_values"] = {key: data["color"][key]["hex"] for key in ["blue", "green", "ink", "mineral"]}
        expected_tokens = {"blue": "#2369B1", "green": "#2AB687", "ink": "#0B0D10", "mineral": "#F4F1E9"}
        if checks["core_token_values"] != expected_tokens:
            errors.append(f"Core token mismatch: {checks['core_token_values']}")

        css_path = ROOT / "assets" / "tokens" / "intag-tokens.css"
        scss_path = ROOT / "assets" / "tokens" / "_intag-tokens.scss"
        css_text = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
        scss_text = scss_path.read_text(encoding="utf-8") if scss_path.exists() else ""
        expected_names = {
            *(f"color-{key.replace('_', '-')}" for key in data["color"]),
            *(f"space-{key}" for key in data["space"]),
            *(f"radius-{key}" for key in data["radius"]),
            *(
                f"motion-{key.removesuffix('_ms').replace('_', '-')}"
                if key.endswith("_ms")
                else f"motion-{key.replace('_', '-')}"
                for key in data["motion"]
            ),
        }
        css_names = set(re.findall(r"--intag-([a-z0-9-]+)\s*:", css_text))
        scss_names = set(re.findall(r"\$intag-([a-z0-9-]+)\s*:", scss_text))
        checks["token_export_parity"] = {
            "expected": len(expected_names),
            "css_missing": sorted(expected_names - css_names),
            "scss_missing": sorted(expected_names - scss_names),
        }
        if expected_names - css_names or expected_names - scss_names:
            errors.append(f"Token export parity failed: {checks['token_export_parity']}")
        latin_weights = data.get("typography", {}).get("latin", {}).get("weights", [])
        checks["latin_weights"] = latin_weights
        if 400 not in latin_weights:
            errors.append("Poppins 400 is packaged/used but missing from Latin typography tokens.")
    contrast_path = ROOT / "assets" / "tokens" / "INTAG_Contrast_Audit_v1.json"
    checks["contrast_audit_present"] = contrast_path.exists()

    # Arabic Markdown wrapper compliance.
    rtl_errors = []
    for path in sorted(path for path in ROOT.rglob("*.md") if is_release_file(path)):
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if "_AR" in path.stem or re.search(r"[\u0600-\u06ff]", text):
            if not text.startswith('<div dir="rtl" align="right">') or not text.endswith("</div>"):
                rtl_errors.append(str(path.relative_to(ROOT)))
    checks["rtl_markdown_wrapper_errors"] = rtl_errors
    if rtl_errors:
        errors.append(f"Arabic Markdown wrapper errors: {rtl_errors}")

    # Release-facing placeholders are allowed only in templates and documentation/examples.
    placeholder_hits = []
    for path in sorted(ROOT.rglob("*")):
        if not is_release_file(path) or path.suffix.lower() not in {".html", ".svg", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = sorted(set(re.findall(r"\[[A-Z][A-Z0-9 _/.-]{2,}\]", text)))
        if hits:
            placeholder_hits.append({"file": str(path.relative_to(ROOT)), "placeholders": hits})
    checks["placeholder_register"] = placeholder_hits

    # Every actual template placeholder must be registered in the handoff checklist.
    placeholder_re = re.compile(r"\[[^\[\]\r\n]{2,80}\]")
    template_placeholders: set[str] = set()
    for path in sorted((ROOT / "templates").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".html", ".svg", ".docx", ".pptx"}:
            continue
        if path.suffix.lower() in {".docx", ".pptx"}:
            pieces: list[str] = []
            try:
                with zipfile.ZipFile(path) as archive:
                    for name in archive.namelist():
                        if name.endswith(".xml"):
                            try:
                                root = ET.fromstring(archive.read(name))
                                pieces.extend(piece.strip() for piece in root.itertext() if piece.strip())
                            except ET.ParseError:
                                continue
                raw = "\n".join(pieces)
            except zipfile.BadZipFile:
                raw = ""
        else:
            raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".svg":
            try:
                parsed = ET.parse(path)
                raw += "\n" + " ".join(piece.strip() for piece in parsed.getroot().itertext() if piece.strip())
            except Exception:
                pass
        template_placeholders.update(placeholder_re.findall(raw))
    placeholder_doc = ROOT / "docs" / "TEMPLATE_PLACEHOLDERS_AR.md"
    doc_text = placeholder_doc.read_text(encoding="utf-8", errors="replace") if placeholder_doc.exists() else ""
    documented_placeholders = set(placeholder_re.findall(doc_text))
    undocumented_placeholders = sorted(template_placeholders - documented_placeholders)
    checks["template_placeholder_completeness"] = {
        "template_placeholders": sorted(template_placeholders),
        "undocumented": undocumented_placeholders,
    }
    if undocumented_placeholders:
        errors.append(f"Undocumented template placeholders: {undocumented_placeholders}")

    # Email signature must remain portable outside the package folder.
    signature_path = ROOT / "templates" / "digital" / "INTAG_Email_Signature_Template_v1.html"
    signature_text = signature_path.read_text(encoding="utf-8", errors="replace") if signature_path.exists() else ""
    checks["email_signature_portable"] = (
        "[LOGO_URL_OR_CID]" in signature_text
        and not re.search(r'''<img[^>]+src=["'](?:\.\.?/|[A-Za-z]:\\)''', signature_text, re.IGNORECASE)
    )
    if not checks["email_signature_portable"]:
        errors.append("Email signature logo source is not portable; use approved HTTPS or CID placeholder.")

    # Reproducibility declarations and pinned dependency versions.
    package_path = ROOT / "package.json"
    requirements_path = ROOT / "requirements.txt"
    lock_path = ROOT / "pnpm-lock.yaml"
    package_data = json.loads(package_path.read_text(encoding="utf-8")) if package_path.exists() else {}
    node_deps = package_data.get("dependencies", {})
    requirements = requirements_path.read_text(encoding="utf-8").splitlines() if requirements_path.exists() else []
    checks["reproducibility"] = {
        "package_json": package_path.exists(),
        "lockfile": lock_path.exists(),
        "requirements": requirements_path.exists(),
        "node_versions_pinned": bool(node_deps) and all(re.fullmatch(r"\d+\.\d+\.\d+", value) for value in node_deps.values()),
        "python_versions_pinned": bool(requirements) and all("==" in line for line in requirements if line.strip() and not line.startswith("#")),
    }
    if not all(checks["reproducibility"].values()):
        errors.append(f"Reproducibility declarations incomplete: {checks['reproducibility']}")

    # The approved positioning deliberately avoids direct terminology and
    # familiar visual shorthand for the excluded technology category.
    forbidden_hits = scan_forbidden_associations()
    checks["forbidden_positioning_association_hits"] = forbidden_hits
    if forbidden_hits:
        errors.append(f"Forbidden positioning associations found: {forbidden_hits}")

    all_files = sorted(path for path in ROOT.rglob("*") if is_release_file(path))
    checks["file_count_excluding_tmp"] = len(all_files)
    checks["total_bytes_excluding_tmp"] = sum(path.stat().st_size for path in all_files)

    status = "TECHNICAL_PASS" if not errors else "FAIL"
    report = {"status": status, "errors": errors, "warnings": warnings, "checks": checks}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "QA_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        '<div dir="rtl" align="right">',
        "",
        "# تقرير الفحص التقني لحزمة هوية INTAG",
        "",
        f"- **النتيجة:** {status}",
        f"- **عدد ملفات سطح التسليم:** {checks['file_count_excluding_tmp']}",
        f"- **عدد ملفات SVG:** {checks['svg_count']}",
        f"- **عدد الصور:** {checks['image_count']}",
        f"- **عدد صفحات دليل الهوية:** {next((p['pages'] for p in pdf_meta if p['file'].endswith('INTAG_Brand_Guidelines_v2.0_Logo02_Approved_Working.pdf')), 'N/A')}",
        f"- **الروابط المحلية المعطلة في HTML:** {len(broken_refs)}",
        f"- **أخطاء قراءة SVG:** {len(svg_errors)}",
        f"- **أخطاء ملفات الصور:** {len(image_errors)}",
        f"- **أخطاء غلاف اتجاه الكتابة في Markdown:** {len(rtl_errors)}",
        f"- **ارتباطات التموضع المستبعدة:** {len(forbidden_hits)}",
        "",
        "## الأخطاء",
        "",
        *(f"- {item}" for item in errors),
        "" if errors else "- لا توجد أخطاء مانعة في الفحوص الآلية.",
        "",
        "## التحذيرات",
        "",
        *(f"- {item}" for item in warnings),
        "" if warnings else "- لا توجد تحذيرات آلية.",
        "",
        "## ملاحظة",
        "",
        "هذا فحص تقني للحزمة، ولا يستبدل المراجعة البصرية، أو فحص العلامة التجارية قانونيًا، أو بروفة الطباعة، أو اعتماد مالك العلامة.",
        "",
        "</div>",
    ]
    (OUTPUT / "QA_REPORT_AR.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"status": status, "errors": len(errors), "warnings": len(warnings), "files": checks["file_count_excluding_tmp"]}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
