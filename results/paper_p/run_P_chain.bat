@echo off
rem Set P chain (resumable): draw pages, digitise pages, make simulated photos, digitise them.
cd /d "D:\Capstone Project"
if not exist results\paper_p\pages_done.flag (
  python -I scripts\analysis\make_pages_generic.py results\paper_p\selected_P.csv results\paper_p inpP >> results\paper_p\make_pages.log 2>&1
  echo done > results\paper_p\pages_done.flag
)
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_pages_generic.py results\paper_p\pages results\paper_p\p_digitized_12lead results\paper_p\digitise_log.csv >> results\paper_p\digitise_pages.log 2>&1
echo done > results\paper_p\pages_digitised.flag
python -I scripts\analysis\make_sim_photos_P.py >> results\paper_p\sim_make.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_sim_photos_P.py >> results\paper_p\sim_digitise.log 2>&1
echo done > results\paper_p\P_sim_done.flag
