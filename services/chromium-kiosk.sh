#!/bin/bash
chromium-browser --kiosk --autoplay-policy=no-user-gesture-required http://localhost:8080 >$HOME/chromium.log 2>&1
