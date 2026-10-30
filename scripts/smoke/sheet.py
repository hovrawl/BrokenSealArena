"""Joins screenshots into one contact sheet: sheet.py OUT.png IN.png ..."""
import sys
from PIL import Image

out, files = sys.argv[1], sys.argv[2:]
images = [Image.open(f).resize((360, 240)) for f in files]
columns = 3
rows = (len(images) + columns - 1) // columns
sheet = Image.new("RGB", (columns * 360, rows * 240))
for i, image in enumerate(images):
    sheet.paste(image, ((i % columns) * 360, (i // columns) * 240))
sheet.save(out)
