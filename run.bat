@echo off
title AI Data Analyst — Desktop Studio
cls
echo Starting AI Data Analyst Desktop Studio...
python main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    pause
)
