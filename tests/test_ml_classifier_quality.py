import json
import math
import os
import time
from pathlib import Path, PureWindowsPath

import pytest

pytest.importorskip("torch")
pytest.importorskip("PIL.Image")
sklearn_metrics = pytest.importorskip("sklearn.metrics")

import config
from pipeline.classifiers.ml_classifier import MLClassifier


def _repo_path(stored_path: str) -> Path:
    return Path(config.BASE_DIR).joinpath(*PureWindowsPath(stored_path).parts)


def _load_test_samples(classifier: MLClassifier) -> list[tuple[str, str]]:
    annotations = Path(config.BASE_DIR) / "datasets" / "scene_type" / "v1" / "annotations.jsonl"
    if not annotations.exists():
        pytest.skip(f"Scene test annotations not found: {annotations}")

    allowed_labels = set(classifier.idx_to_label.values())
    samples: list[tuple[str, str]] = []
    with annotations.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            label = record.get("label")
            if record.get("split") != "test" or label not in allowed_labels:
                continue
            for frame_path in record.get("frames") or []:
                image_path = _repo_path(frame_path)
                if image_path.exists():
                    samples.append((str(image_path), label))

    max_samples = int(os.getenv("ML_EVAL_MAX_SAMPLES", "0"))
    if max_samples > 0:
        samples = samples[:max_samples]

    if not samples:
        pytest.skip("No existing test-split frame samples found for ML evaluation")
    return samples


@pytest.fixture(scope="module")
def ml_classifier() -> MLClassifier:
    classifier = MLClassifier()
    if classifier.model is None or classifier.transform is None:
        pytest.skip("ML model or preprocessing transform is unavailable")
    return classifier


def test_ml_preprocessing_tensor_is_model_ready(ml_classifier):
    samples = _load_test_samples(ml_classifier)
    tensor = ml_classifier.prepare_image_tensor(samples[0][0])

    assert tuple(tensor.shape) == (1, 3, 224, 224)
    assert tensor.is_floating_point()
    assert bool(tensor.isfinite().all())
    assert tensor.std().item() > 0
    assert -5.0 < tensor.mean().item() < 5.0


def test_ml_classifier_quality_on_test_split(ml_classifier):
    samples = _load_test_samples(ml_classifier)
    min_accuracy = float(os.getenv("ML_MIN_ACCURACY", "0.75"))
    min_macro_precision = float(os.getenv("ML_MIN_MACRO_PRECISION", "0.45"))
    min_macro_recall = float(os.getenv("ML_MIN_MACRO_RECALL", "0.45"))
    max_p95_seconds = float(os.getenv("ML_MAX_P95_SECONDS", "0.75"))

    # Warm up the model once so the latency gate measures steady-state inference.
    ml_classifier.predict_thumbnail(samples[0][0])

    y_true = []
    y_pred = []
    latencies = []
    for image_path, expected_label in samples:
        started = time.perf_counter()
        predicted_label, confidence, debug = ml_classifier.predict_thumbnail(image_path)
        latencies.append(time.perf_counter() - started)

        y_true.append(expected_label)
        y_pred.append(predicted_label)

        assert 0.0 <= confidence <= 1.0
        assert set(debug["all_class_probs"]) == set(ml_classifier.idx_to_label.values())
        assert math.isclose(sum(debug["all_class_probs"].values()), 1.0, abs_tol=0.02)

    true_labels = sorted(set(y_true))
    accuracy = sklearn_metrics.accuracy_score(y_true, y_pred)
    macro_precision, macro_recall, macro_f1, _ = sklearn_metrics.precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=true_labels,
        average="macro",
        zero_division=0,
    )
    p95_latency = sorted(latencies)[math.ceil(len(latencies) * 0.95) - 1]

    summary = (
        f"samples={len(samples)}, accuracy={accuracy:.3f}, "
        f"macro_precision={macro_precision:.3f}, macro_recall={macro_recall:.3f}, "
        f"macro_f1={macro_f1:.3f}, p95_latency={p95_latency:.3f}s"
    )
    assert accuracy >= min_accuracy, summary
    assert macro_precision >= min_macro_precision, summary
    assert macro_recall >= min_macro_recall, summary
    assert p95_latency <= max_p95_seconds, summary
