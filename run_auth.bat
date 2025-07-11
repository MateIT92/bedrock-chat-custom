@echo off
echo 🔐 Bedrock Chat Authentication
echo ================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if AWS CLI is available
aws --version >nul 2>&1
if errorlevel 1 (
    echo ❌ AWS CLI is not installed or not in PATH
    echo Please install AWS CLI from https://aws.amazon.com/cli/
    pause
    exit /b 1
)

echo ✅ Python and AWS CLI found
echo.

REM Run the authentication script
python real_cognito_auth.py

echo.
echo Press any key to exit...
pause >nul 