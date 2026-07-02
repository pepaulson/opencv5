#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>
#include <opencv2/calib3d.hpp>
#include <iostream>
#include <vector>

namespace py = pybind11;

struct Point2f_py {
    float x;
    float y;
};

struct KeyPoint_py {
    float x;
    float y;
    float size;
    float angle;
    float response;
    int octave;
    int class_id;
};

struct Match_py {
    int queryIdx;
    int trainIdx;
    float distance;
};

struct FeatureMatchResult {
    bool success;
    int inliers;
    int outliers;
    std::vector<KeyPoint_py> ref_keypoints;
    std::vector<KeyPoint_py> live_keypoints;
    std::vector<Match_py> matches; // these are the good matches after Lowe's and RANSAC
    std::vector<Point2f_py> bounding_box;
};

FeatureMatchResult run_lesson_5_features(const std::string& ref_path, const std::string& live_path, double contrast_alpha = 1.0, int brightness_beta = 0) {
    std::cout << "[C++] Loading reference image: " << ref_path << std::endl;
    cv::Mat img_ref = cv::imread(ref_path, cv::IMREAD_GRAYSCALE);
    if (img_ref.empty()) {
        throw std::runtime_error("Could not read reference image: " + ref_path);
    }

    std::cout << "[C++] Loading live image: " << live_path << std::endl;
    cv::Mat img_live = cv::imread(live_path, cv::IMREAD_GRAYSCALE);
    if (img_live.empty()) {
        throw std::runtime_error("Could not read live image: " + live_path);
    }

    // Apply contrast/brightness adjustments to live image if specified (simulating retries handling different lighting)
    if (contrast_alpha != 1.0 || brightness_beta != 0) {
        img_live.convertTo(img_live, -1, contrast_alpha, brightness_beta);
    }

    // Step 1: Detect the keypoints and extract descriptors using ORB
    auto detector = cv::ORB::create(5000); // Allow more keypoints for better matching
    std::vector<cv::KeyPoint> keypoints_ref, keypoints_live;
    cv::Mat descriptors_ref, descriptors_live;

    detector->detectAndCompute(img_ref, cv::noArray(), keypoints_ref, descriptors_ref);
    detector->detectAndCompute(img_live, cv::noArray(), keypoints_live, descriptors_live);

    FeatureMatchResult result;
    result.success = false;
    result.inliers = 0;
    result.outliers = 0;

    // Convert ref keypoints
    for (const auto& kp : keypoints_ref) {
        result.ref_keypoints.push_back({kp.pt.x, kp.pt.y, kp.size, kp.angle, kp.response, kp.octave, kp.class_id});
    }
    for (const auto& kp : keypoints_live) {
        result.live_keypoints.push_back({kp.pt.x, kp.pt.y, kp.size, kp.angle, kp.response, kp.octave, kp.class_id});
    }

    if (descriptors_ref.empty() || descriptors_live.empty()) {
        std::cout << "[C++] No descriptors found." << std::endl;
        return result;
    }

    // Step 2: Match descriptor vectors using Brute Force Matcher with Hamming distance
    cv::BFMatcher matcher(cv::NORM_HAMMING);
    std::vector<std::vector<cv::DMatch>> knn_matches;
    matcher.knnMatch(descriptors_ref, descriptors_live, knn_matches, 2);

    // Step 3: Filter matches using Lowe's ratio test
    const float ratio_thresh = 0.75f;
    std::vector<cv::DMatch> good_matches;
    for (size_t i = 0; i < knn_matches.size(); i++) {
        if (knn_matches[i].size() >= 2 && knn_matches[i][0].distance < ratio_thresh * knn_matches[i][1].distance) {
            good_matches.push_back(knn_matches[i][0]);
        }
    }

    // We need at least 4 matches to compute homography
    if (good_matches.size() < 4) {
        std::cout << "[C++] Not enough good matches after Lowe's test." << std::endl;
        result.outliers = knn_matches.size() - good_matches.size();
        return result;
    }

    // Step 4: Calculate Homography with RANSAC
    std::vector<cv::Point2f> pts_ref;
    std::vector<cv::Point2f> pts_live;

    for (size_t i = 0; i < good_matches.size(); i++) {
        pts_ref.push_back(keypoints_ref[good_matches[i].queryIdx].pt);
        pts_live.push_back(keypoints_live[good_matches[i].trainIdx].pt);
    }

    std::vector<uchar> inliersMask(pts_ref.size());
    cv::Mat H = cv::findHomography(pts_ref, pts_live, cv::RANSAC, 3.0, inliersMask);

    if (H.empty()) {
        std::cout << "[C++] Homography failed." << std::endl;
        return result;
    }

    // Populate matches and count inliers/outliers
    for (size_t i = 0; i < inliersMask.size(); i++) {
        if (inliersMask[i]) {
            result.inliers++;
            Match_py m;
            m.queryIdx = good_matches[i].queryIdx;
            m.trainIdx = good_matches[i].trainIdx;
            m.distance = good_matches[i].distance;
            result.matches.push_back(m);
        } else {
            result.outliers++;
        }
    }

    result.outliers += (knn_matches.size() - good_matches.size()); // Include Lowe's test failures as outliers

    // Get the corners from the reference image
    std::vector<cv::Point2f> ref_corners(4);
    ref_corners[0] = cv::Point2f(0, 0);
    ref_corners[1] = cv::Point2f((float)img_ref.cols, 0);
    ref_corners[2] = cv::Point2f((float)img_ref.cols, (float)img_ref.rows);
    ref_corners[3] = cv::Point2f(0, (float)img_ref.rows);

    std::vector<cv::Point2f> live_corners(4);
    cv::perspectiveTransform(ref_corners, live_corners, H);

    for (int i = 0; i < 4; i++) {
        result.bounding_box.push_back({live_corners[i].x, live_corners[i].y});
    }

    // Minimum inlier count threshold to consider success
    if (result.inliers > 10) {
        result.success = true;
    }

    return result;
}

extern void init_lesson5_features(py::module_ &m) {
    py::class_<Point2f_py>(m, "Point2f_py")
        .def_readonly("x", &Point2f_py::x)
        .def_readonly("y", &Point2f_py::y);

    py::class_<KeyPoint_py>(m, "KeyPoint_py")
        .def_readonly("x", &KeyPoint_py::x)
        .def_readonly("y", &KeyPoint_py::y)
        .def_readonly("size", &KeyPoint_py::size)
        .def_readonly("angle", &KeyPoint_py::angle)
        .def_readonly("response", &KeyPoint_py::response)
        .def_readonly("octave", &KeyPoint_py::octave)
        .def_readonly("class_id", &KeyPoint_py::class_id);

    py::class_<Match_py>(m, "Match_py")
        .def_readonly("queryIdx", &Match_py::queryIdx)
        .def_readonly("trainIdx", &Match_py::trainIdx)
        .def_readonly("distance", &Match_py::distance);

    py::class_<FeatureMatchResult>(m, "FeatureMatchResult")
        .def_readonly("success", &FeatureMatchResult::success)
        .def_readonly("inliers", &FeatureMatchResult::inliers)
        .def_readonly("outliers", &FeatureMatchResult::outliers)
        .def_readonly("ref_keypoints", &FeatureMatchResult::ref_keypoints)
        .def_readonly("live_keypoints", &FeatureMatchResult::live_keypoints)
        .def_readonly("matches", &FeatureMatchResult::matches)
        .def_readonly("bounding_box", &FeatureMatchResult::bounding_box);

    m.def("run_lesson_5_features", &run_lesson_5_features, "A function that processes feature matching for Lesson 5",
          py::arg("ref_path"), py::arg("live_path"), py::arg("contrast_alpha") = 1.0, py::arg("brightness_beta") = 0);
}
