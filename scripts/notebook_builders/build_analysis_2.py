import json, os
def md(*l): return {"cell_type":"markdown","metadata":{},"source":[x+"\n" for x in l]}
def code(*l): return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":[x+"\n" for x in l]}
cells=[]
cells.append(md("# Analysis Part 2 -- patient-facing outcome per test (heart-rate version, T3-lite)",
"",
"Turns every test into what a patient would be told about their **heart rate** (slow <60, normal 60-100, fast >100 bpm; AHA/ACC ranges) and compares it with the truth:",
"- **correct** | **false alarm** (told abnormal, truth normal) | **false reassurance** (told normal, truth abnormal -- the dangerous one)",
"- **wrong abnormal** (both abnormal, wrong kind e.g. slow vs fast) | **silent drop** (picture unreadable, no answer).",
"",
"Limits (stated on purpose): heart rate only -- PR/QRS/QT and diagnosis-level false reassurance need the raw digitized signals, which were not kept. Prints plain text; runs on CPU."))
cells.append(code(
"from google.colab import drive",
"drive.mount('/content/drive')",
"import pandas as pd, numpy as np",
"D = '/content/drive/MyDrive/MediSense-Cardio-Study'",
"r = pd.read_csv(f'{D}/results_clean.csv')",
"pr = pd.read_csv(f'{D}/per_record_failures.csv')",
"reliable = set(pr[pr.pct_unreadable <= 20].record)",
"r = r[r.gt_hr.notna()].copy()                       # need a measurable ground-truth heart rate",
"r['reliable'] = r.record.isin(reliable)",
"print('tests with ground truth:', len(r), '| records:', r.record.nunique(), '| reliable records:', r[r.reliable].record.nunique())",
))
cells.append(code(
"def cat(hr):",
"    if pd.isna(hr): return None",
"    return 'slow' if hr < 60 else ('fast' if hr > 100 else 'normal')",
"r['truth'] = r.gt_hr.map(cat); r['said'] = r.dig_hr.map(cat)",
"def outcome(t):",
"    if t.said is None: return 'silent_drop'",
"    if t.said == t.truth: return 'correct'",
"    if t.truth == 'normal': return 'false_alarm'",
"    if t.said == 'normal': return 'false_reassurance'",
"    return 'wrong_abnormal'",
"r['outcome'] = r.apply(outcome, axis=1)",
"r['big_err_10'] = pd.to_numeric(r.diff_bpm, errors='coerce') > 10",
"print(r.groupby('reliable').outcome.value_counts().unstack(fill_value=0).to_string())",
))
cells.append(md("## Which records have an abnormal heart rate in the truth (only they can produce false reassurance)?"))
cells.append(code(
"tr = r.drop_duplicates('record')[['record','gt_hr','truth','reliable','is_abnormal','diagnostic_class']].sort_values('gt_hr')",
"print(tr[tr.truth != 'normal'].to_string(index=False))",
"print(); print('truth categories (all records with truth):'); print(tr.truth.value_counts().to_string())",
"print('borderline records (truth within 3 bpm of 60 or 100):'); print(tr[(tr.gt_hr.sub(60).abs() < 3) | (tr.gt_hr.sub(100).abs() < 3)].to_string(index=False))",
))
cells.append(md("## Outcome rates by damage type and level (reliable records only)"))
cells.append(code(
"def wilson(k, n, z=1.96):",
"    if n == 0: return (np.nan, np.nan)",
"    p = k / n; d = 1 + z*z/n; c = p + z*z/(2*n); a = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))",
"    return ((c - a)/d, (c + a)/d)",
"s = r[r.reliable].copy()",
"tab = s.groupby(['axis','level']).outcome.value_counts().unstack(fill_value=0)",
"for c in ['correct','false_alarm','false_reassurance','wrong_abnormal','silent_drop']:",
"    if c not in tab: tab[c] = 0",
"tab['n'] = tab[['correct','false_alarm','false_reassurance','wrong_abnormal','silent_drop']].sum(axis=1)",
"tab['wrong_any'] = tab.n - tab.correct",
"tab['pct_wrong'] = (100*tab.wrong_any/tab.n).round(1)",
"print(tab[['n','correct','false_alarm','false_reassurance','wrong_abnormal','silent_drop','pct_wrong']].to_string())",
))
cells.append(md("## Pooled by severity (1-2 mild, 3 medium, 4-5 severe) with 95% Wilson intervals"))
cells.append(code(
"s2 = s[s.axis != 'clean'].copy()",
"s2['sev'] = pd.cut(s2.level, [0,2,3,5], labels=['mild(1-2)','medium(3)','severe(4-5)'])",
"rows = []",
"for (ax, sv), g in s2.groupby(['axis','sev'], observed=True):",
"    n = len(g)",
"    for name, k in [('any_wrong', int((g.outcome!='correct').sum())), ('false_reassurance', int((g.outcome=='false_reassurance').sum())),",
"                    ('false_alarm', int((g.outcome=='false_alarm').sum())), ('silent_drop', int((g.outcome=='silent_drop').sum()))]:",
"        lo, hi = wilson(k, n); rows.append((ax, sv, name, k, n, round(100*k/n,1), round(100*lo,1), round(100*hi,1)))",
"pool = pd.DataFrame(rows, columns=['axis','severity','type','k','n','pct','ci_lo','ci_hi'])",
"print(pool[pool.type=='any_wrong'].to_string(index=False)); print()",
"print(pool[pool.type=='false_reassurance'].to_string(index=False)); print()",
"print(pool[pool.type=='silent_drop'].to_string(index=False))",
"c0 = s[s.axis=='clean']",
"print('CLEAN baseline (reliable records): n=%d, wrong=%d, false_reassurance=%d, false_alarm=%d, silent_drop=%d' % (len(c0), (c0.outcome!='correct').sum(), (c0.outcome=='false_reassurance').sum(), (c0.outcome=='false_alarm').sum(), (c0.outcome=='silent_drop').sum()))",
))
cells.append(md("## Damage-caused flips: right on the clean picture but wrong on the damaged one"))
cells.append(code(
"cl = s[s.axis=='clean'].set_index('record').outcome.rename('clean_outcome')",
"d = s[s.axis!='clean'].join(cl, on='record')",
"d = d[d.clean_outcome=='correct']",
"d['flipped'] = d.outcome != 'correct'",
"f = d.groupby(['axis','level']).agg(n=('flipped','size'), flipped=('flipped','sum'), false_reassur=('outcome', lambda x: int((x=='false_reassurance').sum())), silent=('outcome', lambda x: int((x=='silent_drop').sum())))",
"print(f.to_string())",
"print('false reassurance events (test, truth, said, gt, dig):')",
"print(s[s.outcome=='false_reassurance'][['variant_id','truth','said','gt_hr','dig_hr']].to_string(index=False))",
))
cells.append(code(
"r.to_csv(f'{D}/t3_hr_outcomes.csv', index=False); tab.to_csv(f'{D}/t3_hr_by_axis_level.csv'); pool.to_csv(f'{D}/t3_hr_pooled.csv', index=False)",
"print('saved t3_hr_outcomes.csv, t3_hr_by_axis_level.csv, t3_hr_pooled.csv')",
))
nb={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"},"colab":{"provenance":[],"name":"MediSense_Cardio_Analysis_Part2.ipynb"}},"nbformat":4,"nbformat_minor":0}
json.dump(nb,open(os.environ.get('NB_OUT','out.ipynb'),'w',encoding='utf-8'),indent=1)
print('ok',len(cells))
