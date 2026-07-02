import cv2
import numpy as np
import os

output_dir = "/home/dev/Projects/opencv5/data/input"
os.makedirs(output_dir, exist_ok=True)

# Generate checkerboard images
board_w = 9
board_h = 6
square_size = 50
width, height = board_w * square_size + 100, board_h * square_size + 100

for i in range(1, 11):
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    for y in range(board_h):
        for x in range(board_w):
            if (x + y) % 2 == 0:
                cv2.rectangle(img, (x * square_size + 50, y * square_size + 50), 
                              ((x+1) * square_size + 50, (y+1) * square_size + 50), (0,0,0), -1)
                
    pts1 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
    perturb = np.random.randint(-30, 30, (4, 2)).astype(np.float32)
    pts2 = pts1 + perturb
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    img = cv2.warpPerspective(img, matrix, (width, height), borderValue=(255,255,255))
    
    cv2.imwrite(os.path.join(output_dir, f"checkerboard_{i}.png"), img)

# Generate ArUco marker
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
marker_img = cv2.aruco.generateImageMarker(aruco_dict, 23, 200)

scene = np.ones((480, 640), dtype=np.uint8) * 255
scene[140:340, 220:420] = marker_img
scene = cv2.cvtColor(scene, cv2.COLOR_GRAY2BGR)

pts1 = np.float32([[0, 0], [640, 0], [0, 480], [640, 480]])
pts2 = np.float32([[50, 50], [590, 20], [20, 430], [620, 450]])
matrix = cv2.getPerspectiveTransform(pts1, pts2)
scene = cv2.warpPerspective(scene, matrix, (640, 480), borderValue=(255,255,255))

cv2.imwrite(os.path.join(output_dir, "aruco_scene.png"), scene)
print("Sample images generated successfully.")
