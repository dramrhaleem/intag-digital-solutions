const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const ROOT = path.resolve(__dirname, '..');
const LOGO_SVG = path.join(ROOT, 'assets', 'logo', 'svg');
const LOGO_PNG = path.join(ROOT, 'assets', 'logo', 'png');
const PREVIEWS = path.join(ROOT, 'output', 'previews');
const KEY_VISUAL = path.join(ROOT, 'assets', 'key-visual', 'INTAG_KeyVisual_Master_16x9_v1.png');

fs.mkdirSync(LOGO_PNG, { recursive: true });
fs.mkdirSync(PREVIEWS, { recursive: true });

async function renderSvg(input, output, opts = {}) {
  const density = opts.density || 240;
  let pipeline = sharp(input, { density, limitInputPixels: false });
  if (opts.width || opts.height) {
    pipeline = pipeline.resize({
      width: opts.width,
      height: opts.height,
      fit: opts.fit || 'contain',
      background: opts.background || { r: 0, g: 0, b: 0, alpha: 0 },
      position: opts.position || 'centre',
    });
  }
  await pipeline.png({ compressionLevel: 9, adaptiveFiltering: true }).toFile(output);
}

async function renderLogoFamily() {
  const symbol = path.join(LOGO_SVG, 'INTAG_Symbol_Color_RGB_v1.svg');
  for (const size of [32, 64, 128, 256, 512, 1024]) {
    await renderSvg(symbol, path.join(LOGO_PNG, `INTAG_Symbol_Color_RGB_v1_${size}.png`), { width: size, height: size });
  }

  const small = path.join(LOGO_SVG, 'INTAG_Symbol_Small_RGB_v1.svg');
  for (const size of [16, 24, 32]) {
    await renderSvg(small, path.join(LOGO_PNG, `INTAG_Symbol_Small_RGB_v1_${size}.png`), { width: size, height: size });
  }
  const smallReverse = path.join(LOGO_SVG, 'INTAG_Symbol_Small_Reverse_RGB_v1.svg');
  for (const size of [16, 24, 32]) {
    await renderSvg(smallReverse, path.join(LOGO_PNG, `INTAG_Symbol_Small_Reverse_RGB_v1_${size}.png`), { width: size, height: size });
  }

  const symbolReverse = path.join(LOGO_SVG, 'INTAG_Symbol_Reverse_RGB_v1.svg');
  for (const size of [32, 64, 128, 256, 512]) {
    await renderSvg(symbolReverse, path.join(LOGO_PNG, `INTAG_Symbol_Reverse_RGB_v1_${size}.png`), { width: size, height: size });
  }

  const app = path.join(LOGO_SVG, 'INTAG_AppIcon_RGB_v1.svg');
  for (const size of [180, 192, 512, 1024]) {
    await renderSvg(app, path.join(LOGO_PNG, `INTAG_AppIcon_RGB_v1_${size}.png`), { width: size, height: size });
  }
  const maskable = path.join(LOGO_SVG, 'INTAG_AppIcon_Maskable_RGB_v1.svg');
  for (const size of [192, 512, 1024]) {
    await renderSvg(maskable, path.join(LOGO_PNG, `INTAG_AppIcon_Maskable_RGB_v1_${size}.png`), { width: size, height: size });
  }

  const avatar = path.join(LOGO_SVG, 'INTAG_Avatar_Dark_RGB_v1.svg');
  for (const size of [320, 512, 1024]) {
    await renderSvg(avatar, path.join(LOGO_PNG, `INTAG_Avatar_Dark_RGB_v1_${size}.png`), { width: size, height: size });
  }

  const horizontal = path.join(LOGO_SVG, 'INTAG_Logo_Primary_Horizontal_RGB_v1.svg');
  for (const width of [320, 640, 1280, 1920]) {
    await renderSvg(horizontal, path.join(LOGO_PNG, `INTAG_Logo_Primary_Horizontal_RGB_v1_${width}w.png`), { width });
  }

  const horizontalReverse = path.join(LOGO_SVG, 'INTAG_Logo_Primary_Horizontal_Reverse_RGB_v1.svg');
  for (const width of [640, 1280]) {
    await renderSvg(horizontalReverse, path.join(LOGO_PNG, `INTAG_Logo_Primary_Horizontal_Reverse_RGB_v1_${width}w.png`), { width });
  }

  const descriptor = path.join(LOGO_SVG, 'INTAG_Logo_Descriptor_EN_RGB_v1.svg');
  for (const width of [640, 1280]) {
    await renderSvg(descriptor, path.join(LOGO_PNG, `INTAG_Logo_Descriptor_EN_RGB_v1_${width}w.png`), { width });
  }

  const additionalFamilies = [
    ['INTAG_Logo_Primary_Horizontal_Black_v1.svg', 'INTAG_Logo_Primary_Horizontal_Black_v1', [640, 1280]],
    ['INTAG_Logo_Primary_Horizontal_White_v1.svg', 'INTAG_Logo_Primary_Horizontal_White_v1', [640, 1280]],
    ['INTAG_Logo_Descriptor_EN_Reverse_RGB_v1.svg', 'INTAG_Logo_Descriptor_EN_Reverse_RGB_v1', [640, 1280]],
    ['INTAG_Logo_Stacked_RGB_v1.svg', 'INTAG_Logo_Stacked_RGB_v1', [512, 1024]],
    ['INTAG_Logo_Stacked_Reverse_RGB_v1.svg', 'INTAG_Logo_Stacked_Reverse_RGB_v1', [512, 1024]],
    ['INTAG_Wordmark_Ink_v1.svg', 'INTAG_Wordmark_Ink_v1', [640, 1280]],
    ['INTAG_Wordmark_White_v1.svg', 'INTAG_Wordmark_White_v1', [640, 1280]],
  ];
  for (const [sourceName, outputStem, widths] of additionalFamilies) {
    for (const width of widths) {
      await renderSvg(path.join(LOGO_SVG, sourceName), path.join(LOGO_PNG, `${outputStem}_${width}w.png`), { width });
    }
  }
}

async function renderKeyVisualCrops() {
  const outDir = path.dirname(KEY_VISUAL);
  await sharp(KEY_VISUAL)
    .resize({ width: 1600, height: 900, fit: 'cover', position: 'attention' })
    .png({ compressionLevel: 9 })
    .toFile(path.join(outDir, 'INTAG_KeyVisual_Hero_1600x900_v1.png'));
  await sharp(KEY_VISUAL)
    .resize({ width: 1080, height: 1080, fit: 'cover', position: 'attention' })
    .png({ compressionLevel: 9 })
    .toFile(path.join(outDir, 'INTAG_KeyVisual_Square_1080_v1.png'));
  await sharp(KEY_VISUAL)
    .resize({ width: 1080, height: 1350, fit: 'cover', position: 'attention' })
    .png({ compressionLevel: 9 })
    .toFile(path.join(outDir, 'INTAG_KeyVisual_Portrait_1080x1350_v1.png'));
  await sharp(KEY_VISUAL)
    .resize({ width: 1080, height: 1920, fit: 'cover', position: 'attention' })
    .png({ compressionLevel: 9 })
    .toFile(path.join(outDir, 'INTAG_KeyVisual_Story_1080x1920_v1.png'));
  await sharp(KEY_VISUAL)
    .resize({ width: 1280, height: 720, fit: 'cover', position: 'attention' })
    .webp({ quality: 88, smartSubsample: true })
    .toFile(path.join(outDir, 'INTAG_KeyVisual_Web_1280x720_v1.webp'));
}

async function renderPreviews() {
  const previewSpecs = [
    ['assets/logo/svg/INTAG_Logo_Concepts_v1.svg', 'INTAG_Logo_Concepts_v1.png', 1600],
    ['assets/logo/svg/INTAG_Logo_Construction_v1.svg', 'INTAG_Logo_Construction_v1.png', 1600],
    ['assets/icons/INTAG_IconLibrary_ContactSheet_v1.svg', 'INTAG_IconLibrary_ContactSheet_v1.png', 1600],
    ['assets/patterns/INTAG_Pattern_ProductionGrid_Light_v1.svg', 'INTAG_Pattern_ProductionGrid_Light_v1.png', 1200],
    ['templates/stationery/INTAG_BusinessCard_Front_90x50mm_v1.svg', 'INTAG_BusinessCard_Front_v1.png', 1400],
    ['templates/stationery/INTAG_BusinessCard_Back_90x50mm_v1.svg', 'INTAG_BusinessCard_Back_v1.png', 1400],
    ['templates/stationery/INTAG_BusinessCard_Front_90x50mm_Bleed3mm_v2.svg', 'INTAG_BusinessCard_Front_v2.png', 1400],
    ['templates/stationery/INTAG_BusinessCard_Back_90x50mm_Bleed3mm_v2.svg', 'INTAG_BusinessCard_Back_v2.png', 1400],
    ['templates/stationery/INTAG_Letterhead_A4_v1.svg', 'INTAG_Letterhead_A4_v1.png', 1200],
    ['templates/proposal/INTAG_Proposal_Cover_A4_v1.svg', 'INTAG_Proposal_Cover_A4_v1.png', 1200],
    ['templates/social/INTAG_Social_Square_1080_v1.svg', 'INTAG_Social_Square_v1.png', 1080],
    ['templates/social/INTAG_Social_Portrait_1080x1350_v1.svg', 'INTAG_Social_Portrait_v1.png', 1080],
    ['templates/social/INTAG_Story_1080x1920_v1.svg', 'INTAG_Story_v1.png', 675],
    ['templates/presentation/INTAG_Presentation_Cover_16x9_v1.svg', 'INTAG_Presentation_Cover_v1.png', 1600],
    ['templates/presentation/INTAG_Presentation_Content_16x9_v1.svg', 'INTAG_Presentation_Content_v1.png', 1600],
    ['templates/digital/INTAG_Website_Hero_1440_v1.svg', 'INTAG_Website_Hero_v1.png', 1440],
    ['templates/large-format/INTAG_Rollup_Mockup_v2.svg', 'INTAG_Rollup_Mockup_v2.png', 1200, 72],
    ['templates/large-format/INTAG_Rollup_85x200cm_ProductionGuide_v2.svg', 'INTAG_Rollup_ProductionGuide_v2.png', 680, 36],
  ];
  for (const [relative, filename, width, density] of previewSpecs) {
    await renderSvg(path.join(ROOT, relative), path.join(PREVIEWS, filename), { width, density });
  }
}

async function main() {
  await renderLogoFamily();
  await renderKeyVisualCrops();
  await renderPreviews();
  console.log('Rendered INTAG PNG, WebP, and preview assets.');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
