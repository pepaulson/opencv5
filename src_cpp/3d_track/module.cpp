#include <pybind11/pybind11.h>
#include <string>

namespace py = pybind11;

std::string generate_point_cloud(const std::string& rgb_path, const std::string& depth_path, const std::string& output_path, double fx, double fy, double cx, double cy, double scale);

PYBIND11_MODULE(cv_lab_3d, m) {
    m.doc() = "OpenCV 3D Track for Temporal Learning Lab";
    
    m.def("generate_point_cloud", &generate_point_cloud, "Generate a point cloud from an RGB-D image pair",
          py::arg("rgb_path"), py::arg("depth_path"), py::arg("output_path"),
          py::arg("fx"), py::arg("fy"), py::arg("cx"), py::arg("cy"), py::arg("scale"));
}
