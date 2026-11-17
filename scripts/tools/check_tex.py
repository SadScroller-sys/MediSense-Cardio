"""Quick structure check for a LaTeX file (no LaTeX needed): environments, braces, cite keys, refs, bare percent signs, figure files.
Usage: python -I scripts/tools/check_tex.py docs/paper/main_v2.tex docs/paper/references.bib"""
import os
import re
import sys

tex, bib = sys.argv[1], sys.argv[2]
s = open(tex, encoding="utf-8").read()
code = re.sub(r"(?m)(?<!\\)%.*$", "", s)
envs = {e: (len(re.findall(r"\\begin\{" + re.escape(e) + r"\}", code)), len(re.findall(r"\\end\{" + re.escape(e) + r"\}", code))) for e in set(re.findall(r"\\begin\{([^}]+)\}", code))}
print("environments (begin, end):", envs, "| unbalanced:", [e for e, (a, b) in envs.items() if a != b])
print("brace balance (0 = ok):", code.count("{") - code.count("}") - code.count("\\{") + code.count("\\}"))
keys = set(re.findall(r"@\w+\{([^,]+),", open(bib, encoding="utf-8").read()))
cites = {k.strip() for m in re.findall(r"\\cite\{([^}]*)\}", code) for k in m.split(",")}
print("cite keys used:", len(cites), "| missing in bib:", sorted(cites - keys))
labs = set(re.findall(r"\\label\{([^}]*)\}", code))
refs = set(re.findall(r"\\ref\{([^}]*)\}", code))
print("refs without label:", sorted(refs - labs), "| labels never referenced:", sorted(labs - refs))
print("unescaped % in text:", len(re.findall(r"(?<!\\)%", code)))
base = os.path.dirname(tex)
figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", code)
print("figures:", [(f, os.path.exists(os.path.join(base, f))) for f in figs])
print("table/figure floats:", len(re.findall(r"\\begin\{table\}", code)), "tables,", len(re.findall(r"\\begin\{figure\}", code)), "figures")
words = len(re.findall(r"[A-Za-z]{2,}", re.sub(r"\\[A-Za-z]+", " ", code)))
print("approx word count:", words)
