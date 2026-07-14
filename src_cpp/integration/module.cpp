#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>

namespace py = pybind11;

// Forward declarations
std::vector<py::dict> detect_harvest_targets(const std::string& rgb_image_path, py::list hsv_lower, py::list hsv_upper);
std::vector<py::dict> extract_3d_coordinates(const std::string& depth_image_path, const std::vector<py::dict>& bounding_boxes, double fx, double fy, double cx, double cy, double scale);

PYBIND11_MODULE(cv_lab_integration, m) {
    m.doc() = "OpenCV Integration Track for Temporal Learning Lab - Lesson 9 Sensor Fusion";
    
    m.def("detect_harvest_targets", &detect_harvest_targets, "Detect plant structures using HSV color space",
          py::arg("rgb_image_path"), py::arg("hsv_lower"), py::arg("hsv_upper"));
          
    m.def("extract_3d_coordinates", &extract_3d_coordinates, "Extract X, Y, Z coordinates from depth image and bounding boxes",
          py::arg("depth_image_path"), py::arg("bounding_boxes"), py::arg("fx"), py::arg("fy"), py::arg("cx"), py::arg("cy"), py::arg("scale"));
}
