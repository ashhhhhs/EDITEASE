import os
import json
from datetime import datetime
import cv2
import numpy as np

from pipeline.processing.detect_scenes import find_scenes
from pipeline.processing.emotion_detect import detect_emotion
from utils.logger import setup_logger

logger = setup_logger("run_pipeline")

import config
from pipeline.classifiers.rule_based_classifier import RuleBasedClassifier
from pipeline.classifiers.ml_classifier import MLClassifier

if config.CLASSIFIER_TYPE == "ml":
    scene_classifier = MLClassifier()
else:
    scene_classifier = RuleBasedClassifier()

VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")


# ---------------- HELPERS ----------------
def has_face(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return False
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(
        os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    )
    faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
    return len(faces) > 0


def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def extract_frame(video_path, timestamp, out_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False

    fps = cap.get(cv2.CAP_PROP_FPS)
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if fps <= 0 or total <= 0:
        cap.release()
        return False

    frame_idx = int(timestamp * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()

    if ret and frame is not None:
        cv2.imwrite(out_path, frame)
        return True
    return False


def sample_emotions_over_scene(video_path, start_sec, end_sec, thumbs_dir, scene_id):
    """
    Temporal emotion sampling inside a scene (Option A)
    Enforces: if no face => emotion None
    Also records face_detected flag explicitly.
    """
    sample_ratios = [0.2, 0.4, 0.6, 0.8]
    emotion_timeline = []
    emotion_votes = {}

    face_hits = 0
    total_samples = 0

    scene_duration = end_sec - start_sec

    for i, r in enumerate(sample_ratios):
        t = start_sec + scene_duration * r
        thumb_name = f"scene_{scene_id:03d}_emo_{i}.jpg"
        thumb_path = os.path.join(thumbs_dir, thumb_name)

        if not extract_frame(video_path, t, thumb_path):
            continue

        total_samples += 1

        face_ok = has_face(thumb_path)
        if face_ok:
            face_hits += 1

        if not face_ok:
            emotion_timeline.append({
                "time_ratio": r,
                "face_detected": False,
                "emotion": None,
                "confidence": None
            })
            continue

        dominant, probs, conf = detect_emotion(thumb_path, enforce_detection=False)

        emotion_timeline.append({
            "time_ratio": r,
            "face_detected": True,
            "emotion": dominant if dominant else None,
            "confidence": conf if dominant else None
        })

        if dominant:
            emotion_votes[dominant] = emotion_votes.get(dominant, 0) + 1

    dominant_overall = max(emotion_votes, key=emotion_votes.get) if emotion_votes else None
    face_present_any = face_hits > 0
    face_present_ratio = (face_hits / total_samples) if total_samples > 0 else 0.0

    return emotion_timeline, dominant_overall, face_present_any, face_present_ratio

# ---------------- MAIN VIDEO PIPELINE ----------------
def process_video(video_path, base_dir, threshold=config.SCENE_DETECT_THRESHOLD):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    logger.info(f"🎬 Processing: {video_name}")

    thumbs_dir = os.path.join(base_dir, "thumbnails", video_name)
    os.makedirs(thumbs_dir, exist_ok=True)

    scenes = find_scenes(video_path, threshold=threshold)
    if not scenes:
        logger.warning(f"⚠️ No scenes detected for {video_name} — skipping.")
        return

    merged = []

    for idx, scene in enumerate(scenes, start=1):
        start = scene[0].get_seconds()
        end = scene[1].get_seconds()
        mid = (start + end) / 2

        thumb_name = f"{video_name}_scene_{idx:03d}.jpg"
        thumb_path = os.path.join(thumbs_dir, thumb_name)
        extract_frame(video_path, mid, thumb_path)

        emotion_timeline, dominant_overall, face_any, face_ratio = sample_emotions_over_scene(
            video_path=video_path,
            start_sec=start,
            end_sec=end,
            thumbs_dir=thumbs_dir,
            scene_id=idx
        )


        # Scene type (Pluggable logic)
        scene_label, scene_conf, scene_debug = scene_classifier.classify(
            video_path=video_path,
            start_sec=start,
            end_sec=end,
            thumbnail_path=thumb_path
        )

        merged.append(make_json_safe({
            "video": video_name,
            "video_path": video_path,  # ✅ REQUIRED for /export
            "scene_id": idx,
            "start_sec": round(start, 3),
            "end_sec": round(end, 3),
            "duration_sec": round(end - start, 3),

            "thumbnail": thumb_path,

            # auto outputs preserved
            "scene_label_auto": scene_label,
            "dominant_emotion_auto": dominant_overall,

            # current/final fields used by UI/search
            "scene_label": scene_label,
            "dominant_emotion_overall": dominant_overall,

            "scene_confidence": scene_conf,
            "scene_debug": scene_debug,

            "faces": {
                "face_present_any": face_any,
                "face_present_ratio": round(face_ratio, 3)
            },

            "emotion_timeline": emotion_timeline,

            # review fields
            "created_at": datetime.now().isoformat(),
            "reviewed": False,
            "uncertain": False,
            "notes": "",
            "manual_scene_label": None,
            "manual_emotion": None
        }))

        logger.info(
                f"📌 Scene {idx}: "
                f"type={scene_label} | "
                f"dominant_emotion={dominant_overall}"
            )

    out_dir = os.path.join(base_dir, "scene_indexes")
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, f"{video_name}_scene_index.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)

    logger.info(f"✅ Saved index → {out_path}")


# ---------------- BATCH RUNNER ----------------
def run_batch():
    data_dir = config.DATA_DIR

    if not data_dir.exists():
        logger.error(f"❌ data/ folder not found at {data_dir}")
        return

    videos = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.lower().endswith(VIDEO_EXTENSIONS)
    ]

    logger.info(f"📁 Found {len(videos)} videos")

    for video in videos:
        process_video(video, str(config.BASE_DIR))


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    run_batch()
