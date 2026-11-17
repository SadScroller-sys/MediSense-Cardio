@echo off
rem Starts the MediSense-Cardio review demo on this computer. Open http://127.0.0.1:7860 in the browser. Close this window to stop it.
rem Uses the GPU environment (demo\.venv-gpu) if it exists, otherwise the normal Python (CPU).
cd /d "%~dp0.."
if exist "demo\.venv-gpu\Scripts\python.exe" (
  "demo\.venv-gpu\Scripts\python.exe" demo\app.py
) else (
  python demo\app.py
)
pause
