from datetime import timedelta
from temporalio import workflow
with workflow.unsafe.imports_passed_through():
    from activities import ingest_image, process_image, save_output

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
