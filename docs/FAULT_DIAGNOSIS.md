# Panel fault diagnosis

`POST /detect` answers with a `diagnosis` that states how sure it is. It says
"confirmed" only when two different models agree, each confidently. On real
photos that the models did not train on, those answers are right **98.5%** of
the time. Otherwise the answer is "likely" or "uncertain", or the user is asked
for a better photo.

## Why the answer abstains instead of always guessing

The accuracy reported before this change was not measured on real photos:

* `data/solar-panel-images/Faulty_solar_panel/` holds 300 files of **random
  noise**. They are placeholders, not panel photos, so any accuracy computed on
  them means nothing.
* The only real labelled photos in the repository are the ones the YOLO run
  printed into its mosaics (`yolo_fault_detection/runs/runs/detect/*/…batch*.jpg`).
  `scripts/fault_detection/real_crops.py` cuts them out. Each label is read from
  the file name printed on the tile. That gives 142 photos (137 distinct) in six
  classes: Bird 31, Clean 27, Dust 37, Electrical 13, Physical 11, Snow 23.
* The source dataset is imperfect: one photo appears under both Bird and Dust.

On those photos, no single model does much better than about 78%:

| model | accuracy |
|---|---|
| YOLO11n detector (the existing model), 94 test+val photos it did not train on | 77.7% |
| YOLO26s-cls embeddings + logistic regression, grouped 5-fold CV ×10 | 77.3% ± 1.6 |
| YOLO26s-cls fine-tuned, 60 epochs, same folds (last epoch) | ≈71% |
| both combined, one answer for every photo | 80.1% |

A model that is right four times out of five cannot be made "almost 100%" by
tuning it on 142 photos. What can be done is to answer only when the answer is
reliable, and to say so in every other case.

## The pipeline (`src/fault_detection/diagnosis.py`)

1. **Quality gate.** The photo is measured at ≤512 px: sharpness (variance of the
   Laplacian) < 30 → `blurry`; mean brightness < 20 → `too_dark`; more than 35%
   of pixels ≥ 250 → `overexposed`; shorter side < 64 px → `too_small`. Status
   `retake`, with the reasons.
2. **One YOLO26s-cls forward pass** gives a 512-d embedding. The backbone is
   `yolo_fault_detection/classifier/yolo26s-cls.pt`, ImageNet weights from
   Ultralytics, vendored so the embedding cannot change under the heads. Its
   sha256 is checked at load.
3. **Panel gate.** Logistic regression on the embedding: is this a solar panel?
   p < 0.5 → `not_panel`.
4. **Fault classifier.** Logistic regression on the same embedding, six classes.
5. **The YOLO11n detector.** Its best box confidence per class.
6. **Decision.**
   * `confirmed`: both models name the same class, the classifier with p ≥ 0.8
     and the detector with a box ≥ 0.6.
   * `likely`: they agree, but less confidently.
   * `uncertain`: they disagree. The app shows no verdict, only what each model
     said, and asks for a retake or a manual check.

The two heads are plain numbers in `yolo_fault_detection/classifier/fault_head.json`.
They add about 0.1 s per photo on a CPU.

## Measured (in `fault_head.json` → `metrics`, served at `GET /detect/model`)

The status rates below come from the 94 test+val photos the detector did not
train on. The classifier's numbers are out-of-fold, over 10 shuffles.

| status | share of photos | accuracy |
|---|---|---|
| confirmed | 49% | **98.5%** |
| likely | 21.5% | 79.7% |
| uncertain | 29.4% | 49.6% (so no verdict is shown) |

| gate | result |
|---|---|
| panel gate: real panels rejected (CV) | 0.7% (1.2% over flipped, rotated, cropped and re-lit copies) |
| panel gate: non-panels accepted (CV; ImageNet, COCO, noise) | 0.12% |
| panel gate: non-panels accepted, 3 325 unseen ImageNet photos | 0.09% |
| quality gate: real photos sent back | 0 of 142 |
| quality gate: blurred / dark / overexposed copies caught | 100% / 100% / 93% |

About 1 answer in 70 marked "confirmed" is still wrong. That error rate is
measured on only ~46 confirmed photos per run.

## Limits, and how to get closer to 100%

* The test set is 94 photos. The numbers above are estimates; ±3–5 points is a
  fair reading.
* The photos are the dataset's (web and drone images), not the user's station.
  Phone photos of a different panel type can be rejected by the panel gate, or
  land more often in "uncertain".
* **More real, correctly labelled photos is what would move the accuracy.**
  The Kaggle source dataset, or better, labelled photos of the user's own
  panels, can be retrained with
  `python scripts/fault_detection/train_head.py` (about 10 minutes on 4 CPUs).
  It re-measures everything and rewrites `fault_head.json`.

## Reproduce

```bash
python scripts/fault_detection/real_crops.py --out /tmp/real_crops   # the 142 photos + groups
python scripts/fault_detection/train_head.py --work /tmp/fh          # metrics + fault_head.json
python -m unittest discover -s tests -p "test_*fault*.py"
```

`train_head.py` downloads Imagenette-160 and COCO128 from the Ultralytics GitHub
releases as "not a panel" examples.
