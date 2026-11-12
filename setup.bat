@echo off
title AI Data Analyst — Setup Wizard
cls
echo ==============================================================================
echo    AI DATA ANALYST — 1-CLICK SETUP WIZARD
echo    SRMIST Chennai - B.Tech CSE (AI ^& ML) Capstone Project
echo    Author: K Mohith Kannan (GitHub: @Mohith535)
echo ==============================================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not found on your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

python setup.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Setup encountered an issue. See above for details.
    pause
    exit /b 1
)
