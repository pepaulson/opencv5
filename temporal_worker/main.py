import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from activities import ingest_image, process_image, save_output, process_lesson2_image, process_grayscale, process_sobel, process_canny, process_lesson4_contours
from workflows import LessonOneWorkflow, VisionCalibrationWorkflow, PathfinderEdgeWorkflow, PartLocalizationWorkflow

async def main():
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    print(f"Connecting to Temporal host: {temporal_host}")
    client = await Client.connect(temporal_host)
    
    worker = Worker(
        client,
        task_queue="cv-learning-tasks",
        workflows=[LessonOneWorkflow, VisionCalibrationWorkflow, PathfinderEdgeWorkflow, PartLocalizationWorkflow],
        activities=[ingest_image, process_image, save_output, process_lesson2_image, process_grayscale, process_sobel, process_canny, process_lesson4_contours],
    )
    
    print("Starting Temporal worker...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
