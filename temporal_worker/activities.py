import os
from temporalio import activity
import cv_engine

@activity.defn
async def ingest_image(input_filename: str) -> str:
    activity.logger.info(f"Ingesting image: {input_filename}")
    input_path = f"/app/data/{input_filename}"
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input image not found: {input_path}")
    return input_path

@activity.defn
async def process_image(params: dict) -> str:
    input_path = params["input_path"]
    output_filename = params.get("output_filename", "output.png")
    output_path = f"/app/data/{output_filename}"
    threshold_value = params.get("threshold", 127)
    
    activity.logger.info(f"Processing image {input_path} with threshold {threshold_value}")
    
    # Call the C++ pybind11 module
    result_path = cv_engine.run_lesson_1(input_path, output_path, threshold_value)
    return result_path

@activity.defn
async def save_output(output_path: str) -> dict:
    activity.logger.info(f"Saving output status for {output_path}")
    # In a more complex app, this might upload to S3 or write to DB
    # For now, we return a dict with the result info
    return {
        "status": "success",
        "output_path": output_path,
        "message": "Image processed successfully."
    }
