"""Quality gate for the emotion track.

Mirrors test_ml_classifier_quality.py: skips cleanly until a labelled dataset
exists, then enforces accuracy floors so a pipeline change cannot silently make
emotion detection worse.

Truth comes from datasets/emotion/v1/annotations.jsonl (written by the labelling
page). Predictions come from candidates.json, which is snapshotted at export time
— so this runs offline with no MongoDB and no DeepFace, like every other test here.

Re-run `python -m scripts.export_emotion_eval_set` after a pipeline change to
refresh the snapshot, then re-run this gate.
"""
import json
import os
from pathlib import Path

import pytest

import config
from scripts.export_emotion_eval_set import LABEL_SCHEME, bucket_for

DATASET_DIR = Path(config.BASE_DIR) / "datasets" / "emotion" / "v1"


def _load_pairs():
    """Return [(human_label, predicted_bucket), ...] for every labelled scene."""
    annotations = DATASET_DIR / "annotations.jsonl"
    candidates = DATASET_DIR / "candidates.json"

    if not candidates.exists():
        pytest.skip(f"No emotion candidates at {candidates} — run scripts.export_emotion_eval_set")
    if not annotations.exists():
        pytest.skip(
            f"No emotion annotations at {annotations} — label clips with "
            "datasets/emotion/v1/label_emotions.html first"
        )

    predictions = {
        c["scene_ref"]: c.get("_prediction")
        for c in json.loads(candidates.read_text(encoding="utf-8"))["candidates"]
    }

    pairs = []
    for line in annotations.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        ref, human = rec.get("scene_ref"), rec.get("human_emotion")
        if not ref or not human or ref not in predictions:
            continue
        pairs.append((human, bucket_for(predictions[ref])))

    if not pairs:
        pytest.skip("No labelled scenes overlap the candidate snapshot")
    return pairs


def test_emotion_labels_use_the_agreed_scheme():
    """A stray label silently distorts every metric downstream."""
    pairs = _load_pairs()
    bad = sorted({h for h, _ in pairs if h not in LABEL_SCHEME})
    assert not bad, f"annotations contain labels outside the scheme {LABEL_SCHEME}: {bad}"


def test_emotion_overall_accuracy_meets_floor():
    pairs = _load_pairs()
    min_accuracy = float(os.getenv("EMOTION_MIN_ACCURACY", "0.55"))

    correct = sum(1 for truth, pred in pairs if truth == pred)
    accuracy = correct / len(pairs)
    assert accuracy >= min_accuracy, (
        f"emotion accuracy {accuracy:.1%} ({correct}/{len(pairs)}) "
        f"below floor {min_accuracy:.0%}. Run scripts.evaluate_emotion for the "
        f"confusion matrix."
    )


def test_sad_precision_meets_floor():
    """The headline promise: when it says sad, it should be sad."""
    pairs = _load_pairs()
    min_precision = float(os.getenv("EMOTION_MIN_SAD_PRECISION", "0.50"))

    said_sad = [(t, p) for t, p in pairs if p == "sad"]
    if not said_sad:
        pytest.skip("pipeline predicted 'sad' on no labelled scene")

    hits = sum(1 for truth, _ in said_sad if truth == "sad")
    precision = hits / len(said_sad)
    assert precision >= min_precision, (
        f"sad precision {precision:.1%} ({hits}/{len(said_sad)}) below floor "
        f"{min_precision:.0%} — clips shown to reviewers as sad are mostly not sad."
    )
