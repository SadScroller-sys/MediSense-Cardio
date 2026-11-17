@echo off
rem Set N chain (resumable): draw pages, digitise pages, make simulated photos, digitise them. GPU steps use the GPU environment.
cd /d "D:\Capstone Project"
if not exist results\paper_n\pages_done.flag (
  python -I scripts\analysis\make_pages_generic.py results\paper_n\selected_N.csv results\paper_n inpN >> results\paper_n\make_pages.log 2>&1
  echo done > results\paper_n\pages_done.flag
)
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_pages_generic.py results\paper_n\pages results\paper_n\n_digitized_12lead results\paper_n\digitise_log.csv >> results\paper_n\digitise_pages.log 2>&1
echo done > results\paper_n\pages_digitised.flag
python -I scripts\analysis\make_sim_photos_N.py >> results\paper_n\sim_make.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_sim_photos_N.py >> results\paper_n\sim_digitise.log 2>&1
echo done > results\paper_n\N_sim_done.flag
