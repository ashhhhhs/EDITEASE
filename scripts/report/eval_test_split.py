"""
Held-out test-set evaluation of the EditEase scene classifier v2.

Filters annotations.jsonl to the videos listed in splits.json["test"], runs
inference on the first available frame of each scene, and writes a fresh
eval_report_v2_test.json under artifacts/.

Run with:
    /mnt/d/EDITEASE/venv/bin/python scripts/report/eval_test_split.py
"""

import json
import os
import sys
from collections import Counter

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

sys.path.insert(0, "/mnt/d/EDITEASE")
import config  # noqa: E402

BASE = str(config.BASE_DIR)
MODEL_PATH = os.path.join(BASE, "pipeline", "models", "scene_classifier_v2.pth")
MANIFEST_PATH = os.path.join(BASE, "datasets", "scene_type", "v2_full", "annotations.jsonl")
SPLITS_PATH = os.path.join(BASE, "datasets", "scene_type", "v2_full", "splits.json")
HISTORY_PATH = os.path.join(BASE, "datasets", "scene_type", "v2_full", "training_history.json")
OUT_PATH = os.path.join(BASE, "artifacts", "eval_report_v2_test.json")


def build_model(num_classes, device):
    backbone = models.resnet18(weights=None)
    in_features = backbone.fc.in_features
    backbone.fc = nn.Sequential(
        nn.Linear(in_features, 256),
        nn.LayerNorm(256),
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(256, num_classes),
    )
    return backbone.to(device)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    ckpt = torch.load(MODEL_PATH, map_location=device, weights_only=True)
    classes = ckpt["classes"]
    label_merge = ckpt.get("label_merge", {})
    num_classes = ckpt.get("num_classes", len(classes))
    print(f"Classes: {classes}")
    print(f"Checkpoint epoch={ckpt.get('epoch')}  val_acc={ckpt.get('val_acc')}  bal_acc={ckpt.get('bal_acc')}")

    model = build_model(num_classes, device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model loaded, {n_params:,} parameters")

    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    splits = json.load(open(SPLITS_PATH))
    test_videos = set(splits["test"])
    print(f"Test videos in split: {len(test_videos)}")

    scenes = []
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("video") not in test_videos:
                continue
            raw = rec.get("label", "")
            true_label = label_merge.get(raw, raw)
            frames = rec.get("frames") or []
            # Manifest stores Windows-style backslashes; normalise for Linux/WSL.
            abs_frames = []
            for fp in frames:
                fp_norm = fp.replace("\\", "/")
                abs_frames.append(fp_norm if os.path.isabs(fp_norm) else os.path.join(BASE, fp_norm))
            scenes.append({
                "key": rec.get("scene_key") or f"{rec.get('video')}::{rec.get('scene_id')}",
                "video": rec.get("video"),
                "true_label": true_label,
                "frames": abs_frames,
                "video_path": rec.get("video_path"),
                "t0": rec.get("t0"),
                "t1": rec.get("t1"),
            })

    print(f"Test scenes in manifest: {len(scenes)}")
    label_to_idx = {c: i for i, c in enumerate(classes)}
    idx_to_label = {i: c for c, i in label_to_idx.items()}

    def extract_midpoint_frame(video_path, t0, t1):
        """Open the source video and return the midpoint frame as a PIL Image, or None."""
        if not video_path:
            return None
        vp_norm = video_path.replace("\\", "/")
        full = vp_norm if os.path.isabs(vp_norm) else os.path.join(BASE, vp_norm)
        if not os.path.exists(full):
            return None
        try:
            cap = cv2.VideoCapture(full)
            if not cap.isOpened():
                return None
            mid_sec = (float(t0) + float(t1)) / 2.0 if (t0 is not None and t1 is not None) else 0.0
            cap.set(cv2.CAP_PROP_POS_MSEC, mid_sec * 1000)
            ok, bgr = cap.read()
            cap.release()
            if not ok or bgr is None:
                return None
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb)
        except Exception:
            return None

    y_true, y_pred, confs = [], [], []
    missing = unknown = errs = recovered = 0

    for s in scenes:
        if s["true_label"] not in label_to_idx:
            unknown += 1
            continue
        # First: try cached thumbnail frames.
        frame_path = next((fp for fp in s["frames"] if os.path.exists(fp)), None)
        img = None
        if frame_path:
            try:
                img = Image.open(frame_path).convert("RGB")
            except Exception as e:
                print(f"  thumb-load err {s['key']}: {e}")
                img = None
        # Fallback: extract midpoint frame from the source video.
        if img is None:
            img = extract_midpoint_frame(s["video_path"], s["t0"], s["t1"])
            if img is not None:
                recovered += 1
        if img is None:
            missing += 1
            continue
        try:
            x = tf(img.convert("RGB")).unsqueeze(0).to(device)
            with torch.no_grad():
                probs = torch.softmax(model(x), dim=1)
                conf, idx = torch.max(probs, 1)
            y_true.append(s["true_label"])
            y_pred.append(idx_to_label[int(idx.item())])
            confs.append(float(conf.item()))
        except Exception as e:
            errs += 1
            print(f"  ERR {s['key']}: {e}")

    print(f"\nEvaluated: {len(y_true)} | missing frames: {missing} | unknown labels: {unknown} | errors: {errs}")
    if not y_true:
        print("Nothing to evaluate.")
        return

    correct = sum(t == p for t, p in zip(y_true, y_pred))
    acc = correct / len(y_true)
    mean_conf = float(np.mean(confs))

    # Per-class metrics over fixed class order from checkpoint
    per_class = {}
    macro_p = macro_r = macro_f = 0.0
    wf = ws = n_seen = 0
    for cls in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
        support = sum(1 for t in y_true if t == cls)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per_class[cls] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": support,
        }
        if support:
            macro_p += prec
            macro_r += rec
            macro_f += f1
            n_seen += 1
            wf += f1 * support
            ws += support

    # Balanced accuracy = mean per-class recall over classes with support > 0
    bal_acc = (
        sum(per_class[c]["recall"] for c in classes if per_class[c]["support"] > 0)
        / n_seen
    ) if n_seen else 0.0

    cm = [
        [
            sum(1 for ti, pi in zip(y_true, y_pred) if ti == tc and pi == pc)
            for pc in classes
        ]
        for tc in classes
    ]

    # Pull training history straight from the file the trainer saved
    history = []
    if os.path.exists(HISTORY_PATH):
        history = json.load(open(HISTORY_PATH))

    label_counts = Counter(y_true)

    print(f"\n{'='*60}")
    print(f"Test-set accuracy:  {acc:.4f}  ({correct}/{len(y_true)})")
    print(f"Balanced accuracy:  {bal_acc:.4f}")
    print(f"Macro F1:           {macro_f/n_seen:.4f}")
    print(f"Weighted F1:        {wf/ws:.4f}")
    print(f"Mean confidence:    {mean_conf:.4f}")
    print(f"{'='*60}\n")
    for cls in classes:
        pc = per_class[cls]
        print(f"  {cls:22s} P={pc['precision']:.3f}  R={pc['recall']:.3f}  F1={pc['f1']:.3f}  n={pc['support']}")

    report = {
        "model_path": MODEL_PATH,
        "manifest_path": MANIFEST_PATH,
        "splits_path": SPLITS_PATH,
        "classes": classes,
        "label_merge": label_merge,
        "test_scenes": len(y_true),
        "test_videos": len(test_videos),
        "missing_frames": missing,
        "unknown_labels": unknown,
        "test_accuracy": round(acc, 4),
        "test_balanced_accuracy": round(bal_acc, 4),
        "test_macro_f1": round(macro_f / n_seen, 4) if n_seen else 0.0,
        "test_weighted_f1": round(wf / ws, 4) if ws else 0.0,
        "mean_confidence": round(mean_conf, 4),
        "label_distribution": dict(label_counts),
        "per_class": per_class,
        "confusion_matrix": {"classes": classes, "matrix": cm},
        "history": history,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
