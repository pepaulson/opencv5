import asyncio
from temporalio.client import Client

async def main():
    client = await Client.connect("localhost:7233")
    print("Executing PoseEstimationWorkflow...")
    result = await client.execute_workflow(
        "PoseEstimationWorkflow",
        {"template_filename": "lesson10_template.ply", "scene_filename": "lesson10_scene.ply"},
        id="test-lesson10-workflow",
        task_queue="cv-learning-tasks"
    )
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
