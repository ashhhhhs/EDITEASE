import json
import os
from datetime import datetime

import cv2
import numpy as np

import config
from database.ingest_to_mongo import upsert_scene_docs
from pipeline.classifiers.rule_based_classifier import RuleBasedClassifier
from pipeline.processing.scene_type_detect import detect_faces_info
from pipeline.processing.detect_scenes import find_scenes
from pipeline.processing.emotion_detect import detect_emotion
from services import cloudinary_service
from utils.logger import setup_logger

logger = setup_logger("run_pipeline")

if config.CLASSIFIER_TYPE == "ml":
    try:
        from pipeline.classifiers.ml_classifier import MLClassifier
        scene_classifier = MLClassifier()
    except ImportError:
        logger.warning("torch/torchvision unavailable — falling back to rule-based classifier")
        scene_classifier = RuleBasedClassifier()
else:
    scene_classifier = RuleBasedClassifier()

VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")

# Built once at import. Constructing a CascadeClassifier re-parses the XML from
# disk, and has_face() runs up to 12 times per scene for every scene in a video.
_FACE_CASCADE = cv2.CascadeClassifier(
    os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")  # type: ignore
)

# ---------------------------------------------------------------------------
# Confidence bands for the agentic decision layer
# ---------------------------------------------------------------------------
# Sourced from config.py so tuning a default there actually changes pipeline
# behaviour. Previously these re-read the env directly, which silently ignored
# any change made in config.py.
CONF_AUTO_HIGH   = config.CONF_AUTO_HIGH   # ML auto-accepts above this
CONF_FUSE_LOW    = config.CONF_FUSE_LOW    # fusion below this → uncertain
ML_WEIGHT        = config.ML_WEIGHT        # ML share in weighted fusion
RULE_WEIGHT      = 1.0 - ML_WEIGHT
AUDIENCE_REACTION_MIN_FACES = config.AUDIENCE_REACTION_MIN_FACES


# ---------------------------------------------------------------------------
# Face / emotion helpers
# ---------------------------------------------------------------------------

def has_face(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return False
    gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = _FACE_CASCADE
    h, w = gray.shape
    # Face must be at least 6% of the smaller frame dimension — kills tiny
    # texture hits (leaves, rocks, building details) that Haar misreads as faces.
    min_side = max(60, int(min(h, w) * 0.06))
    faces = cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=10, minSize=(min_side, min_side)
    )
    if len(faces) == 0:
        return False
    # Require face to occupy ≥1.5% of frame area before we trust it.
    frame_area = float(h * w)
    return any((fw * fh) / frame_area >= 0.015 for (_, _, fw, fh) in faces)


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


def log_pipeline_checkpoint(stage: str, video_name: str, status: str, **fields):
    """Emit a structured checkpoint for cross-stage pipeline tracing."""
    payload = {
        "stage": stage,
        "video": video_name,
        "status": status,
        **fields,
    }
    logger.info(
        "PIPELINE_CHECKPOINT %s",
        json.dumps(make_json_safe(payload), sort_keys=True, default=str),
    )


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------

def extract_frame(video_path, timestamp, out_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False

    fps   = cap.get(cv2.CAP_PROP_FPS)
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if fps <= 0 or total <= 0:
        cap.release()
        return False

    frame_idx = int(timestamp * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()

    if ret and frame is not None:
        # Resize to max-width 1280 to prevent AI models and OpenCV hanging on 4K/8K footage
        height, width = frame.shape[:2]
        if width > 1280:
            scale      = 1280 / width
            frame      = cv2.resize(frame, (1280, int(height * scale)), interpolation=cv2.INTER_AREA)

        cv2.imwrite(out_path, frame)
        return True
    return False


# ---------------------------------------------------------------------------
# Adaptive emotion sampling
# ---------------------------------------------------------------------------

MIN_EMOTION_FACE_HITS = 2
MIN_EMOTION_FACE_RATIO = 0.40

# `neutral` is the emotion model's no-signal class: on subdued expressions (sad footage
# especially) it wins the per-frame argmax by a very small margin, so a plurality vote reads
# "narrowly ahead everywhere" as "certainly neutral". Require it to lead the runner-up by this
# share of the aggregated distribution before it takes the scene.
NEUTRAL_MARGIN = 0.10

# A single scalar `dominant_emotion` hides the case where the subject's expression genuinely
# changes mid-scene (e.g. neutral → sad). We don't split the scene — scene detection is
# cut-based and an emotion change isn't a cut — but we flag the arc so a reviewer can see it.
SHIFT_MIN_CONF = 55.0       # a frame must be at least this confident to count toward the arc
SHIFT_MIN_CONFIDENT = 3     # need this many confident frames before an arc is judged at all


def _get_sample_count(duration_seconds: float) -> int:
    """Scale sample count to scene length — avoids under-sampling long scenes."""
    if duration_seconds < 3:
        return 2
    if duration_seconds < 10:
        return 4
    if duration_seconds < 30:
        return 8
    return 12   # cap — diminishing returns beyond this


def _sample_weight(i: int, total: int) -> float:
    """Edge samples carry more editorial weight — first and last get 1.5×, the rest 1.0×."""
    return 1.5 if i == 0 or i == total - 1 else 1.0


def _resolve_dominant(emotion_votes: dict[str, float]):
    """
    Pick the scene emotion from the aggregated distribution, with a margin rule on `neutral`.

    Neutral absorbs probability mass whenever no expression is strongly present, so a bare
    argmax reports it for subdued-but-real emotions. When it leads by less than
    NEUTRAL_MARGIN, the runner-up carries the scene instead.
    """
    if not emotion_votes:
        return None

    ranked = sorted(emotion_votes.items(), key=lambda kv: kv[1], reverse=True)
    top_label, top_score = ranked[0]
    if top_label != "neutral" or len(ranked) == 1:
        return top_label

    runner_label, runner_score = ranked[1]
    total = sum(emotion_votes.values()) or 1.0
    if (top_score - runner_score) / total < NEUTRAL_MARGIN:
        return runner_label
    return top_label


def _confidence_weighted_top(frames):
    """Given (label, confidence) pairs, return the label carrying the most confidence mass."""
    agg: dict[str, float] = {}
    for label, conf in frames:
        agg[label] = agg.get(label, 0.0) + conf
    return max(agg, key=agg.get) if agg else None


def detect_emotion_shift(emotion_timeline):
    """
    Detect a genuine mid-scene emotion change from the per-frame timeline.

    The timeline is temporally ordered. We keep only confident, face-present frames, split
    them into an earlier and a later half, and compare each half's dominant emotion. A change
    between the two halves — backed by confident evidence on both sides — is reported as a shift.

    Returns: {"shifted": bool, "from": str | None, "to": str | None}. The `from`/`to` labels are
    populated only when `shifted` is True.
    """
    result = {"shifted": False, "from": None, "to": None}

    confident = [
        (f.get("emotion"), float(f.get("confidence")))
        for f in (emotion_timeline or [])
        if f.get("face_detected")
        and f.get("emotion")
        and f.get("confidence") is not None
        and float(f.get("confidence")) >= SHIFT_MIN_CONF
    ]
    if len(confident) < SHIFT_MIN_CONFIDENT:
        return result

    # First half gets the extra frame when the count is odd, so the split never leaves the
    # later half empty.
    mid = (len(confident) + 1) // 2
    first, second = confident[:mid], confident[mid:]
    if not first or not second:
        return result

    from_emotion = _confidence_weighted_top(first)
    to_emotion = _confidence_weighted_top(second)
    if from_emotion and to_emotion and from_emotion != to_emotion:
        result.update(shifted=True)
        result["from"] = from_emotion
        result["to"] = to_emotion
    return result


def sample_emotions_over_scene(video_path, start_sec, end_sec, thumbs_dir, scene_id):
    """
    Temporal emotion sampling inside a scene.
    - Sample count adapts to scene duration.
    - Frames at the start/end are weighted more heavily for dominant emotion
      (editorially more significant than mid-scene).
    - Votes accumulate the full per-frame probability distribution, not just the argmax, so a
      weak win contributes proportionally less than a confident one.
    - Enforces: if face evidence is weak => dominant emotion None.
    """
    scene_duration = end_sec - start_sec
    n_samples = _get_sample_count(scene_duration)

    # Evenly spaced ratios; keep away from exact edges (0 / 1) to avoid black frames.
    sample_ratios = np.linspace(0.1, 0.9, n_samples).tolist()

    emotion_timeline  = []
    emotion_votes: dict[str, float] = {}
    face_hits         = 0
    total_samples     = 0

    for i, ratio in enumerate(sample_ratios):
        timestamp  = start_sec + scene_duration * ratio
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
                "time_ratio"   : round(ratio, 3),
                "face_detected": False,
                "emotion"      : None,
                "confidence"   : None,
            })
            continue

        dominant, probs, conf = detect_emotion(thumb_path, enforce_detection=True)
        emotion_timeline.append({
            "time_ratio"   : round(ratio, 3),
            "face_detected": True,
            "emotion"      : dominant if dominant else None,
            "confidence"   : conf     if dominant else None,
            # Full per-frame distribution, not just the winner. _resolve_dominant
            # aggregates over the whole distribution, so without this the voting
            # rule and NEUTRAL_MARGIN cannot be re-tuned offline — every
            # experiment would mean re-running DeepFace over every video.
            "probs": (
                {k: round(float(v), 2) for k, v in probs.items()}
                if isinstance(probs, dict) and probs else None
            ),
        })

        w = _sample_weight(i, n_samples)
        if isinstance(probs, dict) and probs:
            # Spread the frame's weight across the distribution: a 0.41/0.38 frame is close to
            # a tie and should be counted as one, not as a clean win for the leader.
            total_prob = sum(float(p) for p in probs.values()) or 1.0
            for label, p in probs.items():
                emotion_votes[label] = emotion_votes.get(label, 0.0) + w * (float(p) / total_prob)
        elif dominant:
            # Older DeepFace versions may hand back a label with no distribution.
            emotion_votes[dominant] = emotion_votes.get(dominant, 0.0) + w

    face_present_any    = face_hits > 0
    face_present_ratio  = (face_hits / total_samples) if total_samples > 0 else 0.0
    has_emotion_evidence = (
        face_hits >= MIN_EMOTION_FACE_HITS
        and face_present_ratio >= MIN_EMOTION_FACE_RATIO
    )
    dominant_overall = _resolve_dominant(emotion_votes) if has_emotion_evidence else None

    return emotion_timeline, dominant_overall, face_present_any, face_present_ratio


# ---------------------------------------------------------------------------
# Confidence-weighted fusion (ML + rule-based)
# ---------------------------------------------------------------------------

def _fuse_predictions(
    ml_label: str,   ml_conf: float,
    rb_label: str,   rb_conf: float,
) -> tuple[str, float, bool, str]:
    """
    Combine ML and rule-based predictions when ML confidence is in the
    medium band [CONF_FUSE_LOW, CONF_AUTO_HIGH).

    Returns: (label, fused_confidence, uncertain, agent_action)
    """
    if ml_label == rb_label:
        # Both agree — confidence is slightly boosted.
        fused = min(0.95, (ml_conf * ML_WEIGHT + rb_conf * RULE_WEIGHT) + 0.05)
        return ml_label, round(fused, 4), False, "auto_organized_agreed"

    # Disagreement — weighted vote.
    scores: dict[str, float] = {}
    scores[ml_label]  = ml_conf * ML_WEIGHT
    scores[rb_label]  = rb_conf * RULE_WEIGHT

    winner      = max(scores, key=scores.get)  # type: ignore
    fused_conf  = round(scores[winner], 4)
    uncertain   = fused_conf < CONF_FUSE_LOW

    action = "escalated_disagreement" if uncertain else "auto_organized_fused"
    return winner, fused_conf, uncertain, action


def _face_count_from_debug(scene_debug: dict) -> int | None:
    raw_signals = scene_debug.get("raw_signals") if isinstance(scene_debug, dict) else None
    if not isinstance(raw_signals, dict):
        return None
    try:
        return int(raw_signals.get("face_count"))
    except (TypeError, ValueError):
        return None


def _detect_face_count_for_gate(thumbnail_path: str | None) -> int | None:
    if not thumbnail_path or not os.path.exists(thumbnail_path):
        return None

    img = cv2.imread(thumbnail_path)
    if img is None:
        return None

    face_count, _largest_face_ratio, _face_aspect_ratio = detect_faces_info(img)
    return int(face_count)


def _apply_audience_reaction_face_gate(
    scene_label: str,
    scene_conf: float,
    scene_debug: dict,
    *,
    face_any: bool,
    face_ratio: float,
    thumbnail_path: str | None,
) -> tuple[str, float, dict, bool]:
    """
    Audience reaction must show a visible crowd. This final gate prevents a
    high-confidence ML prediction from bypassing the rule-based face-count rule.
    """
    if scene_label != "audience_reaction":
        return scene_label, scene_conf, scene_debug, False

    gated_debug = dict(scene_debug)
    face_count = _face_count_from_debug(gated_debug)
    face_count_source = "classifier_debug"

    if face_count is None:
        face_count = _detect_face_count_for_gate(thumbnail_path)
        face_count_source = "thumbnail_detector"

    should_block = (
        not face_any
        or face_count is None
        or face_count < AUDIENCE_REACTION_MIN_FACES
    )

    gated_debug["face_gate"] = {
        "label_checked": "audience_reaction",
        "passed": not should_block,
        "deepface_face_present": bool(face_any),
        "deepface_face_ratio": round(float(face_ratio or 0.0), 3),
        "detected_face_count": face_count,
        "min_face_count": AUDIENCE_REACTION_MIN_FACES,
        "face_count_source": face_count_source,
    }

    if not should_block:
        return scene_label, scene_conf, gated_debug, False

    gated_debug["face_gate"]["blocked_label"] = scene_label
    gated_debug["face_gate"]["reason"] = "audience_reaction_requires_3_or_more_faces"
    gated_debug["blocked_label"] = scene_label
    gated_debug["blocked_conf"] = round(float(scene_conf), 4)

    fallback_conf = max(0.0, min(float(scene_conf), CONF_FUSE_LOW - 0.01))
    return "other", round(fallback_conf, 4), gated_debug, True


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_video(
    video_path,
    base_dir,
    threshold=config.SCENE_DETECT_THRESHOLD,
    file_hash: str | None = None,
    user_id: str | None = None,
    progress_callback=None,
):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    logger.info("Processing video: %s", video_name)
    log_pipeline_checkpoint(
        "ingestion",
        video_name,
        "started",
        video_path=video_path,
        base_dir=base_dir,
        threshold=threshold,
    )
    if progress_callback:
        progress_callback(f"Found video '{video_name}'. Preparing for deep analysis...")

    thumbs_dir = os.path.join(base_dir, "thumbnails", video_name)
    os.makedirs(thumbs_dir, exist_ok=True)

    if file_hash:
        from database.organized_videos_schema import slugify
        safe_name            = slugify(video_name)
        cloudinary_public_id = f"editease/videos/{file_hash}/{safe_name}"
    else:
        cloudinary_public_id = f"editease/videos/{video_name}"

    logger.info("DEBUG: [STEP 1] Starting Cloudinary upload for %s", video_name)
    log_pipeline_checkpoint(
        "cloud_upload",
        video_name,
        "started",
        public_id=cloudinary_public_id,
    )
    cloudinary_video_url = cloudinary_service.upload_video(
        video_path, public_id=cloudinary_public_id,
    )
    if cloudinary_video_url:
        logger.info("Video uploaded to Cloudinary: %s", cloudinary_video_url)
        log_pipeline_checkpoint(
            "cloud_upload",
            video_name,
            "completed",
            cloudinary_url=cloudinary_video_url,
        )
        if progress_callback:
            progress_callback("Cloud backup complete. Initiating cut detection...")
    else:
        logger.warning(
            "Cloudinary upload failed for %s — continuing with local path.", video_name,
        )
        log_pipeline_checkpoint("cloud_upload", video_name, "fallback_local")
        if progress_callback:
            progress_callback("Backup failed. Proceeding with local cut detection...")

    logger.info("DEBUG: [STEP 2] Scene detection for %s", video_name)
    log_pipeline_checkpoint(
        "scene_detection",
        video_name,
        "started",
        threshold=threshold,
    )
    if progress_callback:
        progress_callback("Scanning video to detect cuts and transitions...")
    scenes = find_scenes(video_path, threshold=threshold)
    if not scenes:
        logger.warning("No scenes detected for %s, skipping.", video_name)
        log_pipeline_checkpoint("scene_detection", video_name, "empty")
        if progress_callback:
            progress_callback("Finished scanning. No distinct scenes found.")
        return

    merged = []

    logger.info("DEBUG: [STEP 3] Scene processing loop — %s scenes found.", len(scenes))
    log_pipeline_checkpoint(
        "scene_detection",
        video_name,
        "completed",
        scene_count=len(scenes),
    )
    if progress_callback:
        progress_callback(f"Cut detection complete. Found {len(scenes)} distinct scenes to analyze.")

    for idx, scene in enumerate(scenes, start=1):
        logger.info("DEBUG: ---> Scene %s / %s", idx, len(scenes))
        start = scene[0].get_seconds()
        end   = scene[1].get_seconds()
        mid   = (start + end) / 2
        log_pipeline_checkpoint(
            "scene_processing",
            video_name,
            "started",
            scene_id=idx,
            start_sec=round(start, 3),
            end_sec=round(end, 3),
        )

        # ── Thumbnail ──────────────────────────────────────────────────
        thumb_name = f"{video_name}_scene_{idx:03d}.jpg"
        thumb_path = os.path.join(thumbs_dir, thumb_name)
        thumb_ok = extract_frame(video_path, mid, thumb_path)
        log_pipeline_checkpoint(
            "frame_extraction",
            video_name,
            "completed" if thumb_ok else "failed",
            scene_id=idx,
            timestamp=round(mid, 3),
            thumbnail=thumb_path,
        )

        thumbnail_url = None
        if thumb_ok:
            thumbnail_url = cloudinary_service.upload_image(
                thumb_path,
                public_id=f"editease/thumbnails/{video_name}_scene_{idx:03d}",
            )

        # ── Emotion sampling ───────────────────────────────────────────
        if progress_callback:
            progress_callback(f"Analyzing Scene {idx}/{len(scenes)}: Extracting frames and checking for faces...")

        emotion_timeline, dominant_overall, face_any, face_ratio = sample_emotions_over_scene(
            video_path=video_path,
            start_sec=start,
            end_sec=end,
            thumbs_dir=thumbs_dir,
            scene_id=idx,
        )
        emotion_shift = detect_emotion_shift(emotion_timeline)
        log_pipeline_checkpoint(
            "emotion_sampling",
            video_name,
            "completed",
            scene_id=idx,
            samples=len(emotion_timeline),
            face_present=face_any,
            face_ratio=round(face_ratio, 3),
            dominant_emotion=dominant_overall,
            emotion_shift=emotion_shift["shifted"],
        )

        if progress_callback:
            if face_any:
                emo_text = dominant_overall if dominant_overall else 'complex emotions'
                if emotion_shift["shifted"]:
                    emo_text = f"{emotion_shift['from']} → {emotion_shift['to']}"
                progress_callback(f"Scene {idx}/{len(scenes)}: Found faces! Detected emotion: {emo_text}. Classifying scene type...")
            else:
                progress_callback(f"Scene {idx}/{len(scenes)}: No faces detected. Classifying scene type...")

        # ── Classification ─────────────────────────────────────────────
        scene_label, scene_conf, scene_debug = scene_classifier.classify(
            video_path=video_path,
            start_sec=start,
            end_sec=end,
            thumbnail_path=thumb_path,
        )
        log_pipeline_checkpoint(
            "ml_classification",
            video_name,
            "completed",
            scene_id=idx,
            label=scene_label,
            confidence=round(float(scene_conf), 4),
            classifier_used=scene_debug.get("classifier_used", "unknown"),
        )

        scene_label, scene_conf, scene_debug, face_gate_blocked = _apply_audience_reaction_face_gate(
            scene_label,
            scene_conf,
            scene_debug,
            face_any=face_any,
            face_ratio=face_ratio,
            thumbnail_path=thumb_path,
        )

        # ── Agentic Decision Layer ─────────────────────────────────────
        reviewed  = False
        uncertain = True
        c_used    = scene_debug.get("classifier_used", "")

        if face_gate_blocked:
            scene_debug["agent_action"] = "escalated_face_gate"

        elif scene_conf >= CONF_AUTO_HIGH:
            # High-confidence (ML or Rule-Based) — auto-accept.
            reviewed  = True
            uncertain = False
            scene_debug["agent_action"] = "auto_organized_high_conf"

        elif "rule_based" in c_used:
            # ML fell back and confidence is still below high threshold — escalate.
            scene_debug["agent_action"] = "escalated_ml_fallback"

        else:
            # Medium confidence — run weighted fusion with rule-based.
            rb_label, rb_conf, rb_debug = RuleBasedClassifier().classify(
                video_path, start, end, thumb_path,
            )
            scene_label, scene_conf, uncertain, action = _fuse_predictions(
                scene_label, scene_conf, rb_label, rb_conf,
            )
            reviewed = not uncertain
            scene_debug["agent_action"]  = action
            scene_debug["rb_label"]      = rb_label
            scene_debug["rb_conf"]       = round(rb_conf, 4)
            scene_debug["fused_conf"]    = round(scene_conf, 4)

        log_pipeline_checkpoint(
            "rule_evaluation",
            video_name,
            "completed",
            scene_id=idx,
            label=scene_label,
            confidence=round(float(scene_conf), 4),
            reviewed=reviewed,
            uncertain=uncertain,
            action=scene_debug.get("agent_action", "unknown"),
        )

        # ── Build scene record ─────────────────────────────────────────
        merged.append(make_json_safe({
            "video"              : video_name,
            "uploaded_by"         : user_id,
            "video_path"         : video_path,
            "cloudinary_url"     : cloudinary_video_url,
            "scene_id"           : idx,
            "start_sec"          : round(start, 3),
            "end_sec"            : round(end, 3),
            "duration_sec"       : round(end - start, 3),
            "thumbnail"          : thumb_path,
            "thumbnail_url"      : thumbnail_url,
            "scene_label_auto"   : scene_label,
            "dominant_emotion_auto" : dominant_overall,
            "scene_label"        : scene_label,
            "dominant_emotion_overall": dominant_overall,
            "scene_confidence"   : scene_conf,
            "scene_debug"        : scene_debug,
            "faces": {
                "face_present_any"  : face_any,
                "face_present_ratio": round(face_ratio, 3),
            },
            "emotion_timeline"   : emotion_timeline,
            "emotion_shift"      : emotion_shift,
            "created_at"         : datetime.now().isoformat(),
            "reviewed"           : reviewed,
            "uncertain"          : uncertain,
            "notes"              : "",
            "manual_scene_label" : None,
            "manual_emotion"     : None,
            # ── Retraining fields ────────────────────────────────────
            # human_label: filled by the review UI when a user corrects the label.
            # feature_vector_for_training: the normalised signals used to classify
            #   this scene; used by retrain_profiles.py to update Gaussian mu/sigma.
            # used_for_training: set to True after this scene is consumed by retraining.
            "human_label"               : None,
            "feature_vector_for_training": scene_debug.get("normalised_features", {}),
            "used_for_training"         : False,
        }))

        logger.info(
            "Scene %s: type=%s conf=%.2f | emotion=%s | action=%s",
            idx, scene_label, scene_conf, dominant_overall,
            scene_debug.get("agent_action", "?"),
        )

        if progress_callback:
            emo_str    = f"Emotion: {dominant_overall}." if dominant_overall else "No prominent emotions."
            label_disp = scene_label.replace("_", " ").title()
            progress_callback(f"Classified Scene {idx}/{len(scenes)} as '{label_disp}'. {emo_str}")

    # ── Write scene index JSON ─────────────────────────────────────────
    out_dir  = os.path.join(base_dir, "scene_indexes")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{video_name}_scene_index.json")
    log_pipeline_checkpoint(
        "scene_index_storage",
        video_name,
        "started",
        scene_count=len(merged),
        output_path=out_path,
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)

    logger.info("Saved scene index to %s", out_path)
    log_pipeline_checkpoint(
        "scene_index_storage",
        video_name,
        "completed",
        scene_count=len(merged),
        output_path=out_path,
    )

    log_pipeline_checkpoint(
        "database_storage",
        video_name,
        "started",
        scene_count=len(merged),
    )
    try:
        upsert_count = upsert_scene_docs(merged, source_name=os.path.basename(out_path))
    except Exception as exc:
        log_pipeline_checkpoint(
            "database_storage",
            video_name,
            "failed",
            scene_count=len(merged),
            error=str(exc),
        )
        logger.error("Scene database storage failed for %s: %s", video_name, exc, exc_info=True)
        raise
    logger.info("Upserted %s scenes into MongoDB for %s", upsert_count, video_name)
    log_pipeline_checkpoint(
        "database_storage",
        video_name,
        "completed",
        scene_count=len(merged),
        upsert_count=upsert_count,
    )
    if progress_callback:
        progress_callback("Finalizing scene timeline and indexing to database...")


# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------

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

    logger.info("Found %s videos.", len(videos))
    for video in videos:
        process_video(video, str(config.BASE_DIR))


if __name__ == "__main__":
    run_batch()
