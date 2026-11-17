"""Draw pages for a selection CSV with the same patched ECG-Image-Kit and settings as P01-P30 / Q01-Q20 / F001-F100 (2200 x 1700, 200 dpi, clean).
The kit folder scripts/tools/ecg-image-kit is NOT modified: a patched COPY is built in <root>/_kit (the same four patches as the Colab sweeps).
  python -I scripts/analysis/make_pages_generic.py <selection_csv> <root_dir> [header_dir_name]
Reads <selection_csv> (columns page, record, filename_lr); writes <root>/pages/<page>.png and <root>/source_records/ (the exact .hea/.dat used)."""
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = "D:/Capstone Project/"
KIT_SRC = Path(ROOT + "scripts/tools/ecg-image-kit/codes/ecg-image-generator")


def build_patched_kit(kit):
    if kit.exists():
        shutil.rmtree(kit)
    shutil.copytree(KIT_SRC, kit)
    HW = "from HandwrittenText.generate import get_handwritten"
    p = kit / "gen_ecg_image_from_data.py"
    t = p.read_text()
    if ("                " + HW) not in t:
        p.write_text(t.replace(HW + "\n", "").replace("            if(hw_text):", "            if(hw_text):\n                " + HW))
    p = kit / "helper_functions.py"
    t = p.read_text()
    if "from imgaug import augmenters as iaa\n" in t:
        p.write_text(t.replace("from imgaug import augmenters as iaa\n", ""))
    p = kit / "CreasesWrinkles" / "creases.py"
    t = p.read_text()
    if "import imgaug" in t:
        p.write_text(t.replace("import imgaug as ia\n", "").replace("from imgaug import augmenters as iaa\n", ""))
    p = kit / "ImageAugmentation" / "augment.py"
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
    sel = pd.read_csv(sys.argv[1])
    root = Path(sys.argv[2]).resolve()
    head = sys.argv[3] if len(sys.argv) > 3 else "inpG"
    src, inp, out, pages = root / "source_records", root / head, root / "pages_raw", root / "pages"
    for d in (src, inp, out, pages):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    for _, r in sel.iterrows():
        base = ROOT + "data/ptbxl/" + r.filename_lr
        hea = open(base + ".hea").read().replace(r.record, r.page)
        for d in (src, inp):
            (d / f"{r.page}.hea").write_text(hea)
            shutil.copy(base + ".dat", d / f"{r.page}.dat")
    kit = root / "_kit"
    build_patched_kit(kit)
    proc = subprocess.run([sys.executable, "gen_ecg_images_from_data_batch.py", "-i", str(inp), "-o", str(out), "--print_header"], cwd=str(kit), capture_output=True, text=True)
    print(proc.stdout[-300:], proc.stderr[-300:])
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
