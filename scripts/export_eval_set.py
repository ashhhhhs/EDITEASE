"""Export one labelling pass that produces eval sets for BOTH tracks.

Why one pass
------------
Neither the emotion track nor the scene-type track has usable ground truth. The
102 existing `manual_scene_label` corrections cannot serve as an accuracy sample
because they were selected precisely where the machine looked wrong — measuring
accuracy on them is like judging a hospital using only the patients who
complained. An unbiased number needs a random sample.

Since a human has to look at each frame anyway, asking both questions per clip
costs almost nothing extra and unblocks both tracks at once.

Why local thumbnails only
-------------------------
`tests/test_ml_classifier_quality.py` loads real image files through PIL, so a
scene is only scorable for scene type if its thumbnail still exists on disk. Of
475 scenes, 242 qualify. Cloudinary-only scenes are viewable but cannot feed the
ResNet eval, so they are excluded to keep one sample valid for both tracks.

Read-only with respect to MongoDB.

Usage:
    python -m scripts.export_eval_set
    python -m scripts.export_eval_set --target 150 --out datasets
"""
import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from pymongo import MongoClient

import config
from scripts.eval_labels import (
    EMOTION_OPTIONS,
    EMOTION_SCHEME,
    SCENE_TYPE_OPTIONS,
    SCENE_TYPE_SCHEME,
    emotion_bucket,
    scene_type_bucket,
)
from scripts.eval_label_page import render_page


def _relative_frame(thumbnail: str) -> str | None:
    """Path relative to BASE_DIR, which is the form test_ml_classifier_quality expects.

    That test rebuilds the path with `Path(BASE_DIR).joinpath(*PureWindowsPath(p).parts)`,
    so an absolute path would reset the anchor and resolve somewhere else entirely.
    """
    try:
        return str(Path(thumbnail).resolve().relative_to(Path(config.BASE_DIR).resolve()))
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=120,
                        help="how many clips to put in the labelling queue")
    parser.add_argument("--out", default="datasets",
                        help="output root (relative to repo root)")
    parser.add_argument("--batch", default="v1",
                        help="subdirectory name, e.g. 'v1' for the held-out "
                             "evaluation set or 'batch2' for a training pass")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting a batch that already has labels")
    parser.add_argument("--seed", type=int, default=20260724)
    parser.add_argument(
        "--exclude-labelled", action="store_true",
        help="skip scenes that already appear in an annotations.jsonl, so a "
             "second labelling pass extends the dataset instead of repeating it",
    )
    args = parser.parse_args()

    random.seed(args.seed)

    already_labelled: set[str] = set()
    if args.exclude_labelled:
        for path in Path(config.BASE_DIR).glob("datasets/**/annotations.jsonl"):
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if not line:
                    continue
                ref = json.loads(line).get("scene_ref")
                if ref:
                    already_labelled.add(ref)
        print(f"excluding {len(already_labelled)} already-labelled scenes\n")

    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
    col = client[config.DB_NAME][config.COLLECTION]

    eligible = []
    skipped_no_local_frame = 0
    total = 0

    for doc in col.find({}, {
        "video": 1, "scene_id": 1, "_key": 1, "thumbnail": 1,
        "dominant_emotion_overall": 1, "scene_label_auto": 1, "scene_label": 1,
        "faces": 1, "start_sec": 1, "end_sec": 1,
    }):
        total += 1
        scene_ref = doc.get("_key") or f"{doc.get('video')}::{doc.get('scene_id')}"
        if scene_ref in already_labelled:
            continue
        thumbnail = doc.get("thumbnail")
        if not thumbnail or not Path(thumbnail).exists():
            skipped_no_local_frame += 1
            continue
        frame_rel = _relative_frame(thumbnail)
        if not frame_rel:
            skipped_no_local_frame += 1
            continue

        eligible.append({
            "scene_ref": scene_ref,
            "video": doc.get("video"),
            "scene_id": doc.get("scene_id"),
            "image": Path(thumbnail).resolve().as_uri(),
            "frame_rel": frame_rel,
            "start_sec": doc.get("start_sec"),
            "end_sec": doc.get("end_sec"),
            # Retained for the scorers and for stratification. Stripped before the
            # labelling page is rendered — see render_page's contract.
            "_emotion_prediction": doc.get("dominant_emotion_overall") or None,
            "_scene_prediction": doc.get("scene_label_auto") or doc.get("scene_label"),
        })

    # Stratify across the cross-product of both predicted axes, then round-robin.
    # A flat random draw would be dominated by neutral emotions and b-roll scenes.
    groups = defaultdict(list)
    for item in eligible:
        key = (emotion_bucket(item["_emotion_prediction"]),
               scene_type_bucket(item["_scene_prediction"]))
        groups[key].append(item)
    for bucket in groups.values():
        random.shuffle(bucket)

    ordered_keys = sorted(groups, key=lambda k: -len(groups[k]))
    selected = []
    while len(selected) < args.target:
        drained = True
        for key in ordered_keys:
            if groups[key]:
                selected.append(groups[key].pop())
                drained = False
                if len(selected) >= args.target:
                    break
        if drained:
            break

    random.shuffle(selected)  # order must not encode the bucket

    out_root = Path(config.BASE_DIR) / args.out
    emotion_dir = out_root / "emotion" / args.batch
    scene_dir = out_root / "scene_type" / args.batch

    # Refuse to clobber a batch that has already been labelled. Overwriting the
    # candidates of a completed set destroys the predictions the scorers compare
    # against, and silently invalidates the benchmark.
    if not args.force:
        for directory in (emotion_dir, scene_dir):
            if (directory / "annotations.jsonl").exists():
                raise SystemExit(
                    f"{directory} already contains annotations.jsonl.\n"
                    f"Overwriting it would invalidate that labelled set.\n"
                    f"Use --batch <name> to write a new batch, or --force to override."
                )

    for directory in (emotion_dir, scene_dir):
        directory.mkdir(parents=True, exist_ok=True)

    payload = {
        "seed": args.seed,
        "emotion_scheme": EMOTION_SCHEME,
        "scene_type_scheme": SCENE_TYPE_SCHEME,
        "candidates": selected,
    }
    (emotion_dir / "candidates.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (scene_dir / "candidates.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Strip every underscore-prefixed key: those hold the model's predictions, and
    # showing them while labelling would measure agreement with the model.
    blind = [{k: v for k, v in c.items() if not k.startswith("_")} for c in selected]
    page_path = out_root / f"label_eval_{args.batch}.html"
    page_path.write_text(render_page(json.dumps({
        "candidates": blind,
        "emotion_options": EMOTION_OPTIONS,
        "scene_options": SCENE_TYPE_OPTIONS,
    })), encoding="utf-8")

    print(f"scanned scenes                 : {total}")
    print(f"skipped (no local frame on disk): {skipped_no_local_frame}")
    print(f"eligible for both tracks       : {len(eligible)}")
    print(f"queued for labelling           : {len(selected)}")

    print("\npredicted emotion spread in the queue:")
    for bucket, n in Counter(emotion_bucket(c["_emotion_prediction"]) for c in selected).most_common():
        print(f"  {bucket:<20} {n}")
    print("\npredicted scene-type spread in the queue:")
    for bucket, n in Counter(scene_type_bucket(c["_scene_prediction"]) for c in selected).most_common():
        print(f"  {bucket:<20} {n}")

    print(f"\ncandidates written : {emotion_dir / 'candidates.json'}")
    print(f"                     {scene_dir / 'candidates.json'}")
    print(f"labelling page     : {page_path}")
    print("\nOpen the page, label everything, then save the two downloaded files as:")
    print(f"  {emotion_dir / 'annotations.jsonl'}")
    print(f"  {scene_dir / 'annotations.jsonl'}")

    client.close()


if __name__ == "__main__":
    main()
