from pipeline.classifiers.base_classifier import BaseClassifier
from pipeline.processing.scene_type_detect import detect_scene_type

class RuleBasedClassifier(BaseClassifier):
    """
    Current heuristic/rule-based strategy for scene classification.
    Wraps the existing logic in a standard interface.
    """
    def classify(
        self, video_path: str, start_sec: float, end_sec: float, thumbnail_path: str,
        features: dict | None = None, raw_signals: dict | None = None,
    ) -> tuple[str, float, dict]:
        return detect_scene_type(
            video_path, start_sec, end_sec, thumbnail_path,
            features=features, raw_signals=raw_signals,
        )
