"""Live check of the demo pipeline on one UPRIGHT printed-paper photo (before the orientation step the page finder found no page in such photos). Usage: demo\\.venv-gpu\\Scripts\\python.exe -I scripts/tools/check_orient_live.py <photo.jpg>"""
import os
import sys

import cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "demo"))
import pipeline as P  # noqa: E402

img = cv2.imread(sys.argv[1])
print("photo shape (height, width):", img.shape[:2], "| upright:", img.shape[0] > img.shape[1])
out = P.run(img)
print("page found after the orientation step:", out["page_found"], "| light:", out["light"], "| heart rate:", round(out["hr"], 1) if out["hr"] == out["hr"] else None, "| notes:", out["notes"], "| seconds:", round(out["seconds"]))
plain = P.run_plain(img)
print("without straightening (for comparison): light", plain.get("light"), "| heart rate", round(plain["hr"], 1) if plain.get("hr") == plain.get("hr") else None)
