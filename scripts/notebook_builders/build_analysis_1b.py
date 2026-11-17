import json, os
def md(*l): return {"cell_type":"markdown","metadata":{},"source":[x+"\n" for x in l]}
def code(*l): return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":[x+"\n" for x in l]}
cells=[]
cells.append(md("# Analysis Part 1b -- which records fail to give a readable heart rate?",
"","Reads `results_clean.csv` (Part 1 output). Prints plain text only. Runs on CPU."))
cells.append(code(
"from google.colab import drive",
"drive.mount('/content/drive')",
"import pandas as pd, numpy as np",
"D = '/content/drive/MyDrive/MediSense-Cardio-Study'",
"r = pd.read_csv(f'{D}/results_clean.csv')",
"r['unreadable'] = r['dig_hr'].isna()",
"r['no_signal'] = r['snr_db'].isna()      # no usable digitized signal at all (vs signal present but no heart rate)",
"print('rows', len(r), '| unreadable', int(r.unreadable.sum()), '| of which no signal at all', int((r.unreadable & r.no_signal).sum()))",
))
cells.append(md("## 1. Failures on the CLEAN (undamaged) picture"))
cells.append(code(
"c = r[r.axis=='clean']",
"print('clean pictures unreadable:', int(c.unreadable.sum()), 'of', len(c))",
"print(c[c.unreadable][['record','is_abnormal','diagnostic_class','gt_hr','no_signal']].to_string(index=False))",
))
cells.append(md("## 2. Per-record failure rate across all 31 damaged/clean versions"))
cells.append(code(
"pr = r.groupby('record').agg(is_abnormal=('is_abnormal','first'), cls=('diagnostic_class','first'), gt_hr=('gt_hr','first'),",
"    n=('unreadable','size'), n_unreadable=('unreadable','sum'), n_no_signal=('no_signal','sum')).reset_index()",
"pr['pct_unreadable'] = (100*pr.n_unreadable/pr.n).round(0)",
"pr = pr.sort_values('n_unreadable', ascending=False)",
"print(pr.head(15).to_string(index=False))",
"print()",
"bins = pd.cut(pr.pct_unreadable, [-1,0,20,80,100], labels=['never fails','fails sometimes (<=20%)','fails often (20-80%)','fails almost always (>80%)'])",
"print(bins.value_counts().sort_index().to_string())",
))
cells.append(md("## 3. Are failures tied to normal vs abnormal / diagnosis?"))
cells.append(code(
"print('unreadable rate by normal/abnormal:'); print(r.groupby('is_abnormal').unreadable.mean().round(3).to_string())",
"print(); print('unreadable rate by diagnosis class:'); print(r.groupby('diagnostic_class').unreadable.mean().round(3).to_string())",
"print(); print('records that fail >80% of the time, by class:'); print(pr[pr.pct_unreadable>80].cls.value_counts().to_string())",
"print(); print('heart rate of always-failing records vs others (gt_hr):')",
"print(pr.assign(grp=np.where(pr.pct_unreadable>80,'always fails','ok')).groupby('grp').gt_hr.describe().round(1).to_string())",
))
cells.append(md("## 4. Damage effect among records that DO read on clean (removes the baseline-failure records)"))
cells.append(code(
"ok = pr[pr.pct_unreadable<=20].record",
"s = r[r.record.isin(ok)].copy()",
"s['diff_bpm']=pd.to_numeric(s.diff_bpm, errors='coerce')",
"g = s.groupby(['axis','level'])",
"t = pd.DataFrame({'n':g.size(),'unreadable':g.unreadable.sum(),'mean_err':g.diff_bpm.mean(),'median_err':g.diff_bpm.median(),'pct_err_gt5':g.diff_bpm.apply(lambda x:100*(x.dropna()>5).mean())}).round(2)",
"print(len(ok),'records with <=20% failures used'); print(t.to_string())",
))
cells.append(md("## 5. Save"))
cells.append(code(
"pr.to_csv(f'{D}/per_record_failures.csv', index=False)",
"t.to_csv(f'{D}/summary_reliable_records.csv')",
"print('saved per_record_failures.csv and summary_reliable_records.csv')",
))
nb={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"},"colab":{"provenance":[],"name":"MediSense_Cardio_Analysis_Part1b.ipynb"}},"nbformat":4,"nbformat_minor":0}
json.dump(nb,open(os.environ.get('NB_OUT','out.ipynb'),'w',encoding='utf-8'),indent=1)
print('ok',len(cells))
