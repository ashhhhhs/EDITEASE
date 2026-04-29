import os
import json
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import torchvision.transforms as transforms
import torchvision.models as models
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from tqdm import tqdm
import numpy as np
import config
from utils.logger import setup_logger

logger = setup_logger("train_scene_classifier")

ALLOWED_LABELS = [
    "testimonial",
    "presenter",
    "b-roll",
    "audience_reaction",
    "establishing_shot",
    "screen_recording",
    "text_slide",
    "other",
]
LABEL_TO_IDX = {k: i for i, k in enumerate(ALLOWED_LABELS)}
IDX_TO_LABEL = {i: k for k, i in LABEL_TO_IDX.items()}


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class SceneDataset(Dataset):
    def __init__(self, annotations_file, base_dir, split="train", transform=None):
        self.base_dir  = base_dir
        self.transform = transform
        self.samples   = []

        with open(annotations_file, "r", encoding="utf-8") as f:
            for line in f:
                record    = json.loads(line)
                label_str = record.get("label", "")
                if record["split"] != split or label_str not in LABEL_TO_IDX:
                    continue
                label_idx = LABEL_TO_IDX[label_str]
                for frame_path in record.get("frames", []):
                    if frame_path:
                        self.samples.append({
                            "image_path": os.path.join(self.base_dir, frame_path),
                            "label"     : label_idx,
                        })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample     = self.samples[idx]
        label      = sample["label"]
        image_path = sample["image_path"]

        try:
            image = Image.open(image_path).convert("RGB")
        except Exception:
            image = Image.new("RGB", (224, 224))

        if self.transform:
            image = self.transform(image)

        return image, label

    def get_class_counts(self):
        """Return per-class sample count for weighting."""
        counts = np.zeros(len(ALLOWED_LABELS), dtype=np.int64)
        for s in self.samples:
            counts[s["label"]] += 1
        return counts


# ---------------------------------------------------------------------------
# Model builder — proper transfer learning
# ---------------------------------------------------------------------------

def build_model(num_classes: int, device: torch.device):
    """
    ResNet-18 with ImageNet pretrained weights, partially frozen, and a
    deeper classification head.

    Freezing strategy
    -----------------
    - layer1, layer2, layer3  → frozen   (low-level features: edges, textures)
    - layer4                  → trainable (high-level features: shapes, patterns)
    - fc head                 → trainable (your scene classes)

    This protects the expensive ImageNet knowledge while letting the top of
    the network adapt to your specific scene semantics.

    Head architecture
    -----------------
    ResNet-18 body (512-d)
        → Linear(512 → 256) → BatchNorm → ReLU → Dropout(0.4)
        → Linear(256 → num_classes)

    The extra hidden layer + dropout reduces overfitting on small datasets.
    """
    model = models.resnet18(pretrained=True)

    # ── Step 1: Freeze ALL layers ────────────────────────────────────────
    for param in model.parameters():
        param.requires_grad = False

    # ── Step 2: Unfreeze layer4 so it adapts to scene semantics ─────────
    for param in model.layer4.parameters():
        param.requires_grad = True

    # ── Step 3: Replace the head with a deeper classifier ───────────────
    in_features = model.fc.in_features   # 512 for ResNet-18
    model.fc = nn.Linear(in_features, num_classes)
    # New head is trainable by default (requires_grad=True)

    model = model.to(device)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    logger.info(
        "Model ready — trainable params: %s / %s (%.1f%%)",
        f"{trainable:,}", f"{total:,}", 100 * trainable / total,
    )
    return model


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_model(
    data_dir   = "datasets/scene_type/v1",
    epochs     = 20,
    batch_size = 32,
    head_lr    = 1e-3,   # learning rate for the new head
    body_lr    = 1e-4,   # lower LR for the unfrozen layer4 body
    patience   = 5,      # early-stopping patience (epochs without improvement)
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device: %s", device)

    annotations_file = os.path.join(config.BASE_DIR, data_dir, "annotations.jsonl")

    # ── Transforms ───────────────────────────────────────────────────────
    # Training: aggressive augmentation — your dataset is small, this is free data.
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),                          # random crop instead of centre
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.05),
        transforms.RandomGrayscale(p=0.05),                  # occasional grayscale
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.1, scale=(0.02, 0.1)), # randomly mask small regions
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # ── Datasets ──────────────────────────────────────────────────────────
    train_dataset = SceneDataset(annotations_file, str(config.BASE_DIR), split="train", transform=train_transform)
    val_dataset   = SceneDataset(annotations_file, str(config.BASE_DIR), split="val",   transform=val_transform)

    logger.info("Train samples: %s | Val samples: %s", len(train_dataset), len(val_dataset))

    if len(train_dataset) == 0:
        logger.error("No training samples found — run export_dataset.py first.")
        return

    # ── Weighted sampler — fixes class imbalance ──────────────────────────
    # If you have 500 b-roll scenes and 50 text_slides, the model will ignore
    # text_slides without this. Each sample's weight = 1 / class_count.
    class_counts  = train_dataset.get_class_counts()
    class_weights = np.where(class_counts > 0, 1.0 / class_counts, 0.0)
    sample_weights = np.array([
        class_weights[s["label"]] for s in train_dataset.samples
    ])
    sampler = WeightedRandomSampler(
        weights     = sample_weights.tolist(),
        num_samples = len(train_dataset),
        replacement = True,
    )

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size,
        sampler=sampler, num_workers=2, pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size,
        shuffle=False, num_workers=2, pin_memory=True,
    )

    # ── Model ─────────────────────────────────────────────────────────────
    model = build_model(num_classes=len(ALLOWED_LABELS), device=device)

    # ── Loss — class-weighted CrossEntropy ────────────────────────────────
    # Weighted sampler handles sampling; class-weighted loss handles the gradient.
    # Using both gives the minority classes two layers of correction.
    loss_weights = torch.FloatTensor(
        [class_weights[i] if class_counts[i] > 0 else 0.0 for i in range(len(ALLOWED_LABELS))]
    ).to(device)
    # Normalise so weights sum to num_classes (keeps loss scale stable)
    loss_weights = loss_weights / (loss_weights.sum() + 1e-9) * len(ALLOWED_LABELS)
    criterion = nn.CrossEntropyLoss(weight=loss_weights)

    # ── Optimiser — two param groups with different LRs ───────────────────
    # Head trains faster; body adapts slowly to preserve pretrained knowledge.
    optimizer = optim.AdamW([
        {"params": model.layer4.parameters(), "lr": body_lr,  "weight_decay": 1e-4},
        {"params": model.fc.parameters(),     "lr": head_lr,  "weight_decay": 1e-4},
    ])

    # ── LR scheduler — cosine annealing ──────────────────────────────────
    # Smoothly decays LR to near-zero over training; avoids sharp drops.
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    # ── Paths ─────────────────────────────────────────────────────────────
    models_dir      = os.path.join(config.BASE_DIR, "pipeline", "models")
    os.makedirs(models_dir, exist_ok=True)
    best_model_path = os.path.join(models_dir, "scene_classifier.pth")

    # ── Training loop ─────────────────────────────────────────────────────
    best_val_acc    = 0.0
    epochs_no_improve = 0

    for epoch in range(epochs):

        # ── Train ────────────────────────────────────────────────────────
        model.train()
        running_loss = correct = total = 0

        for inputs, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]"):
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss    = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted  = torch.max(outputs.data, 1)
            total        += labels.size(0)
            correct      += (predicted == labels).sum().item()

        train_acc = 100.0 * correct / (total + 1e-9)

        # ── Validate ─────────────────────────────────────────────────────
        model.eval()
        val_loss = val_correct = val_total = 0

        # Per-class accuracy tracking
        class_correct = np.zeros(len(ALLOWED_LABELS))
        class_total   = np.zeros(len(ALLOWED_LABELS))

        with torch.no_grad():
            for inputs, labels in tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [Val]"):
                inputs, labels = inputs.to(device), labels.to(device)
                outputs        = model(inputs)
                loss           = criterion(outputs, labels)

                val_loss      += loss.item()
                _, predicted   = torch.max(outputs.data, 1)
                val_total     += labels.size(0)
                val_correct   += (predicted == labels).sum().item()

                for lbl, pred in zip(labels.cpu().numpy(), predicted.cpu().numpy()):
                    class_total[lbl]   += 1
                    class_correct[lbl] += int(lbl == pred)

        val_acc = 100.0 * val_correct / (val_total + 1e-9)

        # Per-class breakdown
        per_class_str = "  |  ".join(
            f"{ALLOWED_LABELS[i]}: {100*class_correct[i]/(class_total[i]+1e-9):.0f}%"
            for i in range(len(ALLOWED_LABELS))
            if class_total[i] > 0
        )

        logger.info(
            "Epoch %s/%s — Train Loss: %.4f | Train Acc: %.2f%% | "
            "Val Loss: %.4f | Val Acc: %.2f%%",
            epoch + 1, epochs,
            running_loss / len(train_loader), train_acc,
            val_loss     / (len(val_loader) + 1e-9), val_acc,
        )
        logger.info("Per-class val acc → %s", per_class_str)

        scheduler.step()

        # ── Save best model ───────────────────────────────────────────────
        if val_acc > best_val_acc:
            best_val_acc    = val_acc
            epochs_no_improve = 0
            torch.save(model.state_dict(), best_model_path)
            logger.info("✅ New best model saved — Val Acc: %.2f%%", best_val_acc)
        else:
            epochs_no_improve += 1
            logger.info(
                "No improvement for %s/%s epochs (best: %.2f%%)",
                epochs_no_improve, patience, best_val_acc,
            )

        # ── Early stopping ────────────────────────────────────────────────
        if epochs_no_improve >= patience:
            logger.info(
                "Early stopping triggered after %s epochs without improvement.", patience,
            )
            break

    # ── Save label encoder ────────────────────────────────────────────────
    encoder_path = os.path.join(models_dir, "label_encoder.json")
    with open(encoder_path, "w") as f:
        json.dump(IDX_TO_LABEL, f)

    logger.info(
        "Training complete. Best Val Acc: %.2f%%. Model saved to %s",
        best_val_acc, best_model_path,
    )


if __name__ == "__main__":
    train_model(epochs=20, batch_size=16)
