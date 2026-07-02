import os
from datetime import timedelta
from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError
import cv_lab_2d

@activity.defn
async def process_lesson5_features(params: dict) -> dict:
    ref_path = params["ref_path"]
    live_path = params["live_path"]
    contrast_alpha = params.get("contrast_alpha", 1.0)
    brightness_beta = params.get("brightness_beta", 0)

    activity.logger.info(f"Feature matching: ref={ref_path}, live={live_path}, contrast={contrast_alpha}")

    res = cv_lab_2d.run_lesson_5_features(ref_path, live_path, contrast_alpha, brightness_beta)

    # Convert C++ results to JSON-serializable Python types
    ref_kps = [{"x": kp.x, "y": kp.y, "size": kp.size, "angle": kp.angle} for kp in res.ref_keypoints]
    live_kps = [{"x": kp.x, "y": kp.y, "size": kp.size, "angle": kp.angle} for kp in res.live_keypoints]
    matches = [{"queryIdx": m.queryIdx, "trainIdx": m.trainIdx, "distance": m.distance} for m in res.matches]
    bounding_box = [{"x": pt.x, "y": pt.y} for pt in res.bounding_box]

    # If it failed completely to find homography (RANSAC failed or not enough matches), we throw a retryable error
    if len(bounding_box) == 0 and res.inliers == 0 and res.outliers == 0:
        # In this implementation, if homography failed, we'll throw to trigger retry with new contrast
        raise ApplicationError("Homography calculation failed.", type="HomographyFailure")

    # If it succeeded but inliers are low, we treat it as an expected state (occluded)
    # Temporal doesn't need to retry, the pipeline just handles it gracefully
    is_occluded = not res.success

    return {
        "success": res.success,
        "is_occluded": is_occluded,
        "inliers": res.inliers,
        "outliers": res.outliers,
        "ref_keypoints": ref_kps,
        "live_keypoints": live_kps,
        "matches": matches,
        "bounding_box": bounding_box
    }


from temporalio.common import RetryPolicy

@workflow.defn
class PartIdentificationWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        ref_filename = payload.get("ref_filename", "ref_part.png")
        live_filename = payload.get("live_filename", "live_feed.png")
        
        # In a real app we'd ingest them, here we assume they are in input path
        ref_path = f"/app/data/input/{ref_filename}"
        live_path = f"/app/data/input/{live_filename}"

        # Define custom retry policy for homography failures
        # It will retry up to 3 times
        homography_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=1.0,
            maximum_attempts=3,
            non_retryable_error_types=["FileNotFoundError"]
        )

        # We will loop explicitly to modify contrast parameter across retries if we want custom logic,
        # but Temporal's retry policy automatically reruns the activity on failure. 
        # To dynamically change parameters, we can catch the ApplicationError in the workflow and retry manually.
        
        attempts = 0
        contrast_alpha = 1.0
        
        while attempts < 3:
            try:
                result = await workflow.execute_activity(
                    process_lesson5_features,
                    {
                        "ref_path": ref_path, 
                        "live_path": live_path,
                        "contrast_alpha": contrast_alpha
                    },
                    start_to_close_timeout=timedelta(seconds=15),
                    # We handle the retry loop manually to adjust parameters
                    retry_policy=RetryPolicy(maximum_attempts=1) 
                )
                
                # Include the retry count to show on UI
                result["retry_count"] = attempts
                return result
                
            except Exception as e:
                attempts += 1
                contrast_alpha += 0.5 # Increase contrast for the next attempt
                if attempts >= 3:
                    return {
                        "success": False,
                        "is_occluded": True, # Assume occluded after all retries fail
                        "inliers": 0,
                        "outliers": 0,
                        "retry_count": attempts,
                        "error": str(e)
                    }

        return {}
