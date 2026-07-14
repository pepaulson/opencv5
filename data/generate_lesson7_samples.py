import cv2
import numpy as np
import os

output_dir = "/home/dev/Projects/opencv5/data/input"
os.makedirs(output_dir, exist_ok=True)

# Image dimensions
width, height = 640, 480

# RGB image: start with a gray background (table)
rgb = np.ones((height, width, 3), dtype=np.uint8) * 150

# Depth image: start with background depth (e.g., 2000 mm = 2 meters)
depth = np.ones((height, width), dtype=np.uint16) * 2000

# Object 1: A red box closer to the camera (depth = 1200 mm)
cv2.rectangle(rgb, (100, 100), (300, 300), (0, 0, 255), -1)
cv2.rectangle(depth, (100, 100), (300, 300), 1200, -1)

# Object 2: A blue box further away (depth = 1500 mm)
cv2.rectangle(rgb, (400, 200), (550, 400), (255, 0, 0), -1)
cv2.rectangle(depth, (400, 200), (550, 400), 1500, -1)

# Object 3: A green box overlapping (depth = 1000 mm)
cv2.rectangle(rgb, (250, 250), (450, 350), (0, 255, 0), -1)
cv2.rectangle(depth, (250, 250), (450, 350), 1000, -1)

# Add some noise to the depth to make it look realistic
noise = np.random.normal(0, 5, (height, width)).astype(np.int16)
depth = np.clip(depth.astype(np.int32) + noise, 0, 65535).astype(np.uint16)

cv2.imwrite(os.path.join(output_dir, "rgb_scene.png"), rgb)
cv2.imwrite(os.path.join(output_dir, "depth_scene.png"), depth)

print("Lesson 7 samples generated successfully.")
