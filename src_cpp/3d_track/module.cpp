#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/stl.h>
#include <string>
#include <functional>
namespace py = pybind11;

std::string generate_point_cloud(const std::string& rgb_path, const std::string& depth_path, const std::string& output_path, double fx, double fy, double cx, double cy, double scale);
py::dict fit_plane_ransac(const std::string& input_ply, const std::string& output_ply, double distance_threshold, int max_iterations);
py::dict match_3d_template(const std::string& template_ply, const std::string& scene_ply, const std::function<void(const std::string&)>& heartbeat_callback, double relative_sampling_step, double relative_distance_step);

PYBIND11_MODULE(cv_lab_3d, m) {
    m.doc() = "OpenCV 3D Track for Temporal Learning Lab";
    
    m.def("generate_point_cloud", &generate_point_cloud, "Generate a point cloud from an RGB-D image pair",
          py::arg("rgb_path"), py::arg("depth_path"), py::arg("output_path"),
          py::arg("fx"), py::arg("fy"), py::arg("cx"), py::arg("cy"), py::arg("scale"));
          
    m.def("fit_plane_ransac", &fit_plane_ransac, "Fit a plane using RANSAC and return inliers mask",
          py::arg("input_ply"), py::arg("output_ply"), py::arg("distance_threshold"), py::arg("max_iterations"));
          
    m.def("match_3d_template", &match_3d_template, "Match 3D template to scene using PPF",
          py::arg("template_ply"), py::arg("scene_ply"), py::arg("heartbeat_callback"),
          py::arg("relative_sampling_step") = 0.025, py::arg("relative_distance_step") = 0.05);
}
