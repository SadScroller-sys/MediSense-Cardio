"""Redraw ONLY the 20 pages G001-G020 that the user photographs, with the SHORT header ("ID: inpG\\G001") like P01-P30 and Q01-Q20, and rebuild the PDF.
The signal on the pages is the same as in results/fresh_g/pages/ (same records, same kit and settings); only the header text differs (a relative input folder name is used).
  python -I scripts/analysis/make_photo_pages.py
Writes results/fresh_g/pages_photo/G001.png ... G020.png and results/fresh_g/ECG_pages_G001_G020.pdf."""
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path("D:/Capstone Project")
FG = ROOT / "results" / "fresh_g"
KIT = FG / "_kit"
inp = KIT / "inpG"
out = KIT / "outG"
for d in (inp, out):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()
for i in range(1, 21):
    for ext in (".hea", ".dat"):
        shutil.copy(FG / "source_records" / f"G{i:03d}{ext}", inp / f"G{i:03d}{ext}")
proc = subprocess.run([sys.executable, "gen_ecg_images_from_data_batch.py", "-i", inp.as_posix(), "-o", out.as_posix(), "--print_header"], cwd=str(KIT), capture_output=True, text=True)
print(proc.stdout[-200:], proc.stderr[-200:])
pp = FG / "pages_photo"
if pp.exists():
    shutil.rmtree(pp)
pp.mkdir()
ims = []
for i in range(1, 21):
    f = out / f"G{i:03d}-0.png"
    shutil.copy(f, pp / f"G{i:03d}.png")
    ims.append(Image.open(f).convert("RGB"))
ims[0].save(FG / "ECG_pages_G001_G020.pdf", save_all=True, append_images=ims[1:], resolution=200.0)
shutil.rmtree(inp)
shutil.rmtree(out)
print("photo pages and PDF rebuilt:", len(ims))
