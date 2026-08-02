from __future__ import annotations

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
  <desc id="desc">INTAG working brand system v1.0. Vector artwork.</desc>
  {bg}
  {content}
</svg>
'''


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
      <path d="M18 96H64V64" fill="none" stroke="{blue}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M64 64V32H110" fill="none" stroke="{green}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="64" cy="64" r="14" fill="{node}"/>
    </g>'''


def concept_b_markup(x: float, y: float, size: float) -> str:
    s = size / 128.0
    return f'''<g transform="translate({x} {y}) scale({s:.6f})">
      <path d="M20 84V28H72" fill="none" stroke="{COLORS['blue']}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M108 44V100H56" fill="none" stroke="{COLORS['green']}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="64" cy="64" r="14" fill="{COLORS['ink']}"/>
    </g>'''


def concept_c_markup(x: float, y: float, size: float) -> str:
    s = size / 128.0
    return f'''<g transform="translate({x} {y}) scale({s:.6f})">
      <path d="M18 92L54 64L18 36" fill="none" stroke="{COLORS['blue']}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M110 36L74 64L110 92" fill="none" stroke="{COLORS['green']}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="64" cy="64" r="14" fill="{COLORS['ink']}"/>
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
        "INTAG_Symbol_Color_RGB_v1.svg": svg_doc(128, 128, symbol_markup(0, 0, 128, "color"), "INTAG Production Point symbol - color"),
        "INTAG_Symbol_Reverse_RGB_v1.svg": svg_doc(128, 128, symbol_markup(0, 0, 128, "reverse"), "INTAG Production Point symbol - reverse"),
        "INTAG_Symbol_Black_v1.svg": svg_doc(128, 128, symbol_markup(0, 0, 128, "black"), "INTAG Production Point symbol - black"),
        "INTAG_Symbol_White_v1.svg": svg_doc(128, 128, symbol_markup(0, 0, 128, "white"), "INTAG Production Point symbol - white"),
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

    # Small-size optical variants. Integer-aligned 32-unit geometry keeps the
    # node circular and the strokes legible when rasterized at 16/24/32 px.
    def small_symbol(node_color: str) -> str:
        return f'''<g>
          <path d="M4 24H16V16" fill="none" stroke="{COLORS['blue']}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M16 16V8H28" fill="none" stroke="{COLORS['green']}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="16" cy="16" r="4" fill="{node_color}"/>
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

    # Concept comparison board.
    board = f'''
      <rect x="40" y="40" width="340" height="340" rx="24" fill="{COLORS['white']}"/>
      <rect x="410" y="40" width="340" height="340" rx="24" fill="{COLORS['white']}"/>
      <rect x="780" y="40" width="340" height="340" rx="24" fill="{COLORS['white']}"/>
      {symbol_markup(130, 88, 160, 'color')}{concept_b_markup(500, 88, 160)}{concept_c_markup(870, 88, 160)}
      <text x="210" y="318" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="21" font-weight="700" letter-spacing="1.2" text-anchor="middle">PRODUCTION POINT</text>
      <text x="580" y="318" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="21" font-weight="700" letter-spacing="1.2" text-anchor="middle">CONNECTED FRAME</text>
      <text x="950" y="318" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="21" font-weight="700" letter-spacing="1.2" text-anchor="middle">SIGNAL FOLD</text>
      <circle cx="66" cy="66" r="8" fill="{COLORS['green']}"/>
      <text x="210" y="352" fill="{COLORS['green_deep']}" font-family="Arial, sans-serif" font-size="16" text-anchor="middle">RECOMMENDED</text>
      <text x="580" y="352" fill="{COLORS['slate']}" font-family="Arial, sans-serif" font-size="16" text-anchor="middle">ALTERNATE</text>
      <text x="950" y="352" fill="{COLORS['slate']}" font-family="Arial, sans-serif" font-size="16" text-anchor="middle">ALTERNATE</text>
    '''
    write_text(logo_dir / "INTAG_Logo_Concepts_v1.svg", svg_doc(1160, 420, board, "INTAG logo concept comparison", background=COLORS["mineral"]))

    # Construction and clear-space sheet.
    primary, w, _ = logo_lockup_content("color", descriptor=False)
    x_unit = 28
    construction = f'''
      <g opacity=".18" stroke="{COLORS['slate']}" stroke-width="1">
        {''.join(f'<path d="M0 {i}H900"/>' for i in range(0, 520, 20))}
        {''.join(f'<path d="M{i} 0V520"/>' for i in range(0, 920, 20))}
      </g>
      <g transform="translate(70 120)">{primary}</g>
      <rect x="42" y="92" width="{w + x_unit * 2}" height="236" fill="none" stroke="{COLORS['green_deep']}" stroke-width="2" stroke-dasharray="8 8"/>
      <text x="42" y="72" fill="{COLORS['green_deep']}" font-family="Arial, sans-serif" font-size="18">CLEAR SPACE = X = symbol node diameter</text>
      <line x1="42" y1="105" x2="70" y2="105" stroke="{COLORS['green_deep']}" stroke-width="2"/>
      <text x="56" y="98" fill="{COLORS['green_deep']}" font-family="Arial, sans-serif" font-size="16" text-anchor="middle">X</text>
      <text x="70" y="390" fill="{COLORS['ink']}" font-family="Arial, sans-serif" font-size="21" font-weight="700">Minimum digital width: 140 px</text>
      <text x="70" y="425" fill="{COLORS['slate']}" font-family="Arial, sans-serif" font-size="18">Use the small-size symbol below 32 px. Physical minimums require vendor proof.</text>
    '''
    write_text(logo_dir / "INTAG_Logo_Construction_v1.svg", svg_doc(900, 520, construction, "INTAG logo construction and clear space", background=COLORS["mineral"]))


def build_patterns() -> None:
    pattern_dir = ASSETS / "patterns"
    tile = f'''
      <defs>
        <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="1.5" fill="{COLORS['slate']}" opacity=".22"/>
        </pattern>
      </defs>
      <rect width="512" height="512" fill="url(#grid)"/>
      <path d="M-32 420H176V288H304V160H544" fill="none" stroke="{COLORS['blue']}" stroke-width="28" stroke-linecap="round" stroke-linejoin="round" opacity=".95"/>
      <path d="M-64 484H240V352H368V224H576" fill="none" stroke="{COLORS['green']}" stroke-width="28" stroke-linecap="round" stroke-linejoin="round" opacity=".9"/>
      <circle cx="304" cy="288" r="17" fill="{COLORS['ink']}"/>
    '''
    write_text(pattern_dir / "INTAG_Pattern_ProductionGrid_Light_v1.svg", svg_doc(512, 512, tile, "INTAG Production Grid pattern - light", background=COLORS["mineral"]))
    dark_tile = tile.replace(COLORS["slate"], COLORS["aluminum"]).replace(COLORS["ink"], COLORS["mineral"])
    write_text(pattern_dir / "INTAG_Pattern_ProductionGrid_Dark_v1.svg", svg_doc(512, 512, dark_tile, "INTAG Production Grid pattern - dark", background=COLORS["ink"]))
    flow = f'''
      <path d="M28 190H310V114H520V54H772" fill="none" stroke="{COLORS['blue']}" stroke-width="32" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M28 258H386V182H596V122H772" fill="none" stroke="{COLORS['green']}" stroke-width="32" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="520" cy="114" r="19" fill="{COLORS['ink']}"/>
      <circle cx="386" cy="182" r="19" fill="{COLORS['ink']}"/>
    '''
    write_text(pattern_dir / "INTAG_GraphicDevice_ProductionPath_v1.svg", svg_doc(800, 310, flow, "INTAG Production Path graphic device"))


ICON_SPECS = {
    "Strategy_Business": '<path d="M4 18V6h8l4 4h4v8H4Z"/><path d="M12 6v6h8"/><circle cx="12" cy="12" r="2.2" class="node"/>',
    "Brand_Media": '<path d="m12 3 7 7-7 11-7-11 7-7Z"/><path d="m9.5 8 5 4-5 4V8Z"/><circle cx="19" cy="10" r="2.2" class="node"/>',
    "Technology_AI": '<path d="m8 5-5 7 5 7"/><path d="m16 5 5 7-5 7"/><path d="m14 4-4 16"/><circle cx="12" cy="12" r="2.2" class="node"/>',
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


def build_icons() -> None:
    icon_dir = ASSETS / "icons"
    for name, paths in ICON_SPECS.items():
        content = f'''<style>.node{{fill:{COLORS['green']};stroke:none}}</style><g fill="none" stroke="{COLORS['ink']}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{paths}</g>'''
        write_text(icon_dir / f"INTAG_Icon_{name}_v1.svg", svg_doc(24, 24, content, f"INTAG {name.replace('_', ' ')} icon"))
    # Contact sheet.
    cells = []
    for index, (name, paths) in enumerate(ICON_SPECS.items()):
        col, row = index % 4, index // 4
        x, y = 54 + col * 240, 46 + row * 190
        cells.append(f'''<g transform="translate({x} {y})">
          <rect width="190" height="142" rx="18" fill="{COLORS['white']}"/>
          <g transform="translate(63 20) scale(2.7)"><style>.node{{fill:{COLORS['green']};stroke:none}}</style><g fill="none" stroke="{COLORS['ink']}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{paths}</g></g>
          <text x="95" y="122" fill="{COLORS['slate']}" font-family="Arial, sans-serif" font-size="13" text-anchor="middle">{escape(name.replace('_', ' '))}</text>
        </g>''')
    write_text(icon_dir / "INTAG_IconLibrary_ContactSheet_v1.svg", svg_doc(1020, 640, "".join(cells), "INTAG icon library contact sheet", background=COLORS["mineral"]))


def logo_for_template(x: float, y: float, scale: float = 1.0, reverse: bool = False) -> str:
    mode = "reverse" if reverse else "color"
    word_color = COLORS["mineral"] if reverse else COLORS["ink"]
    mark = symbol_markup(x, y, 96 * scale, mode)
    word, _ = wordmark_markup(x + 116 * scale, y + 18 * scale, 58 * scale, word_color, point=False)
    return mark + word


def build_templates() -> None:
    # Business card, front and back. 90 x 50 mm trim size.
    front = f'''
      {symbol_markup(656, 86, 210, 'reverse')}
      <path d="M-40 520H310V378H515V236H940" fill="none" stroke="{COLORS['blue']}" stroke-width="42" stroke-linecap="round" stroke-linejoin="round" opacity=".75"/>
      <path d="M-40 586H386V444H591V302H940" fill="none" stroke="{COLORS['green']}" stroke-width="42" stroke-linecap="round" stroke-linejoin="round" opacity=".8"/>
      <circle cx="515" cy="378" r="24" fill="{COLORS['mineral']}"/>
    '''
    write_text(TEMPLATES / "stationery" / "INTAG_BusinessCard_Front_90x50mm_v1.svg", svg_doc(900, 500, front, "INTAG business card front", physical_width="90mm", physical_height="50mm", background=COLORS["ink"]))
    back = f'''
      {logo_for_template(64, 48, .72, False)}
      <text x="64" y="250" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="30" font-weight="700">[NAME SURNAME]</text>
      <text x="64" y="286" fill="{COLORS['green_deep']}" font-family="Poppins, Arial, sans-serif" font-size="18" font-weight="600">[ROLE]</text>
      <text x="64" y="372" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="15">[EMAIL]  /  [PHONE]</text>
      <text x="64" y="402" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="15">[WEBSITE]</text>
      <circle cx="836" cy="436" r="16" fill="{COLORS['ink']}"/>
    '''
    write_text(TEMPLATES / "stationery" / "INTAG_BusinessCard_Back_90x50mm_v1.svg", svg_doc(900, 500, back, "INTAG business card back", physical_width="90mm", physical_height="50mm", background=COLORS["mineral"]))

    # A4 letterhead.
    letter = f'''
      {logo_for_template(126, 116, 1.25, False)}
      <path d="M132 446H1968" stroke="{COLORS['aluminum']}" stroke-width="3"/>
      <text x="132" y="590" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="40">[DATE]</text>
      <text x="132" y="730" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="52" font-weight="700">[DOCUMENT TITLE]</text>
      <text x="132" y="824" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="30">[Recipient / Subject]</text>
      <rect x="126" y="2660" width="1848" height="112" rx="20" fill="{COLORS['mist']}"/>
      <text x="176" y="2728" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="24">[LEGAL NAME]   /   [ADDRESS]   /   [EMAIL]   /   [WEBSITE]</text>
      <circle cx="1910" cy="2717" r="18" fill="{COLORS['ink']}"/>
    '''
    write_text(TEMPLATES / "stationery" / "INTAG_Letterhead_A4_v1.svg", svg_doc(2100, 2970, letter, "INTAG A4 letterhead", physical_width="210mm", physical_height="297mm", background=COLORS["white"]))

    # Proposal cover.
    proposal = f'''
      <path d="M-120 2570H612V2080H1090V1590H2240" fill="none" stroke="{COLORS['blue']}" stroke-width="126" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M-120 2810H850V2320H1328V1830H2240" fill="none" stroke="{COLORS['green']}" stroke-width="126" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="1090" cy="2080" r="76" fill="{COLORS['ink']}"/>
      {logo_for_template(136, 120, 1.35, False)}
      <text x="136" y="780" fill="{COLORS['green_deep']}" font-family="Poppins, Arial, sans-serif" font-size="34" font-weight="600" letter-spacing="6">PROPOSAL / [CLIENT]</text>
      <text x="136" y="1070" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="104" font-weight="700">[Outcome-led project title]</text>
      <text x="136" y="1308" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="38">Prepared for [CLIENT]  /  [DATE]  /  Draft for discussion</text>
    '''
    write_text(TEMPLATES / "proposal" / "INTAG_Proposal_Cover_A4_v1.svg", svg_doc(2100, 2970, proposal, "INTAG proposal cover", physical_width="210mm", physical_height="297mm", background=COLORS["mineral"]))

    # Social square.
    square = f'''
      {symbol_markup(822, 74, 170, 'reverse')}
      <text x="74" y="94" fill="{COLORS['aluminum']}" font-family="Poppins, Arial, sans-serif" font-size="26" font-weight="600" letter-spacing="5">INTAG / POINT OF VIEW</text>
      <text x="74" y="435" fill="{COLORS['mineral']}" font-family="Poppins, Arial, sans-serif" font-size="96" font-weight="700">Growth systems</text>
      <text x="74" y="542" fill="{COLORS['mineral']}" font-family="Poppins, Arial, sans-serif" font-size="96" font-weight="700">are built.</text>
      <text x="74" y="636" fill="{COLORS['green']}" font-family="Poppins, Arial, sans-serif" font-size="40" font-weight="600">Results are measured.</text>
      <path d="M-60 996H360V860H590V724H1140" fill="none" stroke="{COLORS['blue']}" stroke-width="56" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M-60 1072H470V936H700V800H1140" fill="none" stroke="{COLORS['green']}" stroke-width="56" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="590" cy="860" r="34" fill="{COLORS['mineral']}"/>
    '''
    write_text(TEMPLATES / "social" / "INTAG_Social_Square_1080_v1.svg", svg_doc(1080, 1080, square, "INTAG social square template", background=COLORS["ink"]))

    portrait = f'''
      <rect x="60" y="60" width="960" height="1230" rx="34" fill="none" stroke="{COLORS['aluminum']}" stroke-width="2" opacity=".45"/>
      {logo_for_template(92, 84, .72, False)}
      <text x="92" y="455" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="92" font-weight="700">One growth</text>
      <text x="92" y="558" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="92" font-weight="700">system.</text>
      <text x="92" y="654" fill="{COLORS['green_deep']}" font-family="Poppins, Arial, sans-serif" font-size="34" font-weight="600">Strategy · Brand · Technology · Activation</text>
      <path d="M-40 1270H320V1080H560V890H1120" fill="none" stroke="{COLORS['blue']}" stroke-width="66" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M-40 1370H440V1180H680V990H1120" fill="none" stroke="{COLORS['green']}" stroke-width="66" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="560" cy="1080" r="38" fill="{COLORS['ink']}"/>
    '''
    write_text(TEMPLATES / "social" / "INTAG_Social_Portrait_1080x1350_v1.svg", svg_doc(1080, 1350, portrait, "INTAG social portrait template", background=COLORS["mineral"]))

    story = f'''
      {symbol_markup(816, 82, 182, 'reverse')}
      <text x="84" y="128" fill="{COLORS['aluminum']}" font-family="Poppins, Arial, sans-serif" font-size="24" font-weight="600" letter-spacing="5">INTAG / CASE NOTE</text>
      <text x="84" y="590" fill="{COLORS['mineral']}" font-family="Poppins, Arial, sans-serif" font-size="108" font-weight="700">From scattered</text>
      <text x="84" y="714" fill="{COLORS['mineral']}" font-family="Poppins, Arial, sans-serif" font-size="108" font-weight="700">activity to one</text>
      <text x="84" y="838" fill="{COLORS['green']}" font-family="Poppins, Arial, sans-serif" font-size="108" font-weight="700">system.</text>
      <rect x="84" y="1010" width="912" height="356" rx="34" fill="{COLORS['midnight']}" stroke="{COLORS['slate']}" stroke-width="2"/>
      <text x="136" y="1100" fill="{COLORS['aluminum']}" font-family="Poppins, Arial, sans-serif" font-size="28">[PROBLEM]</text>
      <text x="136" y="1194" fill="{COLORS['mineral']}" font-family="Poppins, Arial, sans-serif" font-size="48" font-weight="600">[Evidence-led result]</text>
      <text x="136" y="1280" fill="{COLORS['green']}" font-family="Poppins, Arial, sans-serif" font-size="28">[METRIC / PROOF]</text>
      <path d="M-40 1900H340V1700H600V1500H1120" fill="none" stroke="{COLORS['blue']}" stroke-width="62" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M-40 1990H470V1790H730V1590H1120" fill="none" stroke="{COLORS['green']}" stroke-width="62" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="600" cy="1700" r="36" fill="{COLORS['mineral']}"/>
    '''
    write_text(TEMPLATES / "social" / "INTAG_Story_1080x1920_v1.svg", svg_doc(1080, 1920, story, "INTAG story template", background=COLORS["ink"]))

    # Presentation cover and content slide.
    cover = f'''
      {logo_for_template(106, 84, .85, False)}
      <text x="106" y="410" fill="{COLORS['green_deep']}" font-family="Poppins, Arial, sans-serif" font-size="34" font-weight="600" letter-spacing="5">[DECK TYPE] / [DATE]</text>
      <text x="106" y="590" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="132" font-weight="700">[Presentation title]</text>
      <text x="106" y="688" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="42">[One clear outcome-led subtitle]</text>
      <path d="M1120 1160V742H1378V488H1642V128" fill="none" stroke="{COLORS['blue']}" stroke-width="96" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M1280 1160V862H1538V608H1810V128" fill="none" stroke="{COLORS['green']}" stroke-width="96" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="1378" cy="742" r="54" fill="{COLORS['ink']}"/>
    '''
    write_text(TEMPLATES / "presentation" / "INTAG_Presentation_Cover_16x9_v1.svg", svg_doc(1920, 1080, cover, "INTAG presentation cover", background=COLORS["mineral"]))
    content = f'''
      {symbol_markup(1740, 46, 110, 'color')}
      <text x="92" y="94" fill="{COLORS['green_deep']}" font-family="Poppins, Arial, sans-serif" font-size="26" font-weight="600" letter-spacing="4">SECTION / 01</text>
      <text x="92" y="235" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="82" font-weight="700">[Answer-first slide title]</text>
      <rect x="92" y="340" width="1100" height="560" rx="28" fill="{COLORS['white']}"/>
      <text x="144" y="430" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="30">[Main evidence / chart / diagram area]</text>
      <rect x="1240" y="340" width="588" height="260" rx="28" fill="{COLORS['ink']}"/>
      <text x="1292" y="423" fill="{COLORS['green']}" font-family="Poppins, Arial, sans-serif" font-size="28" font-weight="600">KEY POINT</text>
      <text x="1292" y="492" fill="{COLORS['mineral']}" font-family="Poppins, Arial, sans-serif" font-size="46" font-weight="700">[One useful</text>
      <text x="1292" y="548" fill="{COLORS['mineral']}" font-family="Poppins, Arial, sans-serif" font-size="46" font-weight="700">takeaway]</text>
      <rect x="1240" y="630" width="588" height="270" rx="28" fill="{COLORS['mist']}"/>
      <text x="1292" y="714" fill="{COLORS['blue_deep']}" font-family="Poppins, Arial, sans-serif" font-size="28" font-weight="600">NEXT DECISION</text>
      <text x="1292" y="786" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="36" font-weight="600">[Owner / action / date]</text>
      <text x="92" y="1010" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="22">INTAG Digital Solutions  /  Confidential draft  /  01</text>
    '''
    write_text(TEMPLATES / "presentation" / "INTAG_Presentation_Content_16x9_v1.svg", svg_doc(1920, 1080, content, "INTAG presentation content slide", background=COLORS["mineral"]))

    # Website hero style tile.
    web = f'''
      <rect x="0" y="0" width="1440" height="900" fill="{COLORS['mineral']}"/>
      {logo_for_template(82, 54, .68, False)}
      <text x="1300" y="108" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="20" text-anchor="end">WORK  ·  CAPABILITIES  ·  ABOUT  ·  CONTACT</text>
      <text x="82" y="342" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="80" font-weight="700">We build the systems</text>
      <text x="82" y="430" fill="{COLORS['ink']}" font-family="Poppins, Arial, sans-serif" font-size="80" font-weight="700">growth needs.</text>
      <text x="82" y="520" fill="{COLORS['slate']}" font-family="Poppins, Arial, sans-serif" font-size="26">Strategy, brand, technology and activation — connected.</text>
      <rect x="82" y="580" width="318" height="62" rx="31" fill="{COLORS['ink']}"/>
      <text x="241" y="619" fill="{COLORS['mineral']}" font-family="Poppins, Arial, sans-serif" font-size="20" font-weight="600" text-anchor="middle">START A CONVERSATION</text>
      <path d="M720 886V610H924V418H1128V156" fill="none" stroke="{COLORS['blue']}" stroke-width="82" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M886 886V714H1090V522H1328V156" fill="none" stroke="{COLORS['green']}" stroke-width="82" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="924" cy="610" r="47" fill="{COLORS['ink']}"/>
    '''
    write_text(TEMPLATES / "digital" / "INTAG_Website_Hero_1440_v1.svg", svg_doc(1440, 900, web, "INTAG website hero style tile"))

    # Editable email signature.
    signature = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>INTAG Email Signature Template</title></head>
<body style="margin:0;padding:24px;background:#fff;font-family:Arial,sans-serif;color:{COLORS['ink']}">
  <!-- Replace [LOGO_URL_OR_CID] with an approved absolute HTTPS URL or a CID attachment reference before sending. -->
  <table role="presentation" cellspacing="0" cellpadding="0" style="border-collapse:collapse;max-width:620px">
    <tr>
      <td style="vertical-align:top;padding-right:20px;border-right:2px solid {COLORS['mist']}">
        <img src="[LOGO_URL_OR_CID]" width="64" height="64" alt="INTAG">
      </td>
      <td style="vertical-align:top;padding-left:20px">
        <div style="font-weight:700;font-size:18px;line-height:1.3">[NAME SURNAME]</div>
        <div style="color:{COLORS['green_deep']};font-weight:600;font-size:14px;margin-top:3px">[ROLE]</div>
        <div style="color:{COLORS['slate']};font-size:13px;line-height:1.6;margin-top:10px">[EMAIL] &nbsp;·&nbsp; [PHONE]<br>[WEBSITE]</div>
        <div style="font-size:11px;color:{COLORS['slate']};margin-top:10px">INTAG Digital Solutions</div>
      </td>
    </tr>
  </table>
</body></html>'''
    write_text(TEMPLATES / "digital" / "INTAG_Email_Signature_Template_v1.html", signature)

    manifest = {
        "name": "INTAG Digital Solutions",
        "short_name": "INTAG",
        "description": "INTAG Digital Solutions brand app icon manifest — working v1.0",
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
        "meta": {"brand": "INTAG Digital Solutions", "version": "1.0-working", "status": "Proposed - requires Brand Owner approval"},
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

    gpl = "GIMP Palette\nName: INTAG Working Brand Palette v1\nColumns: 4\n#\n"
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
