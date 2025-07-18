@echo off
echo Installing Tesseract OCR...

echo.
echo Checking if Tesseract is already installed...
where tesseract >nul 2>nul
if %errorlevel% equ 0 (
    echo Tesseract is already installed!
    tesseract --version
    echo.
    echo If you want to reinstall, please uninstall the current version first.
    pause
    exit /b 0
)

echo.
echo Tesseract OCR is not installed. 
echo.
echo Please follow these steps:
echo 1. Open your web browser
echo 2. Go to: https://github.com/UB-Mannheim/tesseract/wiki
echo 3. Download the latest Windows installer
echo 4. Run the installer with default settings
echo 5. After installation, run this script again to verify
echo.
echo The default installation path is: C:\Program Files\Tesseract-OCR\tesseract.exe
echo This path is already configured in your .env file
echo.
pause
