import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from workflows.track_2d.activities import ingest_image, process_image, save_output, process_lesson2_image, process_grayscale, process_sobel, process_canny, process_lesson4_contours
from workflows.track_2d.workflows import LessonOneWorkflow, VisionCalibrationWorkflow, PathfinderEdgeWorkflow, PartLocalizationWorkflow
from workflows.track_2d.lesson5 import process_lesson5_features, PartIdentificationWorkflow
from workflows.track_2d.lesson6 import CalibrationServiceWorkflow
from workflows.track_2d.activities import calibrate_camera, estimate_pose
from workflows.track_3d.lesson7 import PointCloudGenerationWorkflow, generate_point_cloud_activity
from workflows.track_3d.lesson8 import GraspVectorWorkflow, compute_ransac_plane_activity, bin_shake_activity
async def main():
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    print(f"Connecting to Temporal host: {temporal_host}")
    client = await Client.connect(temporal_host)
    
    worker = Worker(
        client,
        task_queue="cv-learning-tasks",
        workflows=[LessonOneWorkflow, VisionCalibrationWorkflow, PathfinderEdgeWorkflow, PartLocalizationWorkflow, PartIdentificationWorkflow, CalibrationServiceWorkflow, PointCloudGenerationWorkflow, GraspVectorWorkflow],
        activities=[ingest_image, process_image, save_output, process_lesson2_image, process_grayscale, process_sobel, process_canny, process_lesson4_contours, process_lesson5_features, calibrate_camera, estimate_pose, generate_point_cloud_activity, compute_ransac_plane_activity, bin_shake_activity],
    )
    
    print("Starting Temporal worker...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
