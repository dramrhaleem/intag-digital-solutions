import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const execFileAsync = promisify(execFile);

const ROOT = "C:/Users/amroh/Documents/AI Product Dev Intag/brand/intag";
const FINAL = path.join(
  ROOT,
  "templates/presentation/INTAG_Presentation_Starter_AR_v2.pptx",
);
const QA_DIR = process.env.INTAG_PPTX_QA_DIR
  ? path.resolve(process.env.INTAG_PPTX_QA_DIR)
  : path.join(os.tmpdir(), "intag-presentation-ar-v2-qa");

// These v1 filenames are the stable build aliases. The identity build replaces
// their contents with the latest approved assets; they currently resolve to
// Logo 02 — Connected Frame.
const A = {
  logo: path.join(
    ROOT,
    "assets/logo/png/INTAG_Logo_Primary_Horizontal_RGB_v1_1280w.png",
  ),
  logoReverse: path.join(
    ROOT,
    "assets/logo/png/INTAG_Logo_Primary_Horizontal_Reverse_RGB_v1_1280w.png",
  ),
  symbol: path.join(
    ROOT,
    "assets/logo/png/INTAG_Symbol_Color_RGB_v1_512.png",
  ),
  symbolReverse: path.join(
    ROOT,
    "assets/logo/png/INTAG_Symbol_Reverse_RGB_v1_512.png",
  ),
  keyVisual: path.join(
    ROOT,
    "assets/key-visual/INTAG_KeyVisual_Hero_1600x900_v1.png",
  ),
};

const C = {
  ink: "#0B0D10",
  midnight: "#071B2D",
  blue: "#2369B1",
  blueDeep: "#134B82",
  green: "#2AB687",
  greenDeep: "#087058",
  mineral: "#F4F1E9",
  white: "#FFFFFF",
  aluminum: "#C8CED1",
  mist: "#E8F1F2",
  slate: "#50616F",
  textSecondary: "#40515E",
  borderStrong: "#7E8B94",
};

const FONT_AR = "IBM Plex Sans Arabic";
const SLIDE_W = 1280;
const SLIDE_H = 720;
const SAFE_X = 64;
const SAFE_W = 1152;
const FOOTER_LINE_Y = 657;

const ARABIC_DIGITS = new Map([
  ["0", "٠"],
  ["1", "١"],
  ["2", "٢"],
  ["3", "٣"],
  ["4", "٤"],
  ["5", "٥"],
  ["6", "٦"],
  ["7", "٧"],
  ["8", "٨"],
  ["9", "٩"],
]);

function toArabicDigits(value) {
  return String(value)
    .split("")
    .map((character) => ARABIC_DIGITS.get(character) ?? character)
    .join("");
}

function applyRtlMarks(value) {
  return String(value);
}

async function readBytes(filePath) {
  const bytes = await fs.readFile(filePath);
  return bytes.buffer.slice(
    bytes.byteOffset,
    bytes.byteOffset + bytes.byteLength,
  );
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(
    filePath,
    new Uint8Array(await blob.arrayBuffer()),
  );
}

function addText(slide, text, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: options.name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = options.rtl === false ? String(text) : applyRtlMarks(text);
  shape.text.style = {
    typeface: options.typeface ?? FONT_AR,
    fontSize: options.fontSize ?? 20,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
    alignment: options.alignment ?? "right",
    verticalAlignment: options.verticalAlignment ?? "top",
    lineSpacing: options.lineSpacing ?? 1.18,
    autoFit: options.autoFit ?? "none",
    wrap: options.wrap ?? "square",
    insets: options.insets ?? { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

function addRect(slide, position, fill, options = {}) {
  return slide.shapes.add({
    geometry: options.geometry ?? "rect",
    name: options.name,
    position,
    fill,
    line: options.line ?? { style: "solid", fill: "none", width: 0 },
    ...(options.borderRadius !== undefined
      ? { borderRadius: options.borderRadius }
      : {}),
  });
}

function addLine(slide, position, color, width = 2, name) {
  return slide.shapes.add({
    geometry: "line",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: color, width },
  });
}

function addImage(slide, bytes, position, alt, options = {}) {
  return slide.images.add({
    blob: bytes,
    contentType: "image/png",
    alt,
    fit: options.fit ?? "contain",
    position,
    ...(options.crop ? { crop: options.crop } : {}),
    ...(options.geometry ? { geometry: options.geometry } : {}),
    ...(options.borderRadius !== undefined
      ? { borderRadius: options.borderRadius }
      : {}),
  });
}

function addLabel(slide, text, x, y, width, options = {}) {
  return addText(
    slide,
    text,
    { left: x, top: y, width, height: options.height ?? 28 },
    {
      fontSize: options.fontSize ?? 17,
      bold: true,
      color: options.color ?? C.greenDeep,
      alignment: options.alignment ?? "right",
      name: options.name,
    },
  );
}

function addHeader(slide, label, page, options = {}) {
  addLabel(slide, label, 760, 44, 456, {
    color: options.dark ? C.green : C.greenDeep,
    name: `header-label-${page}`,
  });
  addText(
    slide,
    `قالب عرض عربي  ·  ${toArabicDigits(String(page).padStart(2, "0"))}`,
    { left: 144, top: 46, width: 300, height: 24 },
    {
      fontSize: 15,
      bold: true,
      color: options.dark ? C.aluminum : C.textSecondary,
      alignment: "left",
      name: `header-counter-${page}`,
    },
  );
}

function addFooter(slide, page, options = {}) {
  const dark = options.dark ?? false;
  addLine(
    slide,
    { left: SAFE_X, top: FOOTER_LINE_Y, width: SAFE_W, height: 0 },
    dark ? C.slate : C.borderStrong,
    1,
    `footer-divider-${page}`,
  );
  addText(
    slide,
    "نظام الهوية · الإصدار ٢٫٠ · الشعار ٠٢ معتمد · بقية القرارات قيد المراجعة",
    { left: 430, top: 672, width: 786, height: 24 },
    {
      fontSize: 14,
      bold: true,
      color: dark ? C.aluminum : C.textSecondary,
      name: `footer-status-${page}`,
    },
  );
  addText(
    slide,
    toArabicDigits(String(page).padStart(2, "0")),
    { left: SAFE_X, top: 672, width: 72, height: 24 },
    {
      fontSize: 15,
      bold: true,
      color: dark ? C.white : C.ink,
      alignment: "left",
      name: `footer-page-${page}`,
    },
  );
  addRect(
    slide,
    { left: 152, top: 680, width: 40, height: 4 },
    page % 2 ? C.green : C.blue,
    { name: `footer-accent-${page}` },
  );
}

function setSources(slide, lines) {
  slide.speakerNotes.textFrame.setText(["[Sources]", ...lines]);
  slide.speakerNotes.setVisible(true);
}

async function enforceArabicParagraphDirection(pptxPath) {
  // artifact-tool currently exports right alignment but not DrawingML's
  // paragraph RTL flag. PowerPoint consequently lays Arabic words in LTR
  // order. Patch only the generated slide paragraphs, then repackage the PPTX.
  const packageDir = path.join(QA_DIR, "rtl-package");
  const packedPath = path.join(QA_DIR, "INTAG_Presentation_AR_v2_rtl.pptx");
  await fs.rm(packageDir, { recursive: true, force: true });
  await fs.mkdir(packageDir, { recursive: true });
  await execFileAsync("7z", ["x", "-y", pptxPath, `-o${packageDir}`]);

  const slidesDir = path.join(packageDir, "ppt", "slides");
  const slideFiles = (await fs.readdir(slidesDir))
    .filter((fileName) => /^slide\d+\.xml$/i.test(fileName))
    .sort();

  for (const fileName of slideFiles) {
    const filePath = path.join(slidesDir, fileName);
    let xml = await fs.readFile(filePath, "utf8");
    xml = xml.replaceAll("\u200F", "");
    xml = xml.replace(/<a:pPr([^>]*)>/g, (match, attributes) => {
      if (/\brtl="[^"]*"/.test(attributes)) {
        return `<a:pPr${attributes.replace(/\brtl="[^"]*"/, 'rtl="1"')}>`;
      }
      return `<a:pPr${attributes} rtl="1">`;
    });
    await fs.writeFile(filePath, xml, "utf8");
  }

  const escapeXml = (value) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&apos;");
  const upsertXmlElement = (xml, tagName, value, closingRoot) => {
    const element = `<${tagName}>${escapeXml(value)}</${tagName}>`;
    const existing = new RegExp(
      `<${tagName}(?:\\s[^>]*)?>[\\s\\S]*?<\\/${tagName}>`,
    );
    return existing.test(xml)
      ? xml.replace(existing, element)
      : xml.replace(closingRoot, `${element}${closingRoot}`);
  };

  const corePath = path.join(packageDir, "docProps", "core.xml");
  let coreXml = (await fs.readFile(corePath, "utf8")).replace(/^\uFEFF/, "");
  if (!coreXml.includes("xmlns:cp=")) {
    coreXml = coreXml.replace(
      "<coreProperties ",
      '<coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" ',
    );
  }
  const coreMetadata = [
    ["dc:title", "INTAG Presentation Starter — Arabic v2.0"],
    ["dc:subject", "قالب عرض عربي بهوية INTAG Digital Solutions"],
    ["dc:creator", "INTAG Digital Solutions"],
    ["lastModifiedBy", "INTAG Digital Solutions"],
    [
      "dc:description",
      "قالب عرض عربي قابل للتحرير. الإصدار ٢٫٠؛ الشعار ٠٢ Connected Frame معتمد، وبقية قرارات الهوية قيد المراجعة.",
    ],
    [
      "cp:keywords",
      "INTAG, Arabic presentation, RTL, brand template, Connected Frame, Logo 02, v2.0",
    ],
    ["dc:language", "ar"],
  ];
  for (const [tagName, value] of coreMetadata) {
    coreXml = upsertXmlElement(
      coreXml,
      tagName,
      value,
      "</coreProperties>",
    );
  }
  await fs.writeFile(corePath, coreXml, "utf8");

  const appPath = path.join(packageDir, "docProps", "app.xml");
  let appXml = await fs.readFile(appPath, "utf8");
  const extendedMetadata = [
    ["ap:Application", "INTAG Presentation Builder"],
    ["ap:PresentationFormat", "Widescreen 16:9"],
    ["ap:Slides", "7"],
    ["ap:Notes", "7"],
    ["ap:HiddenSlides", "0"],
    ["ap:Template", "INTAG Arabic Presentation Starter v2.0"],
    ["ap:Company", "INTAG Digital Solutions"],
  ];
  for (const [tagName, value] of extendedMetadata) {
    appXml = upsertXmlElement(
      appXml,
      tagName,
      value,
      "</ap:Properties>",
    );
  }
  await fs.writeFile(appPath, appXml, "utf8");

  await fs.rm(packedPath, { force: true });
  await execFileAsync(
    "7z",
    ["a", "-tzip", "-mx=6", packedPath, "*", "-r"],
    { cwd: packageDir },
  );
  await fs.copyFile(packedPath, pptxPath);
  await fs.rm(packageDir, { recursive: true, force: true });
  return slideFiles.length;
}

async function main() {
  await fs.mkdir(path.dirname(FINAL), { recursive: true });
  await fs.rm(QA_DIR, { recursive: true, force: true });
  await fs.mkdir(QA_DIR, { recursive: true });

  const [logo, logoReverse, symbol, symbolReverse, keyVisual] =
    await Promise.all([
      readBytes(A.logo),
      readBytes(A.logoReverse),
      readBytes(A.symbol),
      readBytes(A.symbolReverse),
      readBytes(A.keyVisual),
    ]);

  const presentation = Presentation.create({
    slideSize: { width: SLIDE_W, height: SLIDE_H },
  });
  presentation.theme.colorScheme = {
    name: "INTAG Arabic Working v2",
    themeColors: {
      accent1: C.blue,
      accent2: C.green,
      accent3: C.blueDeep,
      accent4: C.greenDeep,
      accent5: C.aluminum,
      accent6: C.borderStrong,
      bg1: C.mineral,
      bg2: C.white,
      tx1: C.ink,
      tx2: C.textSecondary,
      dk1: C.ink,
      dk2: C.midnight,
      lt1: C.white,
      lt2: C.mist,
      hlink: C.blueDeep,
      folHlink: C.greenDeep,
    },
  };

  // 01 — الغلاف
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.mineral;
    addImage(
      slide,
      keyVisual,
      { left: 0, top: 0, width: 576, height: 720 },
      "المشهد البصري الرئيس لهوية إنتاغ",
      {
        fit: "cover",
        crop: { left: 0.2, top: 0, right: 0.35, bottom: 0 },
      },
    );
    addRect(
      slide,
      { left: 576, top: 0, width: 16, height: 720 },
      C.green,
      { name: "cover-accent-rail" },
    );
    addImage(
      slide,
      logo,
      { left: 956, top: 48, width: 260, height: 86 },
      "شعار إنتاغ المعتمد — Connected Frame",
    );
    addLabel(slide, "[نوع العرض]  ·  [التاريخ]", 656, 180, 560, {
      name: "cover-meta",
    });
    addText(
      slide,
      "[عنوان العرض]",
      { left: 656, top: 230, width: 560, height: 142 },
      {
        fontSize: 58,
        bold: true,
        lineSpacing: 1.02,
        name: "cover-title",
      },
    );
    addText(
      slide,
      "[جملة موجزة توضّح النتيجة المطلوبة من العرض]",
      { left: 656, top: 406, width: 560, height: 84 },
      {
        fontSize: 24,
        color: C.textSecondary,
        lineSpacing: 1.35,
        name: "cover-subtitle",
      },
    );
    addLine(
      slide,
      { left: 1098, top: 546, width: 118, height: 0 },
      C.blue,
      5,
      "cover-rule",
    );
    addText(
      slide,
      "نظام الهوية · الإصدار ٢٫٠",
      { left: 656, top: 574, width: 560, height: 28 },
      {
        fontSize: 18,
        bold: true,
        name: "cover-version",
      },
    );
    addText(
      slide,
      "الشعار ٠٢ معتمد · بقية القرارات قيد المراجعة",
      { left: 656, top: 608, width: 560, height: 28 },
      {
        fontSize: 16,
        color: C.textSecondary,
        name: "cover-status",
      },
    );
    setSources(slide, [
      "- Internal stable asset: assets/logo/png/INTAG_Logo_Primary_Horizontal_RGB_v1_1280w.png (currently Logo 02 — Connected Frame).",
      "- Internal asset: assets/key-visual/INTAG_KeyVisual_Hero_1600x900_v1.png.",
      "- No external claims.",
    ]);
  }

  // 02 — فاصل قسم
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.ink;
    addImage(
      slide,
      logoReverse,
      { left: 946, top: 44, width: 270, height: 89 },
      "شعار إنتاغ المعكوس المعتمد",
    );
    addImage(
      slide,
      symbolReverse,
      { left: 72, top: 112, width: 500, height: 500 },
      "رمز Connected Frame المعكوس",
    );
    addText(
      slide,
      "٠١",
      { left: 936, top: 154, width: 280, height: 104 },
      {
        fontSize: 92,
        bold: true,
        color: C.green,
        name: "section-number",
      },
    );
    addLabel(slide, "فاصل قسم", 700, 270, 516, {
      color: C.aluminum,
      name: "section-label",
    });
    addText(
      slide,
      "[عنوان القسم]",
      { left: 700, top: 312, width: 516, height: 118 },
      {
        fontSize: 56,
        bold: true,
        color: C.white,
        lineSpacing: 1.04,
        name: "section-title",
      },
    );
    addText(
      slide,
      "[سياق قصير يهيئ الجمهور لما سيأتي]",
      { left: 700, top: 458, width: 516, height: 86 },
      {
        fontSize: 23,
        color: C.aluminum,
        lineSpacing: 1.35,
        name: "section-context",
      },
    );
    addFooter(slide, 2, { dark: true });
    setSources(slide, [
      "- Internal stable asset: assets/logo/png/INTAG_Logo_Primary_Horizontal_Reverse_RGB_v1_1280w.png.",
      "- Internal stable asset: assets/logo/png/INTAG_Symbol_Reverse_RGB_v1_512.png (currently Logo 02 — Connected Frame).",
      "- No external claims.",
    ]);
  }

  // 03 — الخلاصة أولًا
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.mineral;
    addHeader(slide, "الخلاصة أولًا", 3);
    addImage(
      slide,
      symbol,
      { left: 64, top: 42, width: 56, height: 56 },
      "رمز Connected Frame الملون",
    );
    addText(
      slide,
      "[الخلاصة التي يجب أن يتذكرها الجمهور]",
      { left: 160, top: 104, width: 1056, height: 92 },
      {
        fontSize: 44,
        bold: true,
        lineSpacing: 1.08,
        name: "answer-title",
      },
    );
    addLine(
      slide,
      { left: SAFE_X, top: 218, width: SAFE_W, height: 0 },
      C.borderStrong,
      1,
      "answer-horizontal-divider",
    );
    addLine(
      slide,
      { left: 742, top: 258, width: 0, height: 322 },
      C.greenDeep,
      5,
      "answer-vertical-divider",
    );

    addLabel(slide, "الدليل الرئيس", 790, 260, 426, {
      name: "evidence-label",
    });
    addText(
      slide,
      "[٠٠٪]",
      { left: 790, top: 308, width: 426, height: 108 },
      {
        fontSize: 82,
        bold: true,
        color: C.blueDeep,
        name: "evidence-number",
      },
    );
    addText(
      slide,
      "[وصف قصير للدليل أو المعلومة]",
      { left: 790, top: 432, width: 426, height: 82 },
      {
        fontSize: 23,
        bold: true,
        lineSpacing: 1.32,
        name: "evidence-description",
      },
    );

    addLabel(slide, "ما الذي يعنيه ذلك؟", 64, 264, 630, {
      color: C.blueDeep,
      name: "implication-label",
    });
    addText(
      slide,
      "[تفسير موجز يربط الدليل بالقرار]",
      { left: 64, top: 310, width: 630, height: 98 },
      {
        fontSize: 29,
        bold: true,
        lineSpacing: 1.25,
        name: "implication-copy",
      },
    );
    addLabel(slide, "القرار المطلوب", 64, 456, 630, {
      name: "decision-label",
    });
    addText(
      slide,
      "[المسؤول · الإجراء · التاريخ]",
      { left: 64, top: 500, width: 630, height: 66 },
      {
        fontSize: 23,
        bold: true,
        color: C.textSecondary,
        name: "decision-copy",
      },
    );
    addFooter(slide, 3);
    setSources(slide, [
      "- Internal stable asset: assets/logo/png/INTAG_Symbol_Color_RGB_v1_512.png.",
      "- All bracketed content is an intentional Arabic template placeholder.",
      "- No external claims.",
    ]);
  }

  // 04 — صورة ورؤية
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.white;
    addHeader(slide, "صورة ورؤية", 4);
    addImage(
      slide,
      keyVisual,
      { left: 64, top: 146, width: 572, height: 420 },
      "المشهد البصري الرئيس لهوية إنتاغ",
      {
        fit: "cover",
        crop: { left: 0.07, top: 0.04, right: 0.12, bottom: 0.04 },
        geometry: "roundRect",
        borderRadius: 20,
      },
    );
    addLabel(slide, "الفكرة الرئيسة", 700, 98, 516, {
      name: "image-insight-label",
    });
    addText(
      slide,
      "[عنوان يقدّم الرؤية مباشرة]",
      { left: 700, top: 136, width: 516, height: 88 },
      {
        fontSize: 42,
        bold: true,
        lineSpacing: 1.08,
        name: "image-insight-title",
      },
    );
    addLine(
      slide,
      { left: 1102, top: 242, width: 114, height: 0 },
      C.greenDeep,
      5,
      "image-insight-rule",
    );
    addText(
      slide,
      "[جملة تفسّر ما ينبغي أن يراه الجمهور في الصورة]",
      { left: 700, top: 276, width: 516, height: 112 },
      {
        fontSize: 30,
        bold: true,
        color: C.blueDeep,
        lineSpacing: 1.28,
        name: "image-insight-statement",
      },
    );
    addText(
      slide,
      "[سياق أو دليل موجز يدعم الفكرة من دون تكرارها]",
      { left: 700, top: 418, width: 516, height: 90 },
      {
        fontSize: 20,
        color: C.textSecondary,
        lineSpacing: 1.42,
        name: "image-insight-context",
      },
    );
    addLine(
      slide,
      { left: 700, top: 542, width: 516, height: 0 },
      C.borderStrong,
      1,
      "image-source-divider",
    );
    addText(
      slide,
      "[المصدر · المنهج · التاريخ]",
      { left: 700, top: 558, width: 516, height: 30 },
      {
        fontSize: 16,
        color: C.textSecondary,
        name: "image-source-line",
      },
    );
    addFooter(slide, 4);
    setSources(slide, [
      "- Internal asset: assets/key-visual/INTAG_KeyVisual_Hero_1600x900_v1.png.",
      "- Replace the visible source placeholder when external evidence is added.",
      "- No external claims.",
    ]);
  }

  // 05 — تصور مبدئي لبنية القدرات
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.midnight;
    addHeader(slide, "تصور مبدئي لبنية القدرات", 5, { dark: true });
    addImage(
      slide,
      symbolReverse,
      { left: 64, top: 40, width: 64, height: 64 },
      "رمز Connected Frame المعكوس",
    );
    addText(
      slide,
      "[ما النتيجة التي يجب أن ينتجها هذا النظام؟]",
      { left: 176, top: 96, width: 1040, height: 76 },
      {
        fontSize: 41,
        bold: true,
        color: C.white,
        lineSpacing: 1.1,
        name: "capability-title",
      },
    );
    addText(
      slide,
      "مقترح عمل يُراجع قبل أي استخدام خارجي أو التزام تجاري.",
      { left: 176, top: 182, width: 1040, height: 34 },
      {
        fontSize: 18,
        color: C.aluminum,
        name: "capability-status",
      },
    );

    // Draw the connector before the nodes so it remains behind them.
    addLine(
      slide,
      { left: 170, top: 354, width: 930, height: 0 },
      C.slate,
      4,
      "capability-rail",
    );
    addLine(
      slide,
      { left: 790, top: 354, width: 310, height: 0 },
      C.blue,
      8,
      "capability-blue-rail",
    );
    addLine(
      slide,
      { left: 170, top: 354, width: 310, height: 0 },
      C.green,
      8,
      "capability-green-rail",
    );

    const nodes = [
      {
        x: 1100,
        number: "٠١",
        title: "الاستراتيجية\nوالأعمال",
        verb: "صياغة القرار",
        color: C.blue,
      },
      {
        x: 790,
        number: "٠٢",
        title: "العلامة\nوالإعلام",
        verb: "إظهار القيمة",
        color: C.blue,
      },
      {
        x: 480,
        number: "٠٣",
        title: "التقنية والمنتجات\nالرقمية",
        verb: "بناء القدرة",
        color: C.green,
      },
      {
        x: 170,
        number: "٠٤",
        title: "النمو\nوالتفعيل",
        verb: "التجربة والتعلّم",
        color: C.green,
      },
    ];

    for (const node of nodes) {
      addRect(
        slide,
        { left: node.x - 36, top: 318, width: 72, height: 72 },
        node.color,
        {
          geometry: "ellipse",
          name: `capability-node-${node.number}`,
        },
      );
      addText(
        slide,
        node.number,
        { left: node.x - 36, top: 337, width: 72, height: 30 },
        {
          fontSize: 20,
          bold: true,
          color: C.ink,
          alignment: "center",
          verticalAlignment: "middle",
          name: `capability-node-number-${node.number}`,
        },
      );
      addText(
        slide,
        node.title,
        { left: node.x - 125, top: 414, width: 250, height: 70 },
        {
          fontSize: 22,
          bold: true,
          color: C.white,
          alignment: "center",
          lineSpacing: 1.2,
          name: `capability-node-title-${node.number}`,
        },
      );
      addText(
        slide,
        node.verb,
        { left: node.x - 122, top: 504, width: 244, height: 42 },
        {
          fontSize: 17,
          color: C.aluminum,
          alignment: "center",
          name: `capability-node-verb-${node.number}`,
        },
      );
    }
    addText(
      slide,
      "حالة المحتوى: مقترح قيد المراجعة، وليس خريطة خدمات أو التزامًا تجاريًا معتمدًا.",
      { left: 250, top: 606, width: 966, height: 28 },
      {
        fontSize: 16,
        bold: true,
        color: C.green,
        name: "capability-disclaimer",
      },
    );
    addFooter(slide, 5, { dark: true });
    setSources(slide, [
      "- Internal working source: docs/BRAND_STRATEGY_WORKING_AR.md.",
      "- Proposed architecture: Strategy & Business / Brand & Media / Technology & Digital Products / Growth & Activation.",
      "- This is not an approved offer map or commercial commitment.",
      "- Internal stable asset: assets/logo/png/INTAG_Symbol_Reverse_RGB_v1_512.png.",
    ]);
  }

  // 06 — مخطط توضيحي قابل للتعديل
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.mineral;
    addHeader(slide, "مخطط توضيحي قابل للتعديل", 6);
    addText(
      slide,
      "سيناريو توضيحي يُستبدل ببيانات موثّقة",
      { left: 160, top: 94, width: 1056, height: 58 },
      {
        fontSize: 40,
        bold: true,
        name: "chart-title",
      },
    );
    addText(
      slide,
      "اعرض اتجاه البيانات، ثم وضّح ما الذي تدعمه الأدلة وما الذي لا تثبته.",
      { left: 160, top: 162, width: 1056, height: 42 },
      {
        fontSize: 19,
        color: C.textSecondary,
        name: "chart-subtitle",
      },
    );

    slide.charts.add("line", {
      position: { left: 64, top: 226, width: 830, height: 344 },
      categories: ["المرحلة ١", "المرحلة ٢", "المرحلة ٣", "المرحلة ٤"],
      series: [
        {
          name: "المسار الأساسي",
          values: [22, 31, 36, 43],
          line: { style: "solid", fill: C.textSecondary, width: 3 },
          marker: { symbol: "circle", size: 7 },
        },
        {
          name: "المسار المنسق",
          values: [22, 39, 55, 72],
          line: { style: "solid", fill: C.greenDeep, width: 4 },
          marker: { symbol: "circle", size: 8 },
        },
      ],
      hasLegend: true,
      legend: {
        position: "bottom",
        overlay: false,
        textStyle: { fill: C.textSecondary, fontSize: 16 },
      },
      lineOptions: {
        grouping: "standard",
        smooth: false,
        varyColors: false,
      },
      xAxis: {
        visible: true,
        textStyle: { fill: C.textSecondary, fontSize: 16 },
        line: { style: "solid", fill: C.borderStrong, width: 1 },
        majorGridlines: null,
      },
      yAxis: {
        visible: true,
        min: 0,
        max: 80,
        majorUnit: 20,
        textStyle: { fill: C.textSecondary, fontSize: 16 },
        line: { style: "solid", fill: C.borderStrong, width: 1 },
        majorGridlines: {
          style: "solid",
          fill: C.borderStrong,
          width: 1,
        },
      },
      chartFill: C.mineral,
      chartLine: { style: "solid", fill: "none", width: 0 },
      plotAreaFill: C.mineral,
      plotAreaLine: { style: "solid", fill: "none", width: 0 },
    });

    addLine(
      slide,
      { left: 934, top: 232, width: 0, height: 330 },
      C.blueDeep,
      5,
      "chart-readout-rule",
    );
    addLabel(slide, "ما الذي تغيّر؟", 970, 238, 246, {
      name: "chart-change-label",
    });
    addText(
      slide,
      "[اكتب الملاحظة الرئيسة]",
      { left: 970, top: 282, width: 246, height: 86 },
      {
        fontSize: 25,
        bold: true,
        lineSpacing: 1.28,
        name: "chart-change",
      },
    );
    addLabel(slide, "ما دلالة ذلك؟", 970, 402, 246, {
      color: C.blueDeep,
      name: "chart-implication-label",
    });
    addText(
      slide,
      "[اربط الملاحظة بالقرار]",
      { left: 970, top: 446, width: 246, height: 88 },
      {
        fontSize: 20,
        color: C.textSecondary,
        lineSpacing: 1.4,
        name: "chart-implication",
      },
    );
    addText(
      slide,
      "بيانات توضيحية فقط؛ ليست توقعًا أو معيارًا أو نتيجة خاصة بعميل.",
      { left: 300, top: 608, width: 916, height: 26 },
      {
        fontSize: 16,
        bold: true,
        color: C.ink,
        name: "chart-disclaimer",
      },
    );
    addFooter(slide, 6);
    setSources(slide, [
      "- No external data source.",
      "- Categories and values are authored placeholder data for this editable template only.",
      "- Not a forecast, benchmark, research result, or client result.",
    ]);
  }

  // 07 — الخاتمة والقرار التالي
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.ink;
    addImage(
      slide,
      logoReverse,
      { left: 956, top: 44, width: 260, height: 86 },
      "شعار إنتاغ المعكوس المعتمد",
    );
    addLabel(slide, "الخطوة التالية", 700, 176, 516, {
      color: C.green,
      name: "closing-label",
    });
    addText(
      slide,
      "[القرار التالي]",
      { left: 276, top: 222, width: 940, height: 108 },
      {
        fontSize: 58,
        bold: true,
        color: C.white,
        lineSpacing: 1.05,
        name: "closing-decision",
      },
    );
    addText(
      slide,
      "[جملة واحدة تُنهي العرض وتوضح ما المطلوب الآن]",
      { left: 276, top: 362, width: 940, height: 76 },
      {
        fontSize: 24,
        color: C.aluminum,
        lineSpacing: 1.35,
        name: "closing-resolution",
      },
    );
    addLine(
      slide,
      { left: 276, top: 478, width: 940, height: 0 },
      C.slate,
      2,
      "closing-divider",
    );

    const actions = [
      { x: 976, label: "المسؤول", value: "[الاسم]", color: C.green },
      { x: 676, label: "الإجراء", value: "[الإجراء]", color: C.green },
      { x: 376, label: "التاريخ", value: "[التاريخ]", color: C.blue },
    ];
    for (const action of actions) {
      addLabel(slide, action.label, action.x, 504, 240, {
        color: action.color,
        name: `closing-label-${action.x}`,
      });
      addText(
        slide,
        action.value,
        { left: action.x, top: 544, width: 240, height: 48 },
        {
          fontSize: 23,
          bold: true,
          color: C.white,
          name: `closing-value-${action.x}`,
        },
      );
    }
    addText(
      slide,
      "[البريد الإلكتروني]  ·  [الموقع الإلكتروني]",
      { left: 376, top: 614, width: 840, height: 24 },
      {
        fontSize: 16,
        color: C.aluminum,
        name: "closing-contact",
      },
    );
    addImage(
      slide,
      symbolReverse,
      { left: 64, top: 426, width: 188, height: 188 },
      "رمز Connected Frame المعكوس",
    );
    addFooter(slide, 7, { dark: true });
    setSources(slide, [
      "- Internal stable asset: assets/logo/png/INTAG_Logo_Primary_Horizontal_Reverse_RGB_v1_1280w.png.",
      "- Internal stable asset: assets/logo/png/INTAG_Symbol_Reverse_RGB_v1_512.png.",
      "- No external claims.",
    ]);
  }

  const qaFiles = [];
  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const pngPath = path.join(QA_DIR, `${stem}.png`);
    const layoutPath = path.join(QA_DIR, `${stem}.layout.json`);
    await writeBlob(
      pngPath,
      await presentation.export({ slide, format: "png", scale: 1.5 }),
    );
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(layoutPath, await layout.text(), "utf8");
    qaFiles.push({ pngPath, layoutPath });
  }

  await writeBlob(
    path.join(QA_DIR, "montage.webp"),
    await presentation.export({ format: "webp", montage: true, scale: 1 }),
  );
  const inspection = await presentation.inspect({
    kind: "slide,textbox,shape,image,chart,notes",
    maxChars: 60000,
  });
  await fs.writeFile(
    path.join(QA_DIR, "inspect.ndjson"),
    inspection.ndjson,
    "utf8",
  );

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL);
  await fs.rm(`${FINAL}.inspect.ndjson`, { force: true });
  const rtlSlides = await enforceArabicParagraphDirection(FINAL);
  console.log(
    JSON.stringify(
      {
        final: FINAL,
        qaDir: QA_DIR,
        slides: presentation.slides.items.length,
        rtlSlides,
        qaFiles,
      },
      null,
      2,
    ),
  );
  process.exit(0);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
