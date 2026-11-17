"""D2b support: the same output features as section_D2_features.py, computed for the 360 digitised real captures (Arm C). Cached to results/analysis/sectionD2b_armC_features.csv."""
import glob
import os
import zipfile
import importlib.util

ROOT = "D:/Capstone Project/"
if __name__ == "__main__":
    import pandas as pd
    import sys
    sys.path.insert(0, ROOT + "scripts/analysis")          # so worker processes can import the feature function by name
    import section_D2_features as f
    cdir = ROOT + "results/armC/"
    if not os.path.isdir(cdir + "armC_digitized_12lead"):
        z = zipfile.ZipFile(cdir + "armC_digitized.zip")
        assert not [n for n in z.namelist() if n.startswith("/") or ".." in n.split("/")]
        z.extractall(cdir)
    files = sorted(glob.glob(cdir + "armC_digitized_12lead/*.npz"))
    assert len(files) == 360, len(files)
    pd.DataFrame(f.run_pool(f.features, files)).to_csv(ROOT + "results/analysis/sectionD2b_armC_features.csv", index=False)
    print("ARM C FEATURES DONE")
