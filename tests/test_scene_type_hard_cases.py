"""Regression guard for scene type on known-hard cases.

READ THIS BEFORE QUOTING ANY NUMBER FROM HERE.

These scenes are the ones a reviewer went in and corrected, so they were selected
precisely where the machine looked wrong. Accuracy here is therefore *not* the
model's accuracy — it is its accuracy on its own worst cases, and it will always
read low. Quoting it as "the model is X% accurate" would be wrong.

Its job is narrower and still useful: catch a change that makes the hard cases
worse. For an unbiased number, label a random sample with
`scripts/export_eval_set.py` and use tests/test_ml_classifier_quality.py.

Measured at 60% (24/40) when this guard was written, so the floor sits at 45% —
low enough to absorb noise on a 40-sample set, high enough to catch a real
regression.
"""
import json
import os
from pathlib import Path, PureWindowsPath

import pytest

pytest.importorskip("torch")
pytest.importorskip("PIL.Image")

import config
from scripts.eval_labels import SCENE_TYPE_SCHEME

ANNOTATIONS = Path(config.BASE_DIR) / "datasets" / "scene_type" / "hard_cases" / "annotations.jsonl"


def _load_samples():
    if not ANNOTATIONS.exists():
        pytest.skip(
            f"No hard-case set at {ANNOTATIONS} — "
            "run `python -m scripts.export_scene_type_hard_cases`"
        )

    samples = []
    for line in ANNOTATIONS.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        for frame in record.get("frames") or []:
            path = Path(config.BASE_DIR).joinpath(*PureWindowsPath(frame).parts)
            if path.exists():
                samples.append((str(path), record["label"]))

    if not samples:
        pytest.skip("Hard-case frames are no longer on disk")
    return samples


@pytest.fixture(scope="module")
def classifier():
    from pipeline.classifiers.ml_classifier import MLClassifier

    clf = MLClassifier()
    if clf.model is None or clf.transform is None:
        pytest.skip("ML model or preprocessing transform is unavailable")
    return clf


def test_hard_case_labels_are_on_scheme():
    """An off-scheme label silently drops out of every metric."""
    samples = _load_samples()
    bad = sorted({label for _, label in samples if label not in SCENE_TYPE_SCHEME})
    assert not bad, f"hard-case labels outside {SCENE_TYPE_SCHEME}: {bad}"


def test_hard_case_labels_are_human_sourced():
    """The whole point is that these are human judgements, not machine echoes.

    datasets/scene_type/v2_full is 252/315 machine-labelled, and scoring a model
    against its own output measures self-consistency rather than correctness.
    This guards against that creeping into the hard-case set.
    """
    _load_samples()  # skips cleanly if the set is absent

    for line in ANNOTATIONS.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        assert record.get("label_source") == "manual_scene_label", (
            f"{record.get('scene_ref')} has label_source={record.get('label_source')!r}; "
            "the hard-case set must contain only human corrections"
        )


def test_resnet_does_not_regress_on_hard_cases(classifier):
    samples = _load_samples()
    min_accuracy = float(os.getenv("SCENE_HARD_MIN_ACCURACY", "0.45"))

    correct = 0
    for image_path, expected in samples:
        predicted, confidence, _debug = classifier.predict_thumbnail(image_path)
        assert 0.0 <= confidence <= 1.0
        correct += (predicted == expected)

    accuracy = correct / len(samples)
    assert accuracy >= min_accuracy, (
        f"hard-case accuracy {accuracy:.1%} ({correct}/{len(samples)}) below floor "
        f"{min_accuracy:.0%}. This set is intentionally biased toward difficult "
        f"scenes, so it measures regression, not overall quality."
    )
