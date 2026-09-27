"""
Recover the real labelled panel photos from the author's YOLO mosaics.

data/solar-panel-images/Faulty_solar_panel/ holds 300 files of random noise
(placeholders), so no accuracy measured on it means anything. The only real
photos in the repository are the 4x4 mosaics YOLO wrote while training
(yolo_fault_detection/runs/runs/detect/{train,val}/*_batch*.jpg). Each tile
shows one photo with its file name printed on it; LABELS below is the class
read from those names, row by row.

Splits follow the author's: "test" tiles come from the run on the test split
(detect/val/), "val" tiles from the validation plots of the training run and
"train" tiles from its training mosaics. Near-duplicate photos (the source
dataset has copies, some under two labels) share a "group" so that
cross-validation never puts copies on both sides.

    python scripts/fault_detection/real_crops.py --out /tmp/real_crops
"""

from __future__ import annotations

import argparse
import collections
import itertools
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "yolo_fault_detection" / "runs" / "runs" / "detect"

_L = {
    ("test", "val_batch0_labels"): "Snow Physical Clean Clean / Bird Physical Dust Dust / "
    "Electrical Physical Dust Clean / Electrical Snow Clean Dust",
    ("test", "val_batch1_labels"): "Bird Snow Snow Bird / Physical Dust Clean Clean / "
    "Dust Dust Physical Electrical / Snow Dust Dust Dust",
    ("test", "val_batch2_labels"): "Snow Dust Dust Dust / Clean Snow Bird Bird / "
    "Snow Clean Dust Bird / Clean Clean Dust Bird",
    ("val", "val_batch0_labels"): "Electrical Snow Snow Snow / Electrical Electrical Bird Bird / "
    "Electrical Electrical Snow Snow / Clean Dust Physical Electrical",
    ("val", "val_batch1_labels"): "Clean Bird Clean Electrical / Bird Bird Dust Snow / "
    "Clean Dust Dust Snow / Clean Clean Snow Dust",
    ("val", "val_batch2_labels"): "Physical Bird Bird Dust / Clean Clean Dust Bird / "
    "Dust Dust Clean Bird / Clean Bird Dust Dust",
    ("train", "train_batch3960"): "Dust Clean Dust Clean / Bird Bird Bird Dust / "
    "Snow Bird Clean Snow / Snow Dust Electrical Electrical",
    ("train", "train_batch3961"): "Snow Electrical Bird Dust / Bird Dust Snow Bird / "
    "Bird Snow Clean Dust / Electrical Clean Bird Physical",
    ("train", "train_batch3962"): "Clean Snow Dust Snow / Dust Dust Dust Bird / "
    "Bird Bird Bird Clean / Physical Physical Physical Bird",
}
LABELS = {k: [row.split() for row in v.split(" / ")] for k, v in _L.items()}


def mosaic_path(split: str, stem: str) -> Path:
    return RUNS / ("val" if split == "test" else "train") / f"{stem}.jpg"


def crop_tile(tile: np.ndarray) -> np.ndarray | None:
    """The photo inside one mosaic tile, without the grey frame and the printed name."""
    q = (tile // 4).reshape(-1, 3)
    vals, counts = np.unique(q, axis=0, return_counts=True)
    bg = vals[counts.argmax()] * 4 + 2
    is_grey = (
        abs(int(bg[0]) - int(bg[1])) < 6
        and abs(int(bg[1]) - int(bg[2])) < 6
        and counts.max() > 0.08 * len(q)
    )
    if is_grey:
        content = np.abs(tile - bg).max(axis=2) > 14
        rf, cf = content.mean(axis=1), content.mean(axis=0)
        yy = np.where(rf > 0.5 * rf.max())[0]
        xx = np.where(cf > 0.5 * cf.max())[0]
    else:  # the photo fills the tile
        yy = np.arange(tile.shape[0])
        xx = np.arange(tile.shape[1])
    if len(yy) < 60 or len(xx) < 60:
        return None
    y0, y1, x0, x1 = yy[0], yy[-1], xx[0], xx[-1]
    # the file name is printed across the top of the photo, the next row's below it
    crop = tile[y0 + 48 : y1 - 32, x0 + 12 : x1 - 12]
    if crop.shape[0] < 60 or crop.shape[1] < 60:
        return None
    return crop


def dhash(path: Path, n: int = 16) -> int:
    im = Image.open(path).convert("L").resize((n + 1, n), Image.LANCZOS)
    a = np.asarray(im, dtype=np.int32)
    bits = (a[:, :-1] > a[:, 1:]).ravel()
    return sum(1 << i for i, b in enumerate(bits) if b)


def extract(out: Path) -> list[dict]:
    meta: list[dict] = []
    for (split, stem), labels in LABELS.items():
        mos = np.asarray(Image.open(mosaic_path(split, stem)).convert("RGB")).astype(int)
        th, tw = mos.shape[0] // 4, mos.shape[1] // 4
        for r, c in itertools.product(range(4), range(4)):
            tile = mos[r * th + 2 : (r + 1) * th - 2, c * tw + 2 : (c + 1) * tw - 2]
            crop = crop_tile(tile)
            if crop is None:
                continue
            label = labels[r][c]
            p = out / split / label / f"{stem}_{r}{c}.jpg"
            p.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(crop.astype(np.uint8)).save(p, quality=95)
            meta.append({"split": split, "label": label, "file": str(p)})

    # near-duplicates share a group (union-find on a 16x16 difference hash)
    hashes = [dhash(Path(m["file"])) for m in meta]
    parent = list(range(len(meta)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in itertools.combinations(range(len(meta)), 2):
        if bin(hashes[i] ^ hashes[j]).count("1") <= 40:
            parent[find(i)] = find(j)
    for i, m in enumerate(meta):
        m["group"] = find(i)
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "solar-panel-images" / "real_crops")
    args = ap.parse_args()
    meta = extract(args.out)
    print(f"{len(meta)} photos in {args.out}")
    print(sorted(collections.Counter((m["split"], m["label"]) for m in meta).items()))
    by_group = collections.defaultdict(set)
    for m in meta:
        by_group[m["group"]].add(m["label"])
    print(
        f"{len(by_group)} distinct photos;",
        "label conflicts:",
        [sorted(v) for v in by_group.values() if len(v) > 1],
    )


if __name__ == "__main__":
    main()
