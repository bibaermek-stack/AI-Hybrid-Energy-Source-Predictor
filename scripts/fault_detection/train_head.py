"""
Fit and measure the fault classifier and the "is it a panel" gate.

Writes yolo_fault_detection/classifier/fault_head.json, which
src/fault_detection/diagnosis.py loads. Every number the API and the app
quote about accuracy comes from the "metrics" block this script measures:

* real photos only: the 142 labelled photos in the author's mosaics
  (real_crops.py), 137 distinct; the Faulty_solar_panel folder is noise;
* grouped, stratified 5-fold cross-validation repeated over 10 shuffles,
  copies of a photo never on both sides;
* the confirmed / likely / uncertain rates on the 94 test+val photos only,
  the ones the YOLO11n detector did not train on;
* the panel gate against ImageNet (Imagenette) and COCO photos plus the
  noise placeholders, and against ~3 300 more Imagenette photos it never saw.

    python scripts/fault_detection/train_head.py            # ~10 min on 4 CPUs
    python scripts/fault_detection/train_head.py --work /tmp/fh --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from real_crops import extract  # noqa: E402

from src.fault_detection import diagnosis as dg  # noqa: E402
from src.fault_detection.yolo.detector import YOLOFaultDetector  # noqa: E402

ASSETS = "https://github.com/ultralytics/assets/releases/download/v0.0.0/"
BACKBONE = "yolo26s-cls.pt"
IMGSZ = 224
C_CLASSIFIER = 0.1  # picked among 0.02-0.3 by the same cross-validation
C_PANEL = 0.1
SEEDS = 10
N_NEG_TRAIN = 600  # Imagenette photos the gate trains on; the rest only test it


def views(img: np.ndarray, rng: np.random.Generator) -> list[np.ndarray]:
    """Original, flips, a quarter turn, two crops, darker, brighter."""
    h, w = img.shape[:2]
    out = [img, img[:, ::-1], img[::-1], np.rot90(img)]
    for s in (0.75, 0.85):
        ch, cw = int(h * s), int(w * s)
        y0, x0 = rng.integers(0, h - ch + 1), rng.integers(0, w - cw + 1)
        out.append(img[y0 : y0 + ch, x0 : x0 + cw])
    out.append(np.clip(img.astype(float) * 0.7 + 10, 0, 255).astype(np.uint8))
    out.append(np.clip(img.astype(float) * 1.25, 0, 255).astype(np.uint8))
    return [np.ascontiguousarray(v) for v in out]


def fetch_negatives(neg: Path) -> None:
    neg.mkdir(parents=True, exist_ok=True)
    for name in ("coco128", "imagenette160"):
        if (neg / name).exists():
            continue
        z = neg / f"{name}.zip"
        print(f"downloading {name} ...", flush=True)
        urllib.request.urlretrieve(ASSETS + f"{name}.zip", z)
        with zipfile.ZipFile(z) as f:
            f.extractall(neg)


def pipeline(C: float, balanced: bool = False):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=5000, C=C, class_weight="balanced" if balanced else None),
    )


def head_spec(clf, classes=None) -> dict:
    sc, lr = clf[0], clf[1]
    r = lambda a: [float(f"{v:.7g}") for v in np.ravel(a)]  # noqa: E731
    spec = {
        "mean": r(sc.mean_),
        "scale": r(sc.scale_),
        "coef": [r(row) for row in lr.coef_],
        "intercept": r(lr.intercept_),
    }
    if classes:
        spec["classes"] = list(classes)
    return spec


def main() -> None:
    import cv2
    from sklearn.model_selection import StratifiedGroupKFold
    from ultralytics import YOLO
    from ultralytics.utils.downloads import attempt_download_asset

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--work", type=Path, default=Path("/tmp/fault_head_work"))
    ap.add_argument("--out", type=Path, default=dg.HEAD_PATH)
    ap.add_argument("--dry-run", action="store_true", help="measure, do not write the head")
    args = ap.parse_args()
    work: Path = args.work
    backbone_path = dg.CLASSIFIER_DIR / BACKBONE
    if not backbone_path.exists():
        backbone_path.parent.mkdir(parents=True, exist_ok=True)
        attempt_download_asset(str(backbone_path))
    backbone = YOLO(str(backbone_path))
    embed = lambda imgs: dg.embed_with(backbone, imgs, IMGSZ)  # noqa: E731

    # ---- labelled photos --------------------------------------------------
    meta = extract(work / "real_crops")
    CLS = list(dg.CLASSES)
    y = np.array([CLS.index(m["label"]) for m in meta])
    g = np.array([m["group"] for m in meta])
    held = np.array([m["split"] in ("test", "val") for m in meta])
    imgs = [cv2.imread(m["file"]) for m in meta]
    rng = np.random.default_rng(0)
    V = [views(im, rng) for im in imgs]
    n_views = len(V[0])
    E = embed([v for vs in V for v in vs]).reshape(len(meta), n_views, -1)
    dim = E.shape[-1]
    print(f"{len(meta)} photos, {len(set(g))} distinct, embedding {dim}", flush=True)

    # ---- classifier: out-of-fold probabilities ----------------------------
    fit_views = [0, 1]  # original + mirror; more views did not help
    P = np.zeros((SEEDS, len(y), len(CLS)))
    for s in range(SEEDS):
        for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=s).split(E[:, 0], y, g):
            clf = pipeline(C_CLASSIFIER).fit(
                E[tr][:, fit_views].reshape(-1, dim), np.repeat(y[tr], len(fit_views))
            )
            P[s, te] = clf.predict_proba(E[te][:, 0])
    acc_clf = [(P[s].argmax(1) == y).mean() for s in range(SEEDS)]

    # ---- the detector on photos it did not train on -----------------------
    det = YOLOFaultDetector()
    D = np.zeros((len(y), len(CLS)))
    for i in np.where(held)[0]:
        D[i] = dg.detector_scores(det.predict(imgs[i], conf=0.05))
    acc_det = float((D[held].argmax(1) == y[held]).mean())

    cfg = dict(dg.DEFAULT_DECISION)
    tiers = {t: {"n": 0, "right": 0} for t in ("confirmed", "likely", "uncertain")}
    fused_right = 0
    for s in range(SEEDS):
        for i in np.where(held)[0]:
            d = dg.decide(P[s, i], D[i], None, [], cfg)
            tiers[d["status"]]["n"] += 1
            tiers[d["status"]]["right"] += d["label"] == CLS[y[i]]
            fused_right += d["label"] == CLS[y[i]]
    n_held = int(held.sum())
    tier_metrics = {
        t: {
            "coverage": round(v["n"] / (SEEDS * n_held), 3),
            "accuracy": round(v["right"] / v["n"], 3) if v["n"] else None,
        }
        for t, v in tiers.items()
    }

    # ---- panel gate ---------------------------------------------------------
    neg_dir = work / "neg"
    fetch_negatives(neg_dir)
    inet = sorted((neg_dir / "imagenette160" / "val").rglob("*.JPEG"))
    np.random.default_rng(0).shuffle(inet)
    coco = sorted((neg_dir / "coco128").rglob("*.jpg"))
    noise = sorted((ROOT / "data" / "solar-panel-images" / "Faulty_solar_panel").rglob("*.jpg"))[
        :100
    ]
    neg_train = inet[:N_NEG_TRAIN] + coco + noise
    neg_test = inet[N_NEG_TRAIN:]
    read = lambda paths: [cv2.imread(str(p)) for p in paths]  # noqa: E731
    N = embed(read(neg_train))
    N_test = np.vstack([embed(read(neg_test[i : i + 256])) for i in range(0, len(neg_test), 256)])
    nfold = np.random.default_rng(0).integers(0, 5, len(N))
    rej = np.zeros(n_views)
    acc_neg = 0
    for k, (tr, te) in enumerate(
        StratifiedGroupKFold(5, shuffle=True, random_state=0).split(E[:, 0], y, g)
    ):
        Xp = E[tr].reshape(-1, dim)
        Xn = N[nfold != k]
        gate = pipeline(C_PANEL, balanced=True).fit(
            np.vstack([Xp, Xn]), np.r_[np.ones(len(Xp)), np.zeros(len(Xn))]
        )
        for v in range(n_views):
            rej[v] += (gate.predict_proba(E[te][:, v])[:, 1] < cfg["panel_min"]).sum()
        acc_neg += (gate.predict_proba(N[nfold == k])[:, 1] >= cfg["panel_min"]).sum()
    gate = pipeline(C_PANEL, balanced=True).fit(
        np.vstack([E.reshape(-1, dim), N]), np.r_[np.ones(len(y) * n_views), np.zeros(len(N))]
    )
    unseen_accept = float((gate.predict_proba(N_test)[:, 1] >= cfg["panel_min"]).mean())

    # ---- quality gate on the real photos and on spoiled copies -------------
    q = [dg.quality_metrics(im) for im in imgs]
    flagged = sum(bool(dg.quality_issues(m)) for m in q)
    spoil = {
        "blurred": lambda im: cv2.GaussianBlur(im, (0, 0), 4),
        "dark": lambda im: (im.astype(float) * 0.06).astype(np.uint8),
        "overexposed": lambda im: np.clip(im.astype(float) * 3 + 80, 0, 255).astype(np.uint8),
    }
    caught = {
        k: round(
            sum(bool(dg.quality_issues(dg.quality_metrics(f(im)))) for im in imgs) / len(imgs), 3
        )
        for k, f in spoil.items()
    }

    # ---- final classifier ---------------------------------------------------
    clf = pipeline(C_CLASSIFIER).fit(E[:, fit_views].reshape(-1, dim), np.repeat(y, len(fit_views)))

    import sklearn
    import ultralytics

    counts = {c: int((y == i).sum()) for i, c in enumerate(CLS)}
    metrics = {
        "data": {
            "photos": len(y),
            "distinct_photos": len(set(g)),
            "per_class": counts,
            "held_out_for_tiers": n_held,
            "label_conflicts": "one photo appears as both Bird and Dust",
        },
        "accuracy": {
            "detector_alone_heldout": round(acc_det, 3),
            "classifier_alone_cv": round(float(np.mean(acc_clf)), 3),
            "classifier_alone_cv_std": round(float(np.std(acc_clf)), 3),
            "both_models_heldout": round(fused_right / (SEEDS * n_held), 3),
        },
        "tiers_heldout": tier_metrics,
        "expected_accuracy": {t: v["accuracy"] for t, v in tier_metrics.items()},
        "panel_gate": {
            "panels_rejected_cv": round(float(rej[0] / len(y)), 4),
            "panels_rejected_cv_all_views": round(float(rej.sum() / (len(y) * n_views)), 4),
            "non_panels_accepted_cv": round(float(acc_neg / len(N)), 4),
            "non_panels_accepted_unseen": round(unseen_accept, 4),
            "unseen_negatives": len(N_test),
        },
        "quality_gate": {"real_photos_flagged": flagged, "spoiled_copies_caught": caught},
    }
    print(json.dumps(metrics, indent=1))

    spec = {
        "version": 1,
        "created": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "software": {"ultralytics": ultralytics.__version__, "scikit-learn": sklearn.__version__},
        "backbone": {
            "file": BACKBONE,
            "sha256": dg.sha256_file(backbone_path),
            "imgsz": IMGSZ,
            "dim": int(dim),
            "source": "Ultralytics YOLO26s-cls (ImageNet), github.com/ultralytics/assets releases",
        },
        "classifier": head_spec(clf, CLS),
        "panel": head_spec(gate),
        "quality": dict(dg.DEFAULT_QUALITY),
        "decision": cfg,
        "metrics": metrics,
    }

    # the numpy heads must give what scikit-learn gives
    x = E[:, 0]
    assert np.abs(dg.LinearHead(spec["classifier"]).proba(x) - clf.predict_proba(x)).max() < 1e-4
    assert np.abs(dg.LinearHead(spec["panel"]).proba(x) - gate.predict_proba(x)[:, 1]).max() < 1e-4
    if args.dry_run:
        return
    args.out.write_text(json.dumps(spec, separators=(",", ":")) + "\n")
    print(f"wrote {args.out} ({args.out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
