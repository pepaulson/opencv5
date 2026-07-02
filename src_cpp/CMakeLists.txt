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

add_library(cv_engine SHARED lesson1.cpp lesson2_filters.cpp lesson3_edges.cpp lesson4_contours.cpp)
target_link_libraries(cv_engine ${OpenCV_LIBS})

# Set the output name with python extension suffix (e.g. .cpython-310-x86_64-linux-gnu.so)
set_target_properties(cv_engine PROPERTIES PREFIX "")
set_target_properties(cv_engine PROPERTIES SUFFIX "${PYTHON_EXT_SUFFIX}")
