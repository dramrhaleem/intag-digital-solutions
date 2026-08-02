from __future__ import annotations

import base64
import json
import math
import struct
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TEMPLATES = ROOT / "templates"

COLORS = {
    "ink": "#0B0D10",
    "midnight": "#071B2D",
    "blue": "#2369B1",
    "blue_deep": "#134B82",
    "green": "#2AB687",
    "green_deep": "#087058",
    "mineral": "#F4F1E9",
    "white": "#FFFFFF",
    "aluminum": "#C8CED1",
    "mist": "#E8F1F2",
    "slate": "#50616F",
    "amber": "#FFB547",
    "coral": "#E95D4F",
}

POPPINS_EXTRA = ASSETS / "fonts" / "Poppins" / "Poppins-ExtraBold.ttf"
POPPINS_BOLD = ASSETS / "fonts" / "Poppins" / "Poppins-Bold.ttf"
POPPINS_MEDIUM = ASSETS / "fonts" / "Poppins" / "Poppins-Medium.ttf"
ARABIC_REGULAR = ASSETS / "fonts" / "IBMPlexSansArabic" / "IBMPlexSansArabic-Regular.ttf"
ARABIC_MEDIUM = ASSETS / "fonts" / "IBMPlexSansArabic" / "IBMPlexSansArabic-Medium.ttf"
ARABIC_SEMIBOLD = ASSETS / "fonts" / "IBMPlexSansArabic" / "IBMPlexSansArabic-SemiBold.ttf"
ARABIC_BOLD = ASSETS / "fonts" / "IBMPlexSansArabic" / "IBMPlexSansArabic-Bold.ttf"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def svg_doc(width: int | float, height: int | float, content: str, title: str, *,
            physical_width: str | None = None, physical_height: str | None = None,
            background: str | None = None) -> str:
    width_attr = physical_width or str(width)
    height_attr = physical_height or str(height)
    bg = f'<rect width="{width}" height="{height}" fill="{background}"/>' if background else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width_attr}" height="{height_attr}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(title)}</title>
  <desc id="desc">INTAG brand system v2.0. Logo 02 Connected Frame is approved; other identity decisions remain working unless stated.</desc>
  {bg}
  {content}
</svg>
'''


def embedded_arabic_css() -> str:
    """Embed the approved Arabic family so print previews remain deterministic."""
    faces = []
    for weight, path in [
        (400, ARABIC_REGULAR),
        (500, ARABIC_MEDIUM),
        (600, ARABIC_SEMIBOLD),
        (700, ARABIC_BOLD),
    ]:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        faces.append(
            "@font-face{font-family:'INTAG Arabic';"
            f"src:url(data:font/ttf;base64,{encoded}) format('truetype');"
            f"font-style:normal;font-weight:{weight};}}"
        )
    return "<style>" + "".join(faces) + "</style>"


class OutlineFont:
    def __init__(self, path: Path):
        self.font = TTFont(path)
        self.glyph_set = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font["hmtx"].metrics
        os2 = self.font["OS/2"]
        self.cap_height = getattr(os2, "sCapHeight", 0) or int(self.font["hhea"].ascent * 0.72)

    def group(self, text: str, x: float, top: float, height: float, color: str,
              tracking: float = 0.0, manual_kern: dict[tuple[str, str], float] | None = None) -> tuple[str, float]:
        scale = height / self.cap_height
        baseline = top + height
        cursor = 0.0
        paths: list[str] = []
        manual_kern = manual_kern or {}
        for index, char in enumerate(text):
            glyph_name = self.cmap.get(ord(char))
            if not glyph_name:
                raise ValueError(f"Missing glyph for {char!r}")
            pen = SVGPathPen(self.glyph_set)
            self.glyph_set[glyph_name].draw(pen)
            commands = pen.getCommands()
            gx = x + cursor * scale
            paths.append(
                f'<path d="{commands}" fill="{color}" transform="translate({gx:.3f} {baseline:.3f}) scale({scale:.6f} {-scale:.6f})"/>'
            )
            advance = self.hmtx[glyph_name][0]
            cursor += advance
            if index < len(text) - 1:
                cursor += tracking + manual_kern.get((char, text[index + 1]), 0.0)
        return "\n".join(paths), cursor * scale


EXTRA = OutlineFont(POPPINS_EXTRA)
BOLD = OutlineFont(POPPINS_BOLD)
MEDIUM = OutlineFont(POPPINS_MEDIUM)


def symbol_markup(x: float, y: float, size: float, mode: str = "color", *, background: str | None = None) -> str:
    """Approved Logo 02 — Connected Frame.

    Two opposing right-angle frames hold a protected central node. The
    128-unit geometry is rotationally balanced, while the intentional gaps
    keep the three components distinct at every approved scale.
    """
    scale = size / 128.0
    if mode == "color":
        blue, green, node = COLORS["blue"], COLORS["green"], COLORS["ink"]
    elif mode == "reverse":
        blue, green, node = COLORS["blue"], COLORS["green"], COLORS["mineral"]
    elif mode == "white":
        blue = green = node = COLORS["white"]
    else:
        blue = green = node = COLORS["ink"]
    bg = f'<rect x="0" y="0" width="128" height="128" rx="26" fill="{background}"/>' if background else ""
    return f'''<g transform="translate({x} {y}) scale({scale:.6f})">
      {bg}
      <path d="M20 84V28H72" fill="none" stroke="{blue}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M108 44V100H56" fill="none" stroke="{green}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="64" cy="64" r="14" fill="{node}"/>
    </g>'''


def concept_a_markup(x: float, y: float, size: float) -> str:
    s = size / 128.0
    return f'''<g transform="translate({x} {y}) scale({s:.6f})">
      <path d="M18 96H64V64" fill="none" stroke="{COLORS['blue']}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M64 64V32H110" fill="none" stroke="{COLORS['green']}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="64" cy="64" r="14" fill="{COLORS['ink']}"/>
    </g>'''


def concept_c_markup(x: float, y: float, size: float) -> str:
    s = size / 128.0
    return f'''<g transform="translate({x} {y}) scale({s:.6f})">
      <path d="M18 92L54 64L18 36" fill="none" stroke="{COLORS['blue']}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M110 36L74 64L110 92" fill="none" stroke="{COLORS['green']}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="64" cy="64" r="14" fill="{COLORS['ink']}"/>
    </g>'''


def frame_device_markup(x: float, y: float, width: float, mode: str = "color", opacity: float = 1.0) -> str:
    """Wide Connected Frame device for application layouts."""
    scale = width / 800.0
    if mode == "reverse":
        blue, green, node = COLORS["blue"], COLORS["green"], COLORS["mineral"]
    elif mode == "white":
        blue = green = node = COLORS["white"]
    elif mode == "black":
        blue = green = node = COLORS["ink"]
    else:
        blue, green, node = COLORS["blue"], COLORS["green"], COLORS["ink"]
    return f'''<g transform="translate({x} {y}) scale({scale:.6f})" opacity="{opacity}">
      <path d="M28 246V54H332" fill="none" stroke="{blue}" stroke-width="32" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M772 64V256H468" fill="none" stroke="{green}" stroke-width="32" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="400" cy="155" r="19" fill="{node}"/>
    </g>'''


def wordmark_markup(x: float, top: float, height: float, color: str, *, point: bool = False) -> tuple[str, float]:
    kern = {("N", "T"): -25, ("T", "A"): -55, ("A", "G"): -20}
    group, width = EXTRA.group("INTAG", x, top, height, color, tracking=-12, manual_kern=kern)
    if point:
        radius = height * 0.085
        cx = x + width + height * 0.105 + radius
        cy = top + height - radius * 0.9
        group += f'\n<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{radius:.3f}" fill="{color}"/>'
        width += height * 0.105 + radius * 2
    return group, width


def descriptor_markup(text: str, x: float, top: float, height: float, color: str) -> tuple[str, float]:
    return MEDIUM.group(text, x, top, height, color, tracking=80)


def logo_lockup_content(mode: str = "color", *, descriptor: bool = False, point: bool = False) -> tuple[str, int, int]:
    dark = mode in {"reverse", "white"}
    word_color = COLORS["mineral"] if dark else COLORS["ink"]
    symbol_mode = "reverse" if mode == "reverse" else ("white" if mode == "white" else ("black" if mode == "black" else "color"))
    content = symbol_markup(24, 26, 128, symbol_mode)
    word, width = wordmark_markup(180, 43, 78, word_color, point=point)
    content += "\n" + word
    h = 180
    if descriptor:
        desc, _ = descriptor_markup("DIGITAL SOLUTIONS", 184, 128, 17, COLORS["aluminum"] if dark else COLORS["slate"])
        content += "\n" + desc
    w = int(180 + width + 34)
    return content, w, h


def build_logo_assets() -> None:
    logo_dir = ASSETS / "logo" / "svg"
    variants = {
        "INTAG_Symbol_Color_RGB_v1.svg": svg_doc(128, 128, symbol_markup(0, 0, 128, "color"), "INTAG Connected Frame symbol - color"),
        "INTAG_Symbol_Reverse_RGB_v1.svg": svg_doc(128, 128, symbol_markup(0, 0, 128, "reverse"), "INTAG Connected Frame symbol - reverse"),
        "INTAG_Symbol_Black_v1.svg": svg_doc(128, 128, symbol_markup(0, 0, 128, "black"), "INTAG Connected Frame symbol - black"),
        "INTAG_Symbol_White_v1.svg": svg_doc(128, 128, symbol_markup(0, 0, 128, "white"), "INTAG Connected Frame symbol - white"),
    }
    for filename, content in variants.items():
        write_text(logo_dir / filename, content)

    for mode, filename, bg in [
        ("color", "INTAG_Logo_Primary_Horizontal_RGB_v1.svg", None),
        ("reverse", "INTAG_Logo_Primary_Horizontal_Reverse_RGB_v1.svg", COLORS["ink"]),
        ("black", "INTAG_Logo_Primary_Horizontal_Black_v1.svg", None),
        ("white", "INTAG_Logo_Primary_Horizontal_White_v1.svg", COLORS["ink"]),
    ]:
        content, w, h = logo_lockup_content(mode, descriptor=False)
        write_text(logo_dir / filename, svg_doc(w, h, content, filename.removesuffix(".svg"), background=bg))

    for mode, filename, bg in [
        ("color", "INTAG_Logo_Descriptor_EN_RGB_v1.svg", None),
        ("reverse", "INTAG_Logo_Descriptor_EN_Reverse_RGB_v1.svg", COLORS["ink"]),
    ]:
        content, w, h = logo_lockup_content(mode, descriptor=True)
        write_text(logo_dir / filename, svg_doc(w, h, content, filename.removesuffix(".svg"), background=bg))

    for color_name, color, filename, bg in [
        ("Ink", COLORS["ink"], "INTAG_Wordmark_Ink_v1.svg", None),
        ("White", COLORS["white"], "INTAG_Wordmark_White_v1.svg", COLORS["ink"]),
    ]:
        word, width = wordmark_markup(20, 20, 110, color, point=True)
        write_text(logo_dir / filename, svg_doc(width + 40, 150, word, f"INTAG wordmark {color_name}", background=bg))

    # Stacked lockups.
    for mode, filename, bg in [
        ("color", "INTAG_Logo_Stacked_RGB_v1.svg", None),
        ("reverse", "INTAG_Logo_Stacked_Reverse_RGB_v1.svg", COLORS["ink"]),
    ]:
        word_color = COLORS["mineral"] if mode == "reverse" else COLORS["ink"]
        mark = symbol_markup(156, 24, 128, mode)
        word, ww = wordmark_markup((440 - 300) / 2, 174, 74, word_color, point=False)
        # Re-center using the actual width.
        word, ww = wordmark_markup((440 - ww) / 2, 174, 74, word_color, point=False)
        desc, dw = descriptor_markup("DIGITAL SOLUTIONS", (440 - 222) / 2, 264, 15, COLORS["aluminum"] if mode == "reverse" else COLORS["slate"])
        write_text(logo_dir / filename, svg_doc(440, 320, mark + word + desc, filename.removesuffix(".svg"), background=bg))

    # Small-size optical variants. Both right-angle frames remain separate and
    # every anchor is integer-aligned so the symbol stays legible at 16/24/32 px.
    def small_symbol(node_color: str) -> str:
        return f'''<g>
          <path d="M5 21V7H19" fill="none" stroke="{COLORS['blue']}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M27 11V25H13" fill="none" stroke="{COLORS['green']}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="16" cy="16" r="3.25" fill="{node_color}"/>
        </g>'''
    write_text(
        logo_dir / "INTAG_Symbol_Small_RGB_v1.svg",
        svg_doc(32, 32, small_symbol(COLORS["ink"]), "INTAG small-size symbol for light backgrounds"),
    )
    write_text(
        logo_dir / "INTAG_Symbol_Small_Reverse_RGB_v1.svg",
        svg_doc(32, 32, small_symbol(COLORS["mineral"]), "INTAG small-size symbol for dark backgrounds"),
    )

    # Social/avatar masters.
    avatar = symbol_markup(112, 112, 288, "reverse")
    write_text(logo_dir / "INTAG_Avatar_Dark_RGB_v1.svg", svg_doc(512, 512, avatar, "INTAG dark social avatar", background=COLORS["ink"]))
    app_icon = f'''<rect x="32" y="32" width="448" height="448" rx="112" fill="{COLORS['ink']}"/>{symbol_markup(128, 128, 256, 'reverse')}'''
    write_text(logo_dir / "INTAG_AppIcon_RGB_v1.svg", svg_doc(512, 512, app_icon, "INTAG app icon"))
    maskable_icon = f'''<rect width="512" height="512" fill="{COLORS['ink']}"/>{symbol_markup(128, 128, 256, 'reverse')}'''
    write_text(logo_dir / "INTAG_AppIcon_Maskable_RGB_v1.svg", svg_doc(512, 512, maskable_icon, "INTAG maskable app icon"))

    # Concept decision board. Logo 02 is the approved symbol decision.
    board = f'''
      {embedded_arabic_css()}
      <rect x="40" y="40" width="340" height="340" rx="24" fill="{COLORS['white']}"/>
      <rect x="410" y="40" width="340" height="340" rx="24" fill="{COLORS['white']}" stroke="{COLORS['green_deep']}" stroke-width="4"/>
      <rect x="780" y="40" width="340" height="340" rx="24" fill="{COLORS['white']}"/>
      {concept_a_markup(130, 88, 160)}{symbol_markup(500, 88, 160, 'color')}{concept_c_markup(870, 88, 160)}
      <text x="210" y="318" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="22" font-weight="700" text-anchor="middle" direction="rtl">الخيار 01</text>
      <text x="580" y="318" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="22" font-weight="700" text-anchor="middle">Connected Frame</text>
      <text x="950" y="318" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="22" font-weight="700" text-anchor="middle" direction="rtl">الخيار 03</text>
      <circle cx="436" cy="66" r="8" fill="{COLORS['green']}"/>
      <text x="210" y="352" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="17" text-anchor="middle" direction="rtl">مؤرشف</text>
      <text x="580" y="352" fill="{COLORS['green_deep']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="17" font-weight="700" text-anchor="middle" direction="rtl">معتمد — الشعار 02</text>
      <text x="950" y="352" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="17" text-anchor="middle" direction="rtl">مؤرشف</text>
    '''
    write_text(logo_dir / "INTAG_Logo_Concepts_v1.svg", svg_doc(1160, 420, board, "INTAG logo concept comparison", background=COLORS["mineral"]))

    # Construction and clear-space sheet.
    primary, w, _ = logo_lockup_content("color", descriptor=False)
    x_unit = 20
    construction = f'''
      {embedded_arabic_css()}
      <g opacity=".18" stroke="{COLORS['slate']}" stroke-width="1">
        {''.join(f'<path d="M0 {i}H900"/>' for i in range(0, 520, 20))}
        {''.join(f'<path d="M{i} 0V520"/>' for i in range(0, 920, 20))}
      </g>
      <g transform="translate(70 120)">{primary}</g>
      <rect x="42" y="92" width="{w + x_unit * 2}" height="236" fill="none" stroke="{COLORS['green_deep']}" stroke-width="2" stroke-dasharray="8 8"/>
      <text x="42" y="72" fill="{COLORS['green_deep']}" font-family="Poppins, Arial, sans-serif" font-size="20" font-weight="600">Clear Space = X = frame stroke width</text>
      <line x1="42" y1="105" x2="70" y2="105" stroke="{COLORS['green_deep']}" stroke-width="2"/>
      <text x="56" y="98" fill="{COLORS['green_deep']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="17" text-anchor="middle" direction="rtl">س</text>
      <text x="42" y="390" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="21" font-weight="700">Minimum horizontal width: 160 px / 32 mm</text>
      <text x="42" y="425" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="17">Use the Small-size version from 16 to 32 px. Confirm print minimums with a supplier proof.</text>
    '''
    write_text(logo_dir / "INTAG_Logo_Construction_v1.svg", svg_doc(900, 520, construction, "INTAG logo construction and clear space", background=COLORS["mineral"]))

    # Keep stable v1 filenames for existing document links, and publish explicit
    # v2 aliases for the approved Logo 02 decision.
    v2_alias_sources = [
        "INTAG_Symbol_Color_RGB_v1.svg",
        "INTAG_Symbol_Reverse_RGB_v1.svg",
        "INTAG_Symbol_Black_v1.svg",
        "INTAG_Symbol_White_v1.svg",
        "INTAG_Symbol_Small_RGB_v1.svg",
        "INTAG_Symbol_Small_Reverse_RGB_v1.svg",
        "INTAG_Logo_Primary_Horizontal_RGB_v1.svg",
        "INTAG_Logo_Primary_Horizontal_Reverse_RGB_v1.svg",
        "INTAG_Logo_Primary_Horizontal_Black_v1.svg",
        "INTAG_Logo_Primary_Horizontal_White_v1.svg",
        "INTAG_Logo_Descriptor_EN_RGB_v1.svg",
        "INTAG_Logo_Descriptor_EN_Reverse_RGB_v1.svg",
        "INTAG_Logo_Stacked_RGB_v1.svg",
        "INTAG_Logo_Stacked_Reverse_RGB_v1.svg",
        "INTAG_Wordmark_Ink_v1.svg",
        "INTAG_Wordmark_White_v1.svg",
        "INTAG_Avatar_Dark_RGB_v1.svg",
        "INTAG_AppIcon_RGB_v1.svg",
        "INTAG_AppIcon_Maskable_RGB_v1.svg",
        "INTAG_Logo_Concepts_v1.svg",
        "INTAG_Logo_Construction_v1.svg",
    ]
    for source_name in v2_alias_sources:
        target_name = source_name.replace("_v1.svg", "_v2.svg")
        write_text(logo_dir / target_name, (logo_dir / source_name).read_text(encoding="utf-8").replace("_v1", "_v2"))


def build_patterns() -> None:
    pattern_dir = ASSETS / "patterns"
    tile = f'''
      <defs>
        <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="1.5" fill="{COLORS['slate']}" opacity=".22"/>
        </pattern>
      </defs>
      <rect width="512" height="512" fill="url(#grid)"/>
      <path d="M-18 304V54H274" fill="none" stroke="{COLORS['blue']}" stroke-width="34" stroke-linecap="round" stroke-linejoin="round" opacity=".95"/>
      <path d="M530 208V458H238" fill="none" stroke="{COLORS['green']}" stroke-width="34" stroke-linecap="round" stroke-linejoin="round" opacity=".92"/>
      <circle cx="256" cy="256" r="21" fill="{COLORS['ink']}"/>
    '''
    light_svg = svg_doc(512, 512, tile, "INTAG Connected Frame pattern - light", background=COLORS["mineral"])
    write_text(pattern_dir / "INTAG_Pattern_ProductionGrid_Light_v1.svg", light_svg)
    write_text(pattern_dir / "INTAG_Pattern_ConnectedFrame_Light_v2.svg", light_svg)
    dark_tile = tile.replace(COLORS["slate"], COLORS["aluminum"]).replace(COLORS["ink"], COLORS["mineral"])
    dark_svg = svg_doc(512, 512, dark_tile, "INTAG Connected Frame pattern - dark", background=COLORS["ink"])
    write_text(pattern_dir / "INTAG_Pattern_ProductionGrid_Dark_v1.svg", dark_svg)
    write_text(pattern_dir / "INTAG_Pattern_ConnectedFrame_Dark_v2.svg", dark_svg)
    flow = f'''
      <path d="M28 246V54H332" fill="none" stroke="{COLORS['blue']}" stroke-width="32" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M772 64V256H468" fill="none" stroke="{COLORS['green']}" stroke-width="32" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="400" cy="155" r="19" fill="{COLORS['ink']}"/>
    '''
    device_svg = svg_doc(800, 310, flow, "INTAG Connected Frame graphic device")
    write_text(pattern_dir / "INTAG_GraphicDevice_ProductionPath_v1.svg", device_svg)
    write_text(pattern_dir / "INTAG_GraphicDevice_ConnectedFrame_v2.svg", device_svg)


ICON_SPECS = {
    "Strategy_Business": '<path d="M4 18V6h8l4 4h4v8H4Z"/><path d="M12 6v6h8"/><circle cx="12" cy="12" r="2.2" class="node"/>',
    "Brand_Media": '<path d="m12 3 7 7-7 11-7-11 7-7Z"/><path d="m9.5 8 5 4-5 4V8Z"/><circle cx="19" cy="10" r="2.2" class="node"/>',
    "Technology_DigitalProducts": '<path d="m8 5-5 7 5 7"/><path d="m16 5 5 7-5 7"/><path d="m14 4-4 16"/><circle cx="12" cy="12" r="2.2" class="node"/>',
    "Growth_Activation": '<path d="M4 19h5v-4h5v-4h6"/><path d="m17 8 3 3-3 3"/><circle cx="20" cy="11" r="2.2" class="node"/>',
    "Development": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/><circle cx="12" cy="12" r="2.2" class="node"/>',
    "Consulting": '<path d="M4 5h11v9H9l-4 4v-4H4V5Z"/><path d="M15 9h5v9h-2v3l-3-3h-4"/><circle cx="15" cy="9" r="2.2" class="node"/>',
    "Data": '<path d="M5 19V9h4v10H5Zm6 0V5h4v14h-4Zm6 0v-7h4v7h-4Z"/><circle cx="15" cy="5" r="2.2" class="node"/>',
    "Workflow": '<path d="M5 6h7v6h7v6"/><path d="M5 18h7v-6"/><circle cx="5" cy="6" r="2.2" class="node"/><circle cx="19" cy="18" r="2.2" class="node"/>',
    "Research": '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/><circle cx="10" cy="10" r="2.2" class="node"/>',
    "Delivery": '<path d="M3 7h12v11H3V7Zm12 4h4l2 3v4h-6v-7Z"/><circle cx="7" cy="19" r="2.2"/><circle cx="18" cy="19" r="2.2"/><circle cx="15" cy="11" r="2.2" class="node"/>',
    "Partnership": '<path d="m8 12 3 3 5-5"/><path d="M4 9 8 5l4 2 4-2 4 4-8 10L4 9Z"/><circle cx="12" cy="15" r="2.2" class="node"/>',
    "Support": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="m6 6 3 3m6 6 3 3m0-12-3 3m-6 6-3 3"/><circle cx="12" cy="12" r="2.2" class="node"/>',
}

ICON_LABELS_EN = {
    "Strategy_Business": ("Strategy &", "Business"),
    "Brand_Media": ("Brand & Media",),
    "Technology_DigitalProducts": ("Technology &", "Digital Products"),
    "Growth_Activation": ("Growth &", "Activation"),
    "Development": ("Development",),
    "Consulting": ("Consulting",),
    "Data": ("Data",),
    "Workflow": ("Workflow",),
    "Research": ("Research",),
    "Delivery": ("Delivery",),
    "Partnership": ("Partnership",),
    "Support": ("Support",),
}


def build_icons() -> None:
    icon_dir = ASSETS / "icons"
    for name, paths in ICON_SPECS.items():
        content = f'''<style>.node{{fill:{COLORS['green']};stroke:none}}</style><g fill="none" stroke="{COLORS['ink']}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{paths}</g>'''
        icon_title = "Technology and Digital Products" if name == "Technology_DigitalProducts" else name.replace("_", " ")
        icon_svg = svg_doc(24, 24, content, f"INTAG {icon_title} icon")
        write_text(icon_dir / f"INTAG_Icon_{name}_v1.svg", icon_svg)
        write_text(icon_dir / f"INTAG_Icon_{name}_v2.svg", icon_svg)
    # Contact sheet.
    cells = [embedded_arabic_css()]
    for index, (name, paths) in enumerate(ICON_SPECS.items()):
        col, row = index % 4, index // 4
        x, y = 54 + col * 240, 46 + row * 190
        label_lines = ICON_LABELS_EN[name]
        label_markup = "".join(
            f'<tspan x="95" y="{112 + line_index * 24 if len(label_lines) > 1 else 126}">{escape(line)}</tspan>'
            for line_index, line in enumerate(label_lines)
        )
        cells.append(f'''<g transform="translate({x} {y})">
          <rect width="190" height="142" rx="18" fill="{COLORS['white']}"/>
          <g transform="translate(63 20) scale(2.7)"><style>.node{{fill:{COLORS['green']};stroke:none}}</style><g fill="none" stroke="{COLORS['ink']}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{paths}</g></g>
          <text fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="20" font-weight="600" text-anchor="middle">{label_markup}</text>
        </g>''')
    contact_sheet = svg_doc(1020, 640, "".join(cells), "INTAG icon library contact sheet", background=COLORS["mineral"])
    write_text(icon_dir / "INTAG_IconLibrary_ContactSheet_v1.svg", contact_sheet)
    write_text(icon_dir / "INTAG_IconLibrary_ContactSheet_v2.svg", contact_sheet)


def logo_for_template(x: float, y: float, scale: float = 1.0, reverse: bool = False) -> str:
    mode = "reverse" if reverse else "color"
    word_color = COLORS["mineral"] if reverse else COLORS["ink"]
    mark = symbol_markup(x, y, 96 * scale, mode)
    word, _ = wordmark_markup(x + 116 * scale, y + 18 * scale, 58 * scale, word_color, point=False)
    return mark + word


def build_templates() -> None:
    # Business card. Stable trim masters remain available to existing links;
    # v2 print masters add 3 mm bleed around the 90 x 50 mm finished size.
    card_font = embedded_arabic_css()
    front_logo, front_logo_width, _ = logo_lockup_content("reverse", descriptor=False)
    front_logo_scale = .78
    front_logo_x = (900 - front_logo_width * front_logo_scale) / 2

    def card_front_art() -> str:
        return f'''
          {card_font}
          <g transform="translate({front_logo_x:.2f} 124) scale({front_logo_scale})">{front_logo}</g>
          <line x1="318" y1="360" x2="582" y2="360" stroke="{COLORS['green']}" stroke-width="4"/>
          <text x="450" y="416" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="23" font-weight="500" text-anchor="middle" direction="rtl">نبني الأنظمة التي يحتاج إليها النمو.</text>
        '''

    def card_back_art() -> str:
        return f'''
          {card_font}
          <g opacity=".055">{symbol_markup(-34, 288, 250, 'black')}</g>
          {symbol_markup(62, 56, 78, 'color')}
          <text x="838" y="156" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="36" font-weight="700" text-anchor="start" direction="rtl">[الاسم الكامل]</text>
          <text x="838" y="203" fill="{COLORS['green_deep']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="21" font-weight="600" text-anchor="start" direction="rtl">[المسمّى الوظيفي]</text>
          <line x1="62" y1="258" x2="838" y2="258" stroke="{COLORS['aluminum']}" stroke-width="2"/>
          <text x="838" y="330" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="18" font-weight="500" text-anchor="start" direction="rtl">[البريد الإلكتروني]   •   [رقم الهاتف]</text>
          <text x="838" y="371" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="18" font-weight="500" text-anchor="start" direction="rtl">[الموقع الإلكتروني]</text>
          <path d="M62 440H116V410" fill="none" stroke="{COLORS['blue']}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M188 388V440H134" fill="none" stroke="{COLORS['green']}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="125" cy="425" r="7" fill="{COLORS['ink']}"/>
        '''

    front = card_front_art()
    back = card_back_art()
    write_text(TEMPLATES / "stationery" / "INTAG_BusinessCard_Front_90x50mm_v1.svg", svg_doc(900, 500, front, "INTAG business card front — Logo 02", physical_width="90mm", physical_height="50mm", background=COLORS["ink"]))
    write_text(TEMPLATES / "stationery" / "INTAG_BusinessCard_Back_90x50mm_v1.svg", svg_doc(900, 500, back, "INTAG business card back — Logo 02", physical_width="90mm", physical_height="50mm", background=COLORS["mineral"]))

    print_meta = '''<metadata>Finished size: 90 × 50 mm. Artwork size: 96 × 56 mm. Bleed: 3 mm on every edge. Keep essential content at least 5 mm inside trim. Supplier proof governs final production.</metadata>'''
    bleed_front = print_meta + f'<rect width="960" height="560" fill="{COLORS["ink"]}"/><g transform="translate(30 30)">{front}</g>'
    bleed_back = print_meta + f'<rect width="960" height="560" fill="{COLORS["mineral"]}"/><g transform="translate(30 30)">{back}</g>'
    write_text(TEMPLATES / "stationery" / "INTAG_BusinessCard_Front_90x50mm_Bleed3mm_v2.svg", svg_doc(960, 560, bleed_front, "INTAG business card front print master v2", physical_width="96mm", physical_height="56mm"))
    write_text(TEMPLATES / "stationery" / "INTAG_BusinessCard_Back_90x50mm_Bleed3mm_v2.svg", svg_doc(960, 560, bleed_back, "INTAG business card back print master v2", physical_width="96mm", physical_height="56mm"))

    # A4 letterhead.
    letter = f'''
      {card_font}
      {logo_for_template(126, 116, 1.25, False)}
      <path d="M132 446H1968" stroke="{COLORS['aluminum']}" stroke-width="3"/>
      <text x="1968" y="590" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="40" text-anchor="start" direction="rtl">[التاريخ]</text>
      <text x="1968" y="730" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="52" font-weight="700" text-anchor="start" direction="rtl">[عنوان المستند]</text>
      <text x="1968" y="824" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="30" text-anchor="start" direction="rtl">[الجهة المستلمة / الموضوع]</text>
      <rect x="126" y="2660" width="1848" height="112" rx="20" fill="{COLORS['mist']}"/>
      <text x="1906" y="2728" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="24" text-anchor="start" direction="rtl">[الاسم القانوني]   •   [العنوان]   •   [البريد الإلكتروني]   •   [الموقع الإلكتروني]</text>
      <circle cx="170" cy="2717" r="18" fill="{COLORS['ink']}"/>
    '''
    write_text(TEMPLATES / "stationery" / "INTAG_Letterhead_A4_v1.svg", svg_doc(2100, 2970, letter, "INTAG A4 letterhead", physical_width="210mm", physical_height="297mm", background=COLORS["white"]))

    # Proposal cover.
    proposal = f'''
      {card_font}
      {frame_device_markup(-90, 1660, 2280, 'color')}
      {logo_for_template(136, 120, 1.35, False)}
      <text x="136" y="780" fill="{COLORS['green_deep']}" font-family="Poppins, Arial, sans-serif" font-size="38" font-weight="600">PROPOSAL FOR [CLIENT]</text>
      <text x="136" y="1070" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="96" font-weight="700">[OUTCOME-LED PROJECT TITLE]</text>
      <text x="136" y="1308" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="38">Prepared for [CLIENT]   •   [DATE]   •   Working draft</text>
    '''
    write_text(TEMPLATES / "proposal" / "INTAG_Proposal_Cover_A4_v1.svg", svg_doc(2100, 2970, proposal, "INTAG proposal cover", physical_width="210mm", physical_height="297mm", background=COLORS["mineral"]))

    # Social square.
    square = f'''
      {card_font}
      {symbol_markup(822, 74, 170, 'reverse')}
      <text x="74" y="104" fill="{COLORS['aluminum']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="end" direction="rtl">رؤية من INTAG</text>
      <text x="1006" y="420" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="88" font-weight="700" text-anchor="start" direction="rtl">منظومات النمو</text>
      <text x="1006" y="548" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="88" font-weight="700" text-anchor="start" direction="rtl">تُبنى بوضوح.</text>
      <text x="1006" y="646" fill="{COLORS['green']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="42" font-weight="600" text-anchor="start" direction="rtl">والنتائج تُقاس.</text>
      {frame_device_markup(-40, 680, 1160, 'reverse')}
    '''
    write_text(TEMPLATES / "social" / "INTAG_Social_Square_1080_v1.svg", svg_doc(1080, 1080, square, "INTAG social square template", background=COLORS["ink"]))

    portrait = f'''
      {card_font}
      <rect x="60" y="60" width="960" height="1230" rx="34" fill="none" stroke="{COLORS['aluminum']}" stroke-width="2" opacity=".45"/>
      {logo_for_template(92, 84, .72, False)}
      <text x="988" y="430" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="86" font-weight="700" text-anchor="start" direction="rtl">منظومة نمو</text>
      <text x="988" y="550" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="86" font-weight="700" text-anchor="start" direction="rtl">واحدة.</text>
      <text x="988" y="654" fill="{COLORS['green_deep']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="29" font-weight="600" text-anchor="start" direction="rtl">استراتيجية   •   علامة تجارية   •   تقنية   •   تسويق ونمو</text>
      {frame_device_markup(-40, 840, 1160, 'color')}
    '''
    write_text(TEMPLATES / "social" / "INTAG_Social_Portrait_1080x1350_v1.svg", svg_doc(1080, 1350, portrait, "INTAG social portrait template", background=COLORS["mineral"]))

    story = f'''
      {card_font}
      {symbol_markup(816, 82, 182, 'reverse')}
      <text x="84" y="136" fill="{COLORS['aluminum']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="end" direction="rtl">ملاحظة من مشروع</text>
      <text x="996" y="570" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="98" font-weight="700" text-anchor="start" direction="rtl">من نشاط متفرّق</text>
      <text x="996" y="708" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="98" font-weight="700" text-anchor="start" direction="rtl">إلى منظومة</text>
      <text x="996" y="846" fill="{COLORS['green']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="98" font-weight="700" text-anchor="start" direction="rtl">واحدة.</text>
      <rect x="84" y="1010" width="912" height="356" rx="34" fill="{COLORS['midnight']}" stroke="{COLORS['slate']}" stroke-width="2"/>
      <text x="944" y="1100" fill="{COLORS['aluminum']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="28" text-anchor="start" direction="rtl">[التحدّي]</text>
      <text x="944" y="1194" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="46" font-weight="600" text-anchor="start" direction="rtl">[نتيجة مدعومة بدليل]</text>
      <text x="944" y="1280" fill="{COLORS['green']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="28" text-anchor="start" direction="rtl">[مؤشر / دليل]</text>
      {frame_device_markup(-40, 1460, 1160, 'reverse')}
    '''
    write_text(TEMPLATES / "social" / "INTAG_Story_1080x1920_v1.svg", svg_doc(1080, 1920, story, "INTAG story template", background=COLORS["ink"]))

    # Presentation cover and content slide.
    cover = f'''
      {card_font}
      {logo_for_template(106, 84, .85, False)}
      <text x="106" y="410" fill="{COLORS['green_deep']}" font-family="Poppins, Arial, sans-serif" font-size="34" font-weight="600">[DECK TYPE]   •   [DATE]</text>
      <text x="106" y="590" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="88" font-weight="700">[PRESENTATION TITLE]</text>
      <text x="106" y="688" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="42">[ONE CLEAR OUTCOME-LED SUBTITLE]</text>
      <g opacity=".92">{symbol_markup(1240, 334, 560, 'color')}</g>
    '''
    write_text(TEMPLATES / "presentation" / "INTAG_Presentation_Cover_16x9_v1.svg", svg_doc(1920, 1080, cover, "INTAG presentation cover", background=COLORS["mineral"]))
    content = f'''
      {card_font}
      {symbol_markup(1740, 46, 110, 'color')}
      <text x="92" y="94" fill="{COLORS['green_deep']}" font-family="Poppins, Arial, sans-serif" font-size="26" font-weight="600">SECTION / 01</text>
      <text x="92" y="235" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="62" font-weight="700">[ANSWER-FIRST SLIDE TITLE]</text>
      <rect x="92" y="340" width="1100" height="560" rx="28" fill="{COLORS['white']}"/>
      <text x="140" y="430" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="30">[MAIN EVIDENCE / CHART / DIAGRAM]</text>
      <rect x="1240" y="340" width="588" height="260" rx="28" fill="{COLORS['ink']}"/>
      <text x="1288" y="423" fill="{COLORS['green']}" font-family="Poppins, Arial, sans-serif" font-size="28" font-weight="600">TAKEAWAY</text>
      <text x="1288" y="503" fill="{COLORS['mineral']}" font-family="Poppins, Arial, sans-serif" font-size="43" font-weight="700">[ONE USEFUL INSIGHT]</text>
      <rect x="1240" y="630" width="588" height="270" rx="28" fill="{COLORS['mist']}"/>
      <text x="1288" y="714" fill="{COLORS['blue_deep']}" font-family="Poppins, Arial, sans-serif" font-size="28" font-weight="600">NEXT DECISION</text>
      <text x="1288" y="796" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="34" font-weight="600">[OWNER / ACTION / DATE]</text>
      <text x="92" y="1010" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="22">INTAG Digital Solutions   •   Confidential working draft   •   01</text>
    '''
    write_text(TEMPLATES / "presentation" / "INTAG_Presentation_Content_16x9_v1.svg", svg_doc(1920, 1080, content, "INTAG presentation content slide", background=COLORS["mineral"]))

    # Website hero style tile.
    web = f'''
      {card_font}
      <rect x="0" y="0" width="1440" height="900" fill="{COLORS['mineral']}"/>
      {logo_for_template(82, 54, .68, False)}
      <text x="1358" y="108" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="22" text-anchor="start" direction="rtl">أعمالنا   •   قدراتنا   •   من نحن   •   تواصل معنا</text>
      <text x="650" y="342" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="62" font-weight="700" text-anchor="start" direction="rtl">نبني الأنظمة التي</text>
      <text x="650" y="430" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="62" font-weight="700" text-anchor="start" direction="rtl">يحتاج إليها النمو.</text>
      <text x="650" y="520" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="24" text-anchor="start" direction="rtl">استراتيجية، علامة تجارية، تقنية، وتسويق ونمو.</text>
      <rect x="82" y="580" width="318" height="62" rx="31" fill="{COLORS['ink']}"/>
      <text x="241" y="621" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="22" font-weight="600" text-anchor="middle" direction="rtl">ابدأ الحوار</text>
      <g opacity=".92">{symbol_markup(870, 230, 440, 'color')}</g>
    '''
    write_text(TEMPLATES / "digital" / "INTAG_Website_Hero_1440_v1.svg", svg_doc(1440, 900, web, "INTAG website hero style tile"))

    # Roll-up banner: finished size 850 × 2000 mm with 3 mm bleed.
    # The clean print master has no visible guides. A separate production-guide
    # file documents trim, safety, and the retractable-hardware reserve.
    rollup_logo, rollup_logo_width, _ = logo_lockup_content("color", descriptor=False)
    rollup_logo_scale = .62

    def rollup_trim_art() -> str:
        return f'''
          {card_font}
          <rect width="850" height="2000" fill="{COLORS['mineral']}"/>
          <g transform="translate(42 44) scale({rollup_logo_scale})">{rollup_logo}</g>

          <text x="792" y="318" fill="{COLORS['blue_deep']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="29" font-weight="600" text-anchor="start" direction="rtl">من الفكرة إلى منظومة نمو متكاملة</text>
          <text x="792" y="470" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="70" font-weight="700" text-anchor="start" direction="rtl">نبني الأنظمة</text>
          <text x="792" y="568" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="70" font-weight="700" text-anchor="start" direction="rtl">التي يحتاج إليها</text>
          <text x="792" y="666" fill="{COLORS['green_deep']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="70" font-weight="700" text-anchor="start" direction="rtl">النمو.</text>
          <text x="792" y="772" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="28" font-weight="400" text-anchor="start" direction="rtl">نجمع مجالات خبرتنا في مسار واحد واضح،</text>
          <text x="792" y="816" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="28" font-weight="400" text-anchor="start" direction="rtl">من التخطيط إلى التنفيذ والقياس.</text>

          <rect x="54" y="934" width="742" height="548" rx="28" fill="{COLORS['ink']}"/>
          <line x1="425" y1="990" x2="425" y2="1426" stroke="{COLORS['slate']}" stroke-width="2" opacity=".72"/>
          <line x1="110" y1="1208" x2="740" y2="1208" stroke="{COLORS['slate']}" stroke-width="2" opacity=".72"/>

          <text x="610" y="1035" fill="{COLORS['green']}" font-family="Poppins, Arial, sans-serif" font-size="19" font-weight="700" text-anchor="middle">01</text>
          <text x="610" y="1094" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="middle" direction="rtl">الاستراتيجية</text>
          <text x="610" y="1134" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="middle" direction="rtl">واستشارات الأعمال</text>
          <text x="240" y="1035" fill="{COLORS['green']}" font-family="Poppins, Arial, sans-serif" font-size="19" font-weight="700" text-anchor="middle">02</text>
          <text x="240" y="1094" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="middle" direction="rtl">العلامة التجارية</text>
          <text x="240" y="1134" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="middle" direction="rtl">والإعلام</text>
          <text x="610" y="1309" fill="{COLORS['green']}" font-family="Poppins, Arial, sans-serif" font-size="19" font-weight="700" text-anchor="middle">03</text>
          <text x="610" y="1366" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="middle" direction="rtl">التقنية والمنتجات</text>
          <text x="610" y="1408" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="middle" direction="rtl">الرقمية</text>
          <text x="240" y="1309" fill="{COLORS['green']}" font-family="Poppins, Arial, sans-serif" font-size="19" font-weight="700" text-anchor="middle">04</text>
          <text x="240" y="1366" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="middle" direction="rtl">التسويق</text>
          <text x="240" y="1408" fill="{COLORS['mineral']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="middle" direction="rtl">والنمو</text>

          <text x="792" y="1612" fill="{COLORS['green_deep']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="26" font-weight="600" text-anchor="start" direction="rtl">لنبدأ بحوار واضح حول ما يحتاجه عملك.</text>
          <text x="792" y="1688" fill="{COLORS['ink']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="38" font-weight="700" text-anchor="start" direction="rtl">[الموقع الإلكتروني]</text>
          <text x="792" y="1738" fill="{COLORS['slate']}" font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="22" font-weight="500" text-anchor="start" direction="rtl">[رمز الاستجابة السريعة]</text>
          <rect x="54" y="1592" width="118" height="118" rx="18" fill="{COLORS['white']}" stroke="{COLORS['aluminum']}" stroke-width="2"/>
          <path d="M78 1616h30v30H78zm40 0h30v30h-30zm-40 40h30v30H78zm46 6h18v18h-18z" fill="{COLORS['ink']}" opacity=".18"/>

          <g opacity=".16">{symbol_markup(38, 1734, 306, 'color')}</g>
          <path d="M405 2000V1902H545" fill="none" stroke="{COLORS['blue']}" stroke-width="34" stroke-linecap="round" stroke-linejoin="round" opacity=".82"/>
          <path d="M846 1818V2000H685" fill="none" stroke="{COLORS['green']}" stroke-width="34" stroke-linecap="round" stroke-linejoin="round" opacity=".82"/>
          <circle cx="615" cy="1920" r="21" fill="{COLORS['ink']}"/>
        '''

    rollup_art = rollup_trim_art()
    rollup_meta = '''<metadata>Finished size: 850 × 2000 mm. Artwork size: 856 × 2006 mm. Bleed: 3 mm on every edge. Safety: 40 mm inside top and side trim edges. Reserve the bottom 150 mm for retractable hardware; keep all essential content above it. Supplier template and proof always govern final production.</metadata>'''
    rollup_print = rollup_meta + f'<rect width="856" height="2006" fill="{COLORS["mineral"]}"/><g transform="translate(3 3)">{rollup_art}</g>'
    rollup_dir = TEMPLATES / "large-format"
    write_text(rollup_dir / "INTAG_Rollup_85x200cm_Bleed3mm_v2.svg", svg_doc(856, 2006, rollup_print, "INTAG roll-up banner print master v2", physical_width="856mm", physical_height="2006mm"))

    guide = rollup_print + f'''
      <g fill="none" pointer-events="none">
        <rect x="3" y="3" width="850" height="2000" stroke="{COLORS['coral']}" stroke-width="2" stroke-dasharray="12 8"/>
        <rect x="43" y="43" width="770" height="1810" stroke="{COLORS['blue_deep']}" stroke-width="2" stroke-dasharray="10 7"/>
        <rect x="3" y="1853" width="850" height="150" fill="{COLORS['amber']}" fill-opacity=".18" stroke="{COLORS['amber']}" stroke-width="2"/>
      </g>
      <g font-family="INTAG Arabic, Tahoma, Arial, sans-serif" font-size="18" font-weight="600" direction="rtl">
        <rect x="474" y="10" width="344" height="34" rx="10" fill="{COLORS['white']}" fill-opacity=".94"/>
        <text x="808" y="34" fill="{COLORS['coral']}" text-anchor="start">حدّ القص: 850 × 2000 مم</text>
        <rect x="474" y="50" width="344" height="34" rx="10" fill="{COLORS['white']}" fill-opacity=".94"/>
        <text x="808" y="74" fill="{COLORS['blue_deep']}" text-anchor="start">منطقة الأمان: 40 مم</text>
        <rect x="270" y="1880" width="548" height="40" rx="10" fill="{COLORS['white']}" fill-opacity=".94"/>
        <text x="808" y="1908" fill="{COLORS['ink']}" text-anchor="start">احتياط قاعدة السحب: 150 مم — دون معلومات مهمة</text>
        <rect x="474" y="1950" width="344" height="34" rx="10" fill="{COLORS['white']}" fill-opacity=".94"/>
        <text x="808" y="1974" fill="{COLORS['coral']}" text-anchor="start">مساحة النزف: 3 مم لكل جانب</text>
      </g>
    '''
    write_text(rollup_dir / "INTAG_Rollup_85x200cm_ProductionGuide_v2.svg", svg_doc(856, 2006, guide, "INTAG roll-up production guide v2", physical_width="856mm", physical_height="2006mm"))

    # Presentational roll-up mockup, generated from the same master artwork.
    mockup = f'''
      <defs>
        <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{COLORS['mist']}"/><stop offset="1" stop-color="{COLORS['aluminum']}"/></linearGradient>
        <filter id="shadow" x="-30%" y="-20%" width="160%" height="160%"><feGaussianBlur stdDeviation="24"/></filter>
      </defs>
      <rect width="1200" height="1500" fill="url(#wall)"/>
      <ellipse cx="600" cy="1372" rx="360" ry="54" fill="{COLORS['ink']}" opacity=".20" filter="url(#shadow)"/>
      <rect x="308" y="88" width="584" height="1288" rx="8" fill="{COLORS['ink']}" opacity=".16" filter="url(#shadow)"/>
      <g transform="translate(338 106) scale(.612)">{rollup_print}</g>
      <rect x="318" y="82" width="564" height="25" rx="8" fill="{COLORS['ink']}"/>
      <rect x="286" y="1330" width="628" height="58" rx="18" fill="{COLORS['ink']}"/>
      <rect x="450" y="1378" width="300" height="20" rx="10" fill="{COLORS['midnight']}" opacity=".88"/>
    '''
    write_text(rollup_dir / "INTAG_Rollup_Mockup_v2.svg", svg_doc(1200, 1500, mockup, "INTAG roll-up banner mockup v2"))

    # Editable email signature.
    signature = f'''<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>قالب توقيع INTAG للبريد الإلكتروني</title></head>
<body dir="rtl" style="margin:0;padding:24px;background:#fff;font-family:Tahoma,Arial,sans-serif;color:{COLORS['ink']}">
  <!-- استبدل [LOGO_URL_OR_CID] برابط HTTPS معتمد أو مرجع CID قبل الإرسال. -->
  <table dir="rtl" role="presentation" cellspacing="0" cellpadding="0" style="border-collapse:collapse;max-width:620px">
    <tr>
      <td style="vertical-align:top;padding-left:20px;border-left:2px solid {COLORS['mist']}">
        <img src="[LOGO_URL_OR_CID]" width="64" height="64" alt="INTAG">
      </td>
      <td style="vertical-align:top;padding-right:20px;text-align:right">
        <div style="font-weight:700;font-size:18px;line-height:1.3">[الاسم الكامل]</div>
        <div style="color:{COLORS['green_deep']};font-weight:600;font-size:14px;margin-top:3px">[المسمّى الوظيفي]</div>
        <div style="color:{COLORS['slate']};font-size:13px;line-height:1.7;margin-top:10px">[البريد الإلكتروني] &nbsp;•&nbsp; [رقم الهاتف]<br>[الموقع الإلكتروني]</div>
        <div style="font-size:11px;color:{COLORS['slate']};margin-top:10px">INTAG Digital Solutions</div>
      </td>
    </tr>
  </table>
</body></html>'''
    write_text(TEMPLATES / "digital" / "INTAG_Email_Signature_Template_v1.html", signature)

    manifest = {
        "name": "INTAG Digital Solutions",
        "short_name": "INTAG",
        "description": "INTAG Digital Solutions brand app icon manifest — v2.0, Logo 02 Connected Frame approved",
        "start_url": "/",
        "display": "standalone",
        "background_color": COLORS["mineral"],
        "theme_color": COLORS["ink"],
        "icons": [
            {"src": "../../assets/logo/png/INTAG_AppIcon_RGB_v1_192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "../../assets/logo/png/INTAG_AppIcon_RGB_v1_512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "../../assets/logo/png/INTAG_AppIcon_Maskable_RGB_v1_192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
            {"src": "../../assets/logo/png/INTAG_AppIcon_Maskable_RGB_v1_512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    write_text(TEMPLATES / "digital" / "site.webmanifest", json.dumps(manifest, ensure_ascii=False, indent=2))


def rgb_tuple(hex_color: str) -> tuple[float, float, float]:
    return tuple(int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))


def cmyk_approx(hex_color: str) -> tuple[int, int, int, int]:
    r, g, b = rgb_tuple(hex_color)
    k = 1 - max(r, g, b)
    if k >= 0.999:
        return 0, 0, 0, 100
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return tuple(round(v * 100) for v in (c, m, y, k))


def relative_luminance(hex_color: str) -> float:
    def linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (linear(v) for v in rgb_tuple(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def build_ase(path: Path, entries: list[tuple[str, str]]) -> None:
    blocks: list[bytes] = []
    for name, value in entries:
        encoded_name = (name + "\0").encode("utf-16-be")
        body = struct.pack(">H", len(name) + 1) + encoded_name
        body += b"RGB " + struct.pack(">fff", *rgb_tuple(value)) + struct.pack(">H", 2)
        blocks.append(struct.pack(">HI", 0x0001, len(body)) + body)
    data = b"ASEF" + struct.pack(">HHI", 1, 0, len(blocks)) + b"".join(blocks)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def build_tokens() -> None:
    tokens_dir = ASSETS / "tokens"
    color_entries = [
        ("INTAG Ink", COLORS["ink"]),
        ("INTAG Midnight", COLORS["midnight"]),
        ("INTAG Blue", COLORS["blue"]),
        ("INTAG Blue Deep", COLORS["blue_deep"]),
        ("INTAG Green", COLORS["green"]),
        ("INTAG Green Deep", COLORS["green_deep"]),
        ("INTAG Mineral", COLORS["mineral"]),
        ("INTAG White", COLORS["white"]),
        ("INTAG Aluminum", COLORS["aluminum"]),
        ("INTAG Mist", COLORS["mist"]),
        ("INTAG Slate", COLORS["slate"]),
        ("INTAG Amber", COLORS["amber"]),
        ("INTAG Coral", COLORS["coral"]),
    ]
    data = {
        "meta": {
            "brand": "INTAG Digital Solutions",
            "version": "2.0-logo02-approved",
            "logo_decision": "Approved — Logo 02 Connected Frame",
            "identity_status": "Working — non-logo brand decisions require Brand Owner approval",
        },
        "color": {
            key.lower().replace("intag ", "").replace(" ", "_"): {
                "hex": value,
                "rgb": [round(v * 255) for v in rgb_tuple(value)],
                "cmyk_process_approx": list(cmyk_approx(value)),
            }
            for key, value in color_entries
        },
        "typography": {
            "latin": {"display": "Poppins", "weights": [400, 500, 600, 700, 800]},
            "arabic": {"primary": "IBM Plex Sans Arabic", "weights": [400, 500, 600, 700]},
            "fallback": {"latin": "Arial, sans-serif", "arabic": "Tahoma, Arial, sans-serif"},
        },
        "space": {"2xs": 4, "xs": 8, "sm": 12, "md": 16, "lg": 24, "xl": 32, "2xl": 48, "3xl": 72, "4xl": 96},
        "radius": {"small": 8, "medium": 16, "large": 28, "pill": 999},
        "motion": {"fast_ms": 140, "standard_ms": 260, "expressive_ms": 520, "ease_standard": "cubic-bezier(.2,.8,.2,1)", "ease_exit": "cubic-bezier(.4,0,1,1)"},
    }
    write_text(tokens_dir / "INTAG_DesignTokens_v1.json", json.dumps(data, ensure_ascii=False, indent=2))

    css_lines = [":root {"]
    for key, value in COLORS.items():
        css_lines.append(f"  --intag-color-{key.replace('_', '-')}: {value};")
    css_lines.extend([
        "  --intag-font-latin: 'Poppins', Arial, sans-serif;",
        "  --intag-font-arabic: 'IBM Plex Sans Arabic', Tahoma, Arial, sans-serif;",
    ])
    for key, value in data["space"].items():
        css_lines.append(f"  --intag-space-{key}: {value}px;")
    for key, value in data["radius"].items():
        css_lines.append(f"  --intag-radius-{key}: {value}px;")
    for key, value in data["motion"].items():
        if key.endswith("_ms"):
            css_lines.append(f"  --intag-motion-{key.removesuffix('_ms').replace('_', '-')}: {value}ms;")
        else:
            css_lines.append(f"  --intag-motion-{key.replace('_', '-')}: {value};")
    css_lines.append("}")
    write_text(tokens_dir / "intag-tokens.css", "\n".join(css_lines) + "\n")
    scss_lines: list[str] = []
    for line in css_lines[1:-1]:
        stripped = line.strip()
        name, value = stripped.removesuffix(";").split(": ", 1)
        scss_lines.append(f"${name.removeprefix('--')}: {value};")
    write_text(tokens_dir / "_intag-tokens.scss", "\n".join(scss_lines) + "\n")

    gpl = "GIMP Palette\nName: INTAG Brand Palette v2 — Logo 02 Approved\nColumns: 4\n#\n"
    for name, value in color_entries:
        r, g, b = (round(v * 255) for v in rgb_tuple(value))
        gpl += f"{r:3d} {g:3d} {b:3d}\t{name}\n"
    write_text(tokens_dir / "INTAG_Palette_v1.gpl", gpl)
    build_ase(tokens_dir / "INTAG_Palette_v1.ase", color_entries)

    # Contrast audit matrix, generated from the actual token values.
    matrix = []
    for fg_name in ["ink", "blue", "blue_deep", "green", "green_deep", "slate", "mineral", "white"]:
        for bg_name in ["white", "mineral", "ink", "blue", "green"]:
            ratio = contrast(COLORS[fg_name], COLORS[bg_name])
            matrix.append({"foreground": fg_name, "background": bg_name, "ratio": round(ratio, 2), "aa_normal": ratio >= 4.5, "aa_large": ratio >= 3.0})
    write_text(tokens_dir / "INTAG_Contrast_Audit_v1.json", json.dumps(matrix, indent=2))


def main() -> None:
    build_logo_assets()
    build_patterns()
    build_icons()
    build_templates()
    build_tokens()
    print(f"Built INTAG identity assets under {ROOT}")


if __name__ == "__main__":
    main()
