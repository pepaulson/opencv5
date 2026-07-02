from datetime import timedelta
from temporalio import workflow
with workflow.unsafe.imports_passed_through():
    from activities import ingest_image, process_image, save_output, process_lesson2_image, process_grayscale, process_sobel, process_canny, process_lesson4_contours

@workflow.defn
class LessonOneWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        input_filename = payload.get("input_filename", "input.png")
        output_filename = payload.get("output_filename", "output.png")
        threshold_value = payload.get("threshold", 127)

        # 1. Ingest
        input_path = await workflow.execute_activity(
            ingest_image,
            input_filename,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # 2. Process (C++)
        process_params = {
            "input_path": input_path,
            "output_filename": output_filename,
            "threshold": threshold_value
        }
        output_path = await workflow.execute_activity(
            process_image,
            process_params,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # 3. Save Output
        result = await workflow.execute_activity(
            save_output,
            output_path,
            start_to_close_timeout=timedelta(seconds=10),
        )

        return result

@workflow.defn
class VisionCalibrationWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        input_filename = payload.get("input_filename", "noisy_part.png")
        output_filename = payload.get("output_filename", "filtered_part.png")
        kernel_sizes = payload.get("kernel_sizes", [payload.get("kernel_size", 5)])
        filter_type = payload.get("filter_type", "Gaussian")
        is_sweep = payload.get("is_sweep", False)

        input_path = await workflow.execute_activity(
            ingest_image,
            input_filename,
            start_to_close_timeout=timedelta(seconds=10),
        )

        results = []
        if is_sweep:
            for k_size in kernel_sizes:
                process_params = {
                    "input_path": input_path,
                    "output_filename": f"{k_size}_{output_filename}",
                    "filter_type": filter_type,
                    "kernel_size": k_size
                }
                res = await workflow.execute_activity(
                    process_lesson2_image,
                    process_params,
                    start_to_close_timeout=timedelta(seconds=30),
                )
                results.append(res)
                output_path = res["output_path"]
        else:
            k_size = kernel_sizes[0]
            process_params = {
                "input_path": input_path,
                "output_filename": output_filename,
                "filter_type": filter_type,
                "kernel_size": k_size
            }
            res = await workflow.execute_activity(
                process_lesson2_image,
                process_params,
                start_to_close_timeout=timedelta(seconds=30),
            )
            results.append(res)
            output_path = res["output_path"]

        final_result = await workflow.execute_activity(
            save_output,
            output_path,
            start_to_close_timeout=timedelta(seconds=10),
        )

        final_result["sweep_results"] = results
        return final_result

@workflow.defn
class PathfinderEdgeWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        input_filename = payload.get("input_filename", "drone_feed.png")
        kernel_size = payload.get("kernel_size", 5)
        threshold1 = payload.get("threshold1", 100)
        threshold2 = payload.get("threshold2", 200)

        # 1. Ingest
        input_path = await workflow.execute_activity(
            ingest_image,
            input_filename,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # 2. Grayscale (Activity 1)
        gray_res = await workflow.execute_activity(
            process_grayscale,
            {"input_path": input_path, "output_filename": "l3_step1_gray.png"},
            start_to_close_timeout=timedelta(seconds=10),
        )

        # 3. Gaussian Blur (Activity 2)
        blur_res = await workflow.execute_activity(
            process_lesson2_image,
            {"input_path": gray_res["output_path"], "output_filename": "l3_step2_blur.png", "filter_type": "Gaussian", "kernel_size": kernel_size},
            start_to_close_timeout=timedelta(seconds=30),
        )

        # 4. Sobel (Activity 3)
        sobel_res = await workflow.execute_activity(
            process_sobel,
            {"input_path": blur_res["output_path"], "output_filename": "l3_step3_sobel.png"},
            start_to_close_timeout=timedelta(seconds=10),
        )

        # 5. Canny (Activity 4)
        canny_res = await workflow.execute_activity(
            process_canny,
            {"input_path": sobel_res["output_path"], "output_filename": "l3_step4_canny.png", "threshold1": threshold1, "threshold2": threshold2},
            start_to_close_timeout=timedelta(seconds=10),
        )

        return {
            "status": "success",
            "gray_path": gray_res["output_path"],
            "blur_path": blur_res["output_path"],
            "sobel_path": sobel_res["output_path"],
            "canny_path": canny_res["output_path"]
        }

@workflow.defn
class PartLocalizationWorkflow:
    def __init__(self) -> None:
        self._trigger_received = False
        self._latest_coordinates = []
        self._is_exit = False

    @workflow.signal(name="CameraTrigger")
    def camera_trigger(self) -> None:
        self._trigger_received = True

    @workflow.signal(name="ExitCell")
    def exit_cell(self) -> None:
        self._is_exit = True

    @workflow.query(name="GetLatestCoordinates")
    def get_latest_coordinates(self) -> list:
        return self._latest_coordinates

    @workflow.run
    async def run(self, payload: dict) -> None:
        input_filename = payload.get("input_filename", "conveyor_parts.png")
        min_area = payload.get("min_area", 100.0)

        # 1. Ingest image
        input_path = await workflow.execute_activity(
            ingest_image,
            input_filename,
            start_to_close_timeout=timedelta(seconds=10),
        )

        while not self._is_exit:
            # Wait continuously for CameraTrigger or ExitCell signals
            await workflow.wait_condition(lambda: self._trigger_received or self._is_exit)

            if self._is_exit:
                break

            self._trigger_received = False

            # Execute C++ contour extraction Activity
            activity_params = {
                "input_path": input_path,
                "min_area": min_area
            }
            coordinates = await workflow.execute_activity(
                process_lesson4_contours,
                activity_params,
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Store the computed spatial coordinates
            self._latest_coordinates = coordinates.get("parts", [])
