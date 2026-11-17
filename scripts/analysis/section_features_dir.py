"""Generic: compute the D2 output features for every .npz in a folder of saved 12-lead digitised signals.
Usage: python -I scripts/analysis/section_features_dir.py <npz_dir> <out_csv> <expected_number_of_files>"""
import glob
import sys

ROOT = "D:/Capstone Project/"
if __name__ == "__main__":
    import pandas as pd
    sys.path.insert(0, ROOT + "scripts/analysis")          # worker processes import the feature function by name
    import section_D2_features as f
    d, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    files = sorted(glob.glob(d.rstrip("/\\") + "/*.npz"))
    assert len(files) == n, f"expected {n} files, found {len(files)}"
    pd.DataFrame(f.run_pool(f.features, files)).to_csv(out, index=False)
    print("FEATURES DONE", len(files))
