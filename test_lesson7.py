import asyncio
from temporalio.client import Client
import uuid

async def main():
    import os
    temporal_host = os.environ.get("TEMPORAL_HOST")
    if not temporal_host:
        import subprocess
        try:
            res = subprocess.check_output("ip route show | grep default", shell=True).decode()
            ip = res.split()[2]
            temporal_host = f"{ip}:7233"
        except:
            temporal_host = "localhost:7233"
    print(f"Connecting to Temporal host: {temporal_host}")
    client = await Client.connect(temporal_host)
    payload = {
        "rgb_filename": "rgb_scene.png",
        "depth_filename": "depth_scene.png",
        "output_filename": "lesson7_output.ply",
        "fx": 500.0,
        "fy": 500.0,
        "cx": 320.0,
        "cy": 240.0,
        "scale": 1000.0
    }
    
    workflow_id = f"test-lesson-7-{uuid.uuid4()}"
    print(f"Executing workflow with ID: {workflow_id}")
    result = await client.execute_workflow(
        "PointCloudGenerationWorkflow",
        payload,
        id=workflow_id,
        task_queue="cv-learning-tasks",
    )
    print("Workflow Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
