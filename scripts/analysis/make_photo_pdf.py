"""Make the PDF of the 20 pages G001-G020 that the user shows on a screen and photographs (2 photos per page: straight on, and from the side at about 30 degrees).
  python -I scripts/analysis/make_photo_pdf.py
Writes results/fresh_g/ECG_pages_G001_G020.pdf (200 dpi, like ECG_pages_P01_P30.pdf and ECG_pages_Q01_Q20.pdf)."""
from PIL import Image

ROOT = "D:/Capstone Project/"
ims = []
for i in range(1, 21):
    im = Image.open(ROOT + f"results/fresh_g/pages/G{i:03d}.png").convert("RGB")
    ims.append(im)
ims[0].save(ROOT + "results/fresh_g/ECG_pages_G001_G020.pdf", save_all=True, append_images=ims[1:], resolution=200.0)
print("pdf written:", len(ims), "pages")
