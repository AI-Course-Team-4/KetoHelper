# Restaurant Menu Crawling System Start Script

Write-Host "Starting Restaurant Menu Crawling System..." -ForegroundColor Green

# Check and create Python virtual environment
if (!(Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install packages
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install -r requirements.txt

# Start server
Write-Host "Starting server..." -ForegroundColor Green
Write-Host "Please open http://localhost:5000 in your browser" -ForegroundColor Cyan

python server.py
