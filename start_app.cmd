@echo off
REM Activate venv and run Flask from Command Prompt
SETLOCAL

IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [!] No venv found. Creating venv...
    py -3 -m venv venv
)

call venv\Scripts\activate.bat

IF EXIST requirements.txt (
    echo Installing requirements...
    pip install -r requirements.txt
)

echo Starting Flask app...
python app.py
