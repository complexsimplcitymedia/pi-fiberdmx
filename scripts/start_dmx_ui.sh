#!/bin/bash
# Startup script to activate conda environment and launch DMX UI

# Source conda
source /home/laser-dmx/miniconda3/etc/profile.d/conda.sh

# Activate the fiber-laser-dmx environment
conda activate fiber-laser-dmx

# Navigate to project directory
cd /home/laser-dmx/fiber-laser-dmx

# Start the DMX UI application
python ui/dmx_ui.py