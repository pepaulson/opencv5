import os
import math
import random

def save_ply(filename, points, normals):
    with open(filename, 'w') as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property float nx\n")
        f.write("property float ny\n")
        f.write("property float nz\n")
        f.write("end_header\n")
        for p, n in zip(points, normals):
            f.write(f"{p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")

def generate_l_shape(offset=(0,0,0), rot_z=0, noise=0.0):
    points = []
    normals = []
    
    random.seed(42)
    
    for _ in range(500):
        x, y, z = random.uniform(-0.1, 0.1), random.uniform(-0.5, 0.5), random.uniform(-0.1, 0.1)
        nx, ny, nz = 0, 0, 0
        if abs(x) > abs(y)/5 and abs(x) > abs(z):
            nx = 1 if x > 0 else -1
        elif abs(y)/5 > abs(x) and abs(y)/5 > abs(z):
            ny = 1 if y > 0 else -1
        else:
            nz = 1 if z > 0 else -1
            
        points.append([x, y, z])
        normals.append([nx, ny, nz])
        
    for _ in range(300):
        x, y, z = random.uniform(0.1, 0.6), random.uniform(-0.5, -0.3), random.uniform(-0.1, 0.1)
        nx, ny, nz = 0, 0, 0
        if abs(x-0.35)/2.5 > abs(y+0.4) and abs(x-0.35)/2.5 > abs(z):
            nx = 1 if (x-0.35) > 0 else -1
        elif abs(y+0.4) > abs(x-0.35)/2.5 and abs(y+0.4) > abs(z):
            ny = 1 if (y+0.4) > 0 else -1
        else:
            nz = 1 if z > 0 else -1
            
        points.append([x, y, z])
        normals.append([nx, ny, nz])
        
    cos_t = math.cos(rot_z)
    sin_t = math.sin(rot_z)
    
    for i in range(len(points)):
        x, y, z = points[i]
        nx, ny, nz = normals[i]
        
        rx = x * cos_t - y * sin_t
        ry = x * sin_t + y * cos_t
        rz = z
        
        rnx = nx * cos_t - ny * sin_t
        rny = nx * sin_t + ny * cos_t
        rnz = nz
        
        rx += random.uniform(-noise, noise)
        ry += random.uniform(-noise, noise)
        rz += random.uniform(-noise, noise)
        
        points[i] = [rx + offset[0], ry + offset[1], rz + offset[2]]
        normals[i] = [rnx, rny, rnz]
        
    return points, normals

def generate_scene(num_parts=1, clutter_points=1000):
    points = []
    normals = []
    
    # Randomly place N parts
    ground_truth_poses = []
    for _ in range(num_parts):
        x = random.uniform(-0.5, 0.5)
        y = random.uniform(-0.5, 0.5)
        z = random.uniform(-0.2, 0.2)
        rot_z = random.uniform(0, 2*math.pi)
        
        ground_truth_poses.append({"offset": (x,y,z), "rot_z": rot_z})
        
        t_points, t_normals = generate_l_shape(offset=(x,y,z), rot_z=rot_z, noise=0.005)
        points.extend(t_points)
        normals.extend(t_normals)
    
    # Add Clutter
    for _ in range(clutter_points):
        points.append([random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.5, 0.5)])
        normals.append([random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)])
        norm = math.sqrt(normals[-1][0]**2 + normals[-1][1]**2 + normals[-1][2]**2)
        if norm > 0:
            normals[-1] = [n/norm for n in normals[-1]]
            
    return points, normals, ground_truth_poses

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    
    t_points, t_normals = generate_l_shape()
    save_ply(os.path.join(out_dir, 'lesson10_template.ply'), t_points, t_normals)

    s_points, s_normals, _ = generate_scene()
    save_ply(os.path.join(out_dir, 'lesson10_scene.ply'), s_points, s_normals)
    print("PLY files generated.")
