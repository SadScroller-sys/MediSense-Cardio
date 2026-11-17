@echo off
rem Set Q chain (resumable): draw pages, digitise pages, make simulated photos, digitise them.
cd /d "D:\Capstone Project"
if not exist results\paper_q\pages_done.flag (
  python -I scripts\analysis\make_pages_generic.py results\paper_q\selected_Q.csv results\paper_q inpQ >> results\paper_q\make_pages.log 2>&1
  echo done > results\paper_q\pages_done.flag
)
python -I scripts\analysis\make_sim_photos_Q.py >> results\paper_q\sim_make.log 2>&1
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_pages_generic.py results\paper_q\pages results\paper_q\q_digitized_12lead results\paper_q\digitise_log.csv >> results\paper_q\digitise_pages.log 2>&1
echo done > results\paper_q\pages_digitised.flag
"demo\.venv-gpu\Scripts\python.exe" -I scripts\analysis\digitise_sim_photos_Q.py >> results\paper_q\sim_digitise.log 2>&1
echo done > results\paper_q\Q_sim_done.flag
