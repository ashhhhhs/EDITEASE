import json
import logging
from pathlib import Path

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")
FrameTimecode = pytest.importorskip("scenedetect.frame_timecode").FrameTimecode

from pipeline.processing import run_pipeline


def _write_synthetic_video(path: Path, fps: int = 10, seconds: int = 2) -> None:
    width, height = 96, 64
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"MJPG"),
        fps,
        (width, height),
    )
    assert writer.isOpened(), "OpenCV could not create synthetic test video"

    for frame_idx in range(fps * seconds):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        if frame_idx < fps:
            frame[:, :] = (30, 30, 220)
        else:
            frame[:, :] = (30, 180, 30)
        cv2.putText(
            frame,
            f"{frame_idx:02d}",
            (8, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        writer.write(frame)
    writer.release()


def _patch_pipeline_dependencies(monkeypatch, upsert_fn=None):
    class FakeSceneClassifier:
        def __init__(self):
            self.calls = []

        def classify(self, video_path, start_sec, end_sec, thumbnail_path):
            self.calls.append({
                "video_path": video_path,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "thumbnail_path": thumbnail_path,
            })
            return (
                "presenter",
                0.72,
                {
                    "classifier_used": "ml_pytorch",
                    "normalised_features": {"motion_mean": 0.25},
                },
            )

    class FakeRuleBasedClassifier:
        calls = []

        def classify(self, video_path, start_sec, end_sec, thumbnail_path):
            self.calls.append((video_path, start_sec, end_sec, thumbnail_path))
            return "presenter", 0.91, {"classifier_used": "rule_based_test"}

    fake_classifier = FakeSceneClassifier()
    monkeypatch.setattr(run_pipeline, "scene_classifier", fake_classifier)
    monkeypatch.setattr(run_pipeline, "RuleBasedClassifier", FakeRuleBasedClassifier)
    monkeypatch.setattr(
        run_pipeline.cloudinary_service,
        "upload_video",
        lambda _path, public_id=None: "https://example.test/video.mp4",
    )
    monkeypatch.setattr(
        run_pipeline.cloudinary_service,
        "upload_image",
        lambda path, public_id=None: f"https://example.test/{Path(path).name}",
    )
    monkeypatch.setattr(run_pipeline, "has_face", lambda _img_path: False)
    monkeypatch.setattr(
        run_pipeline,
        "find_scenes",
        lambda _video_path, threshold=None: [
            (FrameTimecode(0, fps=10), FrameTimecode(10, fps=10)),
            (FrameTimecode(10, fps=10), FrameTimecode(20, fps=10)),
        ],
    )

    if upsert_fn is not None:
        monkeypatch.setattr(run_pipeline, "upsert_scene_docs", upsert_fn)

    return fake_classifier, FakeRuleBasedClassifier


def _checkpoint_payloads(caplog):
    payloads = []
    for record in caplog.records:
        message = record.getMessage()
        if "PIPELINE_CHECKPOINT " not in message:
            continue
        payloads.append(json.loads(message.split("PIPELINE_CHECKPOINT ", 1)[1]))
    return payloads


def test_process_video_traces_raw_video_through_storage(tmp_path, monkeypatch, caplog):
    video_path = tmp_path / "raw_pipeline.avi"
    _write_synthetic_video(video_path)

    stored = {}

    def fake_upsert(docs, source_name=None):
        stored["docs"] = json.loads(json.dumps(docs))
        stored["source_name"] = source_name
        return len(docs)

    fake_classifier, fake_rule_classifier = _patch_pipeline_dependencies(
        monkeypatch,
        upsert_fn=fake_upsert,
    )
    progress_messages = []
    caplog.set_level(logging.INFO, logger="run_pipeline")

    run_pipeline.process_video(
        str(video_path),
        str(tmp_path),
        threshold=12.0,
        progress_callback=progress_messages.append,
    )

    index_path = tmp_path / "scene_indexes" / "raw_pipeline_scene_index.json"
    assert index_path.exists()
    scene_docs = json.loads(index_path.read_text(encoding="utf-8"))

    assert len(scene_docs) == 2
    assert stored["docs"] == scene_docs
    assert stored["source_name"] == "raw_pipeline_scene_index.json"
    assert len(fake_classifier.calls) == 2
    assert len(fake_rule_classifier.calls) == 2
    assert progress_messages

    for expected_id, doc in enumerate(scene_docs, start=1):
        assert doc["scene_id"] == expected_id
        assert doc["video"] == "raw_pipeline"
        assert doc["scene_label"] == "presenter"
        assert doc["cloudinary_url"] == "https://example.test/video.mp4"
        assert Path(doc["thumbnail"]).exists()
        assert doc["thumbnail_url"].startswith("https://example.test/")
        assert doc["reviewed"] is True
        assert doc["uncertain"] is False
        assert doc["faces"]["face_present_any"] is False
        assert len(doc["emotion_timeline"]) == 2
        assert doc["feature_vector_for_training"] == {"motion_mean": 0.25}
        assert doc["scene_debug"]["agent_action"] == "auto_organized_agreed"
        assert doc["scene_debug"]["rb_label"] == "presenter"

    checkpoints = _checkpoint_payloads(caplog)
    stages = {payload["stage"] for payload in checkpoints}
    assert {
        "ingestion",
        "cloud_upload",
        "scene_detection",
        "scene_processing",
        "frame_extraction",
        "emotion_sampling",
        "ml_classification",
        "rule_evaluation",
        "scene_index_storage",
        "database_storage",
    }.issubset(stages)
    assert any(
        payload["stage"] == "database_storage"
        and payload["status"] == "completed"
        and payload["upsert_count"] == 2
        for payload in checkpoints
    )


def test_process_video_logs_database_failures_and_reraises(tmp_path, monkeypatch, caplog):
    video_path = tmp_path / "db_failure.avi"
    _write_synthetic_video(video_path)

    def failing_upsert(_docs, source_name=None):
        raise RuntimeError("database unavailable")

    _patch_pipeline_dependencies(monkeypatch, upsert_fn=failing_upsert)
    caplog.set_level(logging.INFO, logger="run_pipeline")

    with pytest.raises(RuntimeError, match="database unavailable"):
        run_pipeline.process_video(str(video_path), str(tmp_path), threshold=12.0)

    checkpoints = _checkpoint_payloads(caplog)
    assert any(
        payload["stage"] == "database_storage"
        and payload["status"] == "failed"
        and "database unavailable" in payload["error"]
        for payload in checkpoints
    )
