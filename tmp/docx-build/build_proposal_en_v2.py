from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "templates" / "proposal" / "INTAG_Proposal_Starter_AR_v2.docx"
OUTPUT = ROOT / "templates" / "proposal" / "INTAG_Proposal_Starter_EN_v2.docx"
POPPINS_DIR = ROOT / "assets" / "fonts" / "Poppins"
POPPINS_REGULAR = POPPINS_DIR / "Poppins-Regular.ttf"
POPPINS_BOLD = POPPINS_DIR / "Poppins-Bold.ttf"
EXPECTED_REFERENCE_SHA256 = "f1c4c1fab0f4d46d3d83c63f8351cc0b87a5337d95155a826f3b5538c73b25d8"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
DCTERMS = "http://purl.org/dc/terms/"
FONT_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"
HEADER_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header"
FOOTER_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"
FONT_NAME = "Poppins"
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
REMOVE_PARAGRAPH = "__INTAG_REMOVE_PARAGRAPH__"


EN_TEXT_MAP = {
    "مقترح عمل · نسخة قابلة للتحرير": "BUSINESS PROPOSAL · EDITABLE TEMPLATE",
    "[عنوان المشروع أو المبادرة]": "[ENGAGEMENT OR INITIATIVE TITLE]",
    "[وصف موجز يوضح النتيجة المطلوبة بلغة مباشرة]": "[One concise line describing the intended outcome]",
    "مقدم إلى: ": "Prepared for: ",
    "[اسم العميل أو الجهة]": "[Client or organisation]",
    "بيانات الوثيقة": "Document details",
    "المسؤولية": "Ownership",
    "التاريخ": "Date",
    "[التاريخ]": "[Date]",
    "مالك المقترح": "Proposal owner",
    "[اسم المالك]": "[Owner name]",
    "الإصدار": "Version",
    "الإعداد": "Prepared by",
    "إنتاغ للحلول الرقمية": "INTAG Digital Solutions",
    "حالة الوثيقة  ": "DOCUMENT STATUS  ",
    "اعتمد الشعار رقم 02 «الإطار المتصل». أما بقية قرارات الهوية والنطاق والتكلفة والجدول الزمني فما تزال قيد المراجعة والاعتماد.": (
        'Logo 02 “Connected Frame” is approved. All other identity, scope, investment, and timeline decisions '
        "remain under review and approval."
    ),
    "يجب استبدال كل حقل محاط بأقواس مربعة قبل مشاركة النسخة النهائية.": (
        "Replace every bracketed field before sharing the final version."
    ),
    "01 / الملخص التنفيذي": "01 / EXECUTIVE SUMMARY",
    "الملخص التنفيذي": "Executive summary",
    "يوضح هذا القسم سبب العمل والنتيجة المطلوبة وما يحتاج إلى اعتماد قبل بدء التنفيذ.": (
        "Explain why this work matters, the intended outcome, and what must be approved before delivery starts."
    ),
    "السياق": "Context",
    "[اكتب في فقرة قصيرة ما يحدث الآن، ومن يتأثر به، ولماذا يحتاج إلى معالجة في هذا التوقيت.]": (
        "[Summarise the current situation, who it affects, and why action is timely.]"
    ),
    "التحدي والنتيجة المطلوبة": "Challenge and intended outcome",
    "[صغ التحدي من منظور العمل، ثم حدد النتيجة المرغوبة من دون تحويلها إلى وعد أو نتيجة مضمونة.]": (
        "[Define the business challenge and intended outcome without implying a guarantee.]"
    ),
    "حالة المعلومات": "Evidence status",
    "التصنيف": "Classification",
    "ما يكتب هنا": "What to enter",
    "معلومة مؤكدة": "Confirmed fact",
    "[حقيقة موثقة أو قرار معتمد يمكن البناء عليه]": (
        "[Documented fact or approved decision]"
    ),
    "معلومة منقولة": "Reported information",
    "[معلومة ذكرها طرف معني ولم تُتحقق بصورة مستقلة]": (
        "[Stakeholder input not independently verified]"
    ),
    "فرضية للاختبار": "Hypothesis to test",
    "[تفسير أو اتجاه يحتاج إلى تجربة أو تحقق]": "[Interpretation requiring validation]",
    "معايير النجاح المقترحة": "Proposed success criteria",
    "[مؤشر قابل للقياس] — خط الأساس: [القيمة]، والهدف المقترح: [القيمة]، وطريقة القياس: [الطريقة].": (
        "[Measurable indicator] — Baseline: [value]; target: [value]; method: [method]."
    ),
    "[مؤشر جودة أو تجربة] — حد القبول المقترح: [الحد]، ومسؤول القياس: [المالك].": (
        "[Quality or experience indicator] — Threshold: [value]; owner: [name]."
    ),
    "تنبيه اعتماد  ": "APPROVAL NOTE  ",
    "تظل الأهداف والمؤشرات مقترحة إلى أن تُعتمد بيانات خط الأساس وطريقة القياس والمالك المسؤول.": (
        "Targets remain proposed until the baseline, method, and accountable owner are approved."
    ),
    "القرار المطلوب": "Decision required",
    "[اكتب القرار الذي تحتاجه من العميل الآن، وسبب الحاجة إليه، وصاحب الصلاحية المطلوب اعتماده.]": (
        "[State the decision needed now, why it matters, and who can approve it.]"
    ),
    "الأسئلة المفتوحة": "Open questions",
    "[السؤال المؤثر في النطاق] — المالك: [الاسم] — موعد الإجابة: [التاريخ].": (
        "[Scope question] — Owner: [name] — Due: [date]."
    ),
    "[السؤال المؤثر في القياس أو القرار] — المالك: [الاسم] — موعد الإجابة: [التاريخ].": (
        "[Measurement or approval question] — Owner: [name] — Due: [date]."
    ),
    "02 / النطاق والمنهج": "02 / SCOPE AND APPROACH",
    "النطاق والمنهج": "Scope and approach",
    "حوّل الهدف إلى مخرجات محددة ودليل قبول ومسؤول واضح. لا يبقى في النسخة النهائية إلا ما اعتمده أصحاب القرار.": (
        "Turn the objective into defined deliverables, acceptance evidence, and clear ownership. Retain only approved workstreams."
    ),
    "مجال العمل": "Workstream",
    "المخرج المقترح": "Proposed deliverable",
    "دليل القبول": "Acceptance evidence",
    "الحالة": "Status",
    "الاستراتيجية واستشارات الأعمال": "Strategy & Business Advisory",
    "[مخرج استراتيجي محدد]": "[Defined strategy deliverable]",
    "[قرار أو وثيقة اعتماد]": "[Approval record]",
    "قيد المراجعة": "Under review",
    "العلامة التجارية والإعلام": "Brand & Media",
    "[أصل بصري أو محتوى محدد]": "[Defined brand asset or content]",
    "[معايير مراجعة وقائمة أصول]": "[Review criteria and asset list]",
    "التقنية والمنتجات الرقمية": "Technology & Digital Products",
    "[حل أو منتج رقمي محدد]": "[Defined digital solution or product]",
    "[اختبار أو عرض أو تسليم موثق]": "[Documented test or handover]",
    "التسويق والنمو": "Marketing & Growth",
    "[تجربة أو حملة محددة]": "[Defined experiment or campaign]",
    "[نتيجة مقاسة أو تعلم موثق]": "[Measured result or documented learning]",
    "منهج العمل": "Delivery approach",
    "الاكتشاف والتحديد: مراجعة السياق والبيانات والقيود وتثبيت السؤال المطلوب حسمه.": (
        "Discovery and definition: Review context, evidence, and constraints; confirm the core question."
    ),
    "التصميم والتجريب: إعداد اتجاه قابل للمراجعة واختباره ضمن حدود متفق عليها.": (
        "Design and testing: Develop a reviewable direction and test it within agreed boundaries."
    ),
    "التحقق والتحسين: قياس الدليل ومراجعة الملاحظات وتصحيح الفرضيات.": (
        "Validation and refinement: Assess evidence and feedback; revise assumptions."
    ),
    "التسليم والاعتماد: توثيق المخرجات والقرارات والملكية والخطوة التالية.": (
        "Handover and approval: Document outputs, decisions, ownership, and next steps."
    ),
    "حدود النطاق": "Scope boundaries",
    "لا يدخل في النطاق إلا ما يرد صراحة في النسخة المعتمدة من هذا المقترح.": (
        "Only work stated in the approved proposal is included."
    ),
    "تظل التراخيص الخارجية والإنفاق الإعلامي والاستضافة والصيانة والتكاملات قيد التحديد ما لم تُذكر صراحة.": (
        "Licences, media spend, hosting, maintenance, and integrations are excluded unless stated."
    ),
    "أي تغيير مؤثر في النطاق أو المدة أو التكلفة يحتاج إلى قرار تغيير موثق قبل التنفيذ.": (
        "Material changes to scope, duration, or investment require written approval before delivery."
    ),
    "التبعيات والمدخلات": "Dependencies and inputs",
    "من العميل: [بيانات أو أصول أو صلاحيات أو ملاحظات لازمة].": (
        "Client [data, assets, access, feedback] · INTAG [owner, review, handover] · Third party [licence, approval, service if needed]."
    ),
    "من إنتاغ: [مالك التنفيذ ومعايير المراجعة والتسليم].": REMOVE_PARAGRAPH,
    "من طرف ثالث: [ترخيص أو موافقة أو خدمة خارجية، إن وجدت].": REMOVE_PARAGRAPH,
    "03 / الجدول الزمني والمسؤوليات": "03 / TIMELINE AND RESPONSIBILITIES",
    "الجدول الزمني والمسؤوليات": "Timeline and responsibilities",
    "تبدأ المدد بعد اكتمال المدخلات والاعتمادات المرتبطة بكل مرحلة، ولا تعد المدة التقديرية وعدًا نهائيًا قبل اعتماد النطاق.": (
        "Timing begins when each stage's inputs and approvals are complete. Durations remain indicative until scope is approved."
    ),
    "المرحلة": "Stage",
    "المدة التقديرية": "Indicative duration",
    "المخرج الرئيس": "Primary output",
    "المالك": "Owner",
    "الاكتشاف والتحديد": "Discovery and definition",
    "[عدد الأيام أو الأسابيع]": "[Number of days or weeks]",
    "ملخص الفهم والنطاق الأولي": "Validated brief and initial scope",
    "التصميم والتجريب": "Design and testing",
    "نسخة قابلة للمراجعة والاختبار": "Reviewable and testable draft",
    "التحقق والتحسين": "Validation and refinement",
    "نتائج القياس والتعديلات المتفق عليها": "Findings and agreed refinements",
    "التسليم والاعتماد": "Handover and approval",
    "حزمة التسليم وسجل القرارات": "Handover package and decision log",
    "مسؤوليات إنتاغ": "INTAG responsibilities",
    "إدارة العمل المتفق عليه، وتوضيح الافتراضات والقيود، وإبقاء القرارات قابلة للتتبع.": (
        "Manage the agreed work, clarify assumptions and constraints, and keep decisions traceable."
    ),
    "تقديم المخرجات للمراجعة وفق النطاق، وتسجيل ما يحتاج إلى اعتماد أو تدخل من طرف آخر.": (
        "Present outputs for review and record items requiring approval or third-party input."
    ),
    "مسؤوليات العميل": "Client responsibilities",
    "توفير المدخلات والصلاحيات والأصول والملاحظات في الأوقات المتفق عليها.": (
        "Provide required inputs, access, assets, and feedback on time."
    ),
    "تسمية أصحاب القرار واعتماد النطاق والمخرجات والتغييرات في صورة مكتوبة.": (
        "Name authorised decision-makers and approve scope, outputs, and changes in writing."
    ),
    "قاعدة الجدول الزمني  ": "SCHEDULE RULE  ",
    "إذا تأخر اعتماد أو مدخل أساسي، تُراجع المدة والتبعيات والأثر التجاري قبل تثبيت أي موعد جديد.": (
        "If an approval or key input is delayed, review timing, dependencies, and commercial impact before confirming a new date."
    ),
    "نقاط المراجعة": "Review gates",
    "النقطة": "Gate",
    "المعتمد": "Approver",
    "بعد الاكتشاف": "After discovery",
    "تثبيت الهدف والنطاق والقياس": "Confirm objective, scope, and measurement",
    "[الاسم]": "[Name]",
    "بعد النسخة الأولية": "After the first draft",
    "اعتماد اتجاه التحسين أو طلب تعديل محدد": "Approve the direction or request a defined change",
    "قبل التسليم": "Before handover",
    "اعتماد المخرجات والملكية والخطوة التالية": "Approve outputs, ownership, and next step",
    "04 / الاستثمار والاعتماد": "04 / INVESTMENT AND APPROVAL",
    "الاستثمار والاعتماد": "Investment and approval",
    "استخدم هذا القسم لتسجيل أساس التقدير، لا لإدخال سعر نهائي قبل اكتمال المراجعة التجارية والفنية.": (
        "Record the basis of estimate here. Add a final price only after commercial and technical review."
    ),
    "البند": "Item",
    "أساس التقدير": "Basis of estimate",
    "القيمة المقترحة": "Proposed amount",
    "أتعاب العمل": "Professional fees",
    "[النطاق والجهد والمدة]": "[Scope, effort, and duration]",
    "[قيمة تُحدد بعد المراجعة]": "[To be confirmed after review]",
    "خدمات أو تراخيص خارجية": "External services or licences",
    "[المورد والاستخدام المتوقع]": "[Supplier and expected use]",
    "[تقدير منفصل]": "[Separate estimate]",
    "الإنتاج أو الإنفاق الإعلامي": "Production or media spend",
    "[الخطة وحجم التنفيذ]": "[Plan and scale of delivery]",
    "الضرائب والمصروفات": "Taxes and expenses",
    "[وفق الاتفاق والقواعد المطبقة]": "[Agreement and applicable rules]",
    "[تُحدد تعاقديًا]": "[Defined in final agreement]",
    "أسس تجارية تحتاج إلى اعتماد": "Commercial terms requiring approval",
    "صلاحية العرض: [المدة المقترحة بعد الاعتماد].": (
        "Proposal validity: [Proposed period following approval]."
    ),
    "جدول الدفعات: [يحدده المسؤول التجاري ويعتمد كتابيًا].": (
        "Payment schedule: [Set by the commercial owner and approved in writing]."
    ),
    "شروط التغيير والإلغاء: [تراجع وتوثق في الاتفاق النهائي].": (
        "Change and cancellation: [Document in the final agreement]."
    ),
    "حدود الالتزام  ": "COMMITMENT BOUNDARY  ",
    "لا يضمن هذا المقترح مبيعات أو نموًا أو دقة أو موعد تسليم أو جاهزية تشغيلية. يصبح النطاق والتكلفة والمدة ملزمة فقط بعد اعتمادها من أصحاب الصلاحية في وثيقة نهائية.": (
        "This proposal does not guarantee sales, growth, accuracy, delivery dates, or operational readiness. Scope, investment, and timeline become binding only after authorised owners approve them in a final document."
    ),
    "الاعتماد": "Approval",
    "اعتماد العميل": "Client approval",
    "اعتماد إنتاغ": "INTAG approval",
    "الاسم: [اسم المعتمد]": "Name: [Approver name]",
    "الصفة: [الصفة]": "Title: [Role]",
    "التوقيع: [قيد الاستكمال]": "Signature: [Pending]",
    "التاريخ: [التاريخ]": "Date: [Date]",
    "الشعار 02 معتمد، وبقية القرارات قيد المراجعة": (
        "Logo 02 approved; all other decisions remain under review"
    ),
    "قالب مقترح إنتاغ  ·  قالب عمل قابل للتحرير  ·  الإصدار 2.0  ·  صفحة ": (
        "INTAG proposal template  ·  Editable working template  ·  Version 2.0  ·  Page "
    ),
    " من ": " of ",
}


def _q(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def _xml_bytes(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def _obfuscate_font(font_path: Path, font_key: uuid.UUID) -> bytes:
    data = bytearray(font_path.read_bytes())
    key = font_key.bytes_le
    for index in range(min(32, len(data))):
        data[index] ^= key[index % 16]
    return bytes(data)


def _translate_visible_text(root: etree._Element, part_name: str) -> None:
    for node in root.findall(f".//{{{W}}}t"):
        value = node.text or ""
        if value in EN_TEXT_MAP:
            node.text = EN_TEXT_MAP[value]
        elif ARABIC_RE.search(value):
            raise RuntimeError(f"Missing English translation in {part_name}: {value!r}")


def _remove_marked_paragraphs(root: etree._Element) -> None:
    for paragraph in list(root.findall(f".//{{{W}}}p")):
        text = "".join(node.text or "" for node in paragraph.findall(f".//{{{W}}}t"))
        if REMOVE_PARAGRAPH not in text:
            continue
        parent = paragraph.getparent()
        if parent is not None:
            parent.remove(paragraph)


def _set_rpr_font_ltr(r_pr: etree._Element) -> None:
    rtl = r_pr.find(_q(W, "rtl"))
    if rtl is not None:
        r_pr.remove(rtl)

    r_fonts = r_pr.find(_q(W, "rFonts"))
    if r_fonts is None:
        r_fonts = etree.Element(_q(W, "rFonts"))
        r_pr.insert(0, r_fonts)
    for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        r_fonts.attrib.pop(_q(W, attr), None)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        r_fonts.set(_q(W, attr), FONT_NAME)

    lang = r_pr.find(_q(W, "lang"))
    if lang is None:
        lang = etree.SubElement(r_pr, _q(W, "lang"))
    lang.set(_q(W, "val"), "en-US")
    lang.attrib.pop(_q(W, "eastAsia"), None)
    lang.attrib.pop(_q(W, "bidi"), None)


def _patch_ltr_typography(root: etree._Element) -> None:
    for p_pr in root.findall(f".//{{{W}}}pPr"):
        for tag in ("bidi", "mirrorIndents"):
            element = p_pr.find(_q(W, tag))
            if element is not None:
                p_pr.remove(element)
        jc = p_pr.find(_q(W, "jc"))
        if jc is not None:
            value = jc.get(_q(W, "val"))
            if value in {"right", "start"}:
                jc.set(_q(W, "val"), "left")
            elif value == "end":
                jc.set(_q(W, "val"), "right")
        ind = p_pr.find(_q(W, "ind"))
        if ind is not None and _q(W, "right") in ind.attrib and _q(W, "left") not in ind.attrib:
            ind.set(_q(W, "left"), ind.attrib.pop(_q(W, "right")))

    for r_pr in root.findall(f".//{{{W}}}rPr"):
        _set_rpr_font_ltr(r_pr)

    for run in root.findall(f".//{{{W}}}r"):
        r_pr = run.find(_q(W, "rPr"))
        if r_pr is None:
            r_pr = etree.Element(_q(W, "rPr"))
            run.insert(0, r_pr)
        _set_rpr_font_ltr(r_pr)

    for tbl_pr in root.findall(f".//{{{W}}}tblPr"):
        bidi_visual = tbl_pr.find(_q(W, "bidiVisual"))
        if bidi_visual is not None:
            tbl_pr.remove(bidi_visual)
        jc = tbl_pr.find(_q(W, "jc"))
        if jc is None:
            jc = etree.SubElement(tbl_pr, _q(W, "jc"))
        jc.set(_q(W, "val"), "left")

    for level_jc in root.findall(f".//{{{W}}}lvlJc"):
        if level_jc.get(_q(W, "val")) in {"right", "start"}:
            level_jc.set(_q(W, "val"), "left")

    for node in root.iter():
        if "descr" in node.attrib:
            node.set("descr", "INTAG Digital Solutions — approved Logo 02, Connected Frame")
        if "title" in node.attrib:
            node.set("title", "INTAG Logo 02 — Connected Frame")


def _compact_spacing(root: etree._Element, factor: float = 0.78) -> None:
    """Apply one restrained vertical rhythm to the English adaptation."""
    for spacing in root.findall(f".//{{{W}}}spacing"):
        for attribute in ("before", "after"):
            key = _q(W, attribute)
            value = spacing.get(key)
            if value and value.isdigit():
                spacing.set(key, str(max(0, round(int(value) * factor))))


def _promote_manual_page_breaks(root: etree._Element) -> None:
    """Keep the reference breaks and remove only trailing empty spacers."""
    body = root.find(_q(W, "body"))
    if body is None:
        return
    children = list(body)
    for index, child in enumerate(children):
        if child.tag != _q(W, "p"):
            continue
        has_page_break = any(
            br.get(_q(W, "type"), "textWrapping") == "page"
            for br in child.findall(f".//{{{W}}}br")
        )
        has_text = any((node.text or "").strip() for node in child.findall(f".//{{{W}}}t"))
        if not has_page_break or has_text:
            continue
        # Retain the reference break paragraph's neutral RTL mechanics. Word
        # otherwise positions the first post-cover page at the physical top
        # edge instead of the section's top margin in some desktop builds.
        p_pr = child.find(_q(W, "pPr"))
        if p_pr is None:
            p_pr = etree.Element(_q(W, "pPr"))
            child.insert(0, p_pr)
        if p_pr.find(_q(W, "bidi")) is None:
            p_pr.append(etree.Element(_q(W, "bidi")))
        jc = p_pr.find(_q(W, "jc"))
        if jc is None:
            jc = etree.SubElement(p_pr, _q(W, "jc"))
        jc.set(_q(W, "val"), "right")
        break_index = body.index(child)
        while break_index > 0:
            previous = body[break_index - 1]
            if previous.tag != _q(W, "p"):
                break
            has_visible_text = any(
                (node.text or "").strip() for node in previous.findall(f".//{{{W}}}t")
            )
            has_object = any(
                previous.findall(f".//{{{W}}}{tag}")
                for tag in ("drawing", "pict", "object", "fldChar", "sectPr", "br")
            )
            if has_visible_text or has_object:
                break
            body.remove(previous)
            break_index -= 1


def _patch_metadata(entries: dict[str, bytes]) -> None:
    root = etree.fromstring(entries["docProps/core.xml"])
    values = {
        _q(DC, "title"): "INTAG Proposal Starter — Version 2.0",
        _q(DC, "subject"): "Editable business proposal template for client engagements",
        _q(DC, "creator"): "INTAG Digital Solutions",
        _q(CP, "lastModifiedBy"): "INTAG Digital Solutions",
        _q(CP, "keywords"): "INTAG, business proposal, editable template, brand identity",
        _q(DC, "description"): "Working template. Replace all bracketed placeholders before use.",
    }
    for tag, value in values.items():
        node = root.find(tag)
        if node is None:
            node = etree.SubElement(root, tag)
        node.text = value
    entries["docProps/core.xml"] = _xml_bytes(root)


def _embed_poppins(entries: dict[str, bytes]) -> None:
    for font_path in (POPPINS_REGULAR, POPPINS_BOLD):
        if not font_path.exists():
            raise FileNotFoundError(font_path)

    font_table_name = "word/fontTable.xml"
    font_table = etree.fromstring(entries[font_table_name])
    for font_node in list(font_table):
        font_name = font_node.get(_q(W, "name"), "")
        if font_name in {"IBM Plex Sans Arabic", FONT_NAME}:
            font_table.remove(font_node)

    font_node = etree.SubElement(font_table, _q(W, "font"))
    font_node.set(_q(W, "name"), FONT_NAME)
    family = etree.SubElement(font_node, _q(W, "family"))
    family.set(_q(W, "val"), "swiss")
    charset = etree.SubElement(font_node, _q(W, "charset"))
    charset.set(_q(W, "val"), "00")
    pitch = etree.SubElement(font_node, _q(W, "pitch"))
    pitch.set(_q(W, "val"), "variable")

    rels_name = "word/_rels/fontTable.xml.rels"
    if rels_name in entries:
        rels = etree.fromstring(entries[rels_name])
    else:
        rels = etree.Element(_q(REL, "Relationships"), nsmap={None: REL})
    for relation in list(rels):
        if relation.get("Type") == FONT_REL_TYPE:
            rels.remove(relation)

    specs = (
        ("embedRegular", "rIdIntagPoppinsRegular", POPPINS_REGULAR, "Poppins-Regular.odttf"),
        ("embedBold", "rIdIntagPoppinsBold", POPPINS_BOLD, "Poppins-Bold.odttf"),
    )
    for tag, relation_id, font_path, target_name in specs:
        font_key = uuid.uuid5(uuid.NAMESPACE_URL, f"intag-v2:{font_path.name}")
        embed = etree.SubElement(font_node, _q(W, tag))
        embed.set(_q(R, "id"), relation_id)
        embed.set(_q(W, "fontKey"), "{" + str(font_key).upper() + "}")
        embed.set(_q(W, "subsetted"), "0")

        relation = etree.SubElement(rels, _q(REL, "Relationship"))
        relation.set("Id", relation_id)
        relation.set("Type", FONT_REL_TYPE)
        relation.set("Target", f"fonts/{target_name}")
        entries[f"word/fonts/{target_name}"] = _obfuscate_font(font_path, font_key)

    for name in list(entries):
        if name.startswith("word/fonts/IBMPlexSansArabic"):
            del entries[name]

    content_types = etree.fromstring(entries["[Content_Types].xml"])
    if content_types.find(f"{{{CT}}}Default[@Extension='odttf']") is None:
        default = etree.SubElement(content_types, _q(CT, "Default"))
        default.set("Extension", "odttf")
        default.set("ContentType", "application/vnd.openxmlformats-officedocument.obfuscatedFont")

    entries[font_table_name] = _xml_bytes(font_table)
    entries[rels_name] = _xml_bytes(rels)
    entries["[Content_Types].xml"] = _xml_bytes(content_types)


def _add_explicit_even_header_footer(entries: dict[str, bytes]) -> None:
    """Repeat the approved header/footer explicitly on even pages."""
    entries["word/header2.xml"] = entries["word/header1.xml"]
    entries["word/footer2.xml"] = entries["word/footer1.xml"]

    rels_name = "word/_rels/document.xml.rels"
    rels = etree.fromstring(entries[rels_name])
    specs = (
        ("rIdIntagEvenHeader", HEADER_REL_TYPE, "header2.xml"),
        ("rIdIntagEvenFooter", FOOTER_REL_TYPE, "footer2.xml"),
    )
    for relation_id, relation_type, target in specs:
        for relation in list(rels):
            if relation.get("Id") == relation_id:
                rels.remove(relation)
        relation = etree.SubElement(rels, _q(REL, "Relationship"))
        relation.set("Id", relation_id)
        relation.set("Type", relation_type)
        relation.set("Target", target)
    entries[rels_name] = _xml_bytes(rels)

    document = etree.fromstring(entries["word/document.xml"])
    for sect_pr in document.findall(f".//{{{W}}}sectPr"):
        for reference in list(sect_pr.findall(_q(W, "headerReference"))):
            if reference.get(_q(W, "type")) == "even":
                sect_pr.remove(reference)
        for reference in list(sect_pr.findall(_q(W, "footerReference"))):
            if reference.get(_q(W, "type")) == "even":
                sect_pr.remove(reference)

        even_header = etree.Element(_q(W, "headerReference"))
        even_header.set(_q(W, "type"), "even")
        even_header.set(_q(R, "id"), "rIdIntagEvenHeader")
        first_footer_index = next(
            (index for index, child in enumerate(sect_pr) if child.tag == _q(W, "footerReference")),
            len(sect_pr),
        )
        sect_pr.insert(first_footer_index, even_header)

        even_footer = etree.Element(_q(W, "footerReference"))
        even_footer.set(_q(W, "type"), "even")
        even_footer.set(_q(R, "id"), "rIdIntagEvenFooter")
        last_footer_index = max(
            (index for index, child in enumerate(sect_pr) if child.tag == _q(W, "footerReference")),
            default=-1,
        )
        sect_pr.insert(last_footer_index + 1, even_footer)
    entries["word/document.xml"] = _xml_bytes(document)

    settings = etree.fromstring(entries["word/settings.xml"])
    if settings.find(_q(W, "evenAndOddHeaders")) is None:
        settings.append(etree.Element(_q(W, "evenAndOddHeaders")))
    entries["word/settings.xml"] = _xml_bytes(settings)

    content_types = etree.fromstring(entries["[Content_Types].xml"])
    overrides = (
        (
            "/word/header2.xml",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml",
        ),
        (
            "/word/footer2.xml",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
        ),
    )
    for part_name, content_type in overrides:
        for override in list(content_types.findall(_q(CT, "Override"))):
            if override.get("PartName") == part_name:
                content_types.remove(override)
        override = etree.SubElement(content_types, _q(CT, "Override"))
        override.set("PartName", part_name)
        override.set("ContentType", content_type)
    entries["[Content_Types].xml"] = _xml_bytes(content_types)


def _audit_preflight(entries: dict[str, bytes]) -> None:
    visible_parts = [
        name
        for name in entries
        if name == "word/document.xml" or re.fullmatch(r"word/(header|footer)\d+\.xml", name)
    ]
    visible_text: list[str] = []
    for name in visible_parts:
        root = etree.fromstring(entries[name])
        visible_text.extend(node.text or "" for node in root.findall(f".//{{{W}}}t"))
        for node in root.iter():
            for attribute in ("descr", "title"):
                if node.get(attribute):
                    visible_text.append(node.get(attribute))
    joined = "\n".join(visible_text)
    core = entries["docProps/core.xml"].decode("utf-8", errors="replace")

    if ARABIC_RE.search(joined + "\n" + core):
        raise RuntimeError("Arabic text remains in visible content or core metadata.")
    prohibited = (
        r"\bA" + r"I\b",
        "Artificial " + "Intelligence",
        "Open" + "AI",
        "Chat" + "GPT",
        "Code" + "x",
        "Gem" + "ini",
    )
    for pattern in prohibited:
        if re.search(pattern, joined + "\n" + core, flags=re.IGNORECASE):
            raise RuntimeError(f"Disallowed term or tool name detected: {pattern}")
    if "Technology & Digital Products" not in joined:
        raise RuntimeError("Required technical workstream label is missing.")
    if 'Logo 02 “Connected Frame” is approved.' not in joined:
        raise RuntimeError("Approved Logo 02 status wording is missing.")


def build() -> Path:
    if not REFERENCE.exists():
        raise FileNotFoundError(REFERENCE)
    if hashlib.sha256(REFERENCE.read_bytes()).hexdigest() != EXPECTED_REFERENCE_SHA256:
        raise RuntimeError("The retained Arabic proposal reference does not match its approved SHA-256.")

    with zipfile.ZipFile(REFERENCE, "r") as source_zip:
        source_infos = source_zip.infolist()
        entries = {info.filename: source_zip.read(info.filename) for info in source_infos}

    editable_xml_parts = [
        "word/document.xml",
        "word/header1.xml",
        "word/footer1.xml",
        "word/styles.xml",
        "word/stylesWithEffects.xml",
        "word/numbering.xml",
    ]
    for part_name in editable_xml_parts:
        if part_name not in entries:
            continue
        root = etree.fromstring(entries[part_name])
        if part_name in {"word/document.xml", "word/header1.xml", "word/footer1.xml"}:
            _translate_visible_text(root, part_name)
            _remove_marked_paragraphs(root)
        _patch_ltr_typography(root)
        if part_name in {"word/document.xml", "word/styles.xml", "word/stylesWithEffects.xml"}:
            _compact_spacing(root)
        if part_name == "word/document.xml":
            _promote_manual_page_breaks(root)
        entries[part_name] = _xml_bytes(root)

    _patch_metadata(entries)
    _embed_poppins(entries)
    _add_explicit_even_header_footer(entries)
    _audit_preflight(entries)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=OUTPUT.parent, suffix=".docx", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
    try:
        original_names = {info.filename for info in source_infos}
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as output_zip:
            for info in source_infos:
                if info.filename not in entries:
                    continue
                output_zip.writestr(info, entries[info.filename])
            for name in sorted(set(entries) - original_names):
                output_zip.writestr(name, entries[name])
        shutil.move(str(temp_path), str(OUTPUT))
    finally:
        if temp_path.exists():
            temp_path.unlink()

    with zipfile.ZipFile(OUTPUT, "r") as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Corrupt DOCX member: {bad}")
        for name in archive.namelist():
            if name.endswith(".xml") or name.endswith(".rels"):
                etree.fromstring(archive.read(name))
    return OUTPUT


if __name__ == "__main__":
    print(build())
