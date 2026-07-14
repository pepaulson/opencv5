#include <opencv2/opencv.hpp>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

std::string generate_point_cloud(const std::string& rgb_path, const std::string& depth_path, const std::string& output_path, double fx, double fy, double cx, double cy, double scale) {
    cv::Mat rgb = cv::imread(rgb_path, cv::IMREAD_COLOR);
    cv::Mat depth = cv::imread(depth_path, cv::IMREAD_ANYDEPTH);

    if (rgb.empty() || depth.empty()) {
        throw std::runtime_error("Could not load RGB or Depth image.");
    }
    if (depth.type() != CV_16U) {
        throw std::runtime_error("Depth image is not 16-bit unsigned (CV_16U).");
    }

    std::vector<cv::Vec3f> points;
    std::vector<cv::Vec3b> colors;
    
    points.reserve(depth.rows * depth.cols);
    colors.reserve(depth.rows * depth.cols);

    for (int v = 0; v < depth.rows; ++v) {
        for (int u = 0; u < depth.cols; ++u) {
            uint16_t d = depth.at<uint16_t>(v, u);
            if (d == 0) continue; // Invalid depth

            double z = static_cast<double>(d) / scale;
            double x = (u - cx) * z / fx;
            double y = (v - cy) * z / fy;

            points.push_back(cv::Vec3f(static_cast<float>(x), static_cast<float>(y), static_cast<float>(z)));
            cv::Vec3b color = rgb.at<cv::Vec3b>(v, u); // OpenCV reads BGR
            // Convert BGR to RGB for PLY
            colors.push_back(cv::Vec3b(color[2], color[1], color[0]));
        }
    }

    std::ofstream file(output_path);
    if (!file.is_open()) {
        throw std::runtime_error("Could not open output file for writing.");
    }

    file << "ply\n";
    file << "format ascii 1.0\n";
    file << "element vertex " << points.size() << "\n";
    file << "property float x\n";
    file << "property float y\n";
    file << "property float z\n";
    file << "property uchar red\n";
    file << "property uchar green\n";
    file << "property uchar blue\n";
    file << "end_header\n";

    for (size_t i = 0; i < points.size(); ++i) {
        file << points[i][0] << " " << points[i][1] << " " << points[i][2] << " "
             << static_cast<int>(colors[i][0]) << " " << static_cast<int>(colors[i][1]) << " " << static_cast<int>(colors[i][2]) << "\n";
    }
    file.close();

    return output_path;
}
