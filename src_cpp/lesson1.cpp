#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <opencv2/opencv.hpp>
#include <iostream>
#include <string>

namespace py = pybind11;

std::string run_lesson_1(const std::string& input_path, const std::string& output_path, int threshold_value) {
    std::cout << "[C++] Loading image: " << input_path << std::endl;
    cv::Mat image = cv::imread(input_path, cv::IMREAD_COLOR);
    if (image.empty()) {
        throw std::runtime_error("Could not read image: " + input_path);
    }

    std::cout << "[C++] Converting to grayscale..." << std::endl;
    cv::Mat gray;
    cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);

    std::cout << "[C++] Applying binary threshold (value: " << threshold_value << ")..." << std::endl;
    cv::Mat thresholded;
    cv::threshold(gray, thresholded, threshold_value, 255, cv::THRESH_BINARY);

    std::cout << "[C++] Saving output image to: " << output_path << std::endl;
    bool success = cv::imwrite(output_path, thresholded);
    if (!success) {
        throw std::runtime_error("Could not write image to: " + output_path);
    }

    return output_path;
}

extern void init_lesson2_filters(py::module_ &m);

PYBIND11_MODULE(cv_engine, m) {
    m.doc() = "OpenCV C++ core logic for Temporal Learning Lab"; // optional module docstring
    m.def("run_lesson_1", &run_lesson_1, "A function that processes an image for Lesson 1",
          py::arg("input_path"), py::arg("output_path"), py::arg("threshold_value"));
          
    init_lesson2_filters(m);
}
