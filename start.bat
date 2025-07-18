@echo off
echo Starting Grafana Monitoring Agent...

echo Checking Python installation...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

echo Starting Flask application...
python app.py
