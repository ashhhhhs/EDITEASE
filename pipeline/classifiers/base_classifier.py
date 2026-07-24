class BaseClassifier:
    """
    Abstract interface for scene type classification.
    Any future classification strategy (rules, ML, API) must implement this.
    """
    def classify(
        self, video_path: str, start_sec: float, end_sec: float, thumbnail_path: str,
        features: dict | None = None, raw_signals: dict | None = None,
    ) -> tuple[str, float, dict]:
        """
        Classify a scene.

        Args:
            features / raw_signals: optionally precomputed by
                pipeline.processing.scene_type_detect.compute_scene_features().
                Callers that already hold the scene's feature vector pass it in so
                the thumbnail is not re-read and motion is not re-sampled.

        Returns:
            scene_label: str
            confidence: float
            debug_info: dict
        """
        raise NotImplementedError("classify() must be implemented by subclass")
