import os
import json
import glob
import random
from datetime import datetime
from pymongo import MongoClient

from utils.logger import setup_logger
import sys
sys.path.insert(0, "D:/EDITEASE")
import config

logger = setup_logger("export_dataset")

# Target label set (5 final classes after the cleanup).
ALLOWED_LABELS = {
    "testimonial",
    "b-roll",
    "audience_reaction",
    "establishing_shot",
    "other",
}

# Common alias normalization (protects you from label drift).
# Retired classes (presenter, screen_recording, text_slide) are remapped to
# the closest surviving class so historical reviewed data is not discarded.
LABEL_MAP = {
    "talking_head": "testimonial",
    "talkinghead": "testimonial",
    "interview": "testimonial",
    "presenter": "testimonial",          # retired → testimonial

    "broll": "b-roll",
    "b_roll": "b-roll",
    "b-roll": "b-roll",

    "audience": "audience_reaction",
    "audience_reaction": "audience_reaction",
    "reaction": "audience_reaction",

    "establishing": "establishing_shot",
    "establishing_shot": "establishing_shot",

    "screen": "other",                   # retired → other
    "screen_recording": "other",         # retired → other
    "screenrecording": "other",          # retired → other

    "text": "other",                     # retired → other
    "text_slide": "other",               # retired → other
    "slide": "other",                    # retired → other

    "other": "other",
}

def normalize_label(x: str):
    if not x:
        return None
    k = str(x).strip().lower()
    k = k.replace(" ", "_")
    k = k.replace("-", "_")
    # try exact map
    if k in LABEL_MAP:
        return LABEL_MAP[k]
    # try original (for already-correct labels like "b-roll")
    raw = str(x).strip()
    if raw in ALLOWED_LABELS:
        return raw
    # try fixing underscore to hyphen for b-roll
    if k == "b_roll":
        return "b-roll"
    return None

def infer_face_present(doc: dict) -> bool:
    faces = doc.get("faces") or {}
    if "face_present_any" in faces:
        return bool(faces["face_present_any"])

    tl = doc.get("emotion_timeline") or []
    for e in tl:
        if e.get("face_detected") is True:
            return True
        if e.get("emotion") is not None:
            return True
    return False

def safe_relpath(path: str, base_dir: str) -> str:
    if not path:
        return None
    try:
        return os.path.relpath(path, base_dir)
    except Exception:
        return path  # fallback

def collect_frame_paths(doc: dict, base_dir: str, max_frames: int = 6):
    """
    Returns list of frame paths (relative to base_dir when possible):
    - Always includes main 'thumbnail' if it exists.
    - Adds any existing emotion sample images: scene_<id>_emo_*.jpg from same folder.
    """
    frames = []

    thumb = doc.get("thumbnail")
    if thumb and os.path.exists(thumb):
        frames.append(safe_relpath(thumb, base_dir))

        # emotion sample frames live in the same directory as thumbnail (your pipeline)
        thumb_dir = os.path.dirname(thumb)
        scene_id = doc.get("scene_id")
        if scene_id is not None:
            try:
                sid = int(scene_id)
                pattern = os.path.join(thumb_dir, f"scene_{sid:03d}_emo_*.jpg")
                extras = sorted(glob.glob(pattern))
                for p in extras:
                    if os.path.exists(p):
                        frames.append(safe_relpath(p, base_dir))
            except Exception:
                pass

    # de-dup while preserving order
    seen = set()
    uniq = []
    for p in frames:
        if not p:
            continue
        if p not in seen:
            seen.add(p)
            uniq.append(p)

    return uniq[:max_frames]

def build_splits(video_ids, seed=42, train=0.70, val=0.15, test=0.15):
    assert abs((train + val + test) - 1.0) < 1e-9
    vids = list(video_ids)
    rnd = random.Random(seed)
    rnd.shuffle(vids)

    n = len(vids)
    n_train = int(n * train)
    n_val = int(n * val)
    train_vids = set(vids[:n_train])
    val_vids = set(vids[n_train:n_train + n_val])
    test_vids = set(vids[n_train + n_val:])

    return {
        "train": sorted(list(train_vids)),
        "val": sorted(list(val_vids)),
        "test": sorted(list(test_vids)),
        "seed": seed,
        "ratios": {"train": train, "val": val, "test": test}
    }

def export_scene_type_dataset(
    out_dir="datasets/scene_type/v2_full",
    min_duration=2.0,
    max_duration=60.0,
    seed=42
):
    out_path = config.BASE_DIR / out_dir
    out_path.mkdir(parents=True, exist_ok=True)

    client = MongoClient(config.MONGO_URI)
    col = client[config.DB_NAME][config.COLLECTION]

    # reviewed == True and uncertain != True (missing counts as False)
    q = {
        "reviewed": True,
        "$or": [{"uncertain": {"$exists": False}}, {"uncertain": False}],
    }

    # Duration filter (optional)
    if min_duration is not None or max_duration is not None:
        q["duration_sec"] = {}
        if min_duration is not None:
            q["duration_sec"]["$gte"] = float(min_duration)
        if max_duration is not None:
            q["duration_sec"]["$lte"] = float(max_duration)

    docs = list(col.find(q))
    if not docs:
        logger.warning(f"⚠️ No eligible reviewed scenes found. Query: {q}")
        return

    # Choose label source: manual_scene_label if present else scene_label
    eligible = []
    videos = set()

    for d in docs:
        video = d.get("video")
        scene_id = d.get("scene_id")
        if not video or scene_id is None:
            continue

        raw_label = d.get("manual_scene_label") or d.get("scene_label")
        label = normalize_label(raw_label)
        if not label or label not in ALLOWED_LABELS:
            continue

        videos.add(video)
        eligible.append(d)

    if not eligible:
        logger.warning("⚠️ No eligible scenes after label normalization.")
        return

    splits = build_splits(videos, seed=seed)

    # quick helper
    def split_for_video(v):
        if v in set(splits["train"]):
            return "train"
        if v in set(splits["val"]):
            return "val"
        return "test"

    annotations_file = os.path.join(out_path, "annotations.jsonl")
    label_counts = {k: 0 for k in sorted(ALLOWED_LABELS)}
    split_counts = {"train": 0, "val": 0, "test": 0}

    with open(annotations_file, "w", encoding="utf-8") as f:
        for d in eligible:
            video = d.get("video")
            scene_id = int(d.get("scene_id"))
            label_raw = d.get("manual_scene_label") or d.get("scene_label")
            label = normalize_label(label_raw)
            if not label:
                continue

            split = split_for_video(video)

            record = {
                "scene_key": d.get("_key") or f"{video}::{scene_id}",
                "video": video,
                "scene_id": scene_id,

                "video_path": safe_relpath(d.get("video_path"), str(config.BASE_DIR)),
                "t0": d.get("start_sec"),
                "t1": d.get("end_sec"),
                "duration_sec": d.get("duration_sec"),

                "label": label,
                "label_source": "manual_scene_label" if d.get("manual_scene_label") else "scene_label",

                "frames": collect_frame_paths(d, str(config.BASE_DIR)),
                "face_present_any": infer_face_present(d),

                # keep emotion fields but they won't be used for scene-type training
                "dominant_emotion_overall": d.get("dominant_emotion_overall"),
                "emotion_timeline": d.get("emotion_timeline") if infer_face_present(d) else None,

                "reviewed": True,
                "uncertain": bool(d.get("uncertain", False)),
                "notes": d.get("notes", ""),

                "split": split,
                "dataset_version": os.path.basename(out_dir.rstrip("/\\")),
                "exported_at": datetime.now().isoformat()
            }

            # Enforce rule: if no face => emotion timeline must be null
            if not record["face_present_any"]:
                record["dominant_emotion_overall"] = None
                record["emotion_timeline"] = None

            f.write(json.dumps(record, ensure_ascii=False) + "\n")

            label_counts[label] = label_counts.get(label, 0) + 1
            split_counts[split] += 1

    splits_file = os.path.join(out_path, "splits.json")
    with open(splits_file, "w", encoding="utf-8") as sf:
        json.dump(splits, sf, indent=2)

    logger.info("✅ Export complete.")
    logger.info(f"→ {annotations_file}")
    logger.info(f"→ {splits_file}")
    logger.info(f"Split counts: {split_counts}")
    logger.info("Label counts:")
    for k in sorted(label_counts.keys()):
        logger.info(f"  {k:18s}: {label_counts[k]}")

if __name__ == "__main__":
    export_scene_type_dataset(
        out_dir="datasets/scene_type/v2_full",
        min_duration=2.0,
        max_duration=60.0,
        seed=42
    )
