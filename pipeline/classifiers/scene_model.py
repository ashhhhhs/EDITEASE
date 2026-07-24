"""Single source of truth for the scene-classifier architecture and label order.

Why this module exists
----------------------
Training and inference had drifted into incompatibility, silently:

  train_scene_classifier.py built   fc = Linear(512, 8)
  ml_classifier.py expected         fc = Sequential(Linear(512,256), LayerNorm,
                                                    ReLU, Dropout, Linear(256,5))

so a freshly trained checkpoint could not be loaded at all. The label order
disagreed too (`0` meant `testimonial` when training and `b-roll` when
serving), which would have mislabelled every prediction even if the shapes had
matched. On top of that the two used different filenames and different
checkpoint formats, and the script that actually produced the deployed model
was not in the repository.

Keeping the architecture, the label order, and the checkpoint format in one
place is what stops that happening again. Import from here on both sides.
"""
import json
import os

import torch
import torch.nn as nn
from torchvision import models, transforms

import config

MODELS_DIR = os.path.join(config.BASE_DIR, "pipeline", "models")

# Canonical label order. This MUST match label_encoder_v2.json, because the
# deployed checkpoint's output neurons are bound to these positions — permuting
# them silently relabels every prediction.
CANONICAL_LABELS = [
    "b-roll",             # 0
    "testimonial",        # 1
    "other",              # 2
    "audience_reaction",  # 3
    "establishing_shot",  # 4
]

# Normalisation must be identical in training and inference or the model sees a
# different input distribution than it was fitted on.
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def build_scene_model(num_classes: int, pretrained: bool = False) -> nn.Module:
    """ResNet-18 with the project's classification head.

    `pretrained` loads ImageNet weights and belongs in training; inference
    overwrites everything from the checkpoint, so it passes False and avoids
    the download.
    """
    weights = models.ResNet18_Weights.DEFAULT if pretrained else None
    model = models.resnet18(weights=weights)
    num_ftrs = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_ftrs, 256),
        nn.LayerNorm(256),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.3),
        nn.Linear(256, num_classes),
    )
    return model


def inference_transform():
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def model_paths(version: str = "v2") -> tuple[str, str]:
    """(checkpoint_path, encoder_path) for a model version."""
    return (
        os.path.join(MODELS_DIR, f"scene_classifier_{version}.pth"),
        os.path.join(MODELS_DIR, f"label_encoder_{version}.json"),
    )


def load_label_order(version: str = "v2") -> list[str]:
    """Label order from the encoder file, falling back to CANONICAL_LABELS.

    Reading the existing file means retraining preserves the index mapping the
    deployed checkpoint already uses.
    """
    _, encoder_path = model_paths(version)
    if not os.path.exists(encoder_path):
        return list(CANONICAL_LABELS)
    with open(encoder_path, "r", encoding="utf-8") as handle:
        idx_to_label = json.load(handle)
    return [idx_to_label[str(i)] for i in range(len(idx_to_label))]


def save_checkpoint(model, labels, version="v2", **metadata) -> tuple[str, str]:
    """Write checkpoint + encoder in the format ml_classifier expects."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    checkpoint_path, encoder_path = model_paths(version)

    payload = {
        "model_state_dict": model.state_dict(),
        "classes": list(labels),
        "label_map": {str(i): label for i, label in enumerate(labels)},
    }
    payload.update(metadata)
    torch.save(payload, checkpoint_path)

    with open(encoder_path, "w", encoding="utf-8") as handle:
        json.dump({str(i): label for i, label in enumerate(labels)}, handle, indent=2)

    return checkpoint_path, encoder_path
