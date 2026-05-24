"""
retrain_model.py
================
Retrains the EditEase scene classifier on the v2_full dataset.

Label merging
─────────────
  presenter       → testimonial   (same visual semantics: person talking to camera)
  screen_recording → other        (only 1 sample, unlearnable)
  text_slide       → other        (only 1 sample, unlearnable)

Final classes (5)
─────────────────
  b-roll  |  testimonial  |  other  |  audience_reaction  |  establishing_shot

Key improvements over the previous version
──────────────────────────────────────────
  • Deeper classification head (512→256→num_classes) with BatchNorm + Dropout
  • Balanced accuracy used for checkpointing (not raw accuracy)
  • Gradient clipping to prevent unstable updates
  • label_smoothing=0.1 to reduce overconfidence on noisy labels
  • Mid-training layer3 unfreeze at epoch 10 for more capacity
  • Full sklearn classification_report at end of training
  • Checkpoint saves epoch, bal_acc, val_acc, label_map together
  • Scene-level majority-vote evaluation on held-out test set

Run:
    python retrain_model.py
"""

import os, json, random, sys
from collections import Counter, defaultdict

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import models, transforms
from sklearn.metrics import balanced_accuracy_score, classification_report
from PIL import Image

sys.path.insert(0, "D:/EDITEASE")
import config

# ─── Label merging ────────────────────────────────────────────────────────────
# Applied at load time — raw labels in the JSONL are remapped before training.
LABEL_MERGE = {
    "presenter":         "testimonial",   # same visual pattern: person to camera
    "screen_recording":  "other",         # 1 sample — unlearnable as its own class
    "text_slide":        "other",         # 1 sample — unlearnable as its own class
}

# Final class list after merging (order determines the integer index)
TRAINABLE_CLASSES = [
    "b-roll",
    "testimonial",
    "other",
    "audience_reaction",
    "establishing_shot",
]
LABEL_TO_IDX = {c: i for i, c in enumerate(TRAINABLE_CLASSES)}
IDX_TO_LABEL = {i: c for c, i in LABEL_TO_IDX.items()}

# ─── Paths ────────────────────────────────────────────────────────────────────
MANIFEST_PATH = "D:/EDITEASE/datasets/scene_type/v2_full/annotations.jsonl"
SPLIT_PATH    = "D:/EDITEASE/datasets/scene_type/v2_full/splits.json"
OUT_DIR       = "D:/EDITEASE/pipeline/models"
MODEL_PATH    = os.path.join(OUT_DIR, "scene_classifier_v2.pth")
ENCODER_PATH  = os.path.join(OUT_DIR, "label_encoder_v2.json")
EVAL_PATH     = "D:/EDITEASE/eval_report_v2.json"
HISTORY_PATH  = "D:/EDITEASE/datasets/scene_type/v2_full/training_history.json"

# ─── Hyperparameters ─────────────────────────────────────────────────────────
SEED                  = 42
EPOCHS                = 25
BATCH_SIZE            = 16
HEAD_LR               = 1e-3
BODY_LR               = 1e-4
PATIENCE              = 6
UNFREEZE_LAYER3_EPOCH = 10   # gently unfreeze layer3 mid-training


# ─── Helpers ──────────────────────────────────────────────────────────────────

def merge_label(raw: str) -> str:
    """Apply LABEL_MERGE remapping, return the raw label if no mapping exists."""
    return LABEL_MERGE.get(raw, raw)


def stratified_scene_split(scenes, test_ratio=0.25, val_ratio=0.15, seed=42):
    """
    Split at the scene level so frames from one scene are never split across
    train / val / test.  Stratified per class so each split has proportional
    representation.
    """
    by_class = defaultdict(list)
    for s in scenes:
        by_class[s["label"]].append(s)

    rnd = random.Random(seed)
    train, val, test = [], [], []
    for cls, items in by_class.items():
        rnd.shuffle(items)
        n      = len(items)
        n_test = max(1, int(round(n * test_ratio)))
        n_val  = max(1, int(round(n * val_ratio))) if n > 4 else 0
        test.extend(items[:n_test])
        val.extend(items[n_test : n_test + n_val])
        train.extend(items[n_test + n_val :])
    return train, val, test


# ─── Dataset ─────────────────────────────────────────────────────────────────

class FrameDataset(Dataset):
    """
    Loads individual frame images for a list of scenes.
    Returns (image_tensor, label_index).
    """
    def __init__(self, scenes, transform):
        self.transform = transform
        self.samples   = []   # list of (path, label_idx)
        missing        = 0

        for s in scenes:
            lbl_idx = LABEL_TO_IDX[s["label"]]
            for fp in s["frames"]:
                if os.path.exists(fp):
                    self.samples.append((fp, lbl_idx))
                else:
                    missing += 1

        if missing:
            print(f"  WARNING: {missing} frame files not found on disk and were skipped.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            img = Image.new("RGB", (224, 224))
        return self.transform(img), label

    def class_counts(self) -> np.ndarray:
        counts = np.zeros(len(TRAINABLE_CLASSES), dtype=np.int64)
        for _, lbl in self.samples:
            counts[lbl] += 1
        return counts


# ─── Model ────────────────────────────────────────────────────────────────────

def build_model(num_classes: int, device: torch.device) -> nn.Module:
    """
    ResNet-18 with ImageNet weights.

    Freezing strategy
    ─────────────────
    layer1, layer2, layer3  → frozen   (low-level edges / textures)
    layer4                  → trainable (high-level scene features)
    fc head                 → trainable (your 5 scene classes)

    Head architecture (deeper than a single linear layer)
    ─────────────────────────────────────────────────────
    AdaptiveAvgPool (built-in) → 512-d
    Linear(512 → 256) → BatchNorm1d → ReLU → Dropout(0.4)
    Linear(256 → num_classes)

    The BatchNorm + Dropout reduce overfitting on a small dataset.
    """
    backbone = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)

    # Freeze all first, then selectively unfreeze
    for p in backbone.parameters():
        p.requires_grad = False
    for p in backbone.layer4.parameters():
        p.requires_grad = True

    # Deeper head
    in_features = backbone.fc.in_features   # 512
    
# With this
    # With this
    # With this
    backbone.fc = nn.Sequential(
        nn.Linear(in_features, 256),
        nn.LayerNorm(256),            # ← works on any batch size
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(256, num_classes),
    )
    # New head is trainable by default

    model = backbone.to(device)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    print(f"\nModel: trainable {trainable:,} / {total:,} params ({100*trainable/total:.1f}%)")
    return model


# ─── Evaluation helpers ───────────────────────────────────────────────────────

def evaluate(model, loader, criterion, device):
    """Return (loss, raw_accuracy, all_labels, all_preds)."""
    model.eval()
    total_loss = correct = total = 0
    all_labels, all_preds = [], []

    with torch.no_grad():
        for x, y in loader:
            x, y   = x.to(device), y.to(device)
            out    = model(x)
            loss   = criterion(out, y)
            total_loss += loss.item()
            _, pred = torch.max(out, 1)
            correct += (pred == y).sum().item()
            total   += y.size(0)
            all_labels.extend(y.cpu().tolist())
            all_preds.extend(pred.cpu().tolist())

    acc = 100.0 * correct / max(1, total)
    return total_loss / max(1, len(loader)), acc, all_labels, all_preds


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    random.seed(SEED)
    os.makedirs(OUT_DIR, exist_ok=True)

    # ── Load & merge labels ───────────────────────────────────────────────
    print("Loading annotations…")
    raw_scenes = []
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                raw_scenes.append(json.loads(line))

    # Show what merging does
    raw_counts   = Counter(s["label"] for s in raw_scenes)
    merged_scenes = []
    for s in raw_scenes:
        merged_label = merge_label(s["label"])
        if merged_label in LABEL_TO_IDX and s.get("frames"):
            s = dict(s)   # don't mutate the original
            s["label"] = merged_label
            merged_scenes.append(s)

    print("\nLabel merging:")
    for raw, merged in sorted(LABEL_MERGE.items()):
        print(f"  {raw:20s} → {merged}  ({raw_counts.get(raw, 0)} scenes)")

    print(f"\nScenes after merging: {len(merged_scenes)}")
    print(f"Label distribution:   {Counter(s['label'] for s in merged_scenes)}")

    # ── Scene-level stratified split ──────────────────────────────────────
    train_scenes, val_scenes, test_scenes = stratified_scene_split(merged_scenes, seed=SEED)

    print(f"\nSplit (scene-level, stratified):")
    for name, sc in [("train", train_scenes), ("val", val_scenes), ("test", test_scenes)]:
        n_frames = sum(len(s["frames"]) for s in sc)
        dist     = Counter(s["label"] for s in sc)
        print(f"  {name:5s}: {len(sc):3d} scenes, {n_frames:4d} frames  {dict(dist)}")

    # Persist split for reproducibility
    with open(SPLIT_PATH, "w") as f:
        json.dump({
            "train": [{"video": s["video"], "scene_id": s["scene_id"], "label": s["label"]} for s in train_scenes],
            "val":   [{"video": s["video"], "scene_id": s["scene_id"], "label": s["label"]} for s in val_scenes],
            "test":  [{"video": s["video"], "scene_id": s["scene_id"], "label": s["label"]} for s in test_scenes],
            "label_merge": LABEL_MERGE,
            "classes": TRAINABLE_CLASSES,
            "seed": SEED,
        }, f, indent=2)

    # ── Transforms ────────────────────────────────────────────────────────
    train_tf = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.05),
        transforms.RandomGrayscale(p=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.1, scale=(0.02, 0.1)),
    ])
    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_ds = FrameDataset(train_scenes, train_tf)
    val_ds   = FrameDataset(val_scenes,   val_tf)
    test_ds  = FrameDataset(test_scenes,  val_tf)

    # ── Weighted sampler — corrects class imbalance ───────────────────────
    class_counts  = train_ds.class_counts()
    class_weights = np.where(class_counts > 0, 1.0 / class_counts, 0.0)
    sample_weights = [class_weights[lbl] for _, lbl in train_ds.samples]

    sampler = WeightedRandomSampler(
        weights     = sample_weights,
        num_samples = len(train_ds),
        replacement = True,
    )

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,   num_workers=0)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False,   num_workers=0)

    # ── Model ─────────────────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nDevice: {device}")
    model  = build_model(num_classes=len(TRAINABLE_CLASSES), device=device)

    # ── Loss — class-weighted CrossEntropy + label smoothing ──────────────
    # class_weights already computed above; normalise so they sum to num_classes
    loss_weights = torch.FloatTensor(
        class_weights / (class_weights.sum() + 1e-9) * len(TRAINABLE_CLASSES)
    ).to(device)
    criterion = nn.CrossEntropyLoss(
        weight          = loss_weights,
        label_smoothing = 0.1,
    )

    # ── Optimiser — two param groups ──────────────────────────────────────
    optimizer = optim.AdamW([
        {"params": model.layer4.parameters(), "lr": BODY_LR, "weight_decay": 1e-4},
        {"params": model.fc.parameters(),     "lr": HEAD_LR, "weight_decay": 1e-4},
    ])
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-6)

    # ── Training loop ─────────────────────────────────────────────────────
    best_bal_acc  = 0.0
    no_improve    = 0
    history       = []

    print("\n" + "=" * 75)
    print(f"{'Epoch':>5}  {'TrLoss':>8}  {'TrAcc':>7}  {'VaLoss':>8}  {'VaAcc':>7}  {'BalAcc':>7}  {'Best':>7}")
    print("=" * 75)

    for epoch in range(1, EPOCHS + 1):

        # ── Mid-training unfreeze of layer3 ──────────────────────────────
        if epoch == UNFREEZE_LAYER3_EPOCH:
            for p in model.layer3.parameters():
                p.requires_grad = True
            # Add to optimiser with a very low LR so it adapts slowly
            optimizer.add_param_group({
                "params":       list(model.layer3.parameters()),
                "lr":           BODY_LR * 0.1,
                "weight_decay": 1e-4,
            })
            print(f"\n  → Unfroze layer3 at epoch {epoch} (lr={BODY_LR*0.1:.1e})\n")

        # ── Train ─────────────────────────────────────────────────────────
        model.train()
        t_loss = t_correct = t_total = 0

        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out  = model(x)
            loss = criterion(out, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            t_loss    += loss.item()
            _, pred    = torch.max(out, 1)
            t_total   += y.size(0)
            t_correct += (pred == y).sum().item()

        train_loss = t_loss / max(1, len(train_loader))
        train_acc  = 100.0 * t_correct / max(1, t_total)

        # ── Validate ──────────────────────────────────────────────────────
        val_loss, val_acc, val_labels, val_preds = evaluate(
            model, val_loader, criterion, device
        )
        bal_acc = 100.0 * balanced_accuracy_score(val_labels, val_preds)

        scheduler.step()

        improved = bal_acc > best_bal_acc
        flag     = " ✓" if improved else ""
        print(
            f"{epoch:5d}  {train_loss:8.4f}  {train_acc:6.2f}%  "
            f"{val_loss:8.4f}  {val_acc:6.2f}%  {bal_acc:6.2f}%{flag}"
        )

        history.append({
            "epoch":      epoch,
            "train_loss": round(train_loss, 4),
            "train_acc":  round(train_acc, 2),
            "val_loss":   round(val_loss, 4),
            "val_acc":    round(val_acc, 2),
            "bal_acc":    round(bal_acc, 2),
        })

        # ── Checkpoint ────────────────────────────────────────────────────
        # Save on balanced accuracy so minority classes aren't ignored
        if improved:
            best_bal_acc = bal_acc
            no_improve   = 0
            torch.save(
                {
                    "epoch":            epoch,
                    "model_state_dict": model.state_dict(),
                    "val_acc":          round(val_acc, 2),
                    "bal_acc":          round(bal_acc, 2),
                    "label_map":        IDX_TO_LABEL,
                    "classes":          TRAINABLE_CLASSES,
                    "label_merge":      LABEL_MERGE,
                    "num_classes":      len(TRAINABLE_CLASSES),
                },
                MODEL_PATH,
            )
        else:
            no_improve += 1
            if no_improve >= PATIENCE:
                print(f"\nEarly stopping at epoch {epoch} — best bal_acc: {best_bal_acc:.2f}%")
                break

    # ── Save label encoder ────────────────────────────────────────────────
    with open(ENCODER_PATH, "w") as f:
        json.dump(IDX_TO_LABEL, f, indent=2)

    # ── Save training history ─────────────────────────────────────────────
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)

    # ── Validation classification report ──────────────────────────────────
    print("\n── Val set classification report ────────────────────────────────")
    print(classification_report(
        val_labels, val_preds,
        labels      = list(range(len(TRAINABLE_CLASSES))),
        target_names = TRAINABLE_CLASSES,
        zero_division = 0,
    ))

    # ─────────────────────────────────────────────────────────────────────
    # FINAL TEST EVALUATION — held-out set, best model
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 75)
    print("FINAL TEST EVALUATION  (held-out — never seen during training)")
    print("=" * 75)

    checkpoint = torch.load(MODEL_PATH, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    all_true, all_pred = [], []
    with torch.no_grad():
        for x, y in test_loader:
            x, y    = x.to(device), y.to(device)
            out     = model(x)
            _, pred = torch.max(out, 1)
            all_true.extend(y.cpu().tolist())
            all_pred.extend(pred.cpu().tolist())

    # Frame-level accuracy
    frame_acc = sum(t == p for t, p in zip(all_true, all_pred)) / max(1, len(all_true))
    frame_bal = balanced_accuracy_score(all_true, all_pred)
    print(f"\nFrame-level accuracy:          {frame_acc:.4f}  ({int(frame_acc*len(all_true))}/{len(all_true)})")
    print(f"Frame-level balanced accuracy: {frame_bal:.4f}")

    # Scene-level majority vote
    scene_true, scene_pred = [], []
    sample_idx = 0
    for s in test_scenes:
        n_frames = len([fp for fp in s["frames"] if os.path.exists(fp)])
        frame_preds = all_pred[sample_idx : sample_idx + n_frames]
        frame_trues = all_true[sample_idx : sample_idx + n_frames]
        sample_idx += n_frames
        if frame_preds:
            true_label = frame_trues[0]
            majority   = Counter(frame_preds).most_common(1)[0][0]
            scene_true.append(true_label)
            scene_pred.append(majority)

    scene_acc = sum(t == p for t, p in zip(scene_true, scene_pred)) / max(1, len(scene_true))
    scene_bal = balanced_accuracy_score(scene_true, scene_pred)
    print(f"\nScene-level accuracy:          {scene_acc:.4f}  ({int(scene_acc*len(scene_true))}/{len(scene_true)})")
    print(f"Scene-level balanced accuracy: {scene_bal:.4f}")

    # Full per-class report (scene-level)
    print("\n── Per-class report (scene-level) ───────────────────────────────")
    print(classification_report(
        scene_true, scene_pred,
        labels       = list(range(len(TRAINABLE_CLASSES))),
        target_names = TRAINABLE_CLASSES,
        zero_division = 0,
    ))

    # Confusion matrix
    print("── Confusion matrix (scene-level, rows=true, cols=predicted) ────")
    col_w = 16
    header = " " * 22 + "".join(f"{c[:col_w]:>{col_w}}" for c in TRAINABLE_CLASSES)
    print(header)
    print("─" * (22 + col_w * len(TRAINABLE_CLASSES)))
    for ti, true_cls in enumerate(TRAINABLE_CLASSES):
        row = f"{true_cls[:20]:22s}"
        for pi in range(len(TRAINABLE_CLASSES)):
            n = sum(1 for t, p in zip(scene_true, scene_pred) if t == ti and p == pi)
            cell = f"{n}" if n == 0 else f"\033[1m{n}\033[0m" if ti == pi else f"{n}"
            row += f"{cell:>{col_w}}"
        print(row)

    # ── Save eval report ──────────────────────────────────────────────────
    per_class_eval = {}
    for ci, cls in enumerate(TRAINABLE_CLASSES):
        tp  = sum(1 for t, p in zip(scene_true, scene_pred) if t == ci and p == ci)
        fp  = sum(1 for t, p in zip(scene_true, scene_pred) if t != ci and p == ci)
        fn  = sum(1 for t, p in zip(scene_true, scene_pred) if t == ci and p != ci)
        sup = sum(1 for t in scene_true if t == ci)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec  = tp / (tp + fn) if (tp + fn) else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per_class_eval[cls] = {
            "precision": round(prec, 4),
            "recall":    round(rec,  4),
            "f1":        round(f1,   4),
            "support":   sup,
        }

    n_cls      = sum(1 for v in per_class_eval.values() if v["support"] > 0)
    macro_f1   = sum(v["f1"] for v in per_class_eval.values() if v["support"] > 0) / max(1, n_cls)
    total_sup  = sum(v["support"] for v in per_class_eval.values())
    weighted_f1 = sum(v["f1"] * v["support"] for v in per_class_eval.values()) / max(1, total_sup)

    eval_report = {
        "model_path":              MODEL_PATH,
        "classes":                 TRAINABLE_CLASSES,
        "label_merge":             LABEL_MERGE,
        "train_scenes":            len(train_scenes),
        "val_scenes":              len(val_scenes),
        "test_scenes":             len(test_scenes),
        "train_frames":            len(train_ds),
        "test_frames":             len(all_true),
        "best_val_bal_acc":        round(best_bal_acc, 2),
        "test_frame_accuracy":     round(frame_acc, 4),
        "test_frame_balanced_acc": round(frame_bal, 4),
        "test_scene_accuracy":     round(scene_acc, 4),
        "test_scene_balanced_acc": round(scene_bal, 4),
        "test_macro_f1":           round(macro_f1,    4),
        "test_weighted_f1":        round(weighted_f1,  4),
        "per_class":               per_class_eval,
        "confusion_matrix": {
            "classes": TRAINABLE_CLASSES,
            "matrix": [
                [sum(1 for t, p in zip(scene_true, scene_pred) if t == ti and p == pi)
                 for pi in range(len(TRAINABLE_CLASSES))]
                for ti in range(len(TRAINABLE_CLASSES))
            ],
        },
        "history": history,
    }

    with open(EVAL_PATH, "w") as f:
        json.dump(eval_report, f, indent=2)

    print(f"\nModel saved:   {MODEL_PATH}")
    print(f"Eval report:   {EVAL_PATH}")
    print(f"Best bal_acc:  {best_bal_acc:.2f}%  (used for checkpointing)")
    print(f"Test scene acc: {scene_acc:.4f}   balanced: {scene_bal:.4f}")

    return eval_report


if __name__ == "__main__":
    main()