#include <pybind11/pybind11.h>

namespace py = pybind11;

PYBIND11_MODULE(cv_lab_3d, m) {
    m.doc() = "OpenCV 3D Track for Temporal Learning Lab";
}
