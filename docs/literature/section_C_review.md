# Section C: image damage and robustness (7 papers), review of 2026-11-04

Depth of reading: targeted read of the damage lists, severity design, metrics and key results of each paper (searched the
full text for those parts). Model architectures and training details were not read. None of these papers is about ECG.

## Paper by paper

### 1. ImageNet-C, Hendrycks and Dietterich, ICLR 2019 (arXiv 1903.12261): the origin of graded corruption benchmarks
- 15 corruption types in four groups (noise, blur, weather, digital, including JPEG and pixelation) at 5 severities each
  (75 corruptions), applied to ImageNet validation images; four more held-out types for further testing.
- Metrics: error per corruption and severity, divided by AlexNet's error (so hard corruptions do not dominate), averaged
  into mean Corruption Error (mCE); plus Relative mCE, which measures the drop from clean performance.
- Finding: newer classifiers were much more accurate but barely more robust relative to clean (negligible change in
  relative robustness from AlexNet to ResNet).
- For us: confirms that "one corruption at a time, five severities" is the standard design. We report error per type and
  level but no summary index, and no "gap to clean" measure.

### 2. MedMNIST-C, Di Salvo et al., arXiv 2406.17536: severity-graded corruptions for medical images
- 12 datasets, 9 imaging modalities; corruptions chosen per modality (for example uneven illumination and blur for
  microscopy, speckle noise and motion blur for ultrasound) with 5 severities defined by hyperparameters (for example brightness
  factor from 1.1 at level 1 to 1.9 at level 5).
- Finding: models show severe performance drops under some corruptions, most for noise and digital artifacts; domain-specific
  augmentation beats generic augmentation.
- For us: precedent for choosing corruptions that match how the images really degrade. Ours (grid fading, brightness
  gradient across the page) are ECG-page specific; theirs are tied to real acquisition problems.

### 3. Robustness of pathology models to corruptions, Zhang et al., arXiv 2206.14973
- Nine corruptions (including JPEG, pixelate, defocus and motion blur, brightness, saturation, hue) at five levels on
  PatchCamelyon and LocalTCT.
- Findings: error on corrupted images is 1.8 to 2.8 times the clean error; confidence estimates become unreliable
  under corruption; validation error is a poor predictor of corrupted performance.
- For us: supports reporting error by corruption and severity; the unreliable-confidence result is a warning for any
  gate that relies on a model's own confidence.

### 4. CheXphoto, Phillips et al., arXiv 2007.06199 and CheXphotogenic, Rajpurkar et al., arXiv 2011.06129
- Photos of chest X-rays: two natural photo sets (Nokia10k, 10,507 photos; iPhone1k, 1,000 photos) plus synthetic
  transformations designed to mimic photography: digital (glare, moire pattern, tilt/perspective) and spatial (blur,
  motion, rotation, translation).
- CheXphotogenic: eight chest X-ray models, tested on the photos without retraining; most dropped on photos, but the
  drops were small in absolute terms (AUC difference of the order of 0.016 in the reported summary) and several models
  stayed comparable to radiologists.
- For us: this is the closest medical analogue to our setup, "an image of a medical record, photographed". Their
  synthetic list has glare, moire and perspective tilt, which we lack; they also released real photos next to the
  synthetic ones, which is the validation step we have not done. Their way of judging a drop, against radiologists, is the
  analogue of our comparison against the clean-image noise floor.

### 5. Are Synthetic Corruptions A Reliable Proxy For Real-World Corruptions? arXiv 2505.04835
- Compares 2D Common Corruptions (synthetic) with the real ACDC weather dataset for semantic segmentation.
- Mean performance correlates strongly (Pearson 0.69 to 0.86 depending on metric), but individual corruptions differ:
  snow tracks real conditions closely, brightness and fog correlate weakly.
- They use only severity 3 because severity 1 was too weak and severity 5 too strong for the task.
- For us: supports using simulated damage to rank sensitivity, not to predict real numbers. Our brightness damage is the
  type to distrust most. (This is driving-scene segmentation, not ECG.)

### 6. On Interaction Between Augmentations and Corruptions, Mintun et al., arXiv 2102.11273
- Builds a feature space for transforms and shows that robustness depends on how similar test corruptions are to the
  augmentations used in training; on corruptions chosen to be perceptually dissimilar from ImageNet-C, methods that
  look strong on ImageNet-C lose much of the gain (several fall to near baseline error, 57.4 to 54.3%).
- For us: this matches our detector failing on damage types it was not trained on (AUC 0.32 to 0.37 for brightness, JPEG,
  rotation). A single hand-picked corruption set can give a false sense of robustness.

## What Section C means for the project
1. Our design (one damage at a time, five severities, error reported per type and level) is standard and defensible.
2. Missing from ours compared with the medical-photo papers: glare, moire, perspective tilt, motion blur, shadows,
   creases. Say so as a limit.
3. No summary robustness number. ImageNet-C style "error relative to clean" would give one comparable figure per damage type.
4. The biggest gap is the same one these papers address: no real photos. CheXphoto released real photos beside synthetic
   ones, and the proxy-corruption study checked synthetic against real. Even 5 to 10 real phone photos of printed ECG
   pages, run through the same pipeline, would let us say whether our ranking of damage types holds.
5. The detector's failure on unseen damage types is a known pattern, not just our bad luck, and a gate should not rely on
   its own confidence under shift.
6. Combined damage (blur plus tilt plus glare) is not tested here, and the papers also leave it as future work.

## Cautions
- None of these are ECG papers, so use them for design precedent, not for numbers.
- The CheXphotogenic AUC-drop figure comes from one summary line I read; check the table before quoting it.
