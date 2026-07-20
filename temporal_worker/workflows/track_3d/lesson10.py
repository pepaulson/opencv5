from temporalio import activity, workflow
import os
import asyncio
import datetime
import math

@activity.defn
async def ppf_match_activity(payload: dict) -> dict:
    template_filename = payload.get("template_filename", "lesson10_template.ply")
    scene_filename = payload.get("scene_filename", "lesson10_scene.ply")
    
    template_path = os.path.join("/app/data/input", template_filename)
    scene_path = os.path.join("/app/data/input", scene_filename)
    
    def heartbeat_callback(msg: str):
        activity.heartbeat(msg)
        
    try:
        # Pass the python callback to C++
        # It's an async activity, but cv_lab_3d.match_3d_template is blocking
        # However we can run it in a thread executor if needed, but since it's an activity, 
        # blocking is okay as long as we heartbeat. Wait, we should probably run blocking IO in a thread pool.
        # But for this demo, calling it directly works if it releases GIL and we heartbeat from the callback.
        # Wait, if it holds GIL, it will block the asyncio event loop.
        # Let's run it in a thread executor so the event loop can process heartbeats properly if needed.
        # But wait, pybind11 callback requires GIL to be acquired, which it does.
        loop = asyncio.get_running_loop()
        
        # We need to wrap it to be safe or just call it directly since activities run in an executor by default in python sdk!
        # Temporal Python SDK runs async activities on the event loop, and sync activities on a thread pool.
        # Wait! If the activity is `async def`, it runs on the event loop. A blocking C++ call will block the loop.
        # We should define it as a sync activity (just `def`)!
        pass
    except Exception as e:
        return {"success": False, "error": str(e)}

# Redefine as sync activity so it runs in a thread pool
@activity.defn
def ppf_match_activity_sync(payload: dict) -> dict:
    import cv_lab_3d
    template_filename = payload.get("template_filename", "lesson10_template.ply")
    scene_filename = payload.get("scene_filename", "lesson10_scene.ply")
    sampling_step = payload.get("relative_sampling_step", 0.025)
    distance_step = payload.get("relative_distance_step", 0.05)
    
    template_path = os.path.join("/app/data/input", template_filename)
    scene_path = os.path.join("/app/data/input", scene_filename)
    
    def heartbeat_callback(msg: str):
        activity.heartbeat(msg)
        
    try:
        result = cv_lab_3d.match_3d_template(template_path, scene_path, heartbeat_callback, sampling_step, distance_step)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@activity.defn
async def format_pose_activity(payload: dict) -> dict:
    import numpy as np
    poses = payload.get("poses")
    if not poses:
        # Fallback to single pose if present for backward compatibility
        pose = payload.get("pose")
        if pose:
            poses = [{"pose": pose}]
        else:
            return {"success": False, "error": "No poses provided"}
        
    formatted_poses = []
    
    for p in poses:
        pose_matrix = p.get("pose")
        if not pose_matrix:
            continue
            
        rot_matrix = np.array(pose_matrix)[:3, :3]
        sy = math.sqrt(rot_matrix[0,0] * rot_matrix[0,0] +  rot_matrix[1,0] * rot_matrix[1,0])
        singular = sy < 1e-6
        if not singular:
            x = math.atan2(rot_matrix[2,1] , rot_matrix[2,2])
            y = math.atan2(-rot_matrix[2,0], sy)
            z = math.atan2(rot_matrix[1,0], rot_matrix[0,0])
        else:
            x = math.atan2(-rot_matrix[1,2], rot_matrix[1,1])
            y = math.atan2(-rot_matrix[2,0], sy)
            z = 0
            
        formatted_poses.append({
            "pose_matrix": pose_matrix,
            "translation": {
                "x": pose_matrix[0][3],
                "y": pose_matrix[1][3],
                "z": pose_matrix[2][3]
            },
            "rotation_euler_deg": {
                "rx": math.degrees(x),
                "ry": math.degrees(y),
                "rz": math.degrees(z)
            },
            "num_votes": p.get("num_votes"),
            "residual": p.get("residual")
        })
        
    return {"success": True, "poses": formatted_poses}

@workflow.defn
class PoseEstimationWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        # Run PPF matching
        match_result = await workflow.execute_activity(
            ppf_match_activity_sync,
            payload,
            start_to_close_timeout=datetime.timedelta(minutes=5),
            heartbeat_timeout=datetime.timedelta(seconds=10)
        )
        
        if not match_result.get("success"):
            return match_result
            
        # Format the pose
        format_result = await workflow.execute_activity(
            format_pose_activity,
            {"poses": match_result.get("poses")},
            start_to_close_timeout=datetime.timedelta(seconds=10)
        )
        
        # Combine results
        match_result.update(format_result)
        return match_result
