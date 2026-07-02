import math
from PIL import Image, ImageDraw

def generate_image():
    # 1. Create a dark gray background image (simulating a conveyor belt)
    # Size 800x600
    width, height = 800, 600
    bg_color = (30, 30, 30) # Dark gray
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 2. Draw part 1: A circular washer with a center hole
    # Centered at (180, 180), outer radius 60, inner hole radius 20
    c1_x, c1_y = 180, 180
    r_outer = 60
    r_inner = 20
    draw.ellipse([c1_x - r_outer, c1_y - r_outer, c1_x + r_outer, c1_y + r_outer], fill=(220, 220, 220))
    draw.ellipse([c1_x - r_inner, c1_y - r_inner, c1_x + r_inner, c1_y + r_inner], fill=bg_color)

    # 3. Draw part 2: A rotated rectangular plate
    # Centered at (450, 180), size 150x60, rotated by 35 degrees clockwise
    c2_x, c2_y = 450, 180
    rect_w, rect_h = 150, 60
    angle_deg = 35
    angle_rad = math.radians(angle_deg)
    
    # Half dimensions
    hw, hh = rect_w / 2.0, rect_h / 2.0
    
    # 4 corners relative to center before rotation
    corners = [
        (-hw, -hh),
        (hw, -hh),
        (hw, hh),
        (-hw, hh)
    ]
    
    # Rotate and translate corners
    rotated_corners = []
    for x, y in corners:
        rx = x * math.cos(angle_rad) - y * math.sin(angle_rad) + c2_x
        ry = x * math.sin(angle_rad) + y * math.cos(angle_rad) + c2_y
        rotated_corners.append((rx, ry))
        
    draw.polygon(rotated_corners, fill=(240, 240, 240))

    # 4. Draw part 3: Hexagonal nut
    # Centered at (280, 430), outer radius 55, inner hole radius 18
    c3_x, c3_y = 280, 430
    hex_r = 55
    hex_inner_r = 18
    hex_corners = []
    for i in range(6):
        # Rotate by 15 degrees to make it look randomly oriented
        a = i * math.pi / 3.0 + math.radians(15)
        hx = c3_x + hex_r * math.cos(a)
        hy = c3_y + hex_r * math.sin(a)
        hex_corners.append((hx, hy))
        
    draw.polygon(hex_corners, fill=(210, 210, 210))
    draw.ellipse([c3_x - hex_inner_r, c3_y - hex_inner_r, c3_x + hex_inner_r, c3_y + hex_inner_r], fill=bg_color)

    # 5. Draw part 4: Triangular bracket
    # Vertices around (580, 440)
    tri_points = [
        (580, 360),
        (720, 430),
        (600, 520)
    ]
    draw.polygon(tri_points, fill=(230, 230, 230))

    # Save the output image
    import os
    os.makedirs("data/input", exist_ok=True)
    img.save("data/input/conveyor_parts.png", "PNG")
    print("Generated conveyor_parts.png successfully.")

if __name__ == "__main__":
    generate_image()
