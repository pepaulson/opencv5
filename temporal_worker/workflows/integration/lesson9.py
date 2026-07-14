from temporalio import workflow, activity
from temporalio.exceptions import ApplicationError
from temporalio.common import RetryPolicy
import asyncio
from datetime import timedelta
import sys

# Attempt to import C++ extension, handle gracefully if not built yet (for intellisense/linting)
try:
    import cv_lab_integration
except ImportError:
    cv_lab_integration = None

@activity.defn
async def detect_harvest_targets_activity(rgb_image_path: str, hsv_lower: list, hsv_upper: list) -> list:
    if cv_lab_integration is None:
        raise ApplicationError("cv_lab_integration C++ module not found")
    
    # hsv_lower and hsv_upper should be lists of 3 ints
    targets = cv_lab_integration.detect_harvest_targets(rgb_image_path, hsv_lower, hsv_upper)
    return targets

@activity.defn
async def extract_3d_coordinates_activity(depth_image_path: str, bounding_boxes: list, fx: float, fy: float, cx: float, cy: float, scale: float) -> list:
    if cv_lab_integration is None:
        raise ApplicationError("cv_lab_integration C++ module not found")
        
    coords = cv_lab_integration.extract_3d_coordinates(depth_image_path, bounding_boxes, fx, fy, cx, cy, scale)
    return coords

# We'll use a global variable to simulate a transient network failure for the PLC handoff
_plc_attempts = 0

@activity.defn
async def plc_handoff_activity(coords: list, simulate_failure: bool = True) -> str:
    global _plc_attempts
    _plc_attempts += 1
    
    # Simulate a network timeout on the first attempt to demonstrate Temporal retries
    if simulate_failure and _plc_attempts % 2 != 0:
        raise ApplicationError("NETWORK_TIMEOUT: Failed to reach PLC.", type="NetworkError")
        
    # Success on subsequent attempts
    payload_str = f"Transmitted {len(coords)} target coordinates to PLC successfully."
    return payload_str


@workflow.defn
class AutomatedHarvestWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        rgb_image_path = payload.get("rgb_image_path", "/app/data/input/lesson9_rgb.png")
        depth_image_path = payload.get("depth_image_path", "/app/data/input/lesson9_depth.png")
        
        # Red targets (e.g. tomatoes)
        hsv_lower = payload.get("hsv_lower", [0, 100, 100])
        hsv_upper = payload.get("hsv_upper", [20, 255, 255])
        
        fx = payload.get("fx", 500.0)
        fy = payload.get("fy", 500.0)
        cx = payload.get("cx", 320.0)
        cy = payload.get("cy", 240.0)
        scale = payload.get("scale", 1000.0)
        simulate_failure = payload.get("simulate_failure", True)
        
        # Activity 1: 2D Track (HSV Segmentation)
        bounding_boxes = await workflow.execute_activity(
            detect_harvest_targets_activity,
            args=[rgb_image_path, hsv_lower, hsv_upper],
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        # Condition Check: If list is empty, terminate gracefully and "schedule retry"
        if not bounding_boxes:
            # We simulate a cron-like retry by returning a specific status. 
            # In a real system, we might use workflow.continue_as_new or return a special message.
            return {
                "status": "NO_TARGETS_FOUND",
                "message": "No harvestable targets found. Terminating gracefully. Scheduled next check in 4 hours."
            }
            
        # Activity 2: 3D Track (Depth Reprojection)
        coords = await workflow.execute_activity(
            extract_3d_coordinates_activity,
            args=[depth_image_path, bounding_boxes, fx, fy, cx, cy, scale],
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        if not coords:
            return {
                "status": "NO_VALID_DEPTH",
                "message": "Targets found in 2D, but no valid depth data. Aborting."
            }
            
        # Activity 3: Simulated PLC Handoff (with Saga/retry pattern demonstration)
        # Note: Temporal automatically retries activities on failure based on default or custom RetryPolicy.
        # Here we just use the default which retries ApplicationError.
        try:
            plc_result = await workflow.execute_activity(
                plc_handoff_activity,
                args=[coords, simulate_failure],
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    backoff_coefficient=2.0,
                    maximum_attempts=5,
                )
            )
        except Exception as e:
            return {
                "status": "PLC_HANDOFF_FAILED",
                "error": str(e),
                "bounding_boxes": bounding_boxes,
                "coords": coords
            }
            
        return {
            "status": "SUCCESS",
            "message": plc_result,
            "bounding_boxes": bounding_boxes,
            "coords": coords
        }
