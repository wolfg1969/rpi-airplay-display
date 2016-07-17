#!/bin/bash
cd /home/pi/projects/pcd8544-font
./now_playing.py | tee -a now_playing.log &
