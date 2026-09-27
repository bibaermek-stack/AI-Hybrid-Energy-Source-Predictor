# solar-panel-images

`Faulty_solar_panel/` holds 300 files of **random noise** (244×244), 50 per
class. They are placeholders for the Kaggle dataset, not photos, so an accuracy
measured on them means nothing. The fault diagnosis uses them only as
"not a panel" examples.

The real labelled photos in this repository are cut out of the YOLO mosaics by
`scripts/fault_detection/real_crops.py`; see `docs/FAULT_DIAGNOSIS.md`.
