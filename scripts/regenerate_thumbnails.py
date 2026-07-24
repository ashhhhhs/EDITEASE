"""Restore missing scene thumbnails by re-extracting them from the source videos.

Why only thumbnails
-------------------
This re-extracts frames at the timestamps already stored on each scene. It does
NOT re-run the pipeline, and that restraint is deliberate: scene detection could
return different cut boundaries on a second pass, and the evaluation set is keyed
by `video::scene_id`. If scene 1 came back covering a different span, the human
labels would silently describe different content and the benchmark would be
corrupted with no visible symptom.

So nothing here writes to MongoDB. It only puts image files back where the
database already says they should be, which widens the pool of scenes that can
be labelled and evaluated.

Usage:
    python -m scripts.regenerate_thumbnails --dry-run
    python -m scripts.regenerate_thumbnails
"""
import argparse
import os
from collections import Counter
from pathlib import Path

from pymongo import MongoClient

import config
from pipeline.processing.run_pipeline import extract_frame
from utils.logger import setup_logger

logger = setup_logger("regenerate_thumbnails")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would be restored without writing")
    parser.add_argument("--limit", type=int, default=0,
                        help="stop after N extractions (0 = no limit)")
    args = parser.parse_args()

    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
    col = client[config.DB_NAME][config.COLLECTION]

    stats = Counter()
    todo = []

    for doc in col.find({}, {
        "_key": 1, "video": 1, "scene_id": 1, "thumbnail": 1,
        "video_path": 1, "start_sec": 1, "end_sec": 1,
    }):
        thumbnail = doc.get("thumbnail")
        if not thumbnail:
            stats["no_thumbnail_path_recorded"] += 1
            continue
        if Path(thumbnail).exists():
            stats["already_present"] += 1
            continue

        video_path = doc.get("video_path")
        if not video_path or not Path(video_path).exists():
            stats["source_video_missing"] += 1
            continue

        start, end = doc.get("start_sec"), doc.get("end_sec")
        if start is None or end is None:
            stats["no_timestamps"] += 1
            continue

        todo.append({
            "key": doc.get("_key"),
            "thumbnail": thumbnail,
            "video_path": video_path,
            # Mid-scene, matching what process_video extracts.
            "timestamp": (float(start) + float(end)) / 2.0,
        })

    print("Scene thumbnail audit")
    print(f"  already on disk          : {stats['already_present']}")
    print(f"  source video missing     : {stats['source_video_missing']}")
    print(f"  no timestamps recorded   : {stats['no_timestamps']}")
    print(f"  no thumbnail path        : {stats['no_thumbnail_path_recorded']}")
    print(f"  RECOVERABLE              : {len(todo)}")

    if args.dry_run:
        print("\n(dry run — nothing written)")
        for item in todo[:8]:
            print(f"    {item['key']}  t={item['timestamp']:.1f}s")
        if len(todo) > 8:
            print(f"    ... and {len(todo) - 8} more")
        client.close()
        return

    if not todo:
        print("\nNothing to restore.")
        client.close()
        return

    print(f"\nExtracting {len(todo)} frames...")
    restored = failed = 0
    for i, item in enumerate(todo, start=1):
        if args.limit and restored >= args.limit:
            break
        os.makedirs(os.path.dirname(item["thumbnail"]), exist_ok=True)
        try:
            ok = extract_frame(item["video_path"], item["timestamp"], item["thumbnail"])
        except Exception as exc:
            logger.warning("extract failed for %s: %s", item["key"], exc)
            ok = False
        if ok:
            restored += 1
        else:
            failed += 1
        if i % 25 == 0:
            print(f"  {i}/{len(todo)}  restored={restored} failed={failed}")

    print(f"\nrestored : {restored}")
    print(f"failed   : {failed}")
    print("\nNothing in MongoDB was modified.")
    if restored:
        print("Next: python -m scripts.export_eval_set --batch batch2 "
              "--exclude-labelled --target 250")
    client.close()


if __name__ == "__main__":
    main()
