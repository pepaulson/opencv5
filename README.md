# Story-Driven OpenCV 5 & Temporal Learning Lab

A containerized development and learning environment designed to teach computer vision concepts using **OpenCV 5** (native C++) orchestrated by **Temporal** via Python, wrapped in a story-driven **Streamlit** frontend interface.

## Architecture

This environment bridges high-performance computer vision logic with robust workflow orchestration:
- **Orchestration Layer**: A Python-based Temporal worker manages the execution flow, state tracking, and provides deep visibility via the Temporal Workflow History.
- **Computer Vision Engine**: Core image processing operations are written in native C++ using OpenCV 5.
- **Bridge Layer**: Python Temporal activities invoke compiled C++ functions via lightweight `pybind11` bindings.
- **Frontend UI**: A Streamlit web application that guides users through narrative lessons, triggers Temporal workflows, and displays visual results.
- **Infrastructure**: Fully containerized using `docker-compose`, complete with a local Temporal cluster.

## Project Structure

```
├── docker-compose.yml       # Orchestrates Temporal, Worker, and Web UI
├── Dockerfile.worker        # Builds OpenCV 5 from source & sets up Python C++ bridge
├── Dockerfile.frontend      # Minimal environment for the Streamlit Web UI
├── start_worker.sh          # Container entrypoint to compile Pybind11 code and start worker
├── src_cpp/                 # C++ Native OpenCV source code and CMake configurations
├── temporal_worker/         # Python Temporal worker, activities, and workflows
├── frontend/                # Streamlit Web UI application
├── config/                  # Lesson engine configurations (lessons.yaml)
└── data/                    # Shared volume for input/output imagery
```

## Getting Started

> **Note**: Building the `cv_worker` container involves cloning and compiling OpenCV 5 from source to prepare for future hardware acceleration. The initial build may take **10–30 minutes** depending on your hardware.

1. Ensure you have Docker and Docker Compose installed.
2. Spin up the entire environment:

```bash
docker compose up --build
```

### Accessing the Interfaces

Once the containers are running successfully, you can access:
- **Story-Driven Learning Lab (Streamlit)**: [http://localhost:8501](http://localhost:8501)
- **Temporal Workflow UI**: [http://localhost:8080](http://localhost:8080)

## Developing & Iterating

- **Python & UI Changes**: The `frontend/`, `temporal_worker/`, and `config/` directories are mounted as volumes. Modifying these files will generally apply immediately or upon restarting the script.
- **C++ Changes**: The `src_cpp/` directory is mounted into the worker container. Currently, the pybind module compiles on startup. If you modify the C++ code, you will need to restart the `cv_worker` container so it rebuilds the bindings via `start_worker.sh`.
