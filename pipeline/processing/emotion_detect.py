import os
import sys

import config
from utils.logger import setup_logger
from utils.exceptions import EmotionDetectionError

logger = setup_logger("emotion_detect")

DeepFace = None
_deepface_import_error = None


def _ensure_deepface_available():
    global DeepFace, _deepface_import_error
    if DeepFace is not None or _deepface_import_error is not None:
        return

    try:
        from deepface import DeepFace as _DeepFace
        DeepFace = _DeepFace
    except Exception as exc:
        _deepface_import_error = exc
        logger.error(
            "DeepFace import failed: %s. Emotion detection will be skipped.",
            exc,
        )


def detect_emotion(image_path, enforce_detection=False, detector_backend=None):
    """
    Args:
      detector_backend: which face detector verifies a face before the emotion
        model runs. Defaults to config.EMOTION_DETECTOR_BACKEND. This is the
        gate that makes enforce_detection meaningful — with DeepFace's own
        "opencv" default it shares the Haar blind spot of the caller's cheap
        pre-filter, so foliage gets scored as a sad face.

    Returns:
      dominant_emotion (str | None)
      emotion_probs (dict | None)
      confidence (float | None)  # dominant emotion probability
    """
    _ensure_deepface_available()
    if _deepface_import_error is not None:
        return None, None, None

    if detector_backend is None:
        detector_backend = getattr(config, "EMOTION_DETECTOR_BACKEND", "retinaface")

    try:
        result = DeepFace.analyze(
            img_path=image_path,
            actions=["emotion"],
            detector_backend=detector_backend,
            enforce_detection=enforce_detection,  # False = won't crash if no face
            silent=True,
        )

        # DeepFace may return list[dict] or dict depending on version/settings
        if isinstance(result, list):
            result = result[0]

        dominant = result.get("dominant_emotion")
        probs = result.get("emotion")  # dict: {'happy':..., 'sad':..., ...}
        confidence = None
        if isinstance(probs, dict) and dominant in probs:
            confidence = float(probs[dominant])

        return dominant, probs, confidence

    except Exception as e:
        logger.error(f"❌ Emotion detection failed for {image_path}\n   Reason: {e}")
        # Note: We could raise EmotionDetectionError here depending on strictness
        # but the pipeline currently expects None returns for missing faces.
        return None, None, None


if __name__ == "__main__":
   
    script_folder = os.path.dirname(os.path.abspath(__file__))
    test_img = os.path.join(script_folder, "test_frame.jpg")

    dominant, probs, conf = detect_emotion(test_img)

    logger.info("=== RESULT ===")
    logger.info(f"Image: {test_img}")
    logger.info(f"Dominant Emotion: {dominant}")
    logger.info(f"Confidence: {conf}")
    logger.debug(f"All эмо probs: {probs}")
