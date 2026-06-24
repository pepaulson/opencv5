import streamlit as st
import yaml
import os
import asyncio
from temporalio.client import Client
from PIL import Image

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
    payload = {
        "input_filename": lesson["input_filename"],
        "output_filename": lesson["output_filename"]
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
