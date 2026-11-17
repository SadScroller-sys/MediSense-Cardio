"""Resumable chunked download of the PTB-XL+ feature files (open data, PhysioNet 1.0.1) into data/ptbxl_plus/.

Plain GET requests stalled at 0 bytes while range requests worked, so this fetches 2 MB chunks with retries and can be
restarted at any time: it continues from the size of the partial file. Order: 12SL, ECGDeli, Glasgow.
"""
import os
import sys
import time
import urllib.request

OUT = "D:/Capstone Project/data/ptbxl_plus"
BASE = "https://physionet.org/files/ptb-xl-plus/1.0.1/features/"
FILES = ["12sl_features.csv", "ecgdeli_features.csv", "unig_features.csv"]
CHUNK = 2_000_000
os.makedirs(OUT, exist_ok=True)


def total_size(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
    return int(urllib.request.urlopen(req, timeout=60).headers["Content-Length"])


for name in FILES:
    url, path = BASE + name, os.path.join(OUT, name)
    size = total_size(url)
    have = os.path.getsize(path) if os.path.exists(path) else 0
    print(f"{name}: {have}/{size} bytes", flush=True)
    t0 = time.time()
    while have < size:
        end = min(have + CHUNK, size) - 1
        for attempt in range(8):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Range": f"bytes={have}-{end}"})
                data = urllib.request.urlopen(req, timeout=120).read()
                if len(data) != end - have + 1:
                    raise IOError(f"short read {len(data)} != {end - have + 1}")
                break
            except Exception as e:  # retry with a pause
                print(f"  retry {attempt + 1} after error: {e}", flush=True)
                time.sleep(5)
        else:
            sys.exit(f"giving up on {name} at byte {have}")
        with open(path, "ab") as f:
            f.write(data)
        have += len(data)
        print(f"  {name}: {have / 1e6:.1f}/{size / 1e6:.1f} MB ({100 * have / size:.0f}%), {have / max(1, time.time() - t0) / 1e3:.0f} KB/s avg", flush=True)
    assert os.path.getsize(path) == size, f"{name}: size mismatch"
    print(f"{name}: DONE", flush=True)
print("ALL DONE", flush=True)
