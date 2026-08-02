const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const svgDir = path.join(ROOT, 'assets', 'logo', 'svg');
const outDir = path.join(ROOT, 'assets', 'logo', 'print');
fs.mkdirSync(outDir, { recursive: true });

const files = [
  'INTAG_Logo_Primary_Horizontal_RGB_v1.svg',
  'INTAG_Logo_Primary_Horizontal_Reverse_RGB_v1.svg',
  'INTAG_Logo_Primary_Horizontal_Black_v1.svg',
  'INTAG_Logo_Descriptor_EN_RGB_v1.svg',
  'INTAG_Logo_Stacked_RGB_v1.svg',
  'INTAG_Symbol_Color_RGB_v1.svg',
  'INTAG_Symbol_Black_v1.svg',
];

async function main() {
  const chromePath = process.env.INTAG_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  for (const file of files) {
    await page.goto(pathToFileURL(path.join(svgDir, file)).href, { waitUntil: 'load' });
    const box = await page.evaluate(() => {
      const svg = document.querySelector('svg');
      const vb = svg.viewBox.baseVal;
      return { width: Math.ceil(vb.width), height: Math.ceil(vb.height) };
    });
    await page.pdf({
      path: path.join(outDir, file.replace(/\.svg$/i, '.pdf')),
      printBackground: true,
      width: `${box.width}px`,
      height: `${box.height}px`,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
      displayHeaderFooter: false,
    });
  }
  await browser.close();
  console.log(`Rendered ${files.length} vector logo PDFs.`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
