#!/bin/bash
# waits for set P to finish, then runs each one-time test in order (each script refuses to run twice)
cd "D:/Capstone Project"
PY=demo/.venv-gpu/Scripts/python.exe
until [ -f results/paper_p/P_sim_done.flag ]; do sleep 60; done
sleep 30
$PY -I scripts/analysis/section_P_test.py pages > results/paper_p/test_pages.log 2>&1
$PY -I scripts/analysis/section_P_test.py sim > results/paper_p/test_sim.log 2>&1
$PY -I scripts/analysis/section_P_verdict.py > results/paper_p/verdict.log 2>&1
$PY -I scripts/analysis/qt_public_test_T2.py pages > results/qt_public/T2_pages.log 2>&1
$PY -I scripts/analysis/qt_public_test_T2.py sim > results/qt_public/T2_sim.log 2>&1
echo "P TESTS FINISHED"
