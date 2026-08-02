const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const HTML = path.join(ROOT, 'brandbook', 'index.html');
const OUT = path.join(ROOT, 'output', 'previews', 'brandbook-geometry-audit-v2.json');

async function main() {
  const chromePath = process.env.INTAG_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  const page = await browser.newPage({ viewport: { width: 1624, height: 920 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(HTML).href, { waitUntil: 'load', timeout: 60000 });
  await page.waitForFunction(() => !document.fonts || document.fonts.status === 'loaded', null, { timeout: 60000 });

  const audit = await page.evaluate(() => {
    const meaningful = [
      '.page-title', '.display', '.huge', '.lead', '.body-copy', '.card', '.image-frame',
      '.grid-2', '.grid-3', '.grid-4', '.grid-6', '.split', '.logo-grid', '.mockup-grid',
      '.social-grid', '.asset-table', '.timeline', '.composition-demo', '.do-dont', '.type-spec',
    ].join(',');

    return [...document.querySelectorAll('.page')].map((sheet, index) => {
      const sheetRect = sheet.getBoundingClientRect();
      const numbered = sheet.dataset.page || '';
      const zoneExempt = sheet.classList.contains('no-pad') || sheet.classList.contains('no-number');
      const items = [...sheet.querySelectorAll(meaningful)]
        .filter((el) => {
          const style = getComputedStyle(el);
          const rect = el.getBoundingClientRect();
          return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 1 && rect.height > 1;
        })
        .map((el) => {
          const rect = el.getBoundingClientRect();
          const style = getComputedStyle(el);
          return {
            selector: el.className || el.tagName.toLowerCase(),
            top: Math.round(rect.top - sheetRect.top),
            bottom: Math.round(rect.bottom - sheetRect.top),
            height: Math.round(rect.height),
            clientWidth: el.clientWidth,
            clientHeight: el.clientHeight,
            scrollWidth: el.scrollWidth,
            scrollHeight: el.scrollHeight,
            overflowX: style.overflowX,
            overflowY: style.overflowY,
            clippedX: style.overflowX !== 'visible' && el.scrollWidth > el.clientWidth + 2,
            clippedY: style.overflowY !== 'visible' && el.scrollHeight > el.clientHeight + 2,
          };
        });
      const contentBottom = items.reduce((value, item) => Math.max(value, item.bottom), 0);
      const zoneOffenders = zoneExempt ? [] : items.filter((item) => item.bottom > 812);
      const clipped = items.filter((item) => item.clippedX || item.clippedY);
      return {
        index: index + 1,
        page: numbered,
        zoneExempt,
        contentBottom,
        zoneOffenders,
        clipped,
      };
    });
  });

  await browser.close();
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const failures = audit.filter((item) => item.zoneOffenders.length || item.clipped.length);
  const report = { status: failures.length ? 'REVIEW_REQUIRED' : 'PASS', pageCount: audit.length, failures, pages: audit };
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ status: report.status, pageCount: audit.length, failureCount: failures.length, report: OUT }, null, 2));
  if (failures.length) process.exitCode = 2;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
