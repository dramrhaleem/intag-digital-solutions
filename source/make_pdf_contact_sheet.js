const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const ROOT = path.resolve(__dirname, '..');
const inputDir = path.join(ROOT, 'tmp', 'pdfs', 'brandbook-v2');
const output = path.join(ROOT, 'output', 'previews', 'INTAG_BrandBook_AllPages_PDF_Render_v2.png');

async function main() {
  const files = fs.readdirSync(inputDir)
    .filter((name) => name.toLowerCase().endsWith('.png'))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  if (files.length !== 44) throw new Error(`Expected 44 rendered pages, found ${files.length}`);

  const thumbW = 320;
  const thumbH = 180;
  const gap = 14;
  const cols = 4;
  const rows = Math.ceil(files.length / cols);
  const width = cols * thumbW + (cols + 1) * gap;
  const height = rows * thumbH + (rows + 1) * gap;
  const composites = [];

  for (let i = 0; i < files.length; i += 1) {
    const page = await sharp(path.join(inputDir, files[i]))
      .resize(thumbW, thumbH, { fit: 'fill' })
      .png()
      .toBuffer();
    composites.push({
      input: page,
      left: gap + (i % cols) * (thumbW + gap),
      top: gap + Math.floor(i / cols) * (thumbH + gap),
    });
  }

  await sharp({ create: { width, height, channels: 4, background: '#cfd1cf' } })
    .composite(composites)
    .png({ compressionLevel: 9 })
    .toFile(output);
  console.log(output);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
