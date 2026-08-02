from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "INTAG_Brand_Quick_Reference_v2.0_Logo02_Approved_Working.pdf"
FONTS = ROOT / "assets" / "fonts"

INK = HexColor("#0B0D10")
BLUE = HexColor("#2369B1")
BLUE_DEEP = HexColor("#134B82")
GREEN = HexColor("#2AB687")
GREEN_DEEP = HexColor("#087058")
MINERAL = HexColor("#F4F1E9")
WHITE = HexColor("#FFFFFF")
MIST = HexColor("#E8F1F2")
SLATE = HexColor("#50616F")
ALUMINUM = HexColor("#C8CED1")
CORAL = HexColor("#E95D4F")


pdfmetrics.registerFont(TTFont("Poppins", FONTS / "Poppins" / "Poppins-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-SemiBold", FONTS / "Poppins" / "Poppins-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Bold", FONTS / "Poppins" / "Poppins-Bold.ttf"))
pdfmetrics.registerFont(TTFont("PlexAR", FONTS / "IBMPlexSansArabic" / "IBMPlexSansArabic-Regular.ttf"))
pdfmetrics.registerFont(TTFont("PlexAR-SemiBold", FONTS / "IBMPlexSansArabic" / "IBMPlexSansArabic-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("PlexAR-Bold", FONTS / "IBMPlexSansArabic" / "IBMPlexSansArabic-Bold.ttf"))


def rtl(text: str) -> str:
    return get_display(arabic_reshaper.reshape(text))


def draw_ar(c: canvas.Canvas, text: str, x_right: float, y: float, font: str, size: float, color=INK) -> None:
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawRightString(x_right, y, rtl(text))


def wrap_ar(text: str, font: str, size: float, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and pdfmetrics.stringWidth(rtl(candidate), font, size) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_ar_paragraph(c: canvas.Canvas, text: str, x_right: float, y: float, max_width: float,
                      font: str = "PlexAR", size: float = 10.5, leading: float = 16, color=SLATE) -> float:
    for line in wrap_ar(text, font, size, max_width):
        draw_ar(c, line, x_right, y, font, size, color)
        y -= leading
    return y


def rounded_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill=WHITE, stroke=None, radius=15) -> None:
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(1)
    else:
        c.setStrokeColor(fill)
    c.roundRect(x, y, w, h, radius, stroke=1 if stroke else 0, fill=1)


def footer(c: canvas.Canvas, page_num: int, width: float) -> None:
    draw_ar(c, f"مرجع INTAG السريع / الإصدار 2.0 / الشعار 02 معتمد / {page_num:02d}", width - 34, 22,
            "PlexAR-SemiBold", 7.5, SLATE)
    c.setFont("Poppins-SemiBold", 7.5)
    c.setFillColor(SLATE)
    c.drawString(34, 22, "02 AUG 2026")


def page_one(c: canvas.Canvas, width: float, height: float) -> None:
    c.setFillColor(MINERAL)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    logo = ROOT / "assets" / "logo" / "png" / "INTAG_Logo_Primary_Horizontal_RGB_v1_640w.png"
    c.drawImage(str(logo), 34, height - 86, width=198, height=50, preserveAspectRatio=True, mask="auto")
    draw_ar(c, "مرجع سريع / مقترح", width - 34, height - 48, "PlexAR-SemiBold", 9, GREEN_DEEP)

    draw_ar(c, "مرجع استخدام الهوية السريع", width - 34, height - 112, "PlexAR-Bold", 28)
    draw_ar(c, "من الإمكان إلى الإنجاز.", width - 34, height - 146, "PlexAR-Bold", 24, INK)
    draw_ar(c, "أنظمة النمو تُبنى، ونتائجها تُقاس.", width - 34, height - 172,
            "PlexAR-SemiBold", 12, GREEN_DEEP)

    # Core palette.
    draw_ar(c, "الألوان الأساسية", width - 34, height - 198, "PlexAR-SemiBold", 14)
    swatches = [("أزرق INTAG", "#2369B1", BLUE, WHITE), ("أخضر INTAG", "#2AB687", GREEN, INK),
                ("الحبر الداكن", "#0B0D10", INK, WHITE), ("الأبيض الحجري", "#F4F1E9", MINERAL, INK)]
    sx, sy, sw, sh, gap = 34, height - 314, 184, 96, 13
    for index, (name, value, fill, text_color) in enumerate(swatches):
        x = sx + index * (sw + gap)
        c.setFillColor(fill)
        if index == 3:
            c.setStrokeColor(ALUMINUM)
            c.setLineWidth(0.8)
            c.roundRect(x, sy, sw, sh, 13, fill=1, stroke=1)
        else:
            c.roundRect(x, sy, sw, sh, 13, fill=1, stroke=0)
        draw_ar(c, name, x + sw - 12, sy + sh - 22, "PlexAR-SemiBold", 8, text_color)
        c.setFillColor(text_color)
        c.setFont("Poppins-Bold", 11)
        c.drawString(x + 12, sy + 14, value)

    # Usage cards.
    card_y, card_h, card_gap = 74, 170, 15
    card_w = (width - 68 - 2 * card_gap) / 3
    cards = [
        ("الشعار", "استخدم النسخة الأفقية على الخلفيات الفاتحة، والنسخة المعكوسة على الداكنة. مساحة الحماية تساوي قطر النقطة. الحد الرقمي المقترح 140 بكسل."),
        ("الخطوط", "استخدم الخطين المرفقين للعربية والإنجليزية. العناوين قوية، والنص واضح، والحروف الكبيرة للعناوين الدقيقة القصيرة فقط."),
        ("الرسالة", "ابدأ بالنتيجة والمشكلة والدليل. لا تستخدم وعودًا مضمونة عن النمو أو الإيراد أو الأداء التقني من دون دليل واعتماد."),
    ]
    for index, (title, body) in enumerate(cards):
        x = 34 + index * (card_w + card_gap)
        rounded_card(c, x, card_y, card_w, card_h, WHITE)
        c.setFillColor(GREEN)
        c.circle(x + card_w - 22, card_y + card_h - 24, 6, fill=1, stroke=0)
        draw_ar(c, title, x + card_w - 18, card_y + card_h - 52, "PlexAR-Bold", 14)
        draw_ar_paragraph(c, body, x + card_w - 18, card_y + card_h - 80, card_w - 36, size=9.5, leading=15)
    footer(c, 1, width)


def page_two(c: canvas.Canvas, width: float, height: float) -> None:
    c.setFillColor(INK)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    draw_ar(c, "الإنتاج / إتاحة القراءة / الاعتماد", width - 34, height - 46,
            "PlexAR-SemiBold", 9, GREEN)
    draw_ar(c, "قبل أي نشر أو إنتاج", width - 34, height - 92, "PlexAR-Bold", 28, MINERAL)
    draw_ar(c, "ملف صحيح لا يساوي موافقة قانونية أو بروفة إنتاج.", width - 34, height - 124, "PlexAR-SemiBold", 15, ALUMINUM)

    # Contrast cards.
    draw_ar(c, "اختبار التباين", width - 34, height - 170, "PlexAR-SemiBold", 13, MINERAL)
    contrast_cards = [
        (WHITE, BLUE, "5.63:1", "أزرق على أبيض / صالح AA"),
        (WHITE, GREEN, "2.58:1", "أخضر على أبيض / غير صالح للنص"),
        (GREEN, INK, "7.54:1", "حبر داكن على أخضر / صالح AAA"),
        (WHITE, GREEN_DEEP, "6.05:1", "أخضر عميق / صالح AA"),
    ]
    x0, y0, cw, ch, gap = 34, height - 292, 184, 92, 13
    for i, (bg, fg, ratio, label) in enumerate(contrast_cards):
        x = x0 + i * (cw + gap)
        c.setFillColor(bg)
        c.roundRect(x, y0, cw, ch, 13, fill=1, stroke=0)
        c.setFillColor(fg)
        c.setFont("Poppins-Bold", 24)
        c.drawString(x + 13, y0 + 48, "Aa")
        c.setFont("Poppins-SemiBold", 8)
        c.drawString(x + 13, y0 + 27, ratio)
        draw_ar(c, label, x + cw - 13, y0 + 12, "PlexAR", 6.5, fg)

    # Checklist columns.
    columns = [
        ("استخدم", ["ملف Logo بصيغة Vector", "نظام ألوان رقمي موحد", "بروفة فعلية للطباعة", "تسميات مع ألوان البيانات", "بديل ساكن للحركة"]),
        ("تجنّب", ["التمديد أو إعادة التلوين", "الأخضر كنص صغير على الأبيض", "مطابقة Pantone من الشاشة", "ادعاءات بلا دليل", "حقل مؤقت لم يُستبدل"]),
        ("يلزم اعتماده", ["مسؤول العلامة", "البحث القانوني والنطاقات", "الاسم العربي", "سياسة الصور والتصوير", "ملفات المورد والبروفات"]),
    ]
    card_y, card_h, card_gap = 72, 210, 15
    card_w = (width - 68 - 2 * card_gap) / 3
    for index, (title, items) in enumerate(columns):
        x = 34 + index * (card_w + card_gap)
        rounded_card(c, x, card_y, card_w, card_h, fill=HexColor("#111820"), stroke=HexColor("#33404B"))
        draw_ar(c, title, x + card_w - 18, card_y + card_h - 35, "PlexAR-Bold", 14, MINERAL)
        y = card_y + card_h - 67
        for item in items:
            c.setFillColor(GREEN if index != 1 else CORAL)
            c.circle(x + card_w - 19, y + 4, 3.2, fill=1, stroke=0)
            draw_ar(c, item, x + card_w - 30, y, "PlexAR", 9.5, ALUMINUM)
            y -= 27
    draw_ar(c, "الدليل الكامل:", width - 34, 42, "PlexAR", 7, ALUMINUM)
    c.setFillColor(ALUMINUM)
    c.setFont("Poppins", 6.5)
    c.drawString(34, 42, "output/pdf/INTAG_Brand_Guidelines_v2.0_Logo02_Approved_Working.pdf")
    footer(c, 2, width)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(A4)
    c = canvas.Canvas(str(OUT), pagesize=(width, height), pageCompression=1)
    c.setTitle("INTAG Brand Quick Reference v2.0 - Logo 02 Approved")
    c.setAuthor("INTAG Digital Solutions - Logo 02 Approved / System Working")
    page_one(c, width, height)
    c.showPage()
    page_two(c, width, height)
    c.showPage()
    c.save()
    print(OUT)


if __name__ == "__main__":
    main()
