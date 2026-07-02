#include <pybind11/pybind11.h>

namespace py = pybind11;

extern void init_lesson1(py::module_ &m);
extern void init_lesson2_filters(py::module_ &m);
extern void init_lesson3_edges(py::module_ &m);
extern void init_lesson4_contours(py::module_ &m);
extern void init_lesson5_features(py::module_ &m);
extern void init_lesson6_calibration(py::module_ &m);

PYBIND11_MODULE(cv_lab_2d, m) {
    m.doc() = "OpenCV 2D Track for Temporal Learning Lab";
    
    init_lesson1(m);
    init_lesson2_filters(m);
    init_lesson3_edges(m);
    init_lesson4_contours(m);
    init_lesson5_features(m);
    init_lesson6_calibration(m);
}
