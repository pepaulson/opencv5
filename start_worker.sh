#!/bin/bash
set -e

echo "Building C++ bridge..."
mkdir -p /app/src_cpp/build
cd /app/src_cpp/build
cmake ..
make -j$(nproc)

echo "Copying cv_engine module to python worker path..."
cp cv_engine*.so /app/temporal_worker/

echo "Starting Temporal Worker..."
cd /app/temporal_worker
python main.py
