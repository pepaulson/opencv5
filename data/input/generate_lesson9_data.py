import cv2
import numpy as np
import os

# Create data/input directory if it doesn't exist
os.makedirs('/app/data/input', exist_ok=True)

width, height = 640, 480

# 1. Generate RGB Image
# Background (dark green foliage)
rgb_img = np.ones((height, width, 3), dtype=np.uint8)
rgb_img[:] = (20, 60, 20) # BGR: Dark green

# Draw some leaves (lighter green)
cv2.ellipse(rgb_img, (320, 240), (200, 100), 45, 0, 360, (40, 120, 40), -1)
cv2.ellipse(rgb_img, (150, 300), (120, 60), 120, 0, 360, (30, 100, 30), -1)

# Draw Red "Targets" (e.g., ripe fruits)
targets = [
    {"center": (350, 200), "radius": 30, "color": (30, 30, 200), "depth": 800},
    {"center": (200, 350), "radius": 40, "color": (20, 20, 220), "depth": 900},
    {"center": (450, 300), "radius": 25, "color": (40, 40, 190), "depth": 750}
]

for t in targets:
    cv2.circle(rgb_img, t["center"], t["radius"], t["color"], -1)
    # Add a little highlight for realism
    cv2.circle(rgb_img, (t["center"][0]-10, t["center"][1]-10), 5, (100, 100, 255), -1)

cv2.imwrite('/app/data/input/lesson9_rgb.png', rgb_img)

# 2. Generate 16-bit Depth Map (CV_16U)
# Base depth is 1500 (1.5 meters away if scale=1000)
depth_img = np.ones((height, width), dtype=np.uint16) * 1500

# Leaves are closer (1000 to 1200)
cv2.ellipse(depth_img, (320, 240), (200, 100), 45, 0, 360, 1100, -1)
cv2.ellipse(depth_img, (150, 300), (120, 60), 120, 0, 360, 1200, -1)

# Targets have specific depths
for t in targets:
    cv2.circle(depth_img, t["center"], t["radius"], t["depth"], -1)

# Add some noise to depth
noise = np.random.normal(0, 10, (height, width)).astype(np.int16)
depth_img = np.clip(depth_img.astype(np.int32) + noise, 0, 65535).astype(np.uint16)

cv2.imwrite('/app/data/input/lesson9_depth.png', depth_img)

print("Generated lesson9_rgb.png and lesson9_depth.png in /app/data/input/")
