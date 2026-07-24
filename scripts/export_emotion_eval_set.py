"""Export a stratified sample of existing scenes for human emotion labelling.

Why this exists
---------------
`manual_emotion` is empty on every scene in the database, so there is currently no
ground truth for the emotion track and no way to answer "are the sad clips sad?".
This script picks a balanced sample of scenes that are actually viewable and writes
them to a candidates file, which `label_emotions.html` then turns into
`annotations.jsonl`.

It deliberately samples across the machine's predicted emotions so the eval set is
not dominated by `neutral` (which is ~44% of all predictions). It also includes
face-less scenes, because "the pipeline returned no emotion" is itself a prediction
that can be right or wrong.

Nothing here writes to MongoDB — it is read-only.

Usage:
    python -m scripts.export_emotion_eval_set
    python -m scripts.export_emotion_eval_set --per-bucket 25 --out datasets/emotion/v1
"""
import argparse
import json
import os
import random
from collections import Counter, defaultdict
from pathlib import Path

from pymongo import MongoClient

import config
from scripts.emotion_label_page import render_page

# The labelling scheme. DeepFace's `disgust`/`fear`/`surprise` are folded into
# `other` — across 475 scenes disgust fired once and surprise eight times, and a
# human cannot reliably distinguish them from a still frame anyway.
LABEL_SCHEME = ["sad", "happy", "neutral", "other", "none"]

# Machine label -> scheme bucket. Used only for stratification here; the scorer
# applies the same mapping when comparing predictions to human labels.
PREDICTION_TO_BUCKET = {
    "sad": "sad",
    "happy": "happy",
    "neutral": "neutral",
    "angry": "other",
    "fear": "other",
    "disgust": "other",
    "surprise": "other",
    None: "none",
    "": "none",
}


def bucket_for(prediction):
    return PREDICTION_TO_BUCKET.get(prediction, "other")


def viewable_image(doc):
    """Return a URL/path the labeller can actually see, or None.

    Prefers the Cloudinary thumbnail; falls back to a local file only when it
    still exists on disk (most local frames were cleaned up).
    """
    url = doc.get("thumbnail_url")
    if url:
        return url, "cloudinary"
    local = doc.get("thumbnail")
    if local and os.path.exists(local):
        return local, "local"
    return None, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-bucket", type=int, default=30,
                        help="max scenes to sample per predicted-emotion bucket")
    parser.add_argument("--out", default="datasets/emotion/v1",
                        help="output directory (relative to repo root)")
    parser.add_argument("--seed", type=int, default=20260724,
                        help="sampling seed, so the eval set is reproducible")
    args = parser.parse_args()

    random.seed(args.seed)

    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
    col = client[config.DB_NAME][config.COLLECTION]

    by_bucket = defaultdict(list)
    skipped_no_image = 0
    total = 0

    for doc in col.find({}, {
        "video": 1, "scene_id": 1, "_key": 1,
        "thumbnail": 1, "thumbnail_url": 1,
        "dominant_emotion_overall": 1, "faces": 1,
        "start_sec": 1, "end_sec": 1, "duration_sec": 1,
    }):
        total += 1
        image, source = viewable_image(doc)
        if not image:
            skipped_no_image += 1
            continue

        prediction = doc.get("dominant_emotion_overall") or None
        by_bucket[bucket_for(prediction)].append({
            "scene_ref": doc.get("_key") or f"{doc.get('video')}::{doc.get('scene_id')}",
            "video": doc.get("video"),
            "scene_id": doc.get("scene_id"),
            "image": image,
            "image_source": source,
            "start_sec": doc.get("start_sec"),
            "end_sec": doc.get("end_sec"),
            "face_present": bool((doc.get("faces") or {}).get("face_present_any")),
            # Kept for the scorer. The labelling UI must NOT display this.
            "_prediction": prediction,
        })

    candidates = []
    for bucket in LABEL_SCHEME:
        pool = by_bucket.get(bucket, [])
        random.shuffle(pool)
        candidates.extend(pool[:args.per_bucket])

    random.shuffle(candidates)  # so the labeller can't infer buckets from order

    out_dir = Path(config.BASE_DIR) / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "candidates.json"
    out_path.write_text(json.dumps({
        "scheme": LABEL_SCHEME,
        "seed": args.seed,
        "candidates": candidates,
    }, indent=2), encoding="utf-8")

    # The labelling page gets the predictions stripped out — showing the model's
    # answer while labelling would bias the ground truth toward agreeing with it.
    blind = [{k: v for k, v in c.items() if k != "_prediction"} for c in candidates]
    for c in blind:
        if c["image_source"] == "local":
            c["image"] = Path(c["image"]).as_uri()
    page = render_page(json.dumps({"scheme": LABEL_SCHEME, "candidates": blind}))
    (out_dir / "label_emotions.html").write_text(page, encoding="utf-8")

    print(f"scanned scenes          : {total}")
    print(f"skipped (no viewable img): {skipped_no_image}")
    print("\navailable per predicted bucket:")
    for bucket in LABEL_SCHEME:
        print(f"  {bucket:<8} {len(by_bucket.get(bucket, []))}")
    print("\nsampled into eval set:")
    for bucket, n in Counter(bucket_for(c['_prediction']) for c in candidates).most_common():
        print(f"  {bucket:<8} {n}")
    print(f"\ntotal to label          : {len(candidates)}")
    print(f"written                 : {out_path}")
    print(f"\nNext: open {out_dir / 'label_emotions.html'} in a browser.")

    client.close()


if __name__ == "__main__":
    main()
