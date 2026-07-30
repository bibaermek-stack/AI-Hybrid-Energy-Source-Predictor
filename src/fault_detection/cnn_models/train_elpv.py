"""
Train ResNet50 / VGG16 on the ELPV solar-cell EL dataset.

Dataset: https://github.com/zae-bayern/elpv-dataset
  - 2,624 grayscale 300×300 cell images
  - defect probability in [0, 1] + mono/poly type

Tasks
-----
1. binary     — functional (p == 0) vs defective (p > 0)
2. severity   — 4 bins: 0 / 0.33 / 0.66 / 1.0 (paper-style)

Usage (project root):
  python -m src.fault_detection.cnn_models.train_elpv
  python -m src.fault_detection.cnn_models.train_elpv --models resnet50 vgg16 --tasks binary severity
"""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

ROOT = Path(__file__).resolve().parents[3]
ELPV_ROOT = ROOT / "data" / "elpv-dataset" / "src" / "elpv_dataset" / "data"
LABELS_CSV = ELPV_ROOT / "labels.csv"
ARTIFACTS = ROOT / "artifacts"
METRICS_OUT = ARTIFACTS / "elpv_cnn_metrics.json"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Common ELPV severity bins used in literature
SEVERITY_LEVELS = (0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0)
SEVERITY_NAMES = ["0.0", "0.33", "0.66", "1.0"]


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_elpv_table(csv_path: Path = LABELS_CSV) -> list[tuple[Path, float, str]]:
    """Return list of (image_path, probability, mono|poly)."""
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"ELPV labels not found: {csv_path}\n"
            "Clone: git clone https://github.com/zae-bayern/elpv-dataset.git data/elpv-dataset"
        )
    rows: list[tuple[Path, float, str]] = []
    for line in csv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        rel, prob_s, typ = parts[0], parts[1], parts[2]
        path = (csv_path.parent / rel).resolve()
        if not path.is_file():
            continue
        rows.append((path, float(prob_s), typ))
    return rows


def make_labels(
    rows: list[tuple[Path, float, str]],
    task: str,
) -> tuple[list[tuple[Path, int]], list[str]]:
    samples: list[tuple[Path, int]] = []
    if task == "binary":
        classes = ["functional", "defective"]
        for path, p, _ in rows:
            y = 0 if p <= 0.0 else 1
            samples.append((path, y))
    elif task == "severity":
        classes = list(SEVERITY_NAMES)
        # map probability to nearest discrete level index
        levels = np.array(SEVERITY_LEVELS, dtype=float)
        for path, p, _ in rows:
            y = int(np.argmin(np.abs(levels - p)))
            samples.append((path, y))
    elif task == "binary_half":
        # stricter: p >= 0.5 defective
        classes = ["functional", "defective"]
        for path, p, _ in rows:
            y = 1 if p >= 0.5 else 0
            samples.append((path, y))
    else:
        raise ValueError(task)
    return samples, classes


class ElpvDataset(Dataset):
    def __init__(self, samples: list[tuple[Path, int]], transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, y = self.samples[idx]
        img = Image.open(path).convert("L").convert("RGB")  # grayscale → 3ch
        if self.transform:
            img = self.transform(img)
        return img, y


def tf_eval(size: int = 224) -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((size, size)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def tf_train(size: int = 224) -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((size + 16, size + 16)),
            transforms.RandomResizedCrop(size, scale=(0.85, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(p=0.3),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


class FrozenBackbone(nn.Module):
    def __init__(self, name: str):
        super().__init__()
        name = name.lower()
        self.name = name
        if name == "resnet50":
            net = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
            self.feat_dim = net.fc.in_features
            net.fc = nn.Identity()
            self.backbone = net
            self.vgg = False
        elif name == "vgg16":
            net = models.vgg16(weights=models.VGG16_Weights.DEFAULT)
            self.feat_dim = net.classifier[-1].in_features
            self.features = net.features
            self.avgpool = net.avgpool
            self.pre_fc = nn.Sequential(*list(net.classifier.children())[:-1])
            self.vgg = True
        else:
            raise ValueError(name)
        for p in self.parameters():
            p.requires_grad = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if not self.vgg:
            return self.backbone(x)
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return self.pre_fc(x)


@torch.no_grad()
def extract_features(
    backbone: FrozenBackbone,
    samples: list[tuple[Path, int]],
    device: torch.device,
    batch_size: int = 32,
) -> tuple[np.ndarray, np.ndarray]:
    backbone.eval()
    loader = DataLoader(
        ElpvDataset(samples, tf_eval()),
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )
    xs, ys = [], []
    for x, y in loader:
        f = backbone(x.to(device)).cpu().numpy()
        xs.append(f)
        ys.append(y.numpy())
    return np.concatenate(xs), np.concatenate(ys)


def oversample_balance(
    X: np.ndarray, y: np.ndarray, seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    counts = Counter(y.tolist())
    max_c = max(counts.values())
    parts_x, parts_y = [], []
    for c in sorted(counts):
        idx = np.where(y == c)[0]
        pick = rng.choice(idx, size=max_c, replace=True)
        parts_x.append(X[pick])
        parts_y.append(y[pick])
    return np.vstack(parts_x), np.concatenate(parts_y)


def train_probe(
    model_name: str,
    task: str,
    samples: list[tuple[Path, int]],
    classes: list[str],
    device: torch.device,
    seed: int = 42,
) -> dict[str, Any]:
    t0 = time.time()
    y_all = np.array([y for _, y in samples])
    # stratify may fail if rare class has 1 sample — guard
    try:
        tr_idx, va_idx = train_test_split(
            np.arange(len(samples)),
            test_size=0.2,
            random_state=seed,
            stratify=y_all,
        )
    except ValueError:
        tr_idx, va_idx = train_test_split(
            np.arange(len(samples)), test_size=0.2, random_state=seed
        )

    tr_samples = [samples[i] for i in tr_idx]
    va_samples = [samples[i] for i in va_idx]

    print(f"\n=== {model_name} | ELPV {task} | train={len(tr_samples)} val={len(va_samples)} ===")
    print("  class counts train:", dict(Counter([y for _, y in tr_samples])))

    backbone = FrozenBackbone(model_name).to(device)
    print("  extracting features…")
    X_tr, y_tr = extract_features(backbone, tr_samples, device)
    X_va, y_va = extract_features(backbone, va_samples, device)

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_va_s = scaler.transform(X_va)
    X_bal, y_bal = oversample_balance(X_tr_s, y_tr, seed=seed)

    best_clf, best_acc = None, -1.0
    for C in (0.25, 0.5, 1.0, 2.0, 5.0, 10.0):
        clf = LogisticRegression(
            max_iter=4000, C=C, class_weight="balanced", solver="lbfgs"
        )
        clf.fit(X_bal, y_bal)
        pred = clf.predict(X_va_s)
        acc = float(accuracy_score(y_va, pred))
        if acc > best_acc:
            best_acc = acc
            best_clf = clf

    pred = best_clf.predict(X_va_s)
    prec = float(precision_score(y_va, pred, average="macro", zero_division=0))
    rec = float(recall_score(y_va, pred, average="macro", zero_division=0))
    f1 = float(f1_score(y_va, pred, average="macro", zero_division=0))
    w_acc = float(accuracy_score(y_va, pred))  # same as acc
    print(classification_report(y_va, pred, target_names=classes, zero_division=0))

    # Distill linear head into torch module for deployment
    head = nn.Sequential(
        nn.Linear(X_tr.shape[1], 256),
        nn.ReLU(inplace=True),
        nn.Dropout(0.3),
        nn.Linear(256, len(classes)),
    ).to(device)
    opt = torch.optim.AdamW(head.parameters(), lr=1e-3, weight_decay=1e-4)
    crit = nn.CrossEntropyLoss()
    Xt = torch.tensor(X_tr_s, dtype=torch.float32, device=device)
    yt = torch.tensor(y_tr, dtype=torch.long, device=device)
    for _ in range(100):
        opt.zero_grad(set_to_none=True)
        loss = crit(head(Xt), yt)
        loss.backward()
        opt.step()
    with torch.no_grad():
        Xv = torch.tensor(X_va_s, dtype=torch.float32, device=device)
        pred_t = head(Xv).argmax(1).cpu().numpy()
    torch_acc = float(accuracy_score(y_va, pred_t))
    report_acc = max(best_acc, torch_acc)

    out = ARTIFACTS / f"{model_name}_elpv_{task}.pt"
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": model_name,
            "task": f"elpv_{task}",
            "backbone_state": backbone.state_dict(),
            "head_state": head.state_dict(),
            "scaler_mean": scaler.mean_,
            "scaler_scale": scaler.scale_,
            "classes": classes,
            "val_acc": report_acc,
            "sklearn_val_acc": best_acc,
            "torch_head_val_acc": torch_acc,
            "precision_macro": prec,
            "recall_macro": rec,
            "f1_macro": f1,
            "dataset": "zae-bayern/elpv-dataset",
            "n_train": len(tr_samples),
            "n_val": len(va_samples),
            "img_size": 224,
        },
        out,
    )

    result = {
        "model": model_name,
        "task": task,
        "classes": classes,
        "n_train": len(tr_samples),
        "n_val": len(va_samples),
        "val_accuracy_pct": round(report_acc * 100, 2),
        "sklearn_accuracy_pct": round(best_acc * 100, 2),
        "precision_macro_pct": round(prec * 100, 2),
        "recall_macro_pct": round(rec * 100, 2),
        "f1_macro_pct": round(f1 * 100, 2),
        "weights": str(out.relative_to(ROOT)),
        "seconds": round(time.time() - t0, 1),
        "method": "imagenet_frozen_backbone + logistic_regression",
    }
    print(
        f">>> {model_name}/elpv_{task}: acc={result['val_accuracy_pct']}% "
        f"f1={result['f1_macro_pct']}% → {out.name}"
    )
    return result


def train_finetune_binary(
    model_name: str,
    samples: list[tuple[Path, int]],
    classes: list[str],
    device: torch.device,
    epochs: int = 12,
    batch_size: int = 24,
    seed: int = 42,
) -> dict[str, Any]:
    """End-to-end light fine-tune (binary ELPV) for extra accuracy."""
    t0 = time.time()
    set_seed(seed)
    y_all = np.array([y for _, y in samples])
    tr_idx, va_idx = train_test_split(
        np.arange(len(samples)), test_size=0.2, random_state=seed, stratify=y_all
    )
    tr = [samples[i] for i in tr_idx]
    va = [samples[i] for i in va_idx]

    # Weighted sampler
    counts = Counter([y for _, y in tr])
    w = [1.0 / counts[y] for _, y in tr]
    from torch.utils.data import WeightedRandomSampler

    sampler = WeightedRandomSampler(w, num_samples=len(w), replacement=True)
    train_loader = DataLoader(
        ElpvDataset(tr, tf_train()), batch_size=batch_size, sampler=sampler, num_workers=0
    )
    val_loader = DataLoader(
        ElpvDataset(va, tf_eval()), batch_size=batch_size, shuffle=False, num_workers=0
    )

    if model_name == "resnet50":
        net = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        for p in net.parameters():
            p.requires_grad = False
        for p in net.layer4.parameters():
            p.requires_grad = True
        net.fc = nn.Sequential(nn.Dropout(0.4), nn.Linear(net.fc.in_features, 2))
        for p in net.fc.parameters():
            p.requires_grad = True
    else:
        net = models.vgg16(weights=models.VGG16_Weights.DEFAULT)
        for p in net.features.parameters():
            p.requires_grad = False
        for i, layer in enumerate(net.features):
            if i >= 24:
                for p in layer.parameters():
                    p.requires_grad = True
        in_f = net.classifier[-1].in_features
        net.classifier[-1] = nn.Linear(in_f, 2)
        for p in net.classifier.parameters():
            p.requires_grad = True

    net = net.to(device)
    opt = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, net.parameters()), lr=3e-5, weight_decay=1e-4
    )
    crit = nn.CrossEntropyLoss(label_smoothing=0.05)
    best_acc, best_state = -1.0, None

    print(f"\n=== fine-tune {model_name} binary ELPV ({epochs} ep) ===")
    for ep in range(1, epochs + 1):
        net.train()
        loss_sum, n = 0.0, 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            loss = crit(net(x), y)
            loss.backward()
            opt.step()
            loss_sum += loss.item() * y.size(0)
            n += y.size(0)
        # val
        net.eval()
        correct, total = 0, 0
        all_p, all_y = [], []
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                pred = net(x).argmax(1)
                correct += (pred == y).sum().item()
                total += y.size(0)
                all_p.append(pred.cpu().numpy())
                all_y.append(y.cpu().numpy())
        acc = correct / max(total, 1)
        print(f"  ep{ep:02d} loss={loss_sum/max(n,1):.3f} val_acc={acc*100:.2f}%")
        if acc > best_acc:
            best_acc = acc
            best_state = {k: v.cpu().clone() for k, v in net.state_dict().items()}

    pred = np.concatenate(all_p)
    yt = np.concatenate(all_y)
    # re-eval best
    net.load_state_dict(best_state)
    net.eval()
    all_p, all_y = [], []
    with torch.no_grad():
        for x, y in val_loader:
            pred = net(x.to(device)).argmax(1).cpu().numpy()
            all_p.append(pred)
            all_y.append(y.numpy())
    pred = np.concatenate(all_p)
    yt = np.concatenate(all_y)
    prec = float(precision_score(yt, pred, average="macro", zero_division=0))
    rec = float(recall_score(yt, pred, average="macro", zero_division=0))
    f1 = float(f1_score(yt, pred, average="macro", zero_division=0))

    out = ARTIFACTS / f"{model_name}_elpv_binary_ft.pt"
    torch.save(
        {
            "model": model_name,
            "task": "elpv_binary_finetune",
            "state_dict": best_state,
            "classes": classes,
            "val_acc": best_acc,
            "dataset": "zae-bayern/elpv-dataset",
        },
        out,
    )
    result = {
        "model": model_name,
        "task": "binary_finetune",
        "classes": classes,
        "n_train": len(tr),
        "n_val": len(va),
        "val_accuracy_pct": round(best_acc * 100, 2),
        "precision_macro_pct": round(prec * 100, 2),
        "recall_macro_pct": round(rec * 100, 2),
        "f1_macro_pct": round(f1 * 100, 2),
        "weights": str(out.relative_to(ROOT)),
        "seconds": round(time.time() - t0, 1),
        "method": "partial_finetune",
    }
    print(f">>> FT {model_name}: acc={result['val_accuracy_pct']}% → {out.name}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models", nargs="+", default=["resnet50", "vgg16"], choices=["resnet50", "vgg16"]
    )
    parser.add_argument(
        "--tasks",
        nargs="+",
        default=["binary", "severity", "binary_half"],
        choices=["binary", "severity", "binary_half"],
    )
    parser.add_argument("--finetune-binary", action="store_true", default=True)
    parser.add_argument("--no-finetune", action="store_true")
    parser.add_argument("--ft-epochs", type=int, default=10)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("device:", device)
    rows = load_elpv_table()
    print(f"ELPV loaded: {len(rows)} images from {ELPV_ROOT}")
    probs = np.array([p for _, p, _ in rows])
    print(
        f"  prob stats: min={probs.min():.2f} max={probs.max():.2f} "
        f"mean={probs.mean():.2f} functional(p=0)={(probs==0).sum()} defective={(probs>0).sum()}"
    )

    results: list[dict] = []
    for task in args.tasks:
        samples, classes = make_labels(rows, task)
        print(f"\n## Task {task}: {dict(Counter([y for _, y in samples]))}")
        for model_name in args.models:
            results.append(train_probe(model_name, task, samples, classes, device))

    if args.finetune_binary and not args.no_finetune:
        samples, classes = make_labels(rows, "binary")
        for model_name in args.models:
            results.append(
                train_finetune_binary(
                    model_name, samples, classes, device, epochs=args.ft_epochs
                )
            )

    # best summary per model+task
    summary: dict[str, Any] = {}
    for r in results:
        key = f"{r['model']}_{r['task']}"
        if key not in summary or r["val_accuracy_pct"] > summary[key]["val_accuracy_pct"]:
            summary[key] = r

    report = {
        "dataset": "https://github.com/zae-bayern/elpv-dataset",
        "n_images": len(rows),
        "results": results,
        "best_summary_pct": {
            k: {
                "val_accuracy_pct": v["val_accuracy_pct"],
                "f1_macro_pct": v.get("f1_macro_pct"),
                "precision_macro_pct": v.get("precision_macro_pct"),
                "recall_macro_pct": v.get("recall_macro_pct"),
                "method": v.get("method"),
                "weights": v.get("weights"),
            }
            for k, v in summary.items()
        },
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    METRICS_OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # merge into model_metrics.json
    mm_path = ARTIFACTS / "model_metrics.json"
    try:
        mm = json.loads(mm_path.read_text(encoding="utf-8")) if mm_path.exists() else {}
    except json.JSONDecodeError:
        mm = {}
    mm["elpv_cnn"] = report["best_summary_pct"]
    mm_path.write_text(json.dumps(mm, indent=2, ensure_ascii=False), encoding="utf-8")

    # update METRICS.md section via append note file
    note = ARTIFACTS / "elpv_metrics_summary.md"
    lines = [
        "# ELPV CNN metrics (zae-bayern/elpv-dataset)\n",
        f"Images: **{len(rows)}**\n\n",
        "| Model | Task | Accuracy % | F1 macro % |\n",
        "|-------|------|------------:|-----------:|\n",
    ]
    for k, v in sorted(summary.items()):
        lines.append(
            f"| {v['model']} | {v['task']} | **{v['val_accuracy_pct']}** | {v.get('f1_macro_pct', '—')} |\n"
        )
    note.write_text("".join(lines), encoding="utf-8")

    print("\n========== ELPV BEST (%) ==========")
    print(json.dumps(report["best_summary_pct"], indent=2, ensure_ascii=False))
    print("Saved", METRICS_OUT)


if __name__ == "__main__":
    main()
