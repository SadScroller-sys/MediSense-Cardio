"""Shared loader for the printed-paper photos of set H2 (taken by the user's friend; docs/plan/analysis_plan_changes.md, 2026-11-15 night).
primary_items(): the full-resolution photos (primary set) in the STRAIGHTENED variant V2b (orientation step + frozen finder), matched to pages by image content (results/paper_h/photo_id_map.csv).
Returns (paths, ecg_ids, page_ids). WA0000 and unmatched photos are excluded. Only photos whose digitised file exists are returned."""
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PH = os.path.join(ROOT, "results", "paper_h") + os.sep


def items(kind="full", variant="V2b", shot=None):
    maps = [pd.read_csv(PH + n) for n in ("photo_id_map.csv", "photo_id_map_set2.csv") if os.path.exists(PH + n)]          # batch 1 and batch 2 of set H2 (same friend, same phone)
    m = pd.concat(maps, ignore_index=True)
    m = m[m.matched & (m.kind == kind) & (m.file != "IMG-20261115-WA0000.jpg")]
    if shot:
        m = m[m["shot"] == shot]
    paths, ids, pages = [], [], []
    for _, r in m.iterrows():
        f = PH + f"photos_dig_H2/{r.file[:-4]}__{variant}.npz"
        if os.path.exists(f):
            paths.append(f)
            ids.append(int(r.ecg_id))
            pages.append(r.page)
    return paths, ids, pages


def primary_items(variant="V2b"):
    """PRIMARY set (user decision 2026-11-15): full-resolution photos that are straight."""
    return items("full", variant, shot="straight")


def all_full_items(variant="V2b"):
    """SECONDARY: all full-resolution photos (straight and angled)."""
    return items("full", variant)
