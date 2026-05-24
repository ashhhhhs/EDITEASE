"""
Real evaluation of the EditEase scene classifier (v2) against all available
reviewed scenes exported in annotations.jsonl.

Fixes vs the previous version
──────────────────────────────
  • Uses scene_classifier_v2.pth  + label_encoder_v2.json  (v2 filenames)
  • Rebuilds the Sequential head (Linear→LayerNorm→ReLU→Dropout→Linear)
    that retrain_model.py saved — a flat nn.Linear would fail to load
  • Loads weights from checkpoint["model_state_dict"], not the raw dict
  • Reads classes / label_merge from the checkpoint itself (no hard-coding)
  • Applies LABEL_MERGE to ground-truth labels before comparing, so
    presenter→testimonial etc. are treated consistently with training
  • Sources scenes from annotations.jsonl (the exported dataset) instead
    of walking scene_index_*.json files, which may be stale

Run with:
    /mnt/d/EDITEASE/venv/bin/python run_real_eval.py
"""

import os, json, sys
from collections import Counter, defaultdict

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np

# ── Project imports ──────────────────────────────────────────────────────────
sys.path.insert(0, "/mnt/d/EDITEASE")
import config

# ── Paths (v2) ───────────────────────────────────────────────────────────────
MODEL_PATH    = os.path.join(config.BASE_DIR, "pipeline", "models", "scene_classifier_v2.pth")
ENCODER_PATH  = os.path.join(config.BASE_DIR, "pipeline", "models", "label_encoder_v2.json")
MANIFEST_PATH = os.path.join(config.BASE_DIR, "datasets", "scene_type", "v2_full", "annotations.jsonl")
EVAL_OUT_PATH = os.path.join(config.BASE_DIR, "eval_report_v2_real.json")


# ── Build the same head architecture used in retrain_model.py ────────────────

def build_eval_model(num_classes: int, device: torch.device) -> nn.Module:
    """
    Mirrors the head in retrain_model.py exactly:
        Linear(512 → 256) → LayerNorm(256) → ReLU → Dropout(0.4) → Linear(256 → n)

    A flat nn.Linear head would produce a key mismatch when loading the v2
    checkpoint and raise a RuntimeError.
    """
    backbone = models.resnet18(weights=None)
    in_features = backbone.fc.in_features  # 512
    backbone.fc = nn.Sequential(
        nn.Linear(in_features, 256),
        nn.LayerNorm(256),
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(256, num_classes),
    )
    return backbone.to(device)


# ── Load scenes from the exported JSONL ──────────────────────────────────────

def load_scenes(manifest_path: str, label_merge: dict) -> list[dict]:
    """
    Read annotations.jsonl and return one dict per scene with:
        key, video, scene_id, true_label (merged), frames, thumbnail
    Only scenes whose merged label is in the trainable set are included.
    """
    scenes = []
    seen   = set()

    with open(manifest_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            key = rec.get("scene_key") or f"{rec.get('video')}::{rec.get('scene_id')}"
            if key in seen:
                continue
            seen.add(key)

            raw_label = rec.get("label", "")
            true_label = label_merge.get(raw_label, raw_label)

            frames = rec.get("frames") or []
            # Re-root relative paths against BASE_DIR
            abs_frames = []
            for fp in frames:
                if os.path.isabs(fp):
                    abs_frames.append(fp)
                else:
                    abs_frames.append(os.path.join(str(config.BASE_DIR), fp))

            scenes.append({
                "key":        key,
                "video":      rec.get("video"),
                "scene_id":   rec.get("scene_id"),
                "true_label": true_label,
                "frames":     abs_frames,
            })

    return scenes


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("─" * 70)
    print("EditEase Scene Classifier v2 — Real Evaluation")
    print("─" * 70)

    # ── Load checkpoint ──────────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    checkpoint = torch.load(MODEL_PATH, map_location=device, weights_only=True)

    # Prefer metadata baked into the checkpoint over any hard-coded constants
    classes     = checkpoint.get("classes", [])
    label_merge = checkpoint.get("label_merge", {})
    num_classes = checkpoint.get("num_classes", len(classes))

    print(f"Checkpoint — epoch {checkpoint.get('epoch')}  "
          f"val_acc {checkpoint.get('val_acc')}%  "
          f"bal_acc {checkpoint.get('bal_acc')}%")
    print(f"Classes ({num_classes}): {classes}")
    print(f"Label merge: {label_merge}\n")

    idx_to_label = {i: c for i, c in enumerate(classes)}

    # ── Build model and load weights ─────────────────────────────────────────
    model = build_eval_model(num_classes, device)
    model.load_state_dict(checkpoint["model_state_dict"])  # key, not raw dict
    model.eval()

    total_params = sum(p.numel() for p in model.parameters())
    print(f"Model loaded — {total_params:,} parameters\n")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # ── Load scenes ──────────────────────────────────────────────────────────
    scenes = load_scenes(MANIFEST_PATH, label_merge)
    print(f"Scenes in annotations.jsonl: {len(scenes)}")

    label_counts = Counter(s["true_label"] for s in scenes)
    print("\nLabel distribution (after merge):")
    for lbl in sorted(label_counts):
        print(f"  {lbl:25s}: {label_counts[lbl]}")

    # ── Run inference ────────────────────────────────────────────────────────
    print("\nRunning inference...")
    y_true, y_pred, confs = [], [], []
    missing_frames  = 0
    unknown_label   = 0
    error_count     = 0

    label_to_idx = {c: i for i, c in idx_to_label.items()}

    for s in scenes:
        if s["true_label"] not in label_to_idx:
            unknown_label += 1
            continue

        # Use the first frame that exists on disk
        frame_path = None
        for fp in s["frames"]:
            if os.path.exists(fp):
                frame_path = fp
                break

        if not frame_path:
            missing_frames += 1
            continue

        try:
            img = Image.open(frame_path).convert("RGB")
            x   = transform(img).unsqueeze(0).to(device)
            with torch.no_grad():
                logits = model(x)
                probs  = torch.softmax(logits, dim=1)
                conf, pred_idx = torch.max(probs, 1)
            pred = idx_to_label[int(pred_idx.item())]
            y_true.append(s["true_label"])
            y_pred.append(pred)
            confs.append(float(conf.item()))
        except Exception as e:
            error_count += 1
            print(f"  ERROR on {s['key']}: {e}")

    print(f"\nMissing frames:    {missing_frames}")
    print(f"Unknown labels:    {unknown_label}")
    print(f"Inference errors:  {error_count}")
    print(f"Evaluated scenes:  {len(y_true)}")

    if not y_true:
        print("\nNo scenes to evaluate. Bailing out.")
        return

    # ── Overall accuracy ─────────────────────────────────────────────────────
    correct   = sum(t == p for t, p in zip(y_true, y_pred))
    acc       = correct / len(y_true)
    mean_conf = float(np.mean(confs))
    print(f"\n{'='*70}")
    print(f"OVERALL ACCURACY:  {acc:.4f}  ({correct}/{len(y_true)})")
    print(f"Mean confidence:   {mean_conf:.4f}")
    print(f"{'='*70}\n")

    # ── Per-class precision / recall / F1 ────────────────────────────────────
    classes_present = sorted(set(y_true) | set(y_pred))
    print(f"{'Class':25s} {'Prec':>8s} {'Rec':>8s} {'F1':>8s} {'Support':>8s}")
    print("─" * 60)

    macro_p = macro_r = macro_f = 0.0
    weighted_f = total_support = n_classes_seen = 0

    per_class_stats = {}
    for cls in classes_present:
        tp      = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        fp      = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
        fn      = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
        support = sum(1 for t in y_true if t == cls)
        prec    = tp / (tp + fp) if (tp + fp) else 0.0
        rec     = tp / (tp + fn) if (tp + fn) else 0.0
        f1      = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per_class_stats[cls] = {"precision": round(prec, 4), "recall": round(rec, 4),
                                "f1": round(f1, 4), "support": support}
        print(f"{cls:25s} {prec:8.4f} {rec:8.4f} {f1:8.4f} {support:8d}")
        if support > 0:
            macro_p += prec; macro_r += rec; macro_f += f1
            n_classes_seen += 1
            weighted_f  += f1 * support
            total_support += support

    print("─" * 60)
    if n_classes_seen:
        print(f"{'Macro avg':25s} "
              f"{macro_p/n_classes_seen:8.4f} {macro_r/n_classes_seen:8.4f} "
              f"{macro_f/n_classes_seen:8.4f} {total_support:8d}")
    if total_support:
        print(f"{'Weighted avg':25s} {'':8s} {'':8s} "
              f"{weighted_f/total_support:8.4f} {total_support:8d}")

    # ── Confusion matrix ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("CONFUSION MATRIX  (rows = true, columns = predicted)")
    print(f"{'='*70}")
    col_w = 16
    header = " " * 22 + "".join(f"{c[:col_w]:>{col_w}}" for c in classes_present)
    print(header)
    print("─" * (22 + col_w * len(classes_present)))
    for t_cls in classes_present:
        row = f"{t_cls[:20]:22s}"
        for p_cls in classes_present:
            n = sum(1 for ti, pi in zip(y_true, y_pred) if ti == t_cls and pi == p_cls)
            row += f"{n:>{col_w}}"
        print(row)

    # ── Save JSON report ─────────────────────────────────────────────────────
    report = {
        "model_path":          MODEL_PATH,
        "manifest_path":       MANIFEST_PATH,
        "classes":             classes,
        "label_merge":         label_merge,
        "overall_accuracy":    round(acc, 4),
        "mean_confidence":     round(mean_conf, 4),
        "evaluated_scenes":    len(y_true),
        "missing_frames":      missing_frames,
        "unknown_labels":      unknown_label,
        "label_distribution":  dict(label_counts),
        "per_class":           per_class_stats,
        "confusion_matrix": {
            "classes": classes_present,
            "matrix": [
                [sum(1 for t, p in zip(y_true, y_pred) if t == t_cls and p == p_cls)
                 for p_cls in classes_present]
                for t_cls in classes_present
            ],
        },
    }
    with open(EVAL_OUT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: {EVAL_OUT_PATH}")


if __name__ == "__main__":
    main()