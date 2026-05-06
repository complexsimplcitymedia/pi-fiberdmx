#!/bin/bash
# Wrapper to run test_sequential.py with root privileges (required for DMX adapter access)
cd /home/laser-dmx/fiber-laser-dmx
exec sudo python3 scripts/test_sequential.py "$@"
