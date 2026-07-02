#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <opencv2/opencv.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/geometry/2d.hpp>
#include <iostream>
#include <vector>
#include <string>

namespace py = pybind11;

// Struct to hold part localization coordinates
struct PartCoordinates {
    double x;
    double y;
    double angle;
    double area;
    std::vector<std::pair<double, double>> bounding_box;
};

// Struct to hold the overall result of contour detection
struct ContourDetectionResult {
    std::vector<std::vector<cv::Point>> contours;
    std::vector<PartCoordinates> parts;
};

// C++ implementation for Lesson 4
ContourDetectionResult run_lesson_4_contours(const std::string& input_path, double min_area) {
    std::cout << "[C++] Lesson 4: Loading image from: " << input_path << std::endl;
    
    // Load image as grayscale first to perform edge/contour detection
    cv::Mat image = cv::imread(input_path, cv::IMREAD_GRAYSCALE);
    if (image.empty()) {
        throw std::runtime_error("Could not read image: " + input_path);
    }

    std::cout << "[C++] Lesson 4: Binarizing image..." << std::endl;
    cv::Mat binary;
    // Binarize using standard binary threshold (since parts are light on a dark background)
    cv::threshold(image, binary, 127, 255, cv::THRESH_BINARY);

    std::cout << "[C++] Lesson 4: Running cv::findContours..." << std::endl;
    std::vector<std::vector<cv::Point>> raw_contours;
    std::vector<cv::Vec4i> hierarchy;
    
    // RETR_EXTERNAL retrieves only the extreme outer contours
    cv::findContours(binary, raw_contours, hierarchy, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);
    
    std::cout << "[C++] Lesson 4: Found " << raw_contours.size() << " raw contours. Processing..." << std::endl;

    ContourDetectionResult result;
    // Memory management: Reserve space to avoid frequent reallocations in std::vector
    result.parts.reserve(raw_contours.size());
    result.contours.reserve(raw_contours.size());

    for (size_t i = 0; i < raw_contours.size(); ++i) {
        // 1. Calculate contour area
        double area = cv::contourArea(raw_contours[i]);
        if (area < min_area) {
            std::cout << "[C++] Lesson 4: Skipping contour " << i << " with area " << area << " (below min_area threshold of " << min_area << ")" << std::endl;
            continue;
        }

        // Keep this contour
        result.contours.push_back(raw_contours[i]);

        // 2. Calculate moments to find the center of mass (centroid)
        cv::Moments m = cv::moments(raw_contours[i]);
        double cx = 0.0;
        double cy = 0.0;
        if (m.m00 != 0.0) {
            cx = m.m10 / m.m00;
            cy = m.m01 / m.m00;
        }

        // 3. Calculate minimum area bounding rectangle
        cv::RotatedRect min_rect = cv::minAreaRect(raw_contours[i]);

        // 4. Retrieve corners of the bounding rectangle
        cv::Point2f rect_points[4];
        min_rect.points(rect_points);

        std::vector<std::pair<double, double>> bbox;
        bbox.reserve(4);
        for (int j = 0; j < 4; ++j) {
            bbox.push_back({static_cast<double>(rect_points[j].x), static_cast<double>(rect_points[j].y)});
        }

        // Populate our custom struct
        PartCoordinates coords;
        coords.x = cx;
        coords.y = cy;
        coords.angle = static_cast<double>(min_rect.angle);
        coords.area = area;
        coords.bounding_box = bbox;

        result.parts.push_back(coords);
        
        std::cout << "[C++] Lesson 4: Detected Part " << result.parts.size() 
                  << " | Centroid: (" << cx << ", " << cy 
                  << ") | Angle: " << coords.angle 
                  << " | Area: " << area << std::endl;
    }

    std::cout << "[C++] Lesson 4: Extraction finished. Returning " << result.parts.size() << " parts." << std::endl;
    return result;
}

// Bind C++ types and function to pybind11
void init_lesson4_contours(py::module_ &m) {
    // Bind cv::Point so it can be handled across Python boundary
    // cv::Point is an alias for cv::Point2i
    py::class_<cv::Point>(m, "Point")
        .def(py::init<int, int>())
        .def_readwrite("x", &cv::Point::x)
        .def_readwrite("y", &cv::Point::y);

    // Bind our custom structs
    py::class_<PartCoordinates>(m, "PartCoordinates")
        .def(py::init<>())
        .def_readwrite("x", &PartCoordinates::x)
        .def_readwrite("y", &PartCoordinates::y)
        .def_readwrite("angle", &PartCoordinates::angle)
        .def_readwrite("area", &PartCoordinates::area)
        .def_readwrite("bounding_box", &PartCoordinates::bounding_box);

    py::class_<ContourDetectionResult>(m, "ContourDetectionResult")
        .def(py::init<>())
        .def_readwrite("contours", &ContourDetectionResult::contours)
        .def_readwrite("parts", &ContourDetectionResult::parts);

    m.def("run_lesson_4_contours", &run_lesson_4_contours, "Find contours, calculate centroids using moments, and get rotated bounding rects.",
          py::arg("input_path"), py::arg("min_area"));
}
