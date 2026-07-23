"""
Inspect emotion detection on one video — no Mongo, no Cloudinary, no Celery.

Samples frames exactly as the pipeline does and prints the full per-frame probability
distribution alongside the aggregated scene verdict, so you can see *why* a scene got its
label rather than only what it got.

    .\.venv\Scripts\python.exe -m scripts.check_emotion "data\my_sad_clip.mp4"

Options:
    --whole-video   skip scene detection, treat the file as one scene
    --compare       also show what the pre-fix plurality vote would have produced
"""
import argparse
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.processing import run_pipeline
from pipeline.processing.detect_scenes import find_scenes
from pipeline.processing.emotion_detect import detect_emotion


def _plurality_vote(reads, n_samples):
    """The pre-fix aggregation: one whole vote to each frame's argmax label."""
    votes = {}
    for i, (dominant, _probs) in enumerate(reads):
        if dominant:
            votes[dominant] = votes.get(dominant, 0.0) + run_pipeline._sample_weight(i, n_samples)
    return (max(votes, key=votes.get) if votes else None), votes


def _format_votes(votes, top=4):
    ranked = sorted(votes.items(), key=lambda kv: kv[1], reverse=True)[:top]
    return "   ".join(f"{label}={score:.2f}" for label, score in ranked)


def check_scene(video_path, start_sec, end_sec, scene_id, thumbs_dir, compare):
    duration = end_sec - start_sec
    n_samples = run_pipeline._get_sample_count(duration)
    ratios = [0.1 + (0.8 * i / (n_samples - 1)) if n_samples > 1 else 0.5 for i in range(n_samples)]

    reads = []
    votes = {}
    face_hits = 0
    total_samples = 0

    print(f"\n=== scene {scene_id}   {start_sec:.2f}s → {end_sec:.2f}s "
          f"({duration:.2f}s, {n_samples} samples)")

    for i, ratio in enumerate(ratios):
        timestamp = start_sec + duration * ratio
        thumb_path = os.path.join(thumbs_dir, f"scene_{scene_id:03d}_emo_{i}.jpg")
        w = run_pipeline._sample_weight(i, n_samples)

        if not run_pipeline.extract_frame(video_path, timestamp, thumb_path):
            print(f"  [{i}] w={w:<4} frame extraction failed")
            continue

        total_samples += 1
        if not run_pipeline.has_face(thumb_path):
            reads.append((None, None))
            print(f"  [{i}] w={w:<4} no face (Haar)")
            continue

        face_hits += 1
        dominant, probs, _conf = detect_emotion(thumb_path, enforce_detection=True)
        reads.append((dominant, probs))

        if isinstance(probs, dict) and probs:
            total_prob = sum(float(p) for p in probs.values()) or 1.0
            for label, p in probs.items():
                votes[label] = votes.get(label, 0.0) + w * (float(p) / total_prob)
            spread = "  ".join(
                f"{label}:{100 * float(p) / total_prob:.0f}"
                for label, p in sorted(probs.items(), key=lambda kv: -kv[1])[:4]
            )
            print(f"  [{i}] w={w:<4} {str(dominant):<9} {spread}")
        else:
            # Haar found a face but DeepFace's own detector rejected the frame.
            print(f"  [{i}] w={w:<4} Haar face, but DeepFace found none — no vote")

    face_ratio = (face_hits / total_samples) if total_samples else 0.0
    has_evidence = (
        face_hits >= run_pipeline.MIN_EMOTION_FACE_HITS
        and face_ratio >= run_pipeline.MIN_EMOTION_FACE_RATIO
    )
    verdict = run_pipeline._resolve_dominant(votes) if has_evidence else None

    print(f"  faces {face_hits}/{total_samples} (ratio {face_ratio:.2f}, "
          f"need >={run_pipeline.MIN_EMOTION_FACE_HITS} and "
          f">={run_pipeline.MIN_EMOTION_FACE_RATIO}) -> evidence={has_evidence}")
    print(f"  votes    {_format_votes(votes) or '(none)'}")
    print(f"  VERDICT  {verdict}")

    if compare:
        old_label, old_votes = _plurality_vote(reads, n_samples)
        old_verdict = old_label if has_evidence else None
        flag = "   <<< CHANGED" if old_verdict != verdict else ""
        print(f"  pre-fix  {old_verdict}   ({_format_votes(old_votes) or 'none'}){flag}")

    return verdict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="path to a video file")
    parser.add_argument("--whole-video", action="store_true",
                        help="skip scene detection; treat the file as a single scene")
    parser.add_argument("--compare", action="store_true",
                        help="also show the pre-fix plurality-vote result")
    args = parser.parse_args()

    video_path = os.path.abspath(args.video)
    if not os.path.exists(video_path):
        parser.error(f"no such file: {video_path}")

    if args.whole_video:
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        cap.release()
        windows = [(0.0, frames / fps if fps else 0.0)]
    else:
        windows = [(s.get_seconds(), e.get_seconds()) for s, e in find_scenes(video_path)]

    if not windows or windows[0][1] <= 0:
        print("No scenes detected — try --whole-video.")
        return

    print(f"\n{os.path.basename(video_path)}: {len(windows)} scene(s)")
    thumbs_dir = tempfile.mkdtemp(prefix="check_emotion_")
    try:
        verdicts = [
            check_scene(video_path, start, end, i + 1, thumbs_dir, args.compare)
            for i, (start, end) in enumerate(windows)
        ]
    finally:
        shutil.rmtree(thumbs_dir, ignore_errors=True)

    print("\n--- summary ---")
    for i, verdict in enumerate(verdicts):
        print(f"  scene {i + 1}: {verdict}")


if __name__ == "__main__":
    main()
