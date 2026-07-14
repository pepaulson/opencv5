from temporalio import activity, workflow
import os
import asyncio
import datetime

try:
    import cv_lab_3d
except ImportError:
    pass

@activity.defn
async def compute_ransac_plane_activity(payload: dict) -> dict:
    input_filename = payload.get("input_filename", "lesson7_output.ply")
    output_filename = payload.get("output_filename", "lesson8_output.ply")
    distance_threshold = payload.get("distance_threshold", 0.02)
    max_iterations = payload.get("max_iterations", 1000)
    
    input_path = os.path.join("/app/data/output", input_filename)
    if not os.path.exists(input_path):
        input_path = os.path.join("/app/data/input", input_filename)

    output_path = os.path.join("/app/data/output", output_filename)

    try:
        result = cv_lab_3d.fit_plane_ransac(input_path, output_path, distance_threshold, max_iterations)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@activity.defn
async def bin_shake_activity() -> str:
    # Simulate a physical robot action that shakes the bin to expose new surfaces
    await asyncio.sleep(2)
    return "Bin Shake Completed"

@workflow.defn
class GraspVectorWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        confidence_threshold = payload.get("confidence_threshold", 40.0)
        max_retries = 3
        shake_count = 0
        
        for attempt in range(max_retries + 1):
            result = await workflow.execute_activity(
                compute_ransac_plane_activity,
                payload,
                start_to_close_timeout=datetime.timedelta(seconds=60),
            )
            
            if not result.get("success"):
                return result # Error occurred
            
            inlier_ratio = result.get("inlier_ratio", 0)
            result["shake_count"] = shake_count
            
            if inlier_ratio >= confidence_threshold:
                result["message"] = f"Grasp vector found! Confidence: {inlier_ratio:.2f}%"
                return result
                
            if attempt < max_retries:
                # Trigger physical bin shake
                await workflow.execute_activity(
                    bin_shake_activity,
                    start_to_close_timeout=datetime.timedelta(seconds=10),
                )
                shake_count += 1
                
        # If we exhausted retries
        result["message"] = f"Failed to find suitable surface after {shake_count} shakes. Max confidence: {inlier_ratio:.2f}%"
        return result
