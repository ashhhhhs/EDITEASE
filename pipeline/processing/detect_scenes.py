import os
from scenedetect import VideoManager, SceneManager

import config
from scenedetect.detectors import ContentDetector
from scenedetect.frame_timecode import FrameTimecode
from utils.logger import setup_logger

logger = setup_logger("detect_scenes")


def find_scenes(video_path, threshold=config.SCENE_DETECT_THRESHOLD):
    """
    Detect cut-based scenes.
    If no cuts are found, fallback to 1 full-length scene.
    Returns: list of (start_timecode, end_timecode)
    """

    script_folder = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(video_path):
        video_path = os.path.join(script_folder, video_path)

    if not os.path.exists(video_path):
        logger.error(f"❌ Error: Cannot find file at: {video_path}")
        return []

    logger.info(f"🎬 Processing video at: {video_path}...")

    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))

    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    scene_list = scene_manager.get_scene_list()
    #fallback to full video if no scenes found
    if len(scene_list) == 0:
        logger.warning("⚠️ No cuts found. Using full video as a single scene.")
        duration_seconds = video_manager.get_duration()[0].get_seconds()
        fps = video_manager.get_framerate()

        scene_list = [
            (
                FrameTimecode(0, fps=fps),
                FrameTimecode(duration_seconds, fps=fps)
            )
        ]

    logger.info(f"✅ SUCCESS! Found {len(scene_list)} scenes.")
    for i, scene in enumerate(scene_list):
        start = scene[0].get_seconds()
        end = scene[1].get_seconds()
        logger.debug(f"  Scene {i+1}: {start:.2f}s  -->  {end:.2f}s")

    video_manager.release()
    return scene_list


if __name__ == "__main__":
    target_video = "forya.mp4"
    find_scenes(target_video)
