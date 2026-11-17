@echo off
rem Waits for the first downloader (parts 0-3) to finish, then downloads parts 4 and 5 (resumable). Approved by the user 2026-11-15.
cd /d "D:\Capstone Project"
:wait
if not exist data\code15\download_done.flag (
  timeout /t 60 /nobreak >nul
  goto wait
)
del data\code15\download_done.flag
python -I scripts\tools\download_code15.py 6 32 > data\code15\download2.log 2>&1
