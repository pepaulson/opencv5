from PIL import Image, ImageDraw
import random

ref = Image.open("data/input/ref_part.png").convert("RGBA")
# Create a larger background
bg = Image.new("RGB", (1200, 800), (50, 50, 50))
# Scale down ref slightly and rotate it
ref = ref.resize((int(ref.width * 0.6), int(ref.height * 0.6)))
ref = ref.rotate(45, expand=True)
# Paste onto bg
bg.paste(ref, (200, 100), ref)

# Add some random rectangles to simulate occlusion / clutter
draw = ImageDraw.Draw(bg)
for _ in range(15):
    x, y = random.randint(0, 1200), random.randint(0, 800)
    w, h = random.randint(50, 200), random.randint(50, 200)
    draw.rectangle([x, y, x+w, y+h], fill=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))

bg.save("data/input/live_feed.png")
