"""Photo session for set N (real photos, item 3): copy the 60 pages of the real-photo subset in a random order (seed 64) into results/paper_n/photo_session/pages as S01..S60 and write index.html, a full-screen viewer
(arrow keys or space = next page, backspace = previous, F = full screen). The key (S-number -> page) is saved in order_key.csv and is NOT shown in the viewer. Run after the pages exist: python -I scripts/analysis/build_photo_session_N.py"""
import os
import shutil

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = ROOT + "/results/paper_n/"
S = P + "photo_session/"
sel = pd.read_csv(P + "selected_N.csv")
real = sel[sel.real].page.tolist()
order = list(np.random.RandomState(64).permutation(real))
os.makedirs(S + "pages", exist_ok=True)
rows = []
for i, page in enumerate(order, start=1):
    shutil.copyfile(P + f"pages/{page}.png", S + f"pages/S{i:02d}.png")
    rows.append(dict(shown=f"S{i:02d}", page=page))
pd.DataFrame(rows).to_csv(S + "order_key.csv", index=False)
names = ",".join(f'"pages/S{i:02d}.png"' for i in range(1, len(order) + 1))
html = """<!doctype html><html><head><meta charset="utf-8"><title>Photo session N</title>
<style>html,body{margin:0;height:100%;background:#fff;font-family:Arial,sans-serif}
#img{position:fixed;left:0;top:0;width:100vw;height:100vh;object-fit:contain;background:#fff}
#bar{position:fixed;left:0;bottom:0;width:100%;background:rgba(0,0,0,.72);color:#fff;font-size:18px;padding:8px 14px;box-sizing:border-box}
#bar.hide{display:none}</style></head><body>
<img id="img" alt="ECG page"><div id="bar"></div>
<script>
const pages=[""" + names + """];
let i=0, bar=document.getElementById('bar'), img=document.getElementById('img');
function show(){img.src=pages[i];bar.textContent='Page '+(i+1)+' of '+pages.length+':  take 2 photos (1 = phone straight in front, 2 = tilted about 30 degrees).  Next: arrow right or space.  Hide this bar: H.  Full screen: F.';}
document.addEventListener('keydown',e=>{
 if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown'){i=Math.min(i+1,pages.length-1);show();e.preventDefault();}
 else if(e.key==='ArrowLeft'||e.key==='Backspace'||e.key==='PageUp'){i=Math.max(i-1,0);show();e.preventDefault();}
 else if(e.key==='h'||e.key==='H'){bar.classList.toggle('hide');}
 else if(e.key==='f'||e.key==='F'){if(!document.fullscreenElement)document.documentElement.requestFullscreen();else document.exitFullscreen();}
});
show();
</script></body></html>
"""
open(S + "index.html", "w", encoding="utf-8").write(html)
print("photo session ready:", len(order), "pages in", S)
