#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/functional.h>
#include <pybind11/stl.h>

#include <opencv2/core.hpp>
#include <opencv2/surface_matching.hpp>
#include <opencv2/surface_matching/ppf_match_3d.hpp>
#include <opencv2/surface_matching/ppf_helpers.hpp>

#include <iostream>
#include <vector>
#include <string>

namespace py = pybind11;

py::dict match_3d_template(
    const std::string& template_ply,
    const std::string& scene_ply,
    const std::function<void(const std::string&)>& heartbeat_callback,
    double relative_sampling_step = 0.025,
    double relative_distance_step = 0.05)
{
    py::dict result;
    
    try {
        if (heartbeat_callback) {
            py::gil_scoped_acquire acquire;
            heartbeat_callback("Loading point clouds...");
        }

        cv::Mat pc_template = cv::ppf_match_3d::loadPLYSimple(template_ply.c_str(), 1);
        cv::Mat pc_scene = cv::ppf_match_3d::loadPLYSimple(scene_ply.c_str(), 1);

        if (pc_template.empty() || pc_scene.empty()) {
            result["success"] = false;
            result["error"] = "Failed to load PLY files.";
            return result;
        }

        if (heartbeat_callback) {
            py::gil_scoped_acquire acquire;
            heartbeat_callback("Training PPF model...");
        }

        // Initialize detector
        cv::ppf_match_3d::PPF3DDetector detector(relative_sampling_step, relative_distance_step);
        
        // Train the model
        detector.trainModel(pc_template);

        if (heartbeat_callback) {
            py::gil_scoped_acquire acquire;
            heartbeat_callback("Matching template against scene...");
        }

        // Match
        std::vector<cv::ppf_match_3d::Pose3DPtr> results;
        detector.match(pc_scene, results, 1.0/5.0, 0.05);

        if (results.empty()) {
            result["success"] = false;
            result["error"] = "No matches found.";
            return result;
        }

        if (heartbeat_callback) {
            py::gil_scoped_acquire acquire;
            heartbeat_callback("Refining alignment with ICP...");
        }

        // Refine with ICP
        cv::ppf_match_3d::ICP icp(100, 0.005f, 2.5f, 8);
        icp.registerModelToScene(pc_template, pc_scene, results);

        if (results.empty()) {
            result["success"] = false;
            result["error"] = "ICP failed to refine matches.";
            return result;
        }

        py::list poses_list;
        std::vector<cv::Vec3d> accepted_translations;
        
        for (size_t i = 0; i < results.size(); ++i) {
            cv::ppf_match_3d::Pose3DPtr p = results[i];
            
            // Extract translation
            cv::Vec3d t(p->pose(0, 3), p->pose(1, 3), p->pose(2, 3));
            
            // Check if this pose overlaps with an already accepted one (spatial threshold 0.1m)
            bool overlap = false;
            for (const auto& at : accepted_translations) {
                double dist = cv::norm(t - at);
                if (dist < 0.1) {
                    overlap = true;
                    break;
                }
            }
            
            if (!overlap) {
                accepted_translations.push_back(t);
                
                std::vector<std::vector<double>> pose_matrix(4, std::vector<double>(4, 0.0));
                for (int r = 0; r < 4; ++r) {
                    for (int c = 0; c < 4; ++c) {
                        pose_matrix[r][c] = p->pose(r, c);
                    }
                }
                
                py::dict pose_dict;
                pose_dict["pose"] = pose_matrix;
                pose_dict["num_votes"] = p->numVotes;
                pose_dict["residual"] = p->residual;
                
                poses_list.append(pose_dict);
                
                // Cap at top 5 to prevent returning too many
                if (accepted_translations.size() >= 5) break;
            }
        }

        result["success"] = true;
        result["poses"] = poses_list;
        
    } catch (const std::exception& e) {
        result["success"] = false;
        result["error"] = std::string(e.what());
    }
    
    return result;
}
