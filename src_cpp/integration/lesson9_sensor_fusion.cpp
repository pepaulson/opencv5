#include <opencv2/opencv.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
#include <iostream>
#include <algorithm>

namespace py = pybind11;

// Module A (2D): Extract bounding boxes of targets using HSV segmentation
std::vector<py::dict> detect_harvest_targets(const std::string& rgb_image_path, py::list hsv_lower, py::list hsv_upper) {
    std::vector<py::dict> targets;
    
    cv::Mat image = cv::imread(rgb_image_path);
    if (image.empty()) {
        std::cerr << "Failed to load image: " << rgb_image_path << std::endl;
        return targets;
    }
    
    cv::Mat hsv_image;
    cv::cvtColor(image, hsv_image, cv::COLOR_BGR2HSV);
    
    cv::Scalar lower(hsv_lower[0].cast<int>(), hsv_lower[1].cast<int>(), hsv_lower[2].cast<int>());
    cv::Scalar upper(hsv_upper[0].cast<int>(), hsv_upper[1].cast<int>(), hsv_upper[2].cast<int>());
    
    cv::Mat mask;
    cv::inRange(hsv_image, lower, upper, mask);
    
    std::vector<std::vector<cv::Point>> contours;
    cv::findContours(mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);
    
    for (const auto& contour : contours) {
        if (cv::contourArea(contour) > 100) { // Filter out small noise
            cv::Rect bounding_box = cv::boundingRect(contour);
            py::dict target;
            target["x"] = bounding_box.x;
            target["y"] = bounding_box.y;
            target["width"] = bounding_box.width;
            target["height"] = bounding_box.height;
            target["cx"] = bounding_box.x + bounding_box.width / 2;
            target["cy"] = bounding_box.y + bounding_box.height / 2;
            targets.push_back(target);
        }
    }
    
    return targets;
}

// Module B (3D): Extract 3D coordinates based on 2D bounding boxes and depth map
std::vector<py::dict> extract_3d_coordinates(const std::string& depth_image_path, const std::vector<py::dict>& bounding_boxes, double fx, double fy, double cx, double cy, double scale) {
    std::vector<py::dict> coordinates3d;
    
    // Load as 16-bit depth image
    cv::Mat depth_image = cv::imread(depth_image_path, cv::IMREAD_ANYDEPTH);
    if (depth_image.empty()) {
        std::cerr << "Failed to load depth image: " << depth_image_path << std::endl;
        return coordinates3d;
    }
    
    if (depth_image.type() != CV_16U) {
        std::cerr << "Depth image is not 16-bit unsigned (CV_16U)" << std::endl;
        return coordinates3d;
    }
    
    for (const auto& box_dict : bounding_boxes) {
        int x = box_dict["x"].cast<int>();
        int y = box_dict["y"].cast<int>();
        int width = box_dict["width"].cast<int>();
        int height = box_dict["height"].cast<int>();
        int uc = box_dict["cx"].cast<int>();
        int vc = box_dict["cy"].cast<int>();
        
        // Safety check on bounds
        x = std::max(0, x);
        y = std::max(0, y);
        width = std::min(width, depth_image.cols - x);
        height = std::min(height, depth_image.rows - y);
        
        if (width <= 0 || height <= 0) continue;
        
        cv::Rect roi(x, y, width, height);
        cv::Mat depth_roi = depth_image(roi);
        
        std::vector<uint16_t> valid_depths;
        
        for (int r = 0; r < depth_roi.rows; ++r) {
            for (int c = 0; c < depth_roi.cols; ++c) {
                uint16_t d = depth_roi.at<uint16_t>(r, c);
                if (d > 0) { // filter out zero values (invalid depth)
                    valid_depths.push_back(d);
                }
            }
        }
        
        if (valid_depths.empty()) continue; // No valid depth in ROI
        
        // Calculate median
        std::sort(valid_depths.begin(), valid_depths.end());
        uint16_t d_median = valid_depths[valid_depths.size() / 2];
        
        // Reproject to 3D
        double Z = static_cast<double>(d_median) / scale;
        double X = (uc - cx) * Z / fx;
        double Y = (vc - cy) * Z / fy;
        
        py::dict coord;
        coord["X"] = X;
        coord["Y"] = Y;
        coord["Z"] = Z;
        coord["u"] = uc;
        coord["v"] = vc;
        
        coordinates3d.push_back(coord);
    }
    
    return coordinates3d;
}
