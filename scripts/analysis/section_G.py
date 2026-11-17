"""Section G (MASTER_PLAN 4b items 20 and 21): calibration of the detector's probabilities, a sample-size statement against Riley's criteria, and the CLAIM checklist.
Exploratory; descriptive. Rules fixed before running (2026-11-07):
  * Calibration is judged on the C3 held-out predictions (logistic regression of the five photo scores trained on the first 50, scored on the new 100; primary target =
    wrong heart rate > 5 bpm on images with a reading), for the model exactly as specified (class_weight='balanced'). Reported: mean predicted risk vs observed rate,
    calibration-in-the-large (intercept with slope fixed at 1), calibration slope and intercept (logistic regression of the outcome on logit(p)), Brier score vs the Brier
    score of always predicting the prevalence, and a reliability table in 8 equal-count bins. Intervals: bootstrap over recordings (1,000).
  * Exploratory (added because the specified model is class-weighted, which by construction inflates probabilities): the same model WITHOUT class weights.
  * Sample size: Riley, Ensor, Snell et al., BMJ 2020 (three criteria), for p = 5 predictors, shrinkage S = 0.9, delta = 0.05, using the prevalence of wrong readings and
    (a) the apparent Cox-Snell R2 of the unweighted fit on the first 50, (b) 15% of the maximum Cox-Snell R2 (their default when R2 is unknown), (c) R2 = 0.05, 0.10, 0.20.
    Their method assumes independent subjects; our images are 13 to 31 versions of the same recording, so the recording count and the events per recording are shown too.
    For testing a finished model: at least 100 events (Collins).
  * CLAIM 2024 (Tejani et al., Radiol Artif Intell 2024;6(4):e240300): status of each item for this study. Items 37 to 44 come from a summary of the paper, not the checklist table:
    check wording against the official table before quoting.
Reuses the data preparation of scripts/analysis/section_D.py (executed up to its C3 block)."""
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

warnings.filterwarnings("ignore")
src = open("D:/Capstone Project/scripts/analysis/section_D.py", encoding="utf-8").read().split("# ------------------------------------------------------------------ C3")[0]
exec(compile(src, "section_D_prefix", "exec"))          # d, train, test, X_COLS, sig_model, target, wilson-free helpers
ROOT = "D:/Capstone Project/"
OUT = ROOT + "results/analysis/"
rs = np.random.RandomState(21)


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def citl(y, p):
    """calibration-in-the-large: intercept a in logit P(y=1) = a + logit(p), slope fixed at 1."""
    lp = logit(p)

    def nll(a):
        z = a + lp
        return float(np.sum(np.logaddexp(0, z) - y * z))
    return float(minimize_scalar(nll, bounds=(-10, 10), method="bounded").x)


def slope_int(y, p):
    m = LogisticRegression(penalty=None, max_iter=1000).fit(logit(p).reshape(-1, 1), y)
    return float(m.coef_[0][0]), float(m.intercept_[0])


def cal_stats(y, p):
    s, i = slope_int(y, p)
    return dict(mean_pred=float(p.mean()), observed=float(y.mean()), citl=citl(y, p), slope=s, intercept=i, brier=float(brier_score_loss(y, p)),
                brier_null=float(brier_score_loss(y, np.full(len(y), y.mean()))))


def boot(y, p, groups, B=1000):
    recs = np.unique(groups)
    idx = {g: np.where(groups == g)[0] for g in recs}
    out = []
    for _ in range(B):
        ii = np.concatenate([idx[g] for g in rs.choice(recs, len(recs), replace=True)])
        if y[ii].sum() == 0 or y[ii].sum() == len(ii):
            continue
        out.append(cal_stats(y[ii], p[ii]))
    return pd.DataFrame(out)


def wilson(k, n, z=1.96):
    q = k / n
    c = (q + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(q * (1 - q) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def reliability(y, p, nb=8):
    df = pd.DataFrame(dict(y=y, p=p))
    df["bin"] = pd.qcut(df.p.rank(method="first"), nb, labels=False)
    rows = []
    for b, g in df.groupby("bin"):
        lo, hi = wilson(int(g.y.sum()), len(g))
        rows.append(dict(bin=int(b) + 1, n=len(g), mean_predicted=round(g.p.mean(), 3), observed=round(g.y.mean(), 3), obs_lo=round(max(0.0, lo), 3), obs_hi=round(min(1.0, hi), 3)))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ G1 calibration
tr, ytr = target(train, "primary")
te, yte = target(test, "primary")
gte = te.record.values
models = {
    "As specified (class weights 'balanced')": sig_model(),
    "Exploratory: same model without class weights": None,
}
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
models["Exploratory: same model without class weights"] = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=1000))
cal_rows, rel = [], {}
preds = {}
for name, m in models.items():
    m.fit(tr[X_COLS], ytr)
    p = m.predict_proba(te[X_COLS])[:, 1]
    preds[name] = p
    st = cal_stats(yte, p)
    bt = boot(yte, p, gte)
    row = dict(model=name, n=len(yte), events=int(yte.sum()))
    for k, lab in (("mean_pred", "mean predicted risk"), ("observed", "observed rate"), ("citl", "calibration-in-the-large"), ("slope", "calibration slope"),
                   ("intercept", "calibration intercept"), ("brier", "Brier score"), ("brier_null", "Brier of always predicting the prevalence")):
        lo, hi = bt[k].quantile([0.025, 0.975])
        row[lab] = f"{st[k]:.3f} ({lo:.3f} to {hi:.3f})"
    cal_rows.append(row)
    rel[name] = reliability(yte, p)
cal = pd.DataFrame(cal_rows)
cal.to_csv(OUT + "sectionG_calibration.csv", index=False)
for i, (name, r) in enumerate(rel.items()):
    r.to_csv(OUT + f"sectionG_reliability_{i + 1}.csv", index=False)

# figure
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.2, 6.2), dpi=150)
    ax.plot([0, 1], [0, 1], color="#666666", lw=1, ls="--", label="perfect calibration")
    cols = ["#0072B2", "#D55E00"]
    for (name, r), c, mk in zip(rel.items(), cols, ("o", "s")):
        ax.errorbar(r.mean_predicted, r.observed, yerr=[r.observed - r.obs_lo, r.obs_hi - r.observed], fmt=mk + "-", color=c, ms=5, lw=1.4, capsize=2,
                    label=name.replace("Exploratory: ", "(exploratory) "))
    ax.set_xlabel("predicted risk of a wrong heart rate (mean in each bin)")
    ax.set_ylabel("observed share of wrong readings")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("Calibration of the photo-quality detector\n(trained on the first 50 recordings, tested on the new 100)", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT + "sectionG_calibration.png")
    plt.close(fig)
    fig_ok = True
except Exception as exc:  # plotting must never block the numbers
    fig_ok = False
    print("figure skipped:", exc)

# ------------------------------------------------------------------ G2 sample size (Riley et al. 2020)
P = 5
S = 0.9
DELTA = 0.05


def max_r2cs(phi, n=None):
    # maximum Cox-Snell R2 = 1 - exp(2 * lnL_null / n) with lnL_null/n = phi*ln(phi) + (1-phi)*ln(1-phi)
    return 1 - np.exp(2 * (phi * np.log(phi) + (1 - phi) * np.log(1 - phi)))


def n_shrink(r2, S_=S, p=P):
    return p / ((S_ - 1) * np.log(1 - r2 / S_))


def n_riley(r2, phi):
    n1 = n_shrink(r2)                                    # criterion (i): expected shrinkage S = 0.9
    s_vh = r2 / (r2 + DELTA * max_r2cs(phi))             # criterion (ii): small optimism in Nagelkerke R2 (delta = 0.05)
    n2 = n_shrink(r2, S_=s_vh)
    n3 = (1.96 / 0.05) ** 2 * phi * (1 - phi)            # criterion (iii): overall risk to +-0.05
    return n1, n2, n3


phi_tr = float(ytr.mean())
phi_te = float(yte.mean())
m_un = LogisticRegression(max_iter=1000, penalty=None).fit(StandardScaler().fit_transform(tr[X_COLS].fillna(tr[X_COLS].median())), ytr)
Xs = StandardScaler().fit_transform(tr[X_COLS].fillna(tr[X_COLS].median()))
pp = m_un.predict_proba(Xs)[:, 1]
ll1 = float(np.sum(ytr * np.log(pp) + (1 - ytr) * np.log(1 - pp)))
ll0 = float(np.sum(ytr * np.log(phi_tr) + (1 - ytr) * np.log(1 - phi_tr)))
r2_app = 1 - np.exp(2 * (ll0 - ll1) / len(ytr))
r2_max = max_r2cs(phi_tr)
cases = [("apparent Cox-Snell R2 of the unweighted fit on the first 50", r2_app), ("15% of the maximum R2 (Riley default)", 0.15 * r2_max),
         ("R2 = 0.05", 0.05), ("R2 = 0.10", 0.10), ("R2 = 0.20", 0.20)]
rows = []
for lab, r2 in cases:
    n1, n2, n3 = n_riley(r2, phi_tr)
    need = max(n1, n2, n3)
    rows.append(dict(assumed_R2=f"{lab}: {r2:.3f}", n_shrinkage=int(np.ceil(n1)), n_optimism=int(np.ceil(n2)), n_overall_risk=int(np.ceil(n3)),
                     images_needed=int(np.ceil(need)), events_needed=int(np.ceil(need * phi_tr)), events_per_predictor=round(need * phi_tr / P, 1)))
ss = pd.DataFrame(rows)
ss.to_csv(OUT + "sectionG_sample_size.csv", index=False)

n_img_tr = len(ytr)
ev_tr = int(ytr.sum())
rec_tr = tr.record.nunique()
top5_tr = tr.assign(y=ytr).groupby("record").y.sum().sort_values(ascending=False).head(5)
top5_te = te.assign(y=yte).groupby("record").y.sum().sort_values(ascending=False).head(5)
imgs_for_100 = int(np.ceil(100 / phi_te))
have = pd.DataFrame([
    dict(set="first 50 (training)", recordings=rec_tr, images=n_img_tr, events=ev_tr, prevalence=f"{100 * phi_tr:.1f}%", events_per_predictor=round(ev_tr / P, 1),
         recordings_with_an_event=int((tr.assign(y=ytr).groupby('record').y.sum() > 0).sum()), top5_recordings_share_of_events=f"{100 * top5_tr.sum() / ev_tr:.0f}%"),
    dict(set="new 100 (test)", recordings=te.record.nunique(), images=len(yte), events=int(yte.sum()), prevalence=f"{100 * phi_te:.1f}%", events_per_predictor="",
         recordings_with_an_event=int((te.assign(y=yte).groupby('record').y.sum() > 0).sum()), top5_recordings_share_of_events=f"{100 * top5_te.sum() / yte.sum():.0f}%")])
have.to_csv(OUT + "sectionG_events_available.csv", index=False)

# ------------------------------------------------------------------ G3 CLAIM 2024 checklist
claim = [
 (1, "Title/Abstract", "Study identified as AI methodology; technique named", "To do", "Title and abstract are written with the papers (title still to be confirmed with the guide)"),
 (2, "Title/Abstract", "Structured summary (design, data, partitions, statistics, outcomes, availability)", "To do", "Report abstract"),
 (3, "Introduction", "Background; intended use and role of the AI approach", "Partly", "Intended use (photo gate before digitising) in MASTER_PLAN section 5; to be written in the report"),
 (4, "Introduction", "Aims, objectives, hypotheses", "Met", "C1 to C3 and verdict rules written before the new data (docs/plan/analysis_plan_150.md, MASTER_PLAN.md)"),
 (5, "Methods", "Prospective or retrospective", "Met", "Retrospective simulation on existing public recordings; to state"),
 (6, "Methods", "Study goal; type of prediction and target", "Met", "Wrong heart rate > 5 bpm as the target; MASTER_PLAN section 4"),
 (7, "Methods", "Data sources (public datasets, synthetic images), links", "Met", "PTB-XL (public), ECG-Image-Kit synthetic pages, PhysioNet Challenge real captures (Arm C)"),
 (8, "Methods", "Inclusion and exclusion criteria", "Met", "Selection rules (results/extension/selection_summary.md); unreliable recordings excluded by a fixed rule and listed"),
 (9, "Methods", "Data preprocessing, software and versions", "Partly", "Page drawing, damage code, digitiser settings in the notebooks and provenance json; library versions to list in the report"),
 (10, "Methods", "Selection of data subsets", "Met", "First 50 vs new 100; Arm B every 3rd recording; bridge 12 by a stated rule"),
 (11, "Methods", "De-identification", "Not applicable", "Only public, already de-identified PTB-XL data; no new patient data"),
 (12, "Methods", "Missing data", "Met", "No output kept as its own outcome; small signal gaps interpolated; missing skew imputed by the median"),
 (13, "Methods", "Image acquisition protocol", "Partly", "Simulated pages: fully described. Real captures (Arm C): capture types known, devices not controlled"),
 (14, "Methods", "Method used to obtain the reference standard", "Met", "Reference heart rate by the same detector on the 100 Hz record; QT vs 12SL on the original"),
 (15, "Methods", "Rationale, errors and limits of the reference standard", "Met", "Reference-uncertain rule; results/hr_reference_check.md; intervals only moderate vs 12SL"),
 (16, "Methods", "Source of reference annotations (annotators)", "Not applicable", "Algorithmic references, no human annotators for the outcome"),
 (17, "Methods", "Annotation of the test set", "Not applicable", "Same: algorithmic"),
 (18, "Methods", "Inter- and intra-rater variability", "Partly", "No human raters; 12SL vs Glasgow agreement quoted (results/reference_vs_ptbxl_plus.md); repeatability of the digitiser by the bridge run"),
 (19, "Methods", "How data were assigned to partitions", "Met", "First 50 = development set, new 100 = held-out replication in the same pool; fixed in advance"),
 (20, "Methods", "Level at which partitions are disjoint", "Met", "Recording level: all versions of a recording stay together. Both sets come from the same pool"),
 (21, "Methods", "Intended sample size of the test set and how determined", "Not met", "Not derived from a calculation: 100 recordings chosen for time. Post hoc: the new 100 hold 86 wrong readings, fewer than the 100 events recommended; C3 is therefore inconclusive"),
 (22, "Methods", "Detailed description of the model", "Met", "Detector: logistic regression on five scores (code and formulae in the notebooks and METHODS_AND_FORMULAE.md). Digitiser: third party, cited, unchanged"),
 (23, "Methods", "Software libraries and versions", "Partly", "Digitiser commit in extension_provenance.json; local analysis versions (scikit-learn, NeuroKit2, OpenCV) to list in the report"),
 (24, "Methods", "Initialisation of model parameters", "Not applicable", "Convex logistic regression; digitiser weights were not retrained"),
 (25, "Methods", "Details of the training approach", "Met", "Standardised scores, class-weighted logistic regression, no tuning; digitiser not trained by us"),
 (26, "Methods", "Method of selecting the final model", "Met", "One pre-specified model, no selection after seeing results"),
 (27, "Methods", "Ensembling", "Not applicable", "No ensemble"),
 (28, "Methods", "Metrics of model performance", "Met", "Wrong-reading rate, false reassurance, AUC, coverage curve, calibration"),
 (29, "Methods", "Statistical measures of significance and uncertainty", "Met", "Wilson and recording-level bootstrap intervals; exact paired tests with Holm; software versions to add"),
 (30, "Methods", "Robustness or sensitivity analysis", "Met", "With and without reference-uncertain and flagged recordings; second heart-rate detector (weak); Bazett vs Fridericia; bridge repeatability"),
 (31, "Methods", "Explainability or interpretability", "Partly", "Five interpretable scores and single-score results; no saliency maps (not applicable to a five-score model)"),
 (32, "Methods", "Evaluation on internal data", "Met", "Held-out new 100 and grouped cross-validation on all 150"),
 (33, "Methods", "Testing on external data (or justification)", "Partly", "Digitiser: real captures (Arm C, n = 40). Detector: NOT tested on real photos; stated as a limit"),
 (34, "Methods", "Clinical trial registration", "Not applicable", "Not a clinical trial"),
 (35, "Results", "Numbers included and excluded, with a flowchart", "Partly", "Counts exist (150 recordings, 2 unreliable excluded); the flow diagram is still to draw"),
 (36, "Results", "Demographic and clinical characteristics per partition", "Partly", "Sex, age and diagnosis counts exist (selection_summary.md, Section B); one table per partition to add"),
 (37, "Results", "Final model performance across partitions and subgroups (summary-derived item)", "Met", "Sections C, D and B4"),
 (38, "Results", "Accuracy estimates with uncertainty, ROC and calibration (summary-derived item)", "Met", "Intervals throughout; calibration in Section G; ROC figure to make at the freeze"),
 (39, "Results", "Failure analysis, examples of wrong results (summary-derived item)", "Partly", "Section A (good signal but wrong rate), per-recording failures, within-damage AUC; example images to add"),
 (40, "Discussion", "Limitations (summary-derived item)", "Met", "MASTER_PLAN section 5; repeated in every document"),
 (41, "Discussion", "Implications for practice (summary-derived item)", "Partly", "Worded cautiously: no claim that a flag helps patients; to write in the report"),
 (42, "Other", "Reference to the full protocol (summary-derived item)", "Met", "analysis_plan_150.md, MASTER_PLAN.md and the changes log"),
 (43, "Other", "Availability of software, model and data (summary-derived item)", "Partly", "Code and notebooks in the project folder; repository not yet committed or published"),
 (44, "Other", "Funding and support (summary-derived item)", "To do", "To state; ask the team"),
]
ck = pd.DataFrame(claim, columns=["item", "section", "requirement (shortened)", "status", "where / what"])
ck.to_csv(OUT + "sectionG_claim_checklist.csv", index=False)
counts = ck.status.value_counts().to_dict()


def md_table(t):
    head = "| " + " | ".join(map(str, t.columns)) + " |\n|" + "---|" * len(t.columns) + "\n"
    return head + "\n".join("| " + " | ".join(str(z) for z in r) + " |" for r in t.itertuples(index=False))


L = ["# Section G results: calibration, sample size, reporting checklist\n",
     "*Generated by `scripts/analysis/section_G.py`. Exploratory and descriptive; rules in the script header.*\n",
     "## G1. Calibration of the detector's probabilities (trained on the first 50, tested on the new 100; target = wrong heart rate > 5 bpm)\n",
     "A calibration slope of 1 and an intercept of 0 mean the predicted risks can be read as real probabilities. Slope below 1: predictions too extreme. "
     "Calibration-in-the-large above 0: risk under-predicted on average; below 0: over-predicted.\n",
     md_table(cal.T.reset_index().rename(columns={"index": "measure", 0: cal.model[0], 1: cal.model[1]}).iloc[1:]) + "\n",
     "Reliability table (8 equal-count bins), model as specified:\n", md_table(rel[cal.model[0]]) + "\n",
     "Reliability table, exploratory unweighted model:\n", md_table(rel[cal.model[1]]) + "\n",
     ("![Calibration](sectionG_calibration.png)\n" if fig_ok else ""),
     "## G2. Is the sample big enough? (Riley et al., BMJ 2020; 5 predictors, shrinkage 0.9, delta 0.05; approximate, assumes independent subjects)\n",
     f"Prevalence of wrong readings in the training set: {100 * phi_tr:.1f}% (maximum Cox-Snell R2 = {r2_max:.3f}).\n",
     md_table(ss) + "\n",
     "What we have:\n", md_table(have) + "\n",
     f"- Collins: testing a finished model needs at least 100 events. The new 100 hold {int(yte.sum())}. At {100 * phi_te:.1f}% prevalence about {imgs_for_100:,} images would be needed (we have {len(yte):,}).\n"
     "- Images are 13 to 31 versions of the same recording, so the number of independent subjects is closer to the number of recordings, and a few recordings carry many events (last column above). "
     "By this standard the detector is below the recommended sample size; read its numbers as a prototype result.\n",
     "## G3. CLAIM 2024 checklist: items met and not met\n",
     f"Status counts: {', '.join(f'{k} {v}' for k, v in counts.items())}. "
     "Items 37 to 44 were taken from a summary of the paper, not from the checklist table: check wording against the official table (Radiol Artif Intell 2024;6(4):e240300, appendix) before quoting. "
     "'To do' = depends on writing the report or papers.\n",
     md_table(ck) + "\n"]
open(OUT + "SECTION_G.md", "w", encoding="utf-8").write("\n".join(L))

pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 90)
print(cal.T.to_string())
print("\nreliability (specified):\n", rel[cal.model[0]].to_string(index=False))
print("\nreliability (unweighted):\n", rel[cal.model[1]].to_string(index=False))
print(f"\nprev train {phi_tr:.4f} test {phi_te:.4f}; R2 apparent {r2_app:.3f}; max R2 {r2_max:.3f}")
print(ss.to_string(index=False))
print(have.to_string(index=False))
print("images for 100 events at test prevalence:", imgs_for_100)
print("claim counts", counts, "| figure", fig_ok)
