from datetime import timedelta
from temporalio import workflow
with workflow.unsafe.imports_passed_through():
    from activities import ingest_image, process_image, save_output, process_lesson2_image

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
