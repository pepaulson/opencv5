import streamlit as st
import yaml
import os
import asyncio
from temporalio.client import Client, WorkflowExecutionStatus
from PIL import Image, ImageDraw

# Setup Streamlit page
st.set_page_config(page_title="OpenCV 5 & Temporal Learning Lab", layout="wide")

# Constants
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
DATA_DIR = "/app/data"

@st.cache_data
def load_lessons():
    with open("/app/config/lessons.yaml", "r") as f:
        return yaml.safe_load(f)["lessons"]

def run_workflow(workflow_name, payload):
    async def _run():
        client = await Client.connect(TEMPORAL_HOST)
        # Note: In a real app we'd want to handle workflow ID conflicts, maybe generate a UUID
        import uuid
        workflow_id = f"{workflow_name}-{uuid.uuid4()}"
        
        # We need to import the Workflow class for the type stub, or just use string name
        result = await client.execute_workflow(
            workflow_name,
            payload,
            id=workflow_id,
            task_queue="cv-learning-tasks",
        )
        return result, workflow_id
    
    return asyncio.run(_run())

async def start_cell_workflow_async(client, payload):
    workflow_id = "part-localization-workflow-id"
    try:
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        if desc.status == WorkflowExecutionStatus.RUNNING:
            return "running"
    except Exception:
        pass
        
    await client.start_workflow(
        "PartLocalizationWorkflow",
        payload,
        id=workflow_id,
        task_queue="cv-learning-tasks",
    )
    return "started"

async def check_cell_running_async(client):
    workflow_id = "part-localization-workflow-id"
    try:
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        return desc.status == WorkflowExecutionStatus.RUNNING
    except Exception:
        return False

async def trigger_camera_async(client):
    workflow_id = "part-localization-workflow-id"
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("CameraTrigger")

async def stop_cell_async(client):
    workflow_id = "part-localization-workflow-id"
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("ExitCell")

async def query_coordinates_async(client):
    workflow_id = "part-localization-workflow-id"
    handle = client.get_workflow_handle(workflow_id)
    return await handle.query("GetLatestCoordinates")

def call_temporal_func(func, *args, **kwargs):
    async def _run():
        client = await Client.connect(TEMPORAL_HOST)
        return await func(client, *args, **kwargs)
    return asyncio.run(_run())

async def start_calibration_workflow_async(client):
    workflow_id = "calibration-service-workflow-id"
    try:
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        if desc.status == WorkflowExecutionStatus.RUNNING:
            return "running"
    except Exception:
        pass
        
    await client.start_workflow(
        "CalibrationServiceWorkflow",
        id=workflow_id,
        task_queue="cv-learning-tasks",
    )
    return "started"

async def check_calibration_workflow_async(client):
    workflow_id = "calibration-service-workflow-id"
    try:
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        return desc.status == WorkflowExecutionStatus.RUNNING
    except Exception:
        return False

async def submit_calibration_images_async(client, images):
    workflow_id = "calibration-service-workflow-id"
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("SubmitCalibrationImages", images)

async def get_calibration_status_async(client):
    workflow_id = "calibration-service-workflow-id"
    handle = client.get_workflow_handle(workflow_id)
    return await handle.query("GetCalibrationStatus")

async def get_pose_estimation_async(client, image_path):
    workflow_id = "calibration-service-workflow-id"
    handle = client.get_workflow_handle(workflow_id)
    return await handle.execute_update("GetPoseEstimation", image_path)

def main():
    st.title("OpenCV 5 & Temporal Learning Lab")
    
    lessons = load_lessons()
    lesson_titles = [l["title"] for l in lessons]
    
    st.sidebar.title("Curriculum")
    selected_lesson_title = st.sidebar.radio("Select a Lesson", lesson_titles)
    
    lesson = next(l for l in lessons if l["title"] == selected_lesson_title)
    
    st.header(lesson["title"])
    st.markdown(lesson["narrative"])
    
    input_path = os.path.join(DATA_DIR, "input", lesson["input_filename"])
    output_path = os.path.join(DATA_DIR, "output", lesson["output_filename"])
    
    # UI Controls
    payload = {}
    if lesson.get("id") != 5:
        payload = {
            "input_filename": lesson["input_filename"],
            "output_filename": lesson.get("output_filename", "output.png")
        }
    else:
        payload = {
            "ref_filename": lesson["input_filename"],
            "live_filename": lesson["output_filename"]
        }
    
    if lesson.get("id", 1) == 1:
        threshold = st.slider("Select Threshold Value", 0, 255, lesson.get("default_threshold", 127))
        payload["threshold"] = threshold
    elif lesson.get("id") == 2:
        filter_type = st.radio("Select Filter Type", ["Gaussian", "Median"])
        is_sweep = st.checkbox("Run Parameter Sweep (Multiple Kernel Sizes)", value=False)
        if is_sweep:
            kernel_sizes_str = st.text_input("Kernel Sizes (comma separated, odd numbers)", "3, 5, 7, 15")
            kernel_sizes = [int(k.strip()) for k in kernel_sizes_str.split(",") if k.strip().isdigit() and int(k.strip()) % 2 != 0]
            payload["kernel_sizes"] = kernel_sizes
            payload["is_sweep"] = True
            payload["filter_type"] = filter_type
        else:
            kernel_size = st.slider("Select Kernel Size (Odd numbers only)", 3, 31, lesson.get("default_kernel_size", 5), step=2)
            payload["kernel_sizes"] = [kernel_size]
            payload["is_sweep"] = False
            payload["filter_type"] = filter_type
    elif lesson.get("id") == 3:
        kernel_size = st.slider("Gaussian Blur Kernel Size (Noise filtering before Canny)", 3, 31, lesson.get("default_kernel_size", 5), step=2)
        threshold1 = st.slider("Canny Threshold 1 (Lower bound)", 0, 255, lesson.get("default_threshold1", 100))
        threshold2 = st.slider("Canny Threshold 2 (Upper bound)", 0, 255, lesson.get("default_threshold2", 200))
        payload["kernel_size"] = kernel_size
        payload["threshold1"] = threshold1
        payload["threshold2"] = threshold2
    elif lesson.get("id") == 4:
        min_area = st.slider("Minimum Part Area (in pixels)", 10, 5000, lesson.get("default_min_area", 100))
        payload["min_area"] = float(min_area)
    elif lesson.get("id") == 5:
        st.info("Lesson 5 orchestrated via Temporal. Adjusting contrast automatically in Temporal if needed.")
    elif lesson.get("id") == 6:
        st.info("Lesson 6 state persists via a long-running Temporal workflow.")
    
    if lesson.get("id") == 3:
        st.subheader("Pipeline Visualizer")
        
        step_cols = st.columns(4)
        with step_cols[0]:
            st.markdown("**(1) Grayscale**")
        with step_cols[1]:
            st.markdown("**(2) Gaussian Blur**")
        with step_cols[2]:
            st.markdown("**(3) Sobel Gradients**")
        with step_cols[3]:
            st.markdown("**(4) Canny Edges**")
            
        selected_step = st.radio("View Intermediate Artifact:", ["Input", "Grayscale", "Blur", "Sobel", "Canny"], horizontal=True)
        
        output_placeholder = st.empty()
        
        def show_artifact():
            paths = {
                "Input": input_path,
                "Grayscale": os.path.join(DATA_DIR, "output", "l3_step1_gray.png"),
                "Blur": os.path.join(DATA_DIR, "output", "l3_step2_blur.png"),
                "Sobel": os.path.join(DATA_DIR, "output", "l3_step3_sobel.png"),
                "Canny": os.path.join(DATA_DIR, "output", "l3_step4_canny.png"),
            }
            p = paths[selected_step]
            if os.path.exists(p):
                img = Image.open(p)
                output_placeholder.image(img, use_column_width=True)
            else:
                output_placeholder.info(f"Artifact for {selected_step} not available. Run the workflow.")
                
        show_artifact()
        
    elif lesson.get("id") == 4:
        st.subheader("Robot Cell Active Status")
        is_running = call_temporal_func(check_cell_running_async)
        
        status_col, control_col = st.columns([1, 2])
        with status_col:
            if is_running:
                st.success("🤖 ROBOT CELL: ONLINE")
            else:
                st.error("🤖 ROBOT CELL: OFFLINE")
                
        with control_col:
            if not is_running:
                if st.button("Start Robot Cell Workflow", type="primary"):
                    call_temporal_func(start_cell_workflow_async, payload)
                    st.toast("Robot cell workflow started!")
                    st.rerun()
            else:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📸 Trigger Camera (PLC Signal)", type="primary", use_container_width=True):
                        call_temporal_func(trigger_camera_async)
                        st.toast("CameraTrigger signal sent!")
                        st.rerun()
                with c2:
                    if st.button("🛑 Stop Robot Cell", use_container_width=True):
                        call_temporal_func(stop_cell_async)
                        st.toast("ExitCell signal sent.")
                        st.rerun()

        # Check for queryable coordinates
        latest_coords = []
        if is_running:
            try:
                latest_coords = call_temporal_func(query_coordinates_async)
            except Exception as e:
                st.warning("Waiting for camera trigger signal...")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Vision Sensor Feed")
            if os.path.exists(input_path):
                img = Image.open(input_path).convert("RGB")
                if latest_coords:
                    draw = ImageDraw.Draw(img)
                    for idx, part in enumerate(latest_coords):
                        cx, cy = part["x"], part["y"]
                        
                        # Draw crosshair
                        r = 15
                        draw.line((cx - r, cy, cx + r, cy), fill=(0, 255, 0), width=2)
                        draw.line((cx, cy - r, cx, cy + r), fill=(0, 255, 0), width=2)
                        draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(255, 0, 0))
                        
                        # Draw Rotated Bounding Box
                        bbox = part["bounding_box"]
                        pts = [(pt["x"], pt["y"]) for pt in bbox]
                        draw.polygon(pts, outline=(255, 0, 0), width=3)
                        
                        # ID Label
                        draw.text((cx + 15, cy - 15), f"ID: {idx+1}", fill=(255, 255, 0))
                st.image(img, use_column_width=True)
            else:
                st.warning(f"Conveyor image not found at {input_path}")
                
        with col2:
            st.subheader("Robot Gripper Telemetry")
            if latest_coords:
                import pandas as pd
                telemetry_data = []
                for idx, part in enumerate(latest_coords):
                    telemetry_data.append({
                        "Part ID": f"Part_{idx+1}",
                        "Centroid X": round(part["x"], 2),
                        "Centroid Y": round(part["y"], 2),
                        "Gripper Angle (°)": round(part["angle"], 2),
                        "Area (px²)": round(part["area"], 2)
                    })
                df = pd.DataFrame(telemetry_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.success("✅ Target alignment calculated! Controller ready to execute grasp.")
            else:
                st.info("No active telemetry. Click 'Trigger Camera' to scan.")
    elif lesson.get("id") == 5:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Reference Image (Target)")
            ref_path = os.path.join(DATA_DIR, "input", lesson["input_filename"])
            if os.path.exists(ref_path):
                img = Image.open(ref_path)
                st.image(img, use_column_width=True)
            else:
                st.warning(f"Reference image not found at {ref_path}")
        with col2:
            st.subheader("Live Feed (Matched)")
            live_path = os.path.join(DATA_DIR, "input", lesson["output_filename"])
            if os.path.exists(live_path):
                img = Image.open(live_path)
                st.image(img, use_column_width=True)
            else:
                st.warning(f"Live image not found at {live_path}")
                
        st.markdown("---")
        if st.button("Run Target Acquisition Workflow"):
            with st.spinner("Running Feature Matching across Python & C++ bridge..."):
                try:
                    result, workflow_id = run_workflow(lesson["workflow_name"], payload)
                    st.success("Workflow completed!")
                    
                    st.write(f"**Temporal Retries Used:** {result.get('retry_count', 0)}")
                    st.write(f"**Inliers:** {result.get('inliers', 0)} | **Outliers:** {result.get('outliers', 0)}")
                    
                    if result.get("is_occluded", False):
                        st.warning("⚠️ Target is occluded or not found in the live feed. (Graceful failure handled by Temporal)")
                    elif result.get("success", False):
                        st.success("✅ Target Acquired! Calculating Homography...")
                        
                        # Render matches side by side
                        ref_img = Image.open(ref_path).convert("RGB")
                        live_img = Image.open(live_path).convert("RGB")
                        
                        # Create a combined image
                        total_width = ref_img.width + live_img.width
                        max_height = max(ref_img.height, live_img.height)
                        combined_img = Image.new('RGB', (total_width, max_height))
                        combined_img.paste(ref_img, (0, 0))
                        combined_img.paste(live_img, (ref_img.width, 0))
                        
                        draw = ImageDraw.Draw(combined_img)
                        
                        ref_kps = result.get("ref_keypoints", [])
                        live_kps = result.get("live_keypoints", [])
                        
                        # Draw bounding box on live image
                        bbox = result.get("bounding_box", [])
                        if len(bbox) == 4:
                            pts = [(pt["x"] + ref_img.width, pt["y"]) for pt in bbox]
                            draw.polygon(pts, outline=(0, 255, 0), width=4)
                        
                        # Draw matching lines
                        for m in result.get("matches", []):
                            pt1 = ref_kps[m["queryIdx"]]
                            pt2 = live_kps[m["trainIdx"]]
                            
                            x1, y1 = pt1["x"], pt1["y"]
                            x2, y2 = pt2["x"] + ref_img.width, pt2["y"]
                            
                            draw.line((x1, y1, x2, y2), fill=(0, 255, 255, 128), width=1)
                            draw.ellipse((x1-2, y1-2, x1+2, y1+2), fill=(255, 0, 0))
                            draw.ellipse((x2-2, y2-2, x2+2, y2+2), fill=(255, 0, 0))
                            
                        st.image(combined_img, use_column_width=True)
                except Exception as e:
                    st.error(f"Workflow failed: {e}")
                    
    elif lesson.get("id") == 6:
        st.subheader("Calibration and Pose Dashboard")
        is_running = call_temporal_func(check_calibration_workflow_async)
        
        status_col, control_col = st.columns([1, 2])
        with status_col:
            if is_running:
                st.success("🔄 CALIBRATION SERVICE: ONLINE")
            else:
                st.error("🔄 CALIBRATION SERVICE: OFFLINE")
                
        with control_col:
            if not is_running:
                if st.button("Start Calibration Service Workflow", type="primary"):
                    call_temporal_func(start_calibration_workflow_async)
                    st.toast("Calibration service started!")
                    st.rerun()

        if is_running:
            status = call_temporal_func(get_calibration_status_async)
            is_calibrated = status.get("is_calibrated", False)
            
            if not is_calibrated:
                st.warning("Camera is not calibrated. Submit 10 checkerboard images to begin.")
                if st.button("Submit Calibration Images"):
                    images = [f"/app/data/input/checkerboard_{i}.png" for i in range(1, 11)]
                    call_temporal_func(submit_calibration_images_async, images)
                    st.toast("Calibration images submitted!")
                    st.rerun()
            else:
                st.success("✅ Camera Calibrated! Intrinsic matrix persisted in Temporal.")
                
                aruco_path = os.path.join(DATA_DIR, "input", lesson["output_filename"])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Live Feed (ArUco Marker)")
                    if os.path.exists(aruco_path):
                        img = Image.open(aruco_path)
                        st.image(img, use_column_width=True)
                
                with col2:
                    st.subheader("Pose Estimation Overlay")
                    if st.button("Estimate Pose & Draw 3D Axis"):
                        with st.spinner("Calculating Extrinsics..."):
                            try:
                                pose = call_temporal_func(get_pose_estimation_async, aruco_path)
                                if pose.get("success"):
                                    img = Image.open(aruco_path).convert("RGB")
                                    draw = ImageDraw.Draw(img)
                                    
                                    # Draw 3D Axis
                                    axis_points = pose.get("axis_points", [])
                                    if len(axis_points) == 4:
                                        origin = (axis_points[0][0], axis_points[0][1])
                                        x_pt = (axis_points[1][0], axis_points[1][1])
                                        y_pt = (axis_points[2][0], axis_points[2][1])
                                        z_pt = (axis_points[3][0], axis_points[3][1])
                                        
                                        # X Axis - Red
                                        draw.line([origin, x_pt], fill=(255, 0, 0), width=3)
                                        # Y Axis - Green
                                        draw.line([origin, y_pt], fill=(0, 255, 0), width=3)
                                        # Z Axis - Blue
                                        draw.line([origin, z_pt], fill=(0, 0, 255), width=3)
                                        
                                    st.image(img, use_column_width=True)
                                    st.write(f"**Rotational Vector (rvec):** {pose.get('rvec')}")
                                    st.write(f"**Translational Vector (tvec):** {pose.get('tvec')}")
                                else:
                                    st.warning("Marker not found in the image or failed to estimate pose.")
                            except Exception as e:
                                st.error(f"Error querying Temporal: {e}")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Input Image")
            if os.path.exists(input_path):
                img = Image.open(input_path)
                st.image(img, use_column_width=True)
            else:
                st.warning(f"Input image not found at {input_path}")
                
        with col2:
            st.subheader("Output Image")
            
            output_placeholder = st.empty()
            if os.path.exists(output_path):
                img = Image.open(output_path)
                output_placeholder.image(img, use_column_width=True)
            else:
                output_placeholder.info("Run the workflow to generate output.")
            
    if lesson.get("id") not in [4, 5, 6]:
        st.markdown("---")
        
        if st.button("Run Temporal Workflow"):
            if not os.path.exists(input_path):
                st.error("Cannot run workflow: Input image is missing.")
                return
                
            with st.spinner("Executing Workflow across Python & C++ bridge..."):
                try:
                    result, workflow_id = run_workflow(lesson["workflow_name"], payload)
                    st.success("Workflow completed successfully!")
                    
                    # Update output path if workflow returned it
                    if isinstance(result, dict) and "output_path" in result:
                        output_path = result["output_path"]
                    
                    # Update output image
                    if lesson.get("id") == 3:
                        show_artifact()
                    else:
                        if os.path.exists(output_path):
                            # Force image reload by appending a query param or just re-opening
                            img = Image.open(output_path)
                            output_placeholder.image(img, use_column_width=True)
                        
                    if isinstance(result, dict) and "sweep_results" in result:
                        st.subheader("Performance Profiling (C++ Execution)")
                        for res in result["sweep_results"]:
                            st.write(f"Kernel Size: {res['kernel_size']}x{res['kernel_size']} | Filter: {res['filter_type']} | Time: **{res['execution_time_ms']:.2f} ms**")
                        
                    st.info(f"Deep Dive: [View Workflow History in Temporal UI](http://localhost:8080/namespaces/default/workflows/{workflow_id})")
                except Exception as e:
                    st.error(f"Workflow failed: {e}")

if __name__ == "__main__":
    main()
