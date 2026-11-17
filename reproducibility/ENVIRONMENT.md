# Environment used on 2026-11-14 (exact versions)

| Item | Value |
|---|---|
| Computer | Windows 11 Pro (10.0.26300) |
| Python | 3.13.15 (system Python for the analysis scripts; `demo\.venv-gpu` for the digitiser and the demo) |
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU, 4096 MiB, driver 566.07 |
| Analysis packages (system Python) | numpy 2.5.2, pandas 3.0.6, scipy 1.18.1, scikit-learn 1.9.1, neurokit2 0.3.0, wfdb 4.3.1, matplotlib 3.11.2, opencv-python 5.0.0.93, scikit-image 0.26.0, torch 2.15.0, gradio 6.31.0 (full list: `requirements_analysis_system_python.txt`) |
| Demo / digitiser packages (`demo\.venv-gpu`) | numpy 2.5.4, pandas 3.1.1, scipy 1.18.1, scikit-learn 1.9.1, neurokit2 0.3.0, opencv-python 5.0.0.93, scikit-image 0.26.0, torch 2.14.1+cu126, torchvision 0.29.1+cu126, gradio 6.31.0, matplotlib 3.11.2 (full list: `requirements_demo_gpu.txt`) |
| Open-ECG-Digitizer | https://github.com/Ahus-AIM/Open-ECG-Digitizer, commit `97a15087d4abcda843da8c58ee74b1d8f47e6f9a`, one local patch (`patches/open_ecg_digitizer_local_changes.patch`) |
| ECG-Image-Kit | https://github.com/alphanumericslab/ecg-image-kit, commit `27b90f56896c9fc78b05a83ca14844ea2637aa0b`, one local patch (`patches/ecg_image_kit_local_changes.patch`) |
| Weight `unet_weights_07072025.pt` | SHA-256 `17fe7071ef270102631306127262fc08c250d79d4e3aeb572ab1719dd34d320b` |
| Weight `lead_name_unet_weights_07072025.pt` | SHA-256 `840bd6bf2433ee6c22db67f57c861d9d427f29e10a32eeb334f0bcf061b175a2` |
| PTB-XL | v1.0.3, checksums in `data/ptbxl/SHA256SUMS.txt` |
| Drawing settings | 2200 x 1700 px, 200 dpi, 25 mm/s, 10 mm/mV, colour pages (pink grid) |
| Colab / Kaggle | package versions were not saved by the notebooks (only the digitiser commit); a GPU of the T4 class on Colab, a Kaggle GPU for the real-capture runs |

How these were read: `python -m pip freeze` in each environment, `git rev-parse HEAD` and `git diff` in each tool folder, `sha256sum` on the weight files, `nvidia-smi`. The system Python and the GPU environment differ slightly (numpy, pandas, torch): the analysis scripts use the system Python, the digitiser and the demo use the GPU environment.
