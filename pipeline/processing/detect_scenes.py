import os
from scenedetect import VideoManager, SceneManager

import config
from scenedetect.detectors import ContentDetector, AdaptiveDetector
from scenedetect.frame_timecode import FrameTimecode
from utils.logger import setup_logger

logger = setup_logger("detect_scenes")

# Scenes shorter than this (seconds) are likely artifacts, not real shots.
MIN_SCENE_DURATION = float(os.getenv("MIN_SCENE_DURATION", "0.5"))


def find_scenes(video_path, threshold=config.SCENE_DETECT_THRESHOLD):
    """
    Detect cut-based scenes using an ensemble of ContentDetector and
    AdaptiveDetector (catches gradual transitions / dissolves that
    ContentDetector alone misses).

    Post-processing:
      - Scenes shorter than MIN_SCENE_DURATION are merged into the next scene.
      - If nothing remains after filtering, falls back to one full-length scene.

    Returns: list of (start_timecode, end_timecode)
    """
    script_folder = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(video_path):
        video_path = os.path.join(script_folder, video_path)

    if not os.path.exists(video_path):
        logger.error(" Error: Cannot find file at: %s", video_path)
        return []

    logger.info(" Processing video at: %s …", video_path)

    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()

    # Primary detector — hard cuts
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    # Secondary detector — gradual transitions / dissolves
    scene_manager.add_detector(AdaptiveDetector())

    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    scene_list = scene_manager.get_scene_list()
    fps = video_manager.get_framerate()
    duration_seconds = video_manager.get_duration()[0].get_seconds()  # type: ignore

    # Remove duplicate boundaries that arise when both detectors fire together.
    scene_list = _deduplicate_scenes(scene_list)

    # Merge scenes that are too short (artifact cuts).
    scene_list = _filter_short_scenes(scene_list, min_duration=MIN_SCENE_DURATION)

    # Fallback: treat whole video as a single scene.
    if not scene_list:
        logger.warning(" No cuts found after filtering. Using full video as a single scene.")
        scene_list = [
            (
                FrameTimecode(0, fps=fps),
                FrameTimecode(duration_seconds, fps=fps),
            )
        ]

    logger.info(" Found %s scenes (after dedup + short-scene filter).", len(scene_list))
    for i, scene in enumerate(scene_list):
        logger.debug(
            "  Scene %s: %.2fs  -->  %.2fs  (%.2fs)",
            i + 1,
            scene[0].get_seconds(),
            scene[1].get_seconds(),
            scene[1].get_seconds() - scene[0].get_seconds(),
        )

    video_manager.release()
    return scene_list


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deduplicate_scenes(scene_list):
    """
    Both detectors can produce overlapping boundaries at the same frame.
    Keep only the first occurrence of each unique start timecode.
    """
    seen_starts = set()
    deduped = []
    for start, end in scene_list:
        key = round(start.get_seconds(), 3)
        if key not in seen_starts:
            seen_starts.add(key)
            deduped.append((start, end))
    return deduped


def _filter_short_scenes(scene_list, min_duration):
    """
    Merge scenes shorter than `min_duration` seconds into the following scene.
    If the last scene is too short it is merged into the previous one.
    Very short (< 0.1s) orphan scenes at the very end are simply dropped.
    """
    if not scene_list:
        return scene_list

    filtered = []
    pending_start = scene_list[0][0]

    for i, (start, end) in enumerate(scene_list):
        duration = end.get_seconds() - (pending_start.get_seconds() if i == 0 else start.get_seconds())
        # On the first scene keep pending_start; on subsequent scenes start==prev_end
        actual_start = pending_start if i == 0 else start
        actual_dur = end.get_seconds() - actual_start.get_seconds()

        if actual_dur < min_duration and i < len(scene_list) - 1:
            # Too short — extend the window into the next scene (don't commit yet).
            logger.debug(
                "Merging short scene (%.2fs) starting at %.2fs into next scene.",
                actual_dur, actual_start.get_seconds(),
            )
            if i == 0:
                pass  # pending_start already set
            # pending_start carries forward; end boundary comes from next iteration
            continue

        filtered.append((actual_start, end))
        if i < len(scene_list) - 1:
            pending_start = scene_list[i + 1][0]

    # Handle the final dangling scene if the loop ended on a merge.
    if scene_list and filtered:
        last_committed_end = filtered[-1][1].get_seconds()
        true_last_end = scene_list[-1][1].get_seconds()
        if true_last_end > last_committed_end + 0.1:
            last_start, _ = filtered.pop()
            filtered.append((last_start, scene_list[-1][1]))

    return filtered if filtered else scene_list


if __name__ == "__main__":
    target_video = "forya.mp4"
    find_scenes(target_video)
