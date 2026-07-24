"""Guard that a trained scene classifier can actually be loaded for inference.

This is the test that was missing. Training built `Linear(512, 8)` while
inference expected `Sequential(Linear(512,256), LayerNorm, ReLU, Dropout,
Linear(256,5))`, wrote a raw state_dict to a filename inference never read, and
used a different label order — four independent breakages, none of which any
test would have caught, because training was never exercised end to end.
"""
import json

import pytest

pytest.importorskip("torch")

import torch

from pipeline.classifiers import scene_model


def test_label_order_matches_deployed_encoder():
    """A permuted label order silently relabels every prediction."""
    deployed = scene_model.load_label_order("v2")
    assert deployed == scene_model.CANONICAL_LABELS, (
        "label_encoder_v2.json disagrees with CANONICAL_LABELS; the checkpoint's "
        f"output neurons are bound to positions, so this mislabels everything.\n"
        f"  encoder  : {deployed}\n  canonical: {scene_model.CANONICAL_LABELS}"
    )


def test_trained_checkpoint_loads_into_inference_model(tmp_path, monkeypatch):
    """Save a model the way training does, load it the way inference does."""
    monkeypatch.setattr(scene_model, "MODELS_DIR", str(tmp_path))

    labels = list(scene_model.CANONICAL_LABELS)
    trained = scene_model.build_scene_model(len(labels), pretrained=False)
    checkpoint_path, encoder_path = scene_model.save_checkpoint(
        trained, labels, version="roundtrip", epoch=1, val_acc=42.0,
    )

    # --- the inference side, mirroring MLClassifier.__init__ ---
    with open(encoder_path, "r", encoding="utf-8") as handle:
        idx_to_label = json.load(handle)
    assert [idx_to_label[str(i)] for i in range(len(idx_to_label))] == labels

    serving = scene_model.build_scene_model(len(idx_to_label), pretrained=False)
    ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    state_dict = ckpt.get("model_state_dict", ckpt)
    serving.load_state_dict(state_dict)  # raises on any shape/key mismatch

    # And it must actually produce a usable distribution.
    serving.eval()
    with torch.no_grad():
        probs = torch.nn.functional.softmax(serving(torch.zeros(1, 3, 224, 224)), dim=1)
    assert probs.shape == (1, len(labels))
    assert pytest.approx(1.0, abs=1e-4) == float(probs.sum())


def test_checkpoint_carries_the_metadata_inference_expects(tmp_path, monkeypatch):
    monkeypatch.setattr(scene_model, "MODELS_DIR", str(tmp_path))

    labels = list(scene_model.CANONICAL_LABELS)
    model = scene_model.build_scene_model(len(labels), pretrained=False)
    checkpoint_path, _ = scene_model.save_checkpoint(model, labels, version="meta")

    ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    assert "model_state_dict" in ckpt, "ml_classifier looks for model_state_dict"
    assert ckpt["classes"] == labels
    assert ckpt["label_map"]["0"] == labels[0]


def test_training_module_agrees_with_inference():
    """The training script must not reintroduce its own label list."""
    train = pytest.importorskip("pipeline.training.train_scene_classifier")
    assert train.ALLOWED_LABELS == scene_model.load_label_order("v2")
