from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
png_dir = ROOT / "assets" / "logo" / "png"
source = png_dir / "INTAG_AppIcon_RGB_v1_1024.png"
output = png_dir / "favicon.ico"

image = Image.open(source).convert("RGBA")
image.save(output, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(output)
