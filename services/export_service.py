import os
import sys
import subprocess
import shutil
from pathlib import Path
from collections import Counter

import config
from utils.logger import setup_logger
from services.clip_service import col

logger = setup_logger("export_service")

def _get_dominant_scene_type(video_name):
    """Finds the most frequent scene_label for a given video."""
    scenes = list(col.find({"video": video_name}))
    if not scenes:
        return "other"
    
    labels = [s.get("scene_label", "other") or "other" for s in scenes]
    if not labels:
        return "other"
        
    counts = Counter(labels)
    return counts.most_common(1)[0][0]

def export_single_clip(video, scene_id):
    if not video or scene_id is None:
        return {"error": "video and scene_id required"}
        
    key = f"{video}::{int(scene_id)}"
    doc = col.find_one({"_key": key})
    if not doc:
        return {"error": "scene not found"}

    dominant_label = _get_dominant_scene_type(video)

    # Prefer Cloudinary URL — no file copy needed
    cloudinary_url = doc.get("cloudinary_url")
    if cloudinary_url:
        logger.info(f"Export via Cloudinary URL for {key}")
        return {
            "status": "exported_full_video",
            "scene_label": dominant_label,
            "cloudinary_url": cloudinary_url,
        }

    # Fallback: local file copy for legacy docs
    video_path = doc.get("video_path")
    if not video_path or not os.path.exists(video_path):
        return {"error": "invalid video path metadata"}

    EXPORT_DIR = config.EXPORTS_DIR / dominant_label
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    original_ext = os.path.splitext(video_path)[1] or ".mp4"
    out_path = EXPORT_DIR / f"{video}_full{original_ext}"

    try:
        shutil.copy2(video_path, out_path)
    except Exception as e:
        logger.error(f"Copy failed: {e}")
        return {"error": "copy failed", "details": str(e)}

    return {"status": "exported_full_video", "scene_label": dominant_label, "output_path": str(out_path)}


def export_batch(filters):
    q = {}
    
    scene_label = filters.get("scene_label")
    emotion = filters.get("emotion")
    video = filters.get("video")
    
    if scene_label:
        q["scene_label"] = scene_label
    if emotion:
        if emotion == "__NULL__":
            q["$or"] = [{"dominant_emotion_overall": None}, {"dominant_emotion_overall": {"$exists": False}}]
        else:
            q["dominant_emotion_overall"] = emotion
    if video:
        q["video"] = video
        
    cursor = col.find(q)
    results = [d for d in cursor]
    
    exported = []
    failed = []
    
    processed_videos = set()
    
    for doc in results:
        vid_name = doc.get("video")
        if not vid_name or vid_name in processed_videos:
            continue

        dominant_label = _get_dominant_scene_type(vid_name)

        # Prefer Cloudinary URL — no file copy needed
        cloudinary_url = doc.get("cloudinary_url")
        if cloudinary_url:
            exported.append(cloudinary_url)
            logger.info(f"Exported full video {vid_name} via Cloudinary URL")
            processed_videos.add(vid_name)
            continue

        # Fallback: local file copy for legacy docs
        video_path = doc.get("video_path")
        if not video_path or not os.path.exists(video_path):
            continue

        EXPORT_DIR = config.EXPORTS_DIR / dominant_label
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)

        original_ext = os.path.splitext(video_path)[1] or ".mp4"
        out_path = EXPORT_DIR / f"{vid_name}_full{original_ext}"

        try:
            shutil.copy2(video_path, out_path)
            exported.append(str(out_path))
            logger.info(f"Exported full video {vid_name} to {out_path}")
            processed_videos.add(vid_name)
        except Exception as e:
            logger.error(f"Copy failed for {vid_name}: {e}")
            failed.append(str(out_path))
            
    return {"status": "exported_full_videos", "exported_count": len(exported), "failed_count": len(failed)}

def open_local_folder(folder_path):
    """
    Open a local folder in the system file explorer.
    Desktop-only: requires Windows.
    """
    if sys.platform != "win32":
        return {"error": "This feature requires a local Windows environment."}
        
    if not folder_path or not os.path.isdir(folder_path):
        return {"error": "Folder not found"}
    
    try:
        subprocess.Popen(["explorer", os.path.normpath(folder_path)])
        return {"status": "opened", "path": folder_path}
    except Exception as e:
        logger.error(f"Failed to open folder: {e}")
        return {"error": str(e)}
