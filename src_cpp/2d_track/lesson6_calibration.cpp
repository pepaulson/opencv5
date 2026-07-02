#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <opencv2/opencv.hpp>
#include <opencv2/objdetect/aruco_detector.hpp>
#include <opencv2/calib3d.hpp>
#include <iostream>
#include <vector>
#include <string>

namespace py = pybind11;

struct CalibrationResult {
    bool success;
    std::vector<std::vector<float>> camera_matrix;
    std::vector<float> dist_coeffs;
};

struct PoseResult {
    bool success;
    std::vector<float> rvec;
    std::vector<float> tvec;
    std::vector<std::vector<float>> axis_points;
};

CalibrationResult run_lesson_6_calibrate(const std::vector<std::string>& image_paths) {
    CalibrationResult result;
    result.success = false;

    cv::Size board_size(8, 5);
    std::vector<std::vector<cv::Point3f>> obj_points;
    std::vector<std::vector<cv::Point2f>> img_points;

    std::vector<cv::Point3f> objp;
    for (int i = 0; i < board_size.height; i++) {
        for (int j = 0; j < board_size.width; j++) {
            objp.push_back(cv::Point3f(j * 50.0f, i * 50.0f, 0.0f));
        }
    }

    cv::Size img_size;

    for (const auto& path : image_paths) {
        cv::Mat img = cv::imread(path, cv::IMREAD_GRAYSCALE);
        if (img.empty()) continue;
        img_size = img.size();

        std::vector<cv::Point2f> corners;
        bool found = cv::findChessboardCorners(img, board_size, corners, 
            cv::CALIB_CB_ADAPTIVE_THRESH | cv::CALIB_CB_NORMALIZE_IMAGE);

        if (found) {
            cv::cornerSubPix(img, corners, cv::Size(11, 11), cv::Size(-1, -1),
                cv::TermCriteria(cv::TermCriteria::EPS + cv::TermCriteria::MAX_ITER, 30, 0.001));
            img_points.push_back(corners);
            obj_points.push_back(objp);
        }
    }

    if (img_points.empty()) {
        std::cout << "[C++] Error: No checkerboards found in any of the " << image_paths.size() << " images." << std::endl;
        return result;
    }
    std::cout << "[C++] Found checkerboards in " << img_points.size() << " images." << std::endl;

    cv::Mat camera_matrix, dist_coeffs;
    std::vector<cv::Mat> rvecs, tvecs;

    double rms = cv::calibrateCamera(obj_points, img_points, img_size, camera_matrix, dist_coeffs, rvecs, tvecs);

    if (rms >= 0) {
        result.success = true;
        result.camera_matrix.resize(3, std::vector<float>(3));
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                result.camera_matrix[i][j] = static_cast<float>(camera_matrix.at<double>(i, j));
            }
        }
        result.dist_coeffs.resize(dist_coeffs.cols > dist_coeffs.rows ? dist_coeffs.cols : dist_coeffs.rows);
        for (size_t i = 0; i < result.dist_coeffs.size(); i++) {
            result.dist_coeffs[i] = static_cast<float>(dist_coeffs.at<double>(i));
        }
        result.success = true;
        std::cout << "[C++] Camera calibrated successfully." << std::endl;
    } else {
        std::cout << "[C++] Camera calibration failed with rms = " << rms << std::endl;
    }

    return result;
}

PoseResult run_lesson_6_pose(const std::string& image_path, 
                             const std::vector<std::vector<float>>& camera_matrix_vec, 
                             const std::vector<float>& dist_coeffs_vec) {
    PoseResult result;
    result.success = false;

    cv::Mat img = cv::imread(image_path);
    if (img.empty()) {
        std::cout << "[C++] Error: Could not read image " << image_path << std::endl;
        return result;
    }
    std::cout << "[C++] Loaded image " << image_path << std::endl;

    cv::Mat camera_matrix(3, 3, CV_64F);
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            camera_matrix.at<double>(i, j) = static_cast<double>(camera_matrix_vec[i][j]);
        }
    }

    cv::Mat dist_coeffs(1, dist_coeffs_vec.size(), CV_64F);
    for (size_t i = 0; i < dist_coeffs_vec.size(); i++) {
        dist_coeffs.at<double>(i) = static_cast<double>(dist_coeffs_vec[i]);
    }

    cv::aruco::Dictionary dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_6X6_250);
    cv::aruco::DetectorParameters detectorParams = cv::aruco::DetectorParameters();
    cv::aruco::ArucoDetector detector(dictionary, detectorParams);

    std::vector<int> markerIds;
    std::vector<std::vector<cv::Point2f>> markerCorners, rejectedCandidates;

    detector.detectMarkers(img, markerCorners, markerIds, rejectedCandidates);
    
    std::cout << "[C++] Detected " << markerIds.size() << " markers." << std::endl;

    if (!markerIds.empty()) {
        cv::Mat objPoints(4, 1, CV_32FC3);
        float markerLength = 200.0f; // e.g. 200 mm
        objPoints.ptr<cv::Vec3f>(0)[0] = cv::Vec3f(-markerLength/2.f, markerLength/2.f, 0);
        objPoints.ptr<cv::Vec3f>(0)[1] = cv::Vec3f(markerLength/2.f, markerLength/2.f, 0);
        objPoints.ptr<cv::Vec3f>(0)[2] = cv::Vec3f(markerLength/2.f, -markerLength/2.f, 0);
        objPoints.ptr<cv::Vec3f>(0)[3] = cv::Vec3f(-markerLength/2.f, -markerLength/2.f, 0);

        cv::Vec3d rvec, tvec;
        bool valid = cv::solvePnP(objPoints, markerCorners[0], camera_matrix, dist_coeffs, rvec, tvec);
        std::cout << "[C++] solvePnP valid: " << valid << std::endl;
        if (valid) {
            result.success = true;
            result.rvec = {static_cast<float>(rvec[0]), static_cast<float>(rvec[1]), static_cast<float>(rvec[2])};
            result.tvec = {static_cast<float>(tvec[0]), static_cast<float>(tvec[1]), static_cast<float>(tvec[2])};
            
            // Project axis points
            std::vector<cv::Point3f> axis;
            float length = 100.0f; // Axis length
            axis.push_back(cv::Point3f(0, 0, 0));
            axis.push_back(cv::Point3f(length, 0, 0)); // X (Red)
            axis.push_back(cv::Point3f(0, length, 0)); // Y (Green)
            axis.push_back(cv::Point3f(0, 0, length)); // Z (Blue)
            
            std::vector<cv::Point2f> imagePoints;
            cv::projectPoints(axis, rvec, tvec, camera_matrix, dist_coeffs, imagePoints);
            
            for (const auto& pt : imagePoints) {
                result.axis_points.push_back({pt.x, pt.y});
            }
            std::cout << "[C++] Returning success=true" << std::endl;
        }
    } else {
        std::cout << "[C++] No markers found, success=false" << std::endl;
    }
    return result;
}

void init_lesson6_calibration(py::module_ &m) {
    py::class_<CalibrationResult>(m, "CalibrationResult")
        .def_readonly("success", &CalibrationResult::success)
        .def_readonly("camera_matrix", &CalibrationResult::camera_matrix)
        .def_readonly("dist_coeffs", &CalibrationResult::dist_coeffs);

    py::class_<PoseResult>(m, "PoseResult")
        .def_readonly("success", &PoseResult::success)
        .def_readonly("rvec", &PoseResult::rvec)
        .def_readonly("tvec", &PoseResult::tvec)
        .def_readonly("axis_points", &PoseResult::axis_points);

    m.def("run_lesson_6_calibrate", &run_lesson_6_calibrate, "Calibrate camera", py::arg("image_paths"));
    m.def("run_lesson_6_pose", &run_lesson_6_pose, "Estimate pose", py::arg("image_path"), py::arg("camera_matrix"), py::arg("dist_coeffs"));
}
