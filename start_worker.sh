#!/bin/bash
set -e

echo "Building C++ bridge..."
mkdir -p /app/src_cpp/build
cd /app/src_cpp/build
cmake ..
make -j$(nproc)

echo "Copying cv_lab modules to python worker path..."
cp cv_lab_2d*.so /app/temporal_worker/
cp cv_lab_3d*.so /app/temporal_worker/

echo "Starting Temporal Worker..."
cd /app/temporal_worker
python main.py
