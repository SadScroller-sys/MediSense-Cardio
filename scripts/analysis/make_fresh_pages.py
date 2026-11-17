"""Draw the 100 FRESH pages (F001-F100) with the same patched ECG-Image-Kit and settings as P01-P30 / Q01-Q20 (2200 x 1700, 200 dpi, clean).
The kit folder scripts/tools/ecg-image-kit is NOT modified: a patched COPY is built in results/fresh/_kit (the same four patches as the Colab sweeps).
Reads results/fresh/selected_fresh_100.csv; writes results/fresh/pages/F001.png ... and results/fresh/source_records/ (the exact .hea/.dat used).
Run:  python -I scripts/analysis/make_fresh_pages.py"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = "D:/Capstone Project/"
FRESH = Path(ROOT + "results/fresh")
KIT_SRC = Path(ROOT + "scripts/tools/ecg-image-kit/codes/ecg-image-generator")
KIT = FRESH / "_kit"


def build_patched_kit():
    if KIT.exists():
        shutil.rmtree(KIT)
    shutil.copytree(KIT_SRC, KIT)
    HW = "from HandwrittenText.generate import get_handwritten"
    p = KIT / "gen_ecg_image_from_data.py"
    t = p.read_text()
    if ("                " + HW) not in t:
        t = t.replace(HW + "\n", "").replace("            if(hw_text):", "            if(hw_text):\n                " + HW)
        p.write_text(t)
    p = KIT / "helper_functions.py"
    t = p.read_text()
    if "from imgaug import augmenters as iaa\n" in t:
        p.write_text(t.replace("from imgaug import augmenters as iaa\n", ""))
    p = KIT / "CreasesWrinkles" / "creases.py"
    t = p.read_text()
    if "import imgaug" in t:
        p.write_text(t.replace("import imgaug as ia\n", "").replace("from imgaug import augmenters as iaa\n", ""))
    p = KIT / "ImageAugmentation" / "augment.py"
    t = p.read_text()
    if "import imgaug" in t and "def get_augment" in t:
        lines = t.split("\n")
        top = [ln for ln in lines if "imgaug" in ln and not ln.strip().startswith("#")]
        for imp in top:
            if lines.count(imp):
                lines.remove(imp)
        for i, ln in enumerate(lines):
            if ln.strip().startswith("def get_augment"):
                for imp in top:
                    lines.insert(i + 1, "    " + imp.strip())
                break
        p.write_text("\n".join(lines))


def main():
    sel = pd.read_csv(FRESH / "selected_fresh_100.csv")
    src = FRESH / "source_records"
    inp = FRESH / "inpF"
    out = FRESH / "pages_raw"
    for d in (src, inp, out):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    for _, r in sel.iterrows():
        base = ROOT + "data/ptbxl/" + r.filename_lr
        hea = open(base + ".hea").read().replace(r.record, r.page)
        for d in (src, inp):
            (d / f"{r.page}.hea").write_text(hea)
            shutil.copy(base + ".dat", d / f"{r.page}.dat")
    build_patched_kit()
    proc = subprocess.run([sys.executable, "gen_ecg_images_from_data_batch.py", "-i", str(inp), "-o", str(out), "--print_header"], cwd=str(KIT), capture_output=True, text=True)
    print(proc.stdout[-600:], proc.stderr[-600:])
    pages = FRESH / "pages"
    if pages.exists():
        shutil.rmtree(pages)
    pages.mkdir()
    n = 0
    for _, r in sel.iterrows():
        f = out / f"{r.page}-0.png"
        if f.exists():
            shutil.copy(f, pages / f"{r.page}.png")
            n += 1
    shutil.rmtree(inp)
    print(f"pages drawn: {n} of {len(sel)}")
    if n != len(sel):
        sys.exit("some pages are missing")


if __name__ == "__main__":
    main()
