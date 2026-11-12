#!/usr/bin/env bash
# AI Data Analyst — macOS / Linux Setup Script
set -e

echo "=============================================================================="
echo "   AI DATA ANALYST — SETUP WIZARD (macOS / Linux)"
echo "   SRMIST Chennai - B.Tech CSE (AI & ML) Capstone Project"
echo "   Author: K Mohith Kannan (GitHub: @Mohith535)"
echo "=============================================================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed or not in PATH!"
    echo "Please install Python 3.10+ using Homebrew or your package manager."
    exit 1
fi

python3 setup.py
