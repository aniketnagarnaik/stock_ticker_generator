@echo off
REM Startup Script for Stock Ticker Generator (Windows)
REM This script starts the Flask application with proper environment setup

echo 🚀 Starting Stock Ticker Generator...
echo ==================================

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found!
    echo    Creating .env from .env.example...
    
    if exist .env.example (
        copy .env.example .env
        echo    Please edit .env file and set your DATABASE_URL
        echo    Then run this script again.
        pause
        exit /b 1
    ) else (
        echo ❌ .env.example file not found!
        echo    Please create a .env file with DATABASE_URL
        pause
        exit /b 1
    )
)

REM Load environment variables from .env file (Windows batch file limitation)
REM Note: You may need to set environment variables manually in Windows
echo ⚠️  Please ensure DATABASE_URL is set in your environment
echo    or set it manually: set DATABASE_URL=postgresql://username:password@localhost:5432/stock_ticker_db

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo    Please install Python 3.11+
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo ⚠️  Virtual environment not found!
    echo    Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🐍 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies if needed
echo 📦 Checking dependencies...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

REM Set default PORT if not set
if not defined PORT set PORT=5000

echo ✅ Starting Flask application on port %PORT%...
echo 🌐 Access your application at: http://localhost:%PORT%
echo.

REM Start Flask app
python app.py

pause
