from datetime import timedelta
from temporalio import workflow
with workflow.unsafe.imports_passed_through():
    from .activities import calibrate_camera, estimate_pose

@workflow.defn
class CalibrationServiceWorkflow:
    def __init__(self) -> None:
        self._is_calibrated = False
        self._camera_matrix = []
        self._dist_coeffs = []
        self._calibration_images = []
        self._start_calibration = False

    @workflow.signal(name="SubmitCalibrationImages")
    def submit_calibration_images(self, image_paths: list[str]) -> None:
        self._calibration_images = image_paths
        self._start_calibration = True

    @workflow.update(name="GetPoseEstimation")
    async def get_pose_estimation(self, frame_path: str) -> dict:
        if not self._is_calibrated:
            return {"success": False, "error": "Camera not calibrated yet."}
        
        params = {
            "image_path": frame_path,
            "camera_matrix": self._camera_matrix,
            "dist_coeffs": self._dist_coeffs
        }
        
        pose_result = await workflow.execute_activity(
            estimate_pose,
            params,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return pose_result
        
    @workflow.query(name="GetCalibrationStatus")
    def get_calibration_status(self) -> dict:
        return {
            "is_calibrated": self._is_calibrated,
            "camera_matrix": self._camera_matrix,
            "dist_coeffs": self._dist_coeffs
        }

    @workflow.run
    async def run(self) -> None:
        # Long-running workflow loop
        while True:
            # Wait for calibration images
            await workflow.wait_condition(lambda: self._start_calibration)
            self._start_calibration = False
            
            # Run calibration activity
            result = await workflow.execute_activity(
                calibrate_camera,
                self._calibration_images,
                start_to_close_timeout=timedelta(seconds=60),
            )
            
            if result.get("success"):
                self._camera_matrix = result.get("camera_matrix")
                self._dist_coeffs = result.get("dist_coeffs")
                self._is_calibrated = True
