#!/bin/bash

# Start Xvfb
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &

# Clean up any existing profiles
rm -rf $USER_DATA_DIR/*
mkdir -p $USER_DATA_DIR

# Start your Python script
python main.py