@echo off
rem Resumable GPU chain (each step skips what is already done): L simulated photos, then the M set (pages, digitise, simulated photos, digitise).
cd /d "D:\Capstone Project"
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_sim_photos_L.py >> results\intervals_ml\L_sim_digitise.log 2>&1
echo L_sim_done > results\intervals_ml\L_all_done.flag
python -I scripts\analysis\make_pages_generic.py results\intervals_ml\selected_M_100.csv results\intervals_ml\M inpM >> results\intervals_ml\M_make_pages.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_pages_generic.py results\intervals_ml\M\pages results\intervals_ml\M\m_digitized_12lead results\intervals_ml\M\digitise_log.csv >> results\intervals_ml\M_digitise.log 2>&1
python -I scripts\analysis\make_sim_photos_M.py >> results\intervals_ml\M_sim_make.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_sim_photos_M.py >> results\intervals_ml\M_sim_digitise.log 2>&1
echo M_done > results\intervals_ml\M_all_done.flag
