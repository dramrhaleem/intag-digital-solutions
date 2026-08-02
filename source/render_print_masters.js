const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const masters = [
  {
    input: path.join(ROOT, 'templates', 'large-format', 'INTAG_Rollup_85x200cm_Bleed3mm_v2.svg'),
    output: path.join(ROOT, 'templates', 'large-format', 'INTAG_Rollup_85x200cm_Bleed3mm_v2.pdf'),
  },
];

function physicalSize(svg) {
  const tag = svg.match(/<svg\b[^>]*>/i)?.[0] || '';
  const width = tag.match(/\bwidth=["']([^"']+)["']/i)?.[1];
  const height = tag.match(/\bheight=["']([^"']+)["']/i)?.[1];
  if (!width || !height || !/mm$/i.test(width) || !/mm$/i.test(height)) {
    throw new Error(`Print master must declare physical width and height in millimetres: ${tag}`);
  }
  return { width, height };
}

async function main() {
  const chromePath = process.env.INTAG_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  const page = await browser.newPage();

  for (const master of masters) {
    if (!fs.existsSync(master.input)) throw new Error(`Missing print master: ${master.input}`);
    const svg = fs.readFileSync(master.input, 'utf8');
    const { width, height } = physicalSize(svg);
    const html = `<!doctype html><html><head><meta charset="utf-8"><style>
      @page { size: ${width} ${height}; margin: 0; }
      html, body { margin: 0; padding: 0; width: ${width}; height: ${height}; overflow: hidden; }
      body > svg { display: block; width: ${width}; height: ${height}; }
    </style></head><body>${svg}</body></html>`;
    await page.setContent(html, { waitUntil: 'load' });
    await page.waitForFunction(() => !document.fonts || document.fonts.status === 'loaded', null, { timeout: 60000 });
    fs.mkdirSync(path.dirname(master.output), { recursive: true });
    await page.pdf({
      path: master.output,
      printBackground: true,
      preferCSSPageSize: true,
      width,
      height,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
      displayHeaderFooter: false,
    });
    console.log(`Rendered ${path.relative(ROOT, master.output)} at ${width} × ${height}.`);
  }

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
