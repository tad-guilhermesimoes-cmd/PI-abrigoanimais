"""Gera scripts/painel/amparapet.ico (pata branca em fundo azul), em vários tamanhos."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("amparapet.ico")
L = 512
img = Image.new("RGBA", (L, L), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((16, 16, L - 16, L - 16), radius=110, fill=(43, 74, 111, 255))

branco = (255, 255, 255, 255)
d.ellipse((150, 250, 362, 430), fill=branco)                 # almofada principal
for x, y, w, h in [(92, 190, 92, 120), (178, 110, 96, 128),  # dedos
                   (238, 110, 96, 128), (328, 190, 92, 120)]:
    d.ellipse((x, y, x + w, y + h), fill=branco)

img.save(destino, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icone:", destino)
