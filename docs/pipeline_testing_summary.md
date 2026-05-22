# Pipeline Testing Summary

Generated: 2026-05-22

## Test Command

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ml_classifier_quality.py tests\test_rule_system.py tests\test_end_to_end_pipeline.py -q
```

## Latest Local Result

```text
12 passed in 11.90s
```

## ML Classifier Quality

Dataset: `datasets/scene_type/v1/annotations.jsonl`, `split == "test"`

Samples evaluated: 60 frames

True label distribution:

| Label | Count |
| --- | ---: |
| b-roll | 35 |
| testimonial | 20 |
| presenter | 5 |

Measured model-only results using `MLClassifier.predict_thumbnail()`:

| Metric | Value |
| --- | ---: |
| Accuracy | 0.8667 |
| Macro precision | 0.5847 |
| Macro recall | 0.6238 |
| Macro F1 | 0.6029 |
| Weighted precision | 0.8275 |
| Weighted recall | 0.8667 |
| Weighted F1 | 0.8457 |
| Mean inference latency | 0.0596s |
| P95 inference latency | 0.1214s |
| Max inference latency | 0.1284s |

Default quality gates:

| Gate | Threshold |
| --- | ---: |
| Minimum accuracy | 0.75 |
| Minimum macro precision | 0.45 |
| Minimum macro recall | 0.45 |
| Maximum P95 inference latency | 0.75s |

These gates can be tuned with `ML_MIN_ACCURACY`, `ML_MIN_MACRO_PRECISION`, `ML_MIN_MACRO_RECALL`, `ML_MAX_P95_SECONDS`, and `ML_EVAL_MAX_SAMPLES`.

## Coverage Added

| Area | Coverage |
| --- | --- |
| ML preprocessing | Verifies image tensor shape, finite normalized values, and non-empty signal variance. |
| ML inference | Evaluates accuracy, macro precision, macro recall, class probabilities, confidence bounds, and P95 latency on the test split. |
| Rule features | Verifies raw signal normalization and clipping for extreme visual/motion inputs. |
| Rule classification | Verifies Gaussian profile classification and probability distribution shape for a text-slide profile. |
| Contradictory rules | Verifies temporal smoothing and ML/rule fusion behavior for agreement and conflict paths. |
| Metadata tagging | Verifies edited-video detection from filenames and ffprobe metadata, including ffprobe failure fallback. |
| Categorization | Verifies dominant-label metadata, emotion aggregation, face ratios, empty scene sets, and the edited-video variety override. |
| Content filtering | Verifies clip search query construction for labels, null emotions, booleans, duration ranges, pagination, and limit clamping. |
| End-to-end pipeline | Runs a synthetic raw video through ingestion, frame extraction, ML classification, rule evaluation, JSON scene-index writing, and database upsert handoff with Cloudinary/Mongo mocked. |
| Error handling | Verifies database storage failures emit a failed checkpoint and re-raise the original error. |
| Logging | Verifies `PIPELINE_CHECKPOINT` records for ingestion, cloud upload, scene detection, frame extraction, emotion sampling, ML classification, rule evaluation, scene index storage, and database storage. |

## Files Added Or Updated

| File | Purpose |
| --- | --- |
| `tests/test_ml_classifier_quality.py` | Model metrics, preprocessing, probability, and latency gates. |
| `tests/test_rule_system.py` | Rule-based feature, tagging, filtering, fusion, and categorization tests. |
| `tests/test_end_to_end_pipeline.py` | Synthetic-video integration tests for the full processing path and failure logging. |
| `pipeline/classifiers/ml_classifier.py` | Added model-only `prepare_image_tensor()` and `predict_thumbnail()` hooks for direct quality evaluation. |
| `pipeline/processing/run_pipeline.py` | Added structured `PIPELINE_CHECKPOINT` logging at pipeline transitions and database failure logging. |
| `api/celery_worker.py` | Added pure `build_ai_metadata_from_scenes()` helper for testable categorization metadata. |
| `utils/logger.py` | Made console logging UTF-8 tolerant on Windows. |
