#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <opencv2/opencv.hpp>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <random>
#include <sstream>
#include <cmath>

namespace py = pybind11;

struct Point3D {
    float x, y, z;
    int r, g, b;
};

py::dict fit_plane_ransac(const std::string& input_ply, const std::string& output_ply, double distance_threshold, int max_iterations) {
    // 1. Read PLY
    std::ifstream infile(input_ply);
    if (!infile.is_open()) {
        throw std::runtime_error("Could not open input PLY file: " + input_ply);
    }
    std::string line;
    int num_vertices = 0;
    while (std::getline(infile, line)) {
        if (line.find("element vertex") != std::string::npos) {
            std::istringstream iss(line);
            std::string t1, t2;
            iss >> t1 >> t2 >> num_vertices;
        }
        if (line == "end_header") {
            break;
        }
    }
    
    std::vector<Point3D> points;
    points.reserve(num_vertices);
    for (int i = 0; i < num_vertices; ++i) {
        if (!std::getline(infile, line)) break;
        std::istringstream iss(line);
        Point3D p;
        if (iss >> p.x >> p.y >> p.z >> p.r >> p.g >> p.b) {
            points.push_back(p);
        }
    }
    infile.close();

    if (points.size() < 3) {
        throw std::runtime_error("Not enough points to fit a plane.");
    }

    // 2. RANSAC
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, points.size() - 1);

    int best_inlier_count = 0;
    std::vector<int> best_inliers;
    float best_nx = 0, best_ny = 0, best_nz = 1, best_d = 0;

    for (int iter = 0; iter < max_iterations; ++iter) {
        int idx1 = dis(gen);
        int idx2 = dis(gen);
        int idx3 = dis(gen);
        if (idx1 == idx2 || idx1 == idx3 || idx2 == idx3) continue;

        Point3D p1 = points[idx1];
        Point3D p2 = points[idx2];
        Point3D p3 = points[idx3];

        // Vectors
        float v1x = p2.x - p1.x, v1y = p2.y - p1.y, v1z = p2.z - p1.z;
        float v2x = p3.x - p1.x, v2y = p3.y - p1.y, v2z = p3.z - p1.z;

        // Cross product for normal
        float nx = v1y * v2z - v1z * v2y;
        float ny = v1z * v2x - v1x * v2z;
        float nz = v1x * v2y - v1y * v2x;

        float norm = std::sqrt(nx*nx + ny*ny + nz*nz);
        if (norm < 1e-6) continue;
        nx /= norm; ny /= norm; nz /= norm;

        // Plane eq: nx*x + ny*y + nz*z + d = 0
        float d = -(nx * p1.x + ny * p1.y + nz * p1.z);

        std::vector<int> current_inliers;
        for (size_t i = 0; i < points.size(); ++i) {
            float dist = std::abs(nx * points[i].x + ny * points[i].y + nz * points[i].z + d);
            if (dist < distance_threshold) {
                current_inliers.push_back(i);
            }
        }

        if (current_inliers.size() > best_inlier_count) {
            best_inlier_count = current_inliers.size();
            best_inliers = current_inliers;
            best_nx = nx;
            best_ny = ny;
            best_nz = nz;
            best_d = d;
        }
    }

    // 3. Re-calculate centroid and color inliers
    float cx = 0, cy = 0, cz = 0;
    for (int idx : best_inliers) {
        cx += points[idx].x;
        cy += points[idx].y;
        cz += points[idx].z;
        
        // Color inliers bright green
        points[idx].r = 0;
        points[idx].g = 255;
        points[idx].b = 0;
    }
    if (best_inlier_count > 0) {
        cx /= best_inlier_count;
        cy /= best_inlier_count;
        cz /= best_inlier_count;
    }
    
    // Ensure normal points towards camera (Z < 0 typically, but let's check dot product with C)
    if ((cx * best_nx + cy * best_ny + cz * best_nz) > 0) {
        best_nx = -best_nx;
        best_ny = -best_ny;
        best_nz = -best_nz;
    }

    // 4. Write output PLY
    std::ofstream outfile(output_ply);
    outfile << "ply\n";
    outfile << "format ascii 1.0\n";
    outfile << "element vertex " << points.size() << "\n";
    outfile << "property float x\n";
    outfile << "property float y\n";
    outfile << "property float z\n";
    outfile << "property uchar red\n";
    outfile << "property uchar green\n";
    outfile << "property uchar blue\n";
    outfile << "end_header\n";
    for (const auto& p : points) {
        outfile << p.x << " " << p.y << " " << p.z << " " 
                << p.r << " " << p.g << " " << p.b << "\n";
    }
    outfile.close();

    // 5. Return dict
    py::dict result;
    result["success"] = true;
    result["nx"] = best_nx;
    result["ny"] = best_ny;
    result["nz"] = best_nz;
    result["cx"] = cx;
    result["cy"] = cy;
    result["cz"] = cz;
    result["inlier_ratio"] = (float)best_inlier_count / points.size() * 100.0f;
    result["output_path"] = output_ply;
    
    return result;
}
