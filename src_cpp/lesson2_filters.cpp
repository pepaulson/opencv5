#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <opencv2/opencv.hpp>
#include <iostream>
#include <string>
#include <chrono>

namespace py = pybind11;

std::string run_lesson_2_filter(const std::string& input_path, const std::string& output_path, const std::string& filter_type, int kernel_size) {
    std::cout << "[C++] Loading image: " << input_path << std::endl;
    cv::Mat image = cv::imread(input_path, cv::IMREAD_COLOR);
    if (image.empty()) {
        throw std::runtime_error("Could not read image: " + input_path);
    }

    std::cout << "[C++] Applying " << filter_type << " filter with kernel size " << kernel_size << "x" << kernel_size << "..." << std::endl;
    
    // Allocate memory for the output image. cv::Mat automatically manages reference counting 
    // and will release memory when no longer needed.
    cv::Mat filtered_image;
    
    auto start_time = std::chrono::high_resolution_clock::now();

    if (filter_type == "Gaussian") {
        // Gaussian blur uses a convolution kernel where the weights fall off 
        // exponentially from the center (a Gaussian distribution).
        // It's excellent for reducing general Gaussian noise.
        // The standard deviation (sigma) is computed automatically from the kernel size if set to 0.
        cv::GaussianBlur(image, filtered_image, cv::Size(kernel_size, kernel_size), 0);
    } else if (filter_type == "Median") {
        // Median blur replaces each pixel with the median value in its k x k neighborhood.
        // It is highly effective against "salt-and-pepper" noise because it completely
        // ignores outlier values rather than averaging them in.
        cv::medianBlur(image, filtered_image, kernel_size);
    } else {
        throw std::runtime_error("Unknown filter type: " + filter_type);
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> duration = end_time - start_time;
    std::cout << "[C++] Filtering completed in " << duration.count() << " ms." << std::endl;

    std::cout << "[C++] Saving output image to: " << output_path << std::endl;
    bool success = cv::imwrite(output_path, filtered_image);
    if (!success) {
        throw std::runtime_error("Could not write image to: " + output_path);
    }

    return output_path;
}

void init_lesson2_filters(py::module_ &m) {
    m.def("run_lesson_2_filter", &run_lesson_2_filter, "A function that applies spatial filters for Lesson 2",
          py::arg("input_path"), py::arg("output_path"), py::arg("filter_type"), py::arg("kernel_size"));
}
