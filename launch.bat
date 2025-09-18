@echo off
REM Go to backend folder
cd /d D:\HLCare\project\backend

REM Start Flask backend in background
start "" python app.py

REM Wait 5 seconds to ensure server boots
timeout /t 5 >nul

REM Open frontend in default browser via Flask
start http://127.0.0.1:5000
