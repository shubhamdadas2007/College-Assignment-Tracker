@echo off
title College Tracker
echo ========================================================
echo   Launching College Assignment & Practical Tracker v4.0
echo ========================================================
echo Checking requirements...
python -m pip install -r requirements.txt --quiet
echo Starting GUI Application...
python main.py
pause
