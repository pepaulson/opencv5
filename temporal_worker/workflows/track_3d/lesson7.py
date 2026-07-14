from temporalio import activity, workflow
import os
import sys

# In the container, the worker root is /app/temporal_worker
# and the .so modules are built there.
try:
    import cv_lab_3d
except ImportError:
    # We will try again at runtime if needed, or it will fail nicely.
    pass

@activity.defn
async def generate_point_cloud_activity(payload: dict) -> dict:
    """
    Activity for Lesson 7: The Depth Map
    Demonstrates the Claim Check pattern: takes metadata, writes large file, returns file path metadata.
    """
    rgb_path = os.path.join("/app/data/input", payload.get("rgb_filename", "rgb_scene.png"))
    depth_path = os.path.join("/app/data/input", payload.get("depth_filename", "depth_scene.png"))
    output_filename = payload.get("output_filename", "lesson7_output.ply")
    output_path = os.path.join("/app/data/output", output_filename)
    
    fx = payload.get("fx", 500.0)
    fy = payload.get("fy", 500.0)
    cx = payload.get("cx", 320.0)
    cy = payload.get("cy", 240.0)
    scale = payload.get("scale", 1000.0)

    try:
        actual_output_path = cv_lab_3d.generate_point_cloud(
            rgb_path, depth_path, output_path, fx, fy, cx, cy, scale
        )
        return {
            "success": True,
            "output_path": actual_output_path,
            "filename": output_filename,
            "message": "Point cloud generated successfully using Claim Check pattern. Large data was not passed through Temporal."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@workflow.defn
class PointCloudGenerationWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        import datetime
        from temporalio import workflow
        
        result = await workflow.execute_activity(
            generate_point_cloud_activity,
            payload,
            start_to_close_timeout=datetime.timedelta(seconds=60),
        )
        
        return result
