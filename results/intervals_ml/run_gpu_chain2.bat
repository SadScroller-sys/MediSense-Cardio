@echo off
rem Resumable GPU chain 2 (each step skips what is already done). Order: L simulated photos, the printed-paper photos (H2), then the whole M set.
cd /d "D:\Capstone Project"
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_sim_photos_L.py >> results\intervals_ml\L_sim_digitise.log 2>&1
echo L_sim_done > results\intervals_ml\L_all_done.flag
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_h2_photos.py "C:\Users\Nihar Sai\Downloads\Clicked Pics" >> results\paper_h\h2_digitise.log 2>&1
echo H2_done > results\paper_h\H2_all_done.flag
python -I scripts\analysis\make_pages_generic.py results\intervals_ml\selected_M_100.csv results\intervals_ml\M inpM >> results\intervals_ml\M_make_pages.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_pages_generic.py results\intervals_ml\M\pages results\intervals_ml\M\m_digitized_12lead results\intervals_ml\M\digitise_log.csv >> results\intervals_ml\M_digitise.log 2>&1
python -I scripts\analysis\make_sim_photos_M.py >> results\intervals_ml\M_sim_make.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_sim_photos_M.py >> results\intervals_ml\M_sim_digitise.log 2>&1
echo M_done > results\intervals_ml\M_all_done.flag
