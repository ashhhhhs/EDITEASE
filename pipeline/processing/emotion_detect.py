import os
import sys
from deepface import DeepFace

from utils.logger import setup_logger
from utils.exceptions import EmotionDetectionError

logger = setup_logger("emotion_detect")

def detect_emotion(image_path, enforce_detection=False):
    """
    Returns:
      dominant_emotion (str | None)
      emotion_probs (dict | None)
      confidence (float | None)  # dominant emotion probability
    """
    try:
        result = DeepFace.analyze(
            img_path=image_path,
            actions=["emotion"],
            enforce_detection=enforce_detection  # False = won't crash if no face
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
