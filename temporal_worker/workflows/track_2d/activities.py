import os
from temporalio import activity
import cv_lab_2d

@activity.defn
async def ingest_image(input_filename: str) -> str:
    activity.logger.info(f"Ingesting image: {input_filename}")
    input_path = f"/app/data/input/{input_filename}"
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input image not found: {input_path}")
    return input_path

@activity.defn
async def process_image(params: dict) -> str:
    input_path = params["input_path"]
    output_filename = params.get("output_filename", "output.png")
    output_path = f"/app/data/output/{output_filename}"
    threshold_value = params.get("threshold", 127)
    
    activity.logger.info(f"Processing image {input_path} with threshold {threshold_value}")
    
    # Call the C++ pybind11 module
    result_path = cv_lab_2d.run_lesson_1(input_path, output_path, threshold_value)
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

@activity.defn
async def process_lesson2_image(params: dict) -> dict:
    input_path = params["input_path"]
    output_filename = params.get("output_filename", "filtered.png")
    output_path = f"/app/data/output/{output_filename}"
    filter_type = params.get("filter_type", "Gaussian")
    kernel_size = params.get("kernel_size", 5)
    
    activity.logger.info(f"Processing image {input_path} with {filter_type} filter (kernel: {kernel_size})")
    
    import time
    start = time.time()
    result_path = cv_lab_2d.run_lesson_2_filter(input_path, output_path, filter_type, kernel_size)
    end = time.time()
    
    return {
        "output_path": result_path,
        "execution_time_ms": (end - start) * 1000.0,
        "filter_type": filter_type,
        "kernel_size": kernel_size
    }

@activity.defn
async def process_grayscale(params: dict) -> dict:
    input_path = params["input_path"]
    output_filename = params.get("output_filename", "gray.png")
    output_path = f"/app/data/output/{output_filename}"
    activity.logger.info(f"Converting image {input_path} to grayscale")
    result_path = cv_lab_2d.run_grayscale(input_path, output_path)
    return {"output_path": result_path}

@activity.defn
async def process_sobel(params: dict) -> dict:
    input_path = params["input_path"]
    output_filename = params.get("output_filename", "sobel.png")
    output_path = f"/app/data/output/{output_filename}"
    activity.logger.info(f"Applying Sobel to {input_path}")
    result_path = cv_lab_2d.run_lesson_3_sobel(input_path, output_path)
    return {"output_path": result_path}

@activity.defn
async def process_canny(params: dict) -> dict:
    input_path = params["input_path"]
    output_filename = params.get("output_filename", "canny.png")
    output_path = f"/app/data/output/{output_filename}"
    t1 = params.get("threshold1", 100)
    t2 = params.get("threshold2", 200)
    activity.logger.info(f"Applying Canny to {input_path} with thresholds {t1}, {t2}")
    result_path = cv_lab_2d.run_lesson_3_canny(input_path, output_path, t1, t2)
    return {"output_path": result_path}

@activity.defn
async def process_lesson4_contours(params: dict) -> dict:
    input_path = params["input_path"]
    min_area = params.get("min_area", 100.0)
    
    activity.logger.info(f"Extracting contours from {input_path} with min_area {min_area}")
    
    # Call the C++ pybind11 module
    res = cv_lab_2d.run_lesson_4_contours(input_path, min_area)
    
    # Convert C++ object hierarchy to native Python lists/dicts for JSON serialization
    contours_list = []
    for contour in res.contours:
        contour_points = []
        for pt in contour:
            contour_points.append({"x": pt.x, "y": pt.y})
        contours_list.append(contour_points)

    parts_list = []
    for part in res.parts:
        bbox_points = []
        for pt in part.bounding_box:
            bbox_points.append({"x": pt[0], "y": pt[1]})
        parts_list.append({
            "x": part.x,
            "y": part.y,
            "angle": part.angle,
            "area": part.area,
            "bounding_box": bbox_points
        })

    return {
        "status": "success",
        "contours": contours_list,
        "parts": parts_list
    }


