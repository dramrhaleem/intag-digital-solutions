const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');
const sharp = require('sharp');

const ROOT = path.resolve(__dirname, '..');
const HTML = path.join(ROOT, 'brandbook', 'index.html');
const PDF = path.join(ROOT, 'output', 'pdf', 'INTAG_Brand_Guidelines_v2.0_Logo02_Approved_Working.pdf');
const PREVIEWS = path.join(ROOT, 'output', 'previews', 'brandbook-pages-v2');
const CONTACT = path.join(ROOT, 'output', 'previews', 'INTAG_BrandBook_ContactSheet_v2.png');
const PROGRESS = path.join(ROOT, 'output', 'previews', 'brandbook-render-progress-v2.txt');

fs.mkdirSync(path.dirname(PDF), { recursive: true });
fs.mkdirSync(PREVIEWS, { recursive: true });
fs.writeFileSync(PROGRESS, 'render: start\n');

function progress(message) {
  fs.appendFileSync(PROGRESS, `${message}\n`);
  console.log(message);
}

const selectedPages = Array.from({ length: 44 }, (_, index) => index);

async function main() {
  const chromePath = process.env.INTAG_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  progress('render: browser launched');
  const page = await browser.newPage({ viewport: { width: 1624, height: 920 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(HTML).href, { waitUntil: 'load', timeout: 60000 });
  progress('render: document loaded');
  await page.waitForFunction(() => !document.fonts || document.fonts.status === 'loaded', null, { timeout: 60000 });
  progress('render: fonts loaded');

  const pageCount = await page.locator('.page').count();
  if (pageCount < 40) throw new Error(`Expected at least 40 pages, found ${pageCount}`);

  const overflowResults = [];
  for (const width of [1624, 1024, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await page.waitForTimeout(80);
    const metrics = await page.evaluate(() => ({
      width: innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    }));
    overflowResults.push(metrics);
    if (metrics.overflow !== 0) throw new Error(`Horizontal overflow at ${width}px: ${metrics.overflow}px`);
  }
  progress('render: responsive overflow audit passed');

  await page.setViewportSize({ width: 1624, height: 920 });
  await page.waitForTimeout(80);

  // Internal clipping is intentionally verified from the latest PDF renders:
  // getBoundingClientRect on 44 transformed sheets is pathological in some
  // Windows Chrome builds and creates false build hangs.
  const geometryAudit = { method: 'full-page PDF render + fresh-eye visual review', status: 'required after export' };
  progress('render: geometry review delegated to PDF render gate');
  for (const index of selectedPages) {
    const locator = page.locator('.page').nth(index);
    await locator.screenshot({ path: path.join(PREVIEWS, `page-${String(index + 1).padStart(2, '0')}.png`) });
    progress(`render: screenshot ${index + 1}`);
  }
  progress('render: selected screenshots written');

  await page.emulateMedia({ media: 'print' });
  await page.pdf({
    path: PDF,
    printBackground: true,
    preferCSSPageSize: true,
    width: '1600px',
    height: '900px',
    margin: { top: 0, right: 0, bottom: 0, left: 0 },
    displayHeaderFooter: false,
  });
  progress('render: PDF written');

  await browser.close();

  const thumbWidth = 320;
  const thumbHeight = 180;
  const gap = 18;
  const cols = 4;
  const rows = Math.ceil(selectedPages.length / cols);
  const canvasWidth = cols * thumbWidth + (cols + 1) * gap;
  const canvasHeight = rows * thumbHeight + (rows + 1) * gap;
  const composites = [];
  for (let i = 0; i < selectedPages.length; i += 1) {
    const index = selectedPages[i];
    const buffer = await sharp(path.join(PREVIEWS, `page-${String(index + 1).padStart(2, '0')}.png`))
      .resize(thumbWidth, thumbHeight, { fit: 'cover' })
      .png()
      .toBuffer();
    composites.push({ input: buffer, left: gap + (i % cols) * (thumbWidth + gap), top: gap + Math.floor(i / cols) * (thumbHeight + gap) });
  }
  await sharp({ create: { width: canvasWidth, height: canvasHeight, channels: 4, background: '#d8d9d5' } })
    .composite(composites)
    .png({ compressionLevel: 9 })
    .toFile(CONTACT);
  progress('render: contact sheet written');

  const report = {
    pageCount,
    overflowResults,
    geometryAudit,
    pdf: path.relative(ROOT, PDF).split(path.sep).join('/'),
    selectedPagePreviews: selectedPages.map((i) => i + 1),
  };
  fs.writeFileSync(path.join(ROOT, 'output', 'previews', 'brandbook-render-report-v2.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
