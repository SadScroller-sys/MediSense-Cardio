"""LIVE PROOF DEMO -- run this live. Nothing is skipped or summarized: every
sub-step prints its real, full output, and every stage is also saved as an actual picture so it
can be shown, not just described.

You pick any rotation angle. For each one:

  Step 0: rotate the real picture by exactly that angle
  Step 1a: convert to grayscale                      -> saved as an image
  Step 1b: find edges (Canny)                          -> saved as an image, full pixel count printed
  Step 1c: find every straight line in those edges     -> EVERY line's coordinates and angle printed,
                                                           not just a count; drawn on the picture and saved
  Step 2: combine all of those individual line angles into one answer (shown in full, not summarized)
  Step 3: compare that answer to the angle you typed in

The code is never told the angle. If the measured value matches, that is the proof.

Run: python live_proof_demo.py
Pictures are saved into: D:\\Capstone Project\\results\\live_proof\\
"""
import os
import cv2
import numpy as np

IMG_PATH = r"D:\Capstone Project\results\multi_sample_test\images\00003_lr-0.png"
OUT_DIR = r"D:\Capstone Project\results\live_proof"
os.makedirs(OUT_DIR, exist_ok=True)


def rotate_by_any_angle(img, angle_deg):
    h, w = img.shape[:2]
    center = (w / 2, h / 2)
    M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))


def run(angle, run_n):
    tag = f"run{run_n}_{str(angle).replace('.', 'p').replace('-', 'neg')}"
    print("\n" + "#" * 70)
    print(f"# NEW TEST: the chosen angle = {angle} degrees")
    print("#" * 70)

    print("\n--- Step 0: start from a real, undamaged ECG page, then rotate it ---")
    img = cv2.imread(IMG_PATH)
    print(f"Loaded {IMG_PATH}")
    print(f"Size: {img.shape[1]} x {img.shape[0]} pixels")
    rotated = rotate_by_any_angle(img, float(angle))
    p0 = os.path.join(OUT_DIR, f"{tag}_0_rotated.png")
    cv2.imwrite(p0, rotated)
    print(f"Applied a rotation of exactly {angle} degrees. Saved: {p0}")

    print("\n--- Step 1a: convert to grayscale (color thrown away, brightness only) ---")
    gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    p1 = os.path.join(OUT_DIR, f"{tag}_1_gray.png")
    cv2.imwrite(p1, gray)
    print(f"Size unchanged: {gray.shape[1]} x {gray.shape[0]}. Brightness range: "
          f"{int(gray.min())} (darkest pixel) to {int(gray.max())} (brightest pixel).")
    print(f"Saved: {p1}")

    print("\n--- Step 1b: find edges (Canny) -- where does brightness change sharply? ---")
    edges = cv2.Canny(gray, 50, 150)
    p2 = os.path.join(OUT_DIR, f"{tag}_2_edges.png")
    cv2.imwrite(p2, edges)
    n_edge_px = int((edges > 0).sum())
    total_px = edges.size
    print(f"Every pixel checked: {total_px:,} pixels total.")
    print(f"Marked as an edge (white): {n_edge_px:,} pixels ({100*n_edge_px/total_px:.2f}% of the picture).")
    print(f"Saved: {p2}")

    print("\n--- Step 1c: find every straight line among those edges (Hough transform) ---")
    min_len = int(0.3 * gray.shape[1])
    print(f"Rule applied: only keep a line if it is at least {min_len} pixels long "
          f"(30% of the {gray.shape[1]}px width).")
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=min_len, maxLineGap=10)
    n_lines = 0 if lines is None else len(lines)
    print(f"Lines found and kept: {n_lines}\n")

    if lines is None or n_lines < 3:
        print("Too few long lines survived to measure anything at this exact angle -- a known, honest")
        print("limitation: at some specific rotations the grid lines split into pieces too short to pass")
        print("the 30%-of-width rule. Try a slightly different number.")
        return

    lines_arr = lines.reshape(-1, 4) if lines.ndim == 3 else lines
    print(f"{'line #':<8}{'point 1 (x,y)':<18}{'point 2 (x,y)':<18}{'raw angle':<12}{'deviation from flat/upright'}")
    angles = []
    annotated = rotated.copy()
    for i, (x1, y1, x2, y2) in enumerate(lines_arr):
        a = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180
        dev = a % 90
        dev = min(dev, 90 - dev)
        angles.append(dev)
        print(f"{i:<8}{f'({x1},{y1})':<18}{f'({x2},{y2})':<18}{a:<12.3f}{dev:.3f}")
        cv2.line(annotated, (x1, y1), (x2, y2), (0, 0, 255), 4)
    p3 = os.path.join(OUT_DIR, f"{tag}_3_lines_drawn.png")
    cv2.imwrite(p3, annotated)
    print(f"\nAll {n_lines} lines drawn in red on the picture. Saved: {p3}")

    print("\n--- Step 2: combine all the individual line measurements into one answer ---")
    print(f"All {n_lines} individual measurements, in the order they were found:")
    print([round(a, 3) for a in angles])
    measured = float(np.median(angles))
    print(f"\nThe middle (median) value of these {n_lines} numbers = {measured:.3f} degrees")

    print("\n--- Step 3: compare the answer to what you typed in ---")
    expected = abs(float(angle)) % 90
    expected = min(expected, 90 - expected)
    print(f"You typed in:  {angle} degrees")
    print(f"Code measured:        {measured:.3f} degrees")
    print("(the detector reports HOW tilted the page is, not which direction -- a page tilted")
    print(f" +{expected:.1f} degrees and one tilted -{expected:.1f} degrees look identical to it)")
    print(f"Difference:           {abs(expected - measured):.3f} degrees")


if __name__ == "__main__":
    print("=" * 70)
    print("LIVE PROOF: does the code really convert a photo into lines and detect tilt?")
    print("Nothing below is summarized -- every step prints its full, real output.")
    print("=" * 70)
    n = 0
    while True:
        raw = input("\nType any rotation angle in degrees (e.g. 3, 7.5, -10), or 'q' to quit: ").strip()
        if raw.lower() == "q":
            break
        try:
            angle = float(raw)
        except ValueError:
            print("Please type a number.")
            continue
        n += 1
        run(angle, n)
