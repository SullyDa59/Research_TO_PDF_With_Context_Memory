@echo off
REM Quick start script for Research to PDF Generator (Windows)

echo ============================================================
echo Research to PDF Generator - Quick Start
echo ============================================================
echo.

REM Check if OPENAI_API_KEY is set
if "%OPENAI_API_KEY%"=="" (
    echo WARNING: OPENAI_API_KEY is not set
    echo.
    echo Please set your OpenAI API key:
    echo   set OPENAI_API_KEY=your-key-here
    echo.
    echo Get your API key at: https://platform.openai.com/api-keys
    echo.
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo Dependencies ready
echo.

REM Start the Flask app
echo Starting Flask web UI on port 5001...
echo.
python research_ui_flask.py
