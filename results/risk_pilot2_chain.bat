@echo off
rem RISK PILOT 2 chain (resumable): waits for the download (flag), prepares parts 6-17 and joins, trains ONCE. The test is NOT part of this chain (it needs the M set and is run once by hand).
cd /d "D:\Capstone Project"
:wait
if not exist data\code15\download_done.flag (
  timeout /t 60 /nobreak >nul
  goto wait
)
if not exist data\code15\risk2_prepare_done.flag "demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\section_RISK2_prepare.py >> results\risk2_prepare.log 2>&1
if not exist data\code15\risk2_prepare_done.flag exit /b 1
if not exist results\risk_pilot2\calibration_h5.json "demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\section_RISK2_train.py >> results\risk2_train.log 2>&1
echo done > results\risk_pilot2_train_done.flag
