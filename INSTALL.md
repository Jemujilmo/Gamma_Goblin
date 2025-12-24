# Installation Guide

## Prerequisites

You need Python 3.8 or higher installed on your system.

### Check if Python is installed:
```bash
python --version
# or
python3 --version
```

### Install Python (if needed):
- **Windows**: Download from [python.org](https://www.python.org/downloads/) or use `winget install Python.Python.3.12`
- **macOS**: `brew install python3`
- **Linux**: `sudo apt install python3 python3-pip`

## Setup Steps

### 1. Navigate to the project directory
```bash
cd "c:\Users\Kryst\Code Stuff\spytradebot"
```

### 2. (Optional) Create a virtual environment
```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate

# Activate it (macOS/Linux)
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install yfinance pandas numpy ta
```

### 4. Test the installation
```bash
python market_copilot.py
```

## Troubleshooting

### "pip not found"
```bash
python -m pip install -r requirements.txt
```

### "Python not found"
Make sure Python is in your PATH, or use the full path to python.exe

### Yahoo Finance rate limiting
If you get rate limit errors, wait a few minutes between requests.

### Module not found errors
Make sure you're in the project directory and all dependencies are installed:
```bash
pip list | findstr "yfinance pandas numpy ta"
```

## Verify Installation

Run the examples file:
```bash
python examples.py
```

You should see output with SPY analysis including timeframes, indicators, and recommendations.
