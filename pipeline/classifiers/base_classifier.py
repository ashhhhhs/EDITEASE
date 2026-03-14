class BaseClassifier:
    """
    Abstract interface for scene type classification.
    Any future classification strategy (rules, ML, API) must implement this.
    """
    def classify(self, video_path: str, start_sec: float, end_sec: float, thumbnail_path: str) -> tuple[str, float, dict]:
        """
        Classify a scene.
        Returns:
            scene_label: str
            confidence: float
            debug_info: dict
        """
        raise NotImplementedError("classify() must be implemented by subclass")
