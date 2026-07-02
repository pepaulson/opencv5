#include <pybind11/pybind11.h>
#include <opencv2/opencv.hpp>
#include <iostream>
#include <string>

namespace py = pybind11;

std::string run_grayscale(const std::string& input_path, const std::string& output_path) {
    std::cout << "[C++] Grayscale: Loading image: " << input_path << std::endl;
    cv::Mat image = cv::imread(input_path, cv::IMREAD_COLOR);
    if (image.empty()) {
        throw std::runtime_error("Could not read image: " + input_path);
    }
    cv::Mat gray;
    cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);
    cv::imwrite(output_path, gray);
    return output_path;
}

std::string run_lesson_3_sobel(const std::string& input_path, const std::string& output_path) {
    std::cout << "[C++] Sobel: Loading image: " << input_path << std::endl;
    cv::Mat image = cv::imread(input_path, cv::IMREAD_GRAYSCALE);
    if (image.empty()) {
        throw std::runtime_error("Could not read image: " + input_path);
    }

    std::cout << "[C++] Sobel: Calculating gradients..." << std::endl;
    cv::Mat grad_x, grad_y;
    cv::Mat abs_grad_x, abs_grad_y;
    
    // Demonstrate converting to higher depth to avoid overflow
    cv::Sobel(image, grad_x, CV_16S, 1, 0, 3);
    cv::Sobel(image, grad_y, CV_16S, 0, 1, 3);

    // Convert back to 8-bit unsigned
    cv::convertScaleAbs(grad_x, abs_grad_x);
    cv::convertScaleAbs(grad_y, abs_grad_y);

    // Combine gradients
    cv::Mat grad;
    cv::addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0, grad);

    std::cout << "[C++] Sobel: Saving gradient image to: " << output_path << std::endl;
    bool success = cv::imwrite(output_path, grad);
    if (!success) {
        throw std::runtime_error("Could not write image to: " + output_path);
    }

    return output_path;
}

std::string run_lesson_3_canny(const std::string& input_path, const std::string& output_path, double threshold1, double threshold2) {
    std::cout << "[C++] Canny: Loading image: " << input_path << std::endl;
    cv::Mat image = cv::imread(input_path, cv::IMREAD_GRAYSCALE);
    if (image.empty()) {
        throw std::runtime_error("Could not read image: " + input_path);
    }

    std::cout << "[C++] Canny: Applying edge detection..." << std::endl;
    cv::Mat edges;
    cv::Canny(image, edges, threshold1, threshold2);

    std::cout << "[C++] Canny: Saving edges image to: " << output_path << std::endl;
    bool success = cv::imwrite(output_path, edges);
    if (!success) {
        throw std::runtime_error("Could not write image to: " + output_path);
    }

    return output_path;
}

void init_lesson3_edges(py::module_ &m) {
    m.def("run_grayscale", &run_grayscale, "Convert image to grayscale",
          py::arg("input_path"), py::arg("output_path"));
    m.def("run_lesson_3_sobel", &run_lesson_3_sobel, "Calculate Sobel gradients",
          py::arg("input_path"), py::arg("output_path"));
    m.def("run_lesson_3_canny", &run_lesson_3_canny, "Calculate Canny edges",
          py::arg("input_path"), py::arg("output_path"), py::arg("threshold1"), py::arg("threshold2"));
}
