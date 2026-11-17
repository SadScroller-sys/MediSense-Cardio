"""Section FG: failure gallery (2026-11-14, descriptive). Selection rules were logged BEFORE any card was drawn: docs/plan/analysis_plan_changes.md, "Section FG".
Only saved outputs are used; no new digitiser run. Each card: the photo or page, and the digitised signal over the true signal.
Usage: python -I scripts/analysis/section_FG_failure_gallery.py -> results/analysis/SECTION_FG.md, sectionFG_cards.csv, sectionFG_failure_gallery.png
"""
import ast
import glob
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.signal import resample  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
R = os.path.join(ROOT, "results") + os.sep
A = R + "analysis" + os.sep
DL = "C:/Users/Nihar Sai/Downloads/"
sys.path.insert(0, os.path.join(ROOT, "demo"))
sys.path.insert(0, os.path.join(ROOT, "safeguard"))
import ecg_traffic_light as TL  # noqa: E402
import pr_interval as PRI  # noqa: E402


# ---------------------------------------------------------------- helpers (same maths as Section R)
def read_ptbxl(filename_lr, lead):
    base = ROOT + os.sep + "data" + os.sep + "ptbxl" + os.sep + filename_lr
    hdr = open(base + ".hea").read().splitlines()
    n_leads = int(hdr[0].split()[1])
    names = [h.split()[-1] for h in hdr[1:1 + n_leads]]
    idx = [n.lower() for n in names].index(lead.lower())          # PTB-XL writes AVF, the digitiser writes aVF
    line = hdr[1 + idx].split()
    gain = float(line[2].split("(")[0].split("/")[0])
    dat = np.fromfile(base + ".dat", dtype="<i2").reshape(-1, n_leads)
    return to_1k(dat[:, idx].astype(float) / gain, 100)


def read_ptbxl_100(filename_lr, lead):
    """PTB-XL 100 Hz lead in mV (the reference of the study uses the 100 Hz record)."""
    base = ROOT + os.sep + "data" + os.sep + "ptbxl" + os.sep + filename_lr
    hdr = open(base + ".hea").read().splitlines()
    n_leads = int(hdr[0].split()[1])
    names = [h.split()[-1] for h in hdr[1:1 + n_leads]]
    idx = [n.lower() for n in names].index(lead.lower())
    gain = float(hdr[1 + idx].split()[2].split("(")[0].split("/")[0])
    return np.fromfile(base + ".dat", dtype="<i2").reshape(-1, n_leads)[:, idx].astype(float) / gain


def to_1k(sig, fs):
    n = int(round(len(sig) / fs * 1000))
    x = resample(np.asarray(sig, float), n)
    return x[:10000] if n >= 10000 else np.pad(x, (0, 10000 - n), constant_values=np.nan)


def _corr(a, b, lag):
    n = len(a)
    x, y = (a[:n - lag], b[lag:]) if lag >= 0 else (a[-lag:], b[:n + lag])
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < len(a) * 0.2:
        return -2.0
    x, y = x[m], y[m]
    if x.std() < 1e-9 or y.std() < 1e-9:
        return -2.0
    return float(np.mean((x - x.mean()) * (y - y.mean())) / (x.std() * y.std()))


def best_lag(true, dig, max_ms=500):
    cs = [(_corr(true[::4], dig[::4], L), L) for L in range(-max_ms // 4, max_ms // 4 + 1)]
    c0 = max(cs)[1] * 4
    return max((_corr(true, dig, L), L) for L in range(c0 - 8, c0 + 9))[1]


def load_dig(path):
    z = np.load(path)
    return {k: z[k].astype(float) for k in z.files}


def thumb(path, size=900):
    im = Image.open(path).convert("RGB")
    im.thumbnail((size, size))
    return np.asarray(im)


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


# ---------------------------------------------------------------- data
selg = pd.read_csv(R + "fresh_g/selected_g_100.csv").set_index("page")
cards = []

# ---- 1, 2: GREEN but wrong, competition real captures
comp = pd.read_csv(A + "sectionP_competition_lights_labels.csv")
gw = comp[(comp.light == "GREEN") & comp.wrong.astype(bool) & ~comp["none"].astype(bool)].sort_values("variant_id")
tz = np.load(R + "truth/truth_lead_II.npz", allow_pickle=True)
tmeta = pd.read_csv(R + "truth/truth_meta.csv").set_index("id")
npz_comp = {}
for pat in ("armC/**/*.npz", "armCext/**/*.npz"):
    for f in glob.glob(R + pat, recursive=True):
        npz_comp[os.path.basename(f)[:-4]] = f
for i, (_, r) in enumerate(gw.iterrows(), start=1):
    rid = int(str(r.variant_id).split("__")[0])
    true = to_1k(tz[f"r{rid}"], float(tmeta.loc[rid, "fs"]))
    dig = load_dig(npz_comp[r.variant_id])["II"] / 1000.0
    cards.append(dict(n=i, title=f"{i}. GREEN but wrong (competition capture)", img=None, sigs=[("Lead II", true, dig, None)], xmax=6,
                      text=f"{r.axis}\ntrue HR {r.gt_hr_clean:.1f} bpm, read {r.dig_hr_clean:.1f} bpm\nlight GREEN, score {r.score:.3f}\nno picture file on this computer",
                      row=dict(card=i, kind="GREEN wrong, competition", id=r.variant_id, truth_bpm=round(r.gt_hr_clean, 1), read_bpm=round(r.dig_hr_clean, 1), light="GREEN")))

# ---- Z: simulated phone photos
zz = pd.read_csv(A + "sectionZ_all.csv")
z2 = zz[(zz.variant == "v2")]
z2o = z2[~z2["none"].astype(bool)].copy()
z2o["err"] = (z2o.dig_hr - z2o.gt_hr).abs()
green_wrong = z2o[(z2o.light == "GREEN") & z2o.wrong.astype(bool)].sort_values("photo")


def sim_card(n, title, photo, row, extra_text):
    page = row.page
    true = read_ptbxl(selg.loc[page, "filename_lr"], "II")
    dig = load_dig(R + f"fresh_sim/dig_v2/{photo}.npz")["II"] / 1000.0
    return dict(n=n, title=title, img=R + f"fresh_sim/photos/{photo}.jpg", sigs=[("Lead II", true, dig, None)], xmax=6,
                text=f"{photo} (simulated phone photo, extra: {row.extra})\ntrue HR {row.gt_hr:.1f} bpm, read {row.dig_hr:.1f} bpm after straightening\nlight {row.light}. {extra_text}",
                row=dict(card=n, kind=title, id=photo, truth_bpm=round(row.gt_hr, 1), read_bpm=round(row.dig_hr, 1), light=row.light))


g1 = green_wrong.iloc[0]
cards.append(sim_card(3, "3. GREEN but wrong (simulated photo)", g1.photo, g1, ""))
rest = z2o[z2o.photo != g1.photo].sort_values("err", ascending=False).iloc[0]
cards.append(sim_card(4, "4. Largest error after straightening", rest.photo, rest, f"error {rest.err:.1f} bpm."))

# ---- 5: Q2, page that stays wrong after straightening
q2 = pd.read_csv(A + "sectionQ2_all_variants.csv")
qm = pd.read_csv(R + "ownphotos2/pages_mapping.csv").set_index("page")
q2v2 = q2[(q2.variant == "V2_straighten") & q2.wrong.astype(bool)].sort_values("photo")
q = q2v2.iloc[0]
qtrue = read_ptbxl(qm.loc[q.page, "filename_lr"], "II")
qdig = load_dig(R + f"ownphotos2/confirm_out/confirm_digitized_12lead/{q.photo}__V2_straighten.npz")["II"] / 1000.0
cards.append(dict(n=5, title="5. Stays wrong after straightening", img=DL + f"ownphotos2/{q.photo}.jpg", sigs=[("Lead II", qtrue, qdig, None)], xmax=6,
                  text=f"page {q.page}, {q.shot} shot\ntrue HR {q.gt_hr_clean:.1f} bpm, read {q.dig_hr_clean:.1f} bpm\nlight {q.light}; the same page gave 66 bpm on both photos",
                  row=dict(card=5, kind="stays wrong after straightening (Q2)", id=q.photo, truth_bpm=round(q.gt_hr_clean, 1), read_bpm=round(q.dig_hr_clean, 1), light=q.light)))

# ---- 6: axis, largest circular error on straightened phone photos
aw = pd.read_csv(A + "sectionW_confirm_per_photo.csv")
aw = aw[(aw.version == "V2") & aw.axis.notna() & aw.ref.notna()].copy()
aw["err"] = wrap(aw.axis - aw.ref)
w = aw.loc[aw.err.abs().idxmax()]
pm = pd.read_csv(R + ("ownphotos/pages_mapping.csv" if w.set == "P" else "ownphotos2/pages_mapping.csv")).set_index("page")
folder = "ownphotos/fixexp_out/fixexp_digitized_12lead" if w.set == "P" else "ownphotos2/confirm_out/confirm_digitized_12lead"
wd = load_dig(R + f"{folder}/{w.photo}__V2_straighten.npz")
fn = pm.loc[w.page, "filename_lr"]
lagII = best_lag(read_ptbxl(fn, "II"), wd["II"] / 1000.0)
cards.append(dict(n=6, title="6. Axis failure (real photo)", img=DL + f"{'ownphotos' if w.set == 'P' else 'ownphotos2'}/{w.photo}.jpg",
                  sigs=[("Lead I", read_ptbxl(fn, "I"), wd["I"] / 1000.0, lagII), ("Lead aVF", read_ptbxl(fn, "aVF"), wd["aVF"] / 1000.0, lagII)], xmax=10,
                  text=f"page {w.page}\n12SL axis {w.ref:.0f} deg, ours {w.axis:.0f} deg (error {abs(w.err):.0f} deg)\nright-axis recording; the next largest error is 70 deg or less",
                  row=dict(card=6, kind="axis failure (W confirmation)", id=w.photo, truth_bpm=float("nan"), read_bpm=float("nan"), light="n/a", axis_12sl=round(w.ref, 1), axis_ours=round(w.axis, 1))))

# ---- 7: atrial fibrillation page with a PR value
db = pd.read_csv(ROOT + "/data/ptbxl/ptbxl_database.csv").set_index("ecg_id")
af_pages = [p for p, r in selg.iterrows() if any(k in ast.literal_eval(db.loc[int(r.ecg_id), "scp_codes"]) for k in ("AFIB", "AFLT"))]
best = None
for p in af_pages:
    lead = load_dig(R + f"fresh_g/g_digitized_12lead/{p}.npz")
    pr = PRI.pr_from_leads(lead)
    if np.isfinite(pr) and (best is None or pr > best[1]):
        best = (p, pr, lead)
p, pr, lead = best
chk = TL.check(lead)
rr = (chk.get("features") or {}).get("rr_cv")
true = read_ptbxl(selg.loc[p, "filename_lr"], "II")
hidden = (chk["light"] != "GREEN") or (rr is None) or (not np.isfinite(rr)) or (rr > 0.12) or any("irregular" in s for s in chk["reasons"])
cards.append(dict(n=7, title="7. Made-up PR on atrial fibrillation", img=R + f"fresh_g/pages/{p}.png", sigs=[("Lead II", true, lead["II"] / 1000.0, None)], xmax=6,
                  text=f"page {p} ({len(af_pages)} AF/flutter pages in G)\nour PR {pr:.0f} ms; 12SL gives no PR (no P waves)\nlight {chk['light']}, beat-spacing variation {rr:.2f}\ndemo guard hides it: {'yes' if hidden else 'NO'}",
                  row=dict(card=7, kind="AF page with a PR value", id=p, truth_bpm=float("nan"), read_bpm=float("nan"), light=chk["light"], pr_ms=round(pr, 1), rr_cv=round(float(rr), 3), hidden_by_demo_guard=bool(hidden))))

# ---- 8: no usable heart rate on the original photo
z0 = zz[(zz.variant == "v0") & zz["none"].astype(bool)].sort_values("photo").iloc[0]
v2row = z2[z2.photo == z0.photo].iloc[0]
_v2none = bool(v2row["none"])
_sig8 = [] if _v2none else [("Lead II, after straightening", read_ptbxl(selg.loc[z0.page, "filename_lr"], "II"), load_dig(R + f"fresh_sim/dig_v2/{z0.photo}.npz")["II"] / 1000.0, None)]
cards.append(dict(n=8, title="8. No usable heart rate (original photo)", img=R + f"fresh_sim/photos/{z0.photo}.jpg", sigs=_sig8, xmax=6,
                  text=f"{z0.photo} (extra: {z0.extra})\nthe digitiser gave no usable heart rate on the photo as it is\nafter straightening: " + ("none" if bool(v2row["none"]) else f"{v2row.dig_hr:.1f} bpm vs true {z0.gt_hr:.1f}, light {v2row.light}"),
                  row=dict(card=8, kind="no usable HR (Z, original photo)", id=z0.photo, truth_bpm=round(z0.gt_hr, 1), read_bpm=float("nan"), light="RED by rule")))

# ---- 9: Amplitude shrink on an own-phone photo (Section R): the original photo of set P with the lowest gain error
from pipeline import hr_clean  # noqa: E402

rr = pd.read_csv(A + "sectionR_waveform_per_image.csv")
own_r = rr[(rr.set == "own phone P")].dropna(subset=["gain_error_pct"])
g9 = own_r.loc[own_r.gain_error_pct.idxmin()]
pmP = pd.read_csv(R + "ownphotos/pages_mapping.csv").set_index("page")
true9 = read_ptbxl(pmP.loc[g9.recording, "filename_lr"], "II")
dig9 = load_dig(R + f"ownphotos/kaggle_out/ownphotos_digitized_12lead/{g9.variant_id}.npz")["II"] / 1000.0
lab9 = pd.read_csv(A + "sectionP_own_lights_labels.csv").set_index("variant_id").loc[g9.variant_id]
cards.append(dict(n=9, title="9. Amplitude shrunk on an angled photo", img=DL + f"ownphotos/{g9.variant_id}.jpg", sigs=[("Lead II", true9, dig9, None)], xmax=6,
                  text=f"page {g9.recording}, {g9.group} shot, photo as taken (no straightening)\ngain error {g9.gain_error_pct:.0f}% (the trace is much smaller than the true one)\nlight {lab9.light}, wrong HR: {'yes' if bool(lab9.wrong) else 'no'}",
                  row=dict(card=9, kind="amplitude shrink (R, own phone P)", id=g9.variant_id, truth_bpm=float("nan"), read_bpm=float("nan"), light=lab9.light, gain_error_pct=round(float(g9.gain_error_pct), 1))))

# ---- 10: false alarm on an atrial fibrillation page: heart rate right, light not GREEN (highest score among such pages)
cand = []
for p_ in af_pages:
    lead_ = load_dig(R + f"fresh_g/g_digitized_12lead/{p_}.npz")
    c_ = TL.check(lead_)
    hr_d, _ = hr_clean(lead_["II"] / 1000.0, 1000)
    t100 = read_ptbxl_100(selg.loc[p_, "filename_lr"], "II")
    hr_t, _ = hr_clean(t100, 100)
    cand.append(dict(page=p_, light=c_["light"], score=c_["score"], hr_dig=hr_d, hr_true=hr_t, right=bool(np.isfinite(hr_d) and np.isfinite(hr_t) and abs(hr_d - hr_t) <= 5), lead=lead_))
fa = [c_ for c_ in cand if c_["right"] and c_["light"] != "GREEN"]
n_right = sum(c_["right"] for c_ in cand)
if fa:
    f10 = max(fa, key=lambda c_: c_["score"])
    t10 = read_ptbxl(selg.loc[f10["page"], "filename_lr"], "II")
    cards.append(dict(n=10, title="10. False alarm on a right reading", img=R + f"fresh_g/pages/{f10['page']}.png", sigs=[("Lead II", t10, f10["lead"]["II"] / 1000.0, None)], xmax=6,
                      text=f"page {f10['page']}, atrial fibrillation / flutter\nheart rate right ({f10['hr_dig']:.1f} vs {f10['hr_true']:.1f} bpm), light {f10['light']}\n{len(fa)} of {n_right} AF pages with a right heart rate are not GREEN",
                      row=dict(card=10, kind="false alarm on a right reading (AF page)", id=f10["page"], truth_bpm=round(f10["hr_true"], 1), read_bpm=round(f10["hr_dig"], 1), light=f10["light"])))

# ---------------------------------------------------------------- figure
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
BLUE, GRAY = "#2a78d6", "#8a8984"
plt.rcParams.update({"font.size": 8, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
rvals = {}
fig = plt.figure(figsize=(21, 11.2))
outer = fig.add_gridspec(2, 5, hspace=0.12, wspace=0.2, left=0.02, right=0.99, top=0.93, bottom=0.02)
for k, c in enumerate(sorted(cards, key=lambda c: c["n"])):
    inner = outer[k // 5, k % 5].subgridspec(4, 1, height_ratios=[2.3, 0.9, 0.9, 1.35], hspace=0.35)
    axi = fig.add_subplot(inner[0])
    axi.set_title(c["title"], fontsize=9, loc="left", color=INK, fontweight="bold")
    axi.set_xticks([])
    axi.set_yticks([])
    for s in axi.spines.values():
        s.set_color(GRID)
    if c["img"] and os.path.exists(c["img"]):
        axi.imshow(thumb(c["img"]))
    else:
        axi.text(0.5, 0.5, "no picture file\non this computer" if not c["img"] else "picture not found", ha="center", va="center", color=INK2, fontsize=9)
    sigs = c["sigs"]
    if len(sigs) == 1:
        axs = [fig.add_subplot(inner[1:3])]
    elif len(sigs) == 2:
        axs = [fig.add_subplot(inner[1]), fig.add_subplot(inner[2])]
    else:
        axs = []
        axn = fig.add_subplot(inner[1:3])
        axn.axis("off")
        axn.text(0.5, 0.5, "no signal to show", ha="center", va="center", color=INK2, fontsize=9)
    for ax, (lab, true, dig, lag) in zip(axs, sigs):
        L = best_lag(true, dig) if lag is None else lag
        t = np.arange(len(true)) / 1000.0
        tm = true - np.nanmean(true)
        dm = dig - np.nanmean(dig)
        ax.plot(t, tm, color=GRAY, lw=1.0, label="true")
        ax.plot((np.arange(len(dig)) - L) / 1000.0, dm, color=BLUE, lw=1.1, label="digitised")
        ax.set_xlim(0, c["xmax"])
        lim = np.nanpercentile(np.abs(tm), 99.5) * 1.6
        ax.set_ylim(-lim, lim)
        ax.set_ylabel(f"{lab} (mV)", fontsize=7)
        r_ = _corr(true, dig, L)
        rvals.setdefault(c["n"], []).append((lab, r_))
        ax.text(0.01, 0.93, "trace match r = " + (f"{r_:.2f}" if r_ > -1.5 else "n/a (too little overlap)"), transform=ax.transAxes, fontsize=7.5, color=INK2, va="top")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=7)
        if c is not None and ax is axs[0]:
            ax.legend(frameon=False, fontsize=7, loc="upper right", ncol=2)
    axs[-1].set_xlabel("seconds", fontsize=7) if axs else None
    axt = fig.add_subplot(inner[3])
    axt.axis("off")
    if c["n"] == 6:
        ravf = [r for lab, r in rvals.get(6, []) if lab == "Lead aVF"]
        if ravf and ravf[0] < -0.5:
            c["text"] += f"\naVF trace is upside down against the true aVF (r = {ravf[0]:.2f})"
    axt.text(0, 1, c["text"], va="top", ha="left", fontsize=7.6, color=INK2, linespacing=1.35)
fig.suptitle("Failure gallery: 10 real failures chosen by a rule, not by how they look (what a failure looks like, not how often it happens)", x=0.02, ha="left", fontsize=11.5, color=INK)
fig.savefig(A + "sectionFG_failure_gallery.png", dpi=150, facecolor="white")
os.makedirs(os.path.join(ROOT, "docs", "reports", "figures"), exist_ok=True)
fig.savefig(os.path.join(ROOT, "docs", "reports", "figures", "fig4_fg_failure_gallery.png"), dpi=150, facecolor="white")

rows = pd.DataFrame([c["row"] for c in sorted(cards, key=lambda c: c["n"])])
rows.to_csv(A + "sectionFG_cards.csv", index=False)
md = ["# Section FG: failure gallery (descriptive)",
      "Selection rules: `docs/plan/analysis_plan_changes.md`, 'Section FG' (logged before any card was drawn). Cases are picked by a rule. They show what a failure looks like, not how often it happens; counts are in `results/FINAL_NUMBERS.md`.",
      "", "Figure: `results/analysis/sectionFG_failure_gallery.png` (also `docs/reports/figures/fig4_fg_failure_gallery.png`). Table: `sectionFG_cards.csv`.", "",
      "| Card | Rule | What the card shows |", "|---|---|---|"]
for c in sorted(cards, key=lambda c: c["n"]):
    md.append(f"| {c['n']} | {c['row']['kind']} | " + c["text"].replace("\n", "; ") + " |")
rl = {n: "; ".join(f"{lab} {r:.2f}" if r > -1.5 else f"{lab} n/a" for lab, r in v) for n, v in rvals.items()}
md += ["", "Waveform match (Pearson r of the digitised against the true trace after the best lag; the gain is not fitted): " + "; ".join(f"card {n}: {t}" for n, t in sorted(rl.items())) + ".",
       "Reading: where r is high (cards 2, 5 and 7) the traced waveform follows the true one, so the wrong number comes from the step after tracing (the heart-rate or interval measure), as the clean-page diagnosis in Section I found. Where r is low (cards 1, 3 and 4) the trace itself is wrong; cards 1 and 3 were still GREEN, which is why GREEN is not a guarantee. On card 6 the aVF trace is upside down against the true aVF (negative r), which is consistent with the wrong axis. Card 8: the trace is still poor after straightening (low r), so the heart rate that looks close (94.1 against 97.7) is partly luck, and the light is RED. Card 9: the trace of an angled, unstraightened photo is far too small (large negative gain error), and the light is RED. Card 10 is the other kind of failure, a false alarm: the trace is good (r about 0.97) and the heart rate is right, but atrial fibrillation beats are irregular, so the light is not GREEN (the cost recorded in FINAL_NUMBERS 3.1)."]
md += ["", "Cards 1 and 2 have no picture because the competition image files are not stored on this computer (only their digitised signals). Signals are shown as mean-removed lead II (mV) with the digitised trace shifted by the best lag within 0.5 s; the gain is not fitted."]
open(A + "SECTION_FG.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
