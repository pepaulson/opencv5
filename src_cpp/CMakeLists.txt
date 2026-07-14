cmake_minimum_required(VERSION 3.14)
project(cv_engine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find OpenCV
find_package(OpenCV REQUIRED)
message(STATUS "OpenCV library status:")
message(STATUS "    config: ${OpenCV_DIR}")
message(STATUS "    version: ${OpenCV_VERSION}")
message(STATUS "    libraries: ${OpenCV_LIBS}")
message(STATUS "    include path: ${OpenCV_INCLUDE_DIRS}")

# Find Pybind11
# Pybind11 installed via pip is usually found at python path
execute_process(
    COMMAND python3 -m pybind11 --includes
    OUTPUT_VARIABLE PYBIND11_INCLUDES
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Extract directories from -I flags
string(REPLACE "-I" "" PYBIND11_INCLUDES "${PYBIND11_INCLUDES}")
separate_arguments(PYBIND11_INCLUDES)

include_directories(${OpenCV_INCLUDE_DIRS} ${PYBIND11_INCLUDES})

# python3 extension suffix
execute_process(
    COMMAND python3-config --extension-suffix
    OUTPUT_VARIABLE PYTHON_EXT_SUFFIX
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Add 2D Track library
add_library(cv_lab_2d SHARED 
    2d_track/module.cpp 
    2d_track/lesson1.cpp 
    2d_track/lesson2_filters.cpp 
    2d_track/lesson3_edges.cpp 
    2d_track/lesson4_contours.cpp
    2d_track/lesson5_features.cpp
    2d_track/lesson6_calibration.cpp)
target_link_libraries(cv_lab_2d ${OpenCV_LIBS})
set_target_properties(cv_lab_2d PROPERTIES PREFIX "")
set_target_properties(cv_lab_2d PROPERTIES SUFFIX "${PYTHON_EXT_SUFFIX}")

# Add 3D Track library
add_library(cv_lab_3d SHARED 
    3d_track/module.cpp
    3d_track/lesson7_depth.cpp
    3d_track/lesson8_normals.cpp)
target_link_libraries(cv_lab_3d ${OpenCV_LIBS})
set_target_properties(cv_lab_3d PROPERTIES PREFIX "")
set_target_properties(cv_lab_3d PROPERTIES SUFFIX "${PYTHON_EXT_SUFFIX}")
