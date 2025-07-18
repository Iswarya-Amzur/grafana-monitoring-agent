@echo off
echo Setting up Grafana Monitoring Agent...

echo.
echo Step 1: Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Checking Tesseract installation...
where tesseract >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Tesseract OCR not found in PATH
    echo Please install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki
    echo After installation, update the TESSERACT_PATH in .env file
) else (
    echo Tesseract OCR found in PATH
)

echo.
echo Step 3: Creating environment configuration...
if not exist .env (
    copy .env.example .env
    echo Created .env file from template
    echo Please edit .env file with your Grafana credentials
) else (
    echo .env file already exists
)

echo.
echo Step 4: Creating necessary directories...
if not exist uploads mkdir uploads
if not exist outputs mkdir outputs
if not exist static mkdir static
echo Directories created successfully

echo.
echo Step 5: Testing configuration...
python -c "from config import Config; print('Configuration loaded successfully')"

if %errorlevel% neq 0 (
    echo ERROR: Configuration test failed
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Setup completed successfully!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env file with your Grafana credentials
echo 2. Install Tesseract OCR if not already installed
echo 3. Run: python app.py
echo 4. Open http://localhost:5000 in your browser
echo.
echo For automated monitoring, also run: python scheduler.py
echo.
pause
