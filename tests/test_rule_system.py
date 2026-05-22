import json
import subprocess

import pytest

pytest.importorskip("numpy")
pytest.importorskip("pymongo")
pytest.importorskip("celery")

celery_worker = pytest.importorskip("api.celery_worker")
from pipeline.processing.run_pipeline import _fuse_predictions
from pipeline.processing.scene_type_detect import (
    SCENE_PROFILES,
    SceneSmoothing,
    classify_scene,
    extract_features,
)
from services import clip_service


def test_rule_feature_extraction_normalizes_extreme_values():
    features = extract_features(
        face_count=99,
        largest_face_ratio=4.0,
        face_aspect_ratio=8.0,
        mean_motion=9.0,
        peak_motion=12.0,
        motion_std=9.0,
        edge_density=3.0,
        sharpness=9000.0,
        text_density=1200.0,
        color_variance=4.0,
        color_temperature=2.5,
    )

    assert all(0.0 <= value <= 1.0 for value in features.values())
    assert features["face_presence"] == 1.0
    assert features["motion_consistency"] == 0.0
    assert features["color_temperature"] == 1.0


def test_rule_classifier_identifies_text_slide_profile():
    features = {
        feature_name: mu
        for feature_name, (mu, _sigma) in SCENE_PROFILES["text_slide"].items()
    }

    label, confidence, probabilities = classify_scene(features)

    assert label == "text_slide"
    assert 0.40 <= confidence <= 0.95
    assert probabilities["text_slide"] == max(probabilities.values())
    assert sum(probabilities.values()) == pytest.approx(1.0, abs=0.02)


def test_temporal_smoothing_penalizes_contradictory_single_frame_labels():
    smoother = SceneSmoothing(window=3)

    assert smoother.smooth("b-roll", 0.8) == ("b-roll", 0.8)
    label, confidence = smoother.smooth("testimonial", 0.8)

    assert label == "b-roll"
    assert confidence == pytest.approx(0.7)


def test_prediction_fusion_handles_agreement_and_conflict():
    agreed_label, agreed_conf, agreed_uncertain, agreed_action = _fuse_predictions(
        "presenter",
        0.72,
        "presenter",
        0.88,
    )
    assert agreed_label == "presenter"
    assert agreed_conf > 0.72
    assert agreed_uncertain is False
    assert agreed_action == "auto_organized_agreed"

    conflict_label, conflict_conf, conflict_uncertain, conflict_action = _fuse_predictions(
        "presenter",
        0.60,
        "text_slide",
        0.90,
    )
    assert conflict_label == "presenter"
    assert conflict_conf < 0.58
    assert conflict_uncertain is True
    assert conflict_action == "escalated_disagreement"


def test_metadata_tagging_detects_edited_filename_and_ffprobe_tags(monkeypatch):
    assert celery_worker.check_if_edited_by_filename("client_final_v2_export.mp4")
    assert not celery_worker.check_if_edited_by_filename("C0018_raw_take.mp4")

    def fake_check_output(cmd):
        assert "-show_format" in cmd
        return json.dumps({
            "format": {
                "tags": {
                    "encoder": "Lavf 60.0",
                    "software": "DaVinci Resolve",
                }
            }
        }).encode("utf-8")

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    assert celery_worker.check_if_edited_by_metadata("edited.mp4")

    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda _cmd: (_ for _ in ()).throw(RuntimeError("ffprobe missing")),
    )
    assert not celery_worker.check_if_edited_by_metadata("unreadable.mp4")


def test_categorization_metadata_prefers_variety_override_for_conflicting_rules():
    scenes = [
        {
            "scene_label": "b-roll",
            "scene_confidence": 0.91,
            "reviewed": True,
            "dominant_emotion_overall": "happy",
            "emotion_timeline": [{"emotion": "happy", "confidence": 80.0, "face_detected": True}],
            "faces": {"face_present_any": True},
            "scene_debug": {"agent_action": "auto_organized_high_conf"},
        },
        {
            "scene_label": "b-roll",
            "scene_confidence": 0.88,
            "reviewed": True,
            "dominant_emotion_overall": "happy",
            "emotion_timeline": [{"emotion": "happy", "confidence": 70.0, "face_detected": True}],
            "faces": {"face_present_any": True},
        },
        {
            "scene_label": "testimonial",
            "scene_confidence": 0.62,
            "reviewed": False,
            "emotion_timeline": [{"emotion": "neutral", "confidence": 65.0, "face_detected": True}],
            "faces": {"face_present_any": True},
        },
        {
            "scene_label": "presenter",
            "scene_confidence": 0.64,
            "reviewed": False,
            "emotion_timeline": [],
            "faces": {"face_present_any": False},
        },
    ]

    dominant_label, metadata = celery_worker.build_ai_metadata_from_scenes(scenes, "demo")

    assert dominant_label == "edited"
    assert metadata["dominant_label"] == "edited"
    assert metadata["action_taken"] == "auto_detected_by_variety"
    assert metadata["label_distribution"] == {
        "b-roll": 2,
        "testimonial": 1,
        "presenter": 1,
    }
    assert metadata["dominant_emotion"] == "happy"
    assert metadata["dominant_emotion_confidence"] == pytest.approx(75.0)
    assert metadata["face_scene_ratio"] == pytest.approx(0.75)


def test_categorization_metadata_handles_empty_scene_sets():
    dominant_label, metadata = celery_worker.build_ai_metadata_from_scenes([], "empty")

    assert dominant_label == "other"
    assert metadata["dominant_label"] == "other"
    assert metadata["total_scenes_detected"] == 0
    assert metadata["label_distribution"] == {}
    assert metadata["action_taken"] == "unknown"


def test_content_filtering_rules_build_safe_clip_queries(monkeypatch):
    class FakeCursor:
        def sort(self, *_args):
            return self

        def skip(self, *_args):
            return self

        def limit(self, *_args):
            return self

        def __iter__(self):
            return iter([])

    class FakeCollection:
        def __init__(self):
            self.queries = []

        def count_documents(self, query):
            self.queries.append(query)
            return 0

        def find(self, query):
            self.queries.append(query)
            return FakeCursor()

    fake_col = FakeCollection()
    monkeypatch.setattr(clip_service, "col", fake_col)

    result = clip_service.search_clips(
        {
            "scene_label": "b-roll",
            "emotion": "__NULL__",
            "reviewed": "true",
            "uncertain": "0",
            "min_duration": "1.5",
            "max_duration": "4.0",
            "page": "0",
        },
        limit=500,
    )

    query = result["query"]
    assert result["page"] == 1
    assert result["limit"] == 200
    assert query["scene_label"] == "b-roll"
    assert query["reviewed"] is True
    assert query["uncertain"] is False
    assert query["duration_sec"] == {"$gte": 1.5, "$lte": 4.0}
    assert query["$or"] == [
        {"dominant_emotion_overall": None},
        {"dominant_emotion_overall": {"$exists": False}},
    ]
