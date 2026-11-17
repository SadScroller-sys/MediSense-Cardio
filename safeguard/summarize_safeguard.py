"""Tables for the traffic-light evaluation (after safeguard/evaluate_safeguard.py). Writes results/analysis/sectionP_*.csv and SECTION_P.md."""
import sys

import numpy as np
import pandas as pd

ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"
sys.path.insert(0, ROOT + "safeguard")
from evaluate_safeguard import table, wilson

lt = pd.read_csv(OUT + "sectionP_lights_all.csv")
J = pd.read_csv(OUT + "sectionJ_remeasured.csv")
J["wrong"] = J.diff_clean > 5
J["none"] = J.dig_hr.isna()
comp = J.merge(lt[["variant_id", "light", "score", "reasons"]], on="variant_id", how="left")
# no output image (no signal file): RED by rule
comp.loc[comp.none & comp.light.isna(), "light"] = "RED"
comp["wrong_or_none"] = comp.wrong | comp.none
assert comp.light.notna().all()
real = comp.axis != "C0_kit_original"
O = pd.read_csv(OUT + "sectionO_ownphotos_scored.csv").merge(lt[["variant_id", "light", "score", "reasons"]], on="variant_id", how="left")
assert O.light.notna().all()
O["wrong"] = O.wrong_c & ~O.none
O["wrong_or_none"] = O.wrong | O.none


def md(t):
    h = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return h + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


tabs = {}
tabs["comp_with_output_all"] = table(comp[~comp.none], "wrong")
tabs["comp_with_output_real_C1_C8"] = table(comp[~comp.none & real], "wrong")
tabs["comp_incl_no_output_all"] = table(comp, "wrong_or_none")
tabs["own_with_output"] = table(O[~O.none], "wrong")
tabs["own_incl_no_output"] = table(O, "wrong_or_none")
for sh in ("A_straight", "B_angled"):
    tabs["own_incl_no_output_" + sh] = table(O[O.shot == sh], "wrong_or_none")
for k, v in tabs.items():
    v.to_csv(OUT + f"sectionP_{k}.csv", index=False)
comp.to_csv(OUT + "sectionP_competition_lights_labels.csv", index=False)
O.to_csv(OUT + "sectionP_own_lights_labels.csv", index=False)
T = {"comp_with_output_all": "Competition real captures C0-C8, images with an output (wrong heart rate > 5 bpm, cleaned)",
     "comp_with_output_real_C1_C8": "Competition real captures C1-C8 only, images with an output",
     "comp_incl_no_output_all": "Competition real captures C0-C8, 'bad' = no output OR wrong (no-output images are RED by rule)",
     "own_with_output": "Own phone, 60 photos: the 54 with an output (wrong > 5 bpm)",
     "own_incl_no_output": "Own phone, all 60 photos, 'bad' = no usable heart rate OR wrong",
     "own_incl_no_output_A_straight": "Own phone, straight photos (30)", "own_incl_no_output_B_angled": "Own phone, angled photos (30)"}
L = ["# Section P: traffic-light safeguard, evaluated once on real captures and own-phone photos\n",
     "*Tool and rules frozen before this evaluation (docs/plan/analysis_plan_changes.md, 2026-11-10; one rule added before the evaluation). Trained only on the simulated new 100. Wilson 95% intervals treat images as independent, which is optimistic because the same recording appears up to 9 times (competition) or 2 times (own photos). Descriptive: fewer than 100 wrong readings on real captures.*\n"]
for k, v in tabs.items():
    L += [f"## {T[k]}\n", md(v) + "\n"]
open(OUT + "SECTION_P.md", "w", encoding="utf-8").write("\n".join(L))
pd.set_option("display.width", 250)
for k, v in tabs.items():
    print("\n" + T[k]); print(v.to_string(index=False))
print("\nreasons among RED/AMBER (competition, with output), most common:")
print(comp[~comp.none & (comp.light != "GREEN")].reasons.str.split("; ").explode().value_counts().head(8).to_string())
