import json
import os
from datetime import datetime

import cv2
import numpy as np

import config
from database.ingest_to_mongo import upsert_scene_docs
from pipeline.classifiers.ml_classifier import MLClassifier
from pipeline.classifiers.rule_based_classifier import RuleBasedClassifier
from pipeline.processing.detect_scenes import find_scenes
from pipeline.processing.emotion_detect import detect_emotion
from services import cloudinary_service
from utils.logger import setup_logger

logger = setup_logger("run_pipeline")

if config.CLASSIFIER_TYPE == "ml":
    scene_classifier = MLClassifier()
else:
    scene_classifier = RuleBasedClassifier()

VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")


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
    Temporal emotion sampling inside a scene.
    Enforces: if no face => emotion None.
    """
    sample_ratios = [0.2, 0.4, 0.6, 0.8]
    emotion_timeline = []
    emotion_votes = {}

    face_hits = 0
    total_samples = 0
    scene_duration = end_sec - start_sec

    for i, ratio in enumerate(sample_ratios):
        timestamp = start_sec + scene_duration * ratio
        thumb_name = f"scene_{scene_id:03d}_emo_{i}.jpg"
        thumb_path = os.path.join(thumbs_dir, thumb_name)

        if not extract_frame(video_path, timestamp, thumb_path):
            continue

        total_samples += 1
        face_ok = has_face(thumb_path)
        if face_ok:
            face_hits += 1

        if not face_ok:
            emotion_timeline.append({
                "time_ratio": ratio,
                "face_detected": False,
                "emotion": None,
                "confidence": None,
            })
            continue

        dominant, probs, conf = detect_emotion(thumb_path, enforce_detection=False)
        emotion_timeline.append({
            "time_ratio": ratio,
            "face_detected": True,
            "emotion": dominant if dominant else None,
            "confidence": conf if dominant else None,
        })

        if dominant:
            emotion_votes[dominant] = emotion_votes.get(dominant, 0) + 1

    dominant_overall = max(emotion_votes, key=emotion_votes.get) if emotion_votes else None
    face_present_any = face_hits > 0
    face_present_ratio = (face_hits / total_samples) if total_samples > 0 else 0.0

    return emotion_timeline, dominant_overall, face_present_any, face_present_ratio


def process_video(video_path, base_dir, threshold=config.SCENE_DETECT_THRESHOLD, file_hash: str | None = None, progress_callback=None):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    logger.info(f"Processing video: {video_name}")
    if progress_callback: progress_callback(f"Started analyzing {video_name}...")

    thumbs_dir = os.path.join(base_dir, "thumbnails", video_name)
    os.makedirs(thumbs_dir, exist_ok=True)

    # Use hash-safe public ID when available (auto_organize flow) to prevent
    # filename collisions at the first upload step — before any rename occurs.
    if file_hash:
        from database.organized_videos_schema import slugify
        safe_name = slugify(video_name)
        cloudinary_public_id = f"editease/videos/{file_hash}/{safe_name}"
    else:
        cloudinary_public_id = f"editease/videos/{video_name}"

    cloudinary_video_url = cloudinary_service.upload_video(
        video_path,
        public_id=cloudinary_public_id,
    )
    if cloudinary_video_url:
        logger.info("Video uploaded to Cloudinary: %s", cloudinary_video_url)
        if progress_callback: progress_callback("Secure backup complete. Detecting cuts...")
    else:
        logger.warning(
            "Cloudinary video upload failed for %s, continuing with local path fallback",
            video_name,
        )
        if progress_callback: progress_callback("Backup failed. Processing locally...")

    scenes = find_scenes(video_path, threshold=threshold)
    if not scenes:
        logger.warning("No scenes detected for %s, skipping", video_name)
        if progress_callback: progress_callback("No distinct scenes found.")
        return

    merged = []

    for idx, scene in enumerate(scenes, start=1):
        start = scene[0].get_seconds()
        end = scene[1].get_seconds()
        mid = (start + end) / 2

        thumb_name = f"{video_name}_scene_{idx:03d}.jpg"
        thumb_path = os.path.join(thumbs_dir, thumb_name)
        extract_frame(video_path, mid, thumb_path)

        thumbnail_url = cloudinary_service.upload_image(
            thumb_path,
            public_id=f"editease/thumbnails/{video_name}_scene_{idx:03d}",
        )

        emotion_timeline, dominant_overall, face_any, face_ratio = sample_emotions_over_scene(
            video_path=video_path,
            start_sec=start,
            end_sec=end,
            thumbs_dir=thumbs_dir,
            scene_id=idx,
        )

        scene_label, scene_conf, scene_debug = scene_classifier.classify(
            video_path=video_path,
            start_sec=start,
            end_sec=end,
            thumbnail_path=thumb_path,
        )

        # Agentic Decision Layer
        reviewed = False
        uncertain = True
        
        c_used = scene_debug.get("classifier_used", "")
        if "rule_based" in c_used:
            # Low confidence ML forced a fallback
            scene_debug["agent_action"] = "escalated_low_conf"
        else:
            if scene_conf >= 0.85:
                # High ML confidence -> Auto-organize
                reviewed = True
                uncertain = False
                scene_debug["agent_action"] = "auto_organized_high_conf"
            else:
                # Medium confidence (0.60 - 0.85) -> Ask fallback
                fallback_label, _, _ = RuleBasedClassifier().classify(video_path, start, end, thumb_path)
                if fallback_label == scene_label:
                    reviewed = True
                    uncertain = False
                    scene_debug["agent_action"] = "auto_organized_agreed"
                else:
                    scene_debug["agent_action"] = "escalated_disagreement"

        merged.append(make_json_safe({
            "video": video_name,
            "video_path": video_path,
            "cloudinary_url": cloudinary_video_url,
            "scene_id": idx,
            "start_sec": round(start, 3),
            "end_sec": round(end, 3),
            "duration_sec": round(end - start, 3),
            "thumbnail": thumb_path,
            "thumbnail_url": thumbnail_url,
            "scene_label_auto": scene_label,
            "dominant_emotion_auto": dominant_overall,
            "scene_label": scene_label,
            "dominant_emotion_overall": dominant_overall,
            "scene_confidence": scene_conf,
            "scene_debug": scene_debug,
            "faces": {
                "face_present_any": face_any,
                "face_present_ratio": round(face_ratio, 3),
            },
            "emotion_timeline": emotion_timeline,
            "created_at": datetime.now().isoformat(),
            "reviewed": reviewed,
            "uncertain": uncertain,
            "notes": "",
            "manual_scene_label": None,
            "manual_emotion": None,
        }))

        logger.info(
            "Scene %s: type=%s | dominant_emotion=%s",
            idx,
            scene_label,
            dominant_overall,
        )
        
        if progress_callback:
            emo_str = f"Emotion: {dominant_overall}." if dominant_overall else "No faces."
            label_disp = scene_label.replace("_", " ").title()
            progress_callback(f"Scene {idx}/{len(scenes)}: Classified as {label_disp}. {emo_str}")

    out_dir = os.path.join(base_dir, "scene_indexes")
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, f"{video_name}_scene_index.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)

    logger.info("Saved scene index to %s", out_path)

    upsert_count = upsert_scene_docs(merged, source_name=os.path.basename(out_path))
    logger.info("Upserted %s scenes into MongoDB for %s", upsert_count, video_name)
    if progress_callback: progress_callback("Indexing timeline directly into database...")


def run_batch():
    data_dir = config.DATA_DIR

    if not data_dir.exists():
        logger.error("data/ folder not found at %s", data_dir)
        return

    videos = [
        os.path.join(data_dir, filename)
        for filename in os.listdir(data_dir)
        if filename.lower().endswith(VIDEO_EXTENSIONS)
    ]

    logger.info("Found %s videos", len(videos))

    for video in videos:
        process_video(video, str(config.BASE_DIR))


if __name__ == "__main__":
    run_batch()
