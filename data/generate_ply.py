import numpy as np

num_points = 50000

# Bin walls (random noise in a box)
x_bin = np.random.uniform(-1.0, 1.0, num_points // 2)
y_bin = np.random.uniform(-1.0, 1.0, num_points // 2)
z_bin = np.random.uniform(-0.5, 0.5, num_points // 2)
r_bin = np.random.randint(100, 150, num_points // 2)
g_bin = np.random.randint(100, 150, num_points // 2)
b_bin = np.random.randint(100, 150, num_points // 2)

# Flat part (a clear plane tilted slightly)
x_plane = np.random.uniform(-0.4, 0.4, num_points // 2)
y_plane = np.random.uniform(-0.4, 0.4, num_points // 2)
z_plane = 0.2 * x_plane + 0.1 * y_plane + 0.3 # plane equation
z_plane += np.random.normal(0, 0.005, num_points // 2) # small noise
r_plane = np.full(num_points // 2, 200)
g_plane = np.full(num_points // 2, 50)
b_plane = np.full(num_points // 2, 50)

x = np.concatenate([x_bin, x_plane])
y = np.concatenate([y_bin, y_plane])
z = np.concatenate([z_bin, z_plane])
r = np.concatenate([r_bin, r_plane])
g = np.concatenate([g_bin, g_plane])
b = np.concatenate([b_bin, b_plane])

with open("data/input/lesson8_sample.ply", "w") as f:
    f.write("ply\n")
    f.write("format ascii 1.0\n")
    f.write(f"element vertex {len(x)}\n")
    f.write("property float x\n")
    f.write("property float y\n")
    f.write("property float z\n")
    f.write("property uchar red\n")
    f.write("property uchar green\n")
    f.write("property uchar blue\n")
    f.write("end_header\n")
    for i in range(len(x)):
        f.write(f"{x[i]:.4f} {y[i]:.4f} {z[i]:.4f} {r[i]} {g[i]} {b[i]}\n")
