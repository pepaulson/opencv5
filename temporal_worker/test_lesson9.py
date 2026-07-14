import asyncio
import os
from temporalio.client import Client

async def test_lesson9():
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(temporal_host)
    
    payload = {
        "rgb_image_path": "/app/data/input/lesson9_rgb.png",
        "depth_image_path": "/app/data/input/lesson9_depth.png",
        "hsv_lower": [160, 100, 100],
        "hsv_upper": [180, 255, 255],
        "simulate_failure": True
    }
    
    print("Executing AutomatedHarvestWorkflow...")
    import uuid
    result = await client.execute_workflow(
        "AutomatedHarvestWorkflow",
        payload,
        id=f"lesson9-test-workflow-{uuid.uuid4()}",
        task_queue="cv-learning-tasks",
    )
    
    print("Workflow Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_lesson9())
