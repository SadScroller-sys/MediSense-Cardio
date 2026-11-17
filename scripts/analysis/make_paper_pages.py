"""Draw the 20 pages H01-H20 for PRINTING (Section H), with the SHORT header ("ID: inpH\\H01") like P01-P30 / Q01-Q20, and write one PDF to print.
Same patched ECG-Image-Kit copy and settings as every other set (2200 x 1700 px, 200 dpi, clean).
  python -I scripts/analysis/make_paper_pages.py
Writes results/paper_h/pages/H01.png ... H20.png, results/paper_h/source_records/ (the exact .hea/.dat) and results/paper_h/ECG_pages_H01_H20_PRINT.pdf (Letter landscape, 11 x 8.5 in)."""
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
from PIL import Image

ROOT = Path("D:/Capstone Project")
OUT = ROOT / "results" / "paper_h"
KIT = ROOT / "results" / "fresh_g" / "_kit"          # the patched kit copy built for the G pages
assert KIT.exists(), "patched kit copy not found: run scripts/analysis/make_pages_generic.py first"
sel = pd.read_csv(OUT / "selected_h_20.csv")
inp, out, src, pages = KIT / "inpH", KIT / "outH", OUT / "source_records", OUT / "pages"
for d in (inp, out, src, pages):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
for _, r in sel.iterrows():
    base = (ROOT / "data" / "ptbxl" / r.filename_lr).as_posix()
    hea = open(base + ".hea").read().replace(r.record, r.page)
    for d in (inp, src):
        (d / f"{r.page}.hea").write_text(hea)
        shutil.copy(base + ".dat", d / f"{r.page}.dat")
proc = subprocess.run([sys.executable, "gen_ecg_images_from_data_batch.py", "-i", inp.as_posix(), "-o", out.as_posix(), "--print_header"], cwd=str(KIT), capture_output=True, text=True)
print(proc.stdout[-200:], proc.stderr[-200:])
ims = []
for _, r in sel.iterrows():
    f = out / f"{r.page}-0.png"
    assert f.exists(), f"missing page {r.page}"
    shutil.copy(f, pages / f"{r.page}.png")
    ims.append(Image.open(f).convert("RGB"))
ims[0].save(OUT / "ECG_pages_H01_H20_PRINT.pdf", save_all=True, append_images=ims[1:], resolution=200.0)
shutil.rmtree(inp)
shutil.rmtree(out)
print("pages and PDF written:", len(ims))
