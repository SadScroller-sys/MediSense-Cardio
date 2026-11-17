@echo off
rem GPU queue (resumable). Order: full-resolution photos of batch 1 and batch 2 first (primary), then a flag, then the recompressed copies (secondary), then the M set.
cd /d "D:\Capstone Project"
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_h2_photos.py "C:\Users\Nihar Sai\Downloads\Clicked Pics" photo_id_map.csv full >> results\paper_h\h2_digitise.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_h2_photos.py "C:\Users\Nihar Sai\Downloads\clickedpics2" photo_id_map_set2.csv full >> results\paper_h\h2b_digitise.log 2>&1
echo H2_full_done > results\paper_h\H2_full_done.flag
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_h2_photos.py "C:\Users\Nihar Sai\Downloads\Clicked Pics" photo_id_map.csv compressed >> results\paper_h\h2_digitise.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_h2_photos.py "C:\Users\Nihar Sai\Downloads\clickedpics2" photo_id_map_set2.csv compressed >> results\paper_h\h2b_digitise.log 2>&1
echo H2_all_done > results\paper_h\H2_all_done.flag
python -I scripts\analysis\make_pages_generic.py results\intervals_ml\selected_M_100.csv results\intervals_ml\M inpM >> results\intervals_ml\M_make_pages.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_pages_generic.py results\intervals_ml\M\pages results\intervals_ml\M\m_digitized_12lead results\intervals_ml\M\digitise_log.csv >> results\intervals_ml\M_digitise.log 2>&1
python -I scripts\analysis\make_sim_photos_M.py >> results\intervals_ml\M_sim_make.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_sim_photos_M.py >> results\intervals_ml\M_sim_digitise.log 2>&1
echo M_done > results\intervals_ml\M_all_done.flag
