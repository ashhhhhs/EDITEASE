"""Build a scene-type regression set from human corrections.

What this is, and what it is NOT
--------------------------------
These are the scenes a reviewer went in and *corrected*. That makes them a
deliberately biased sample: they were selected precisely where the machine looked
wrong. Accuracy measured here will be far below true accuracy, in the same way
that judging a hospital using only the patients who filed complaints would be.

So this set is a **regression guard**, not a benchmark. Its job is "do not get
worse on the cases we already know are hard". For an unbiased accuracy number use
`scripts/export_eval_set.py`, which draws a random sample for human labelling.

Only `manual_scene_label` is used. The pre-existing datasets/scene_type/v2_full
set is 252/315 machine-labelled (`label_source: scene_label`), so scoring against
it would measure the model agreeing with itself.

Usage:
    python -m scripts.export_scene_type_hard_cases
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from pymongo import MongoClient

import config
from scripts.eval_labels import RETIRED_SCENE_LABELS, SCENE_TYPE_SCHEME


def _relative_frame(thumbnail: str) -> str | None:
    try:
        return str(Path(thumbnail).resolve().relative_to(Path(config.BASE_DIR).resolve()))
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="datasets/scene_type/hard_cases")
    args = parser.parse_args()

    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
    col = client[config.DB_NAME][config.COLLECTION]

    rows = []
    skipped_retired = skipped_unknown = skipped_no_frame = 0

    for doc in col.find({"manual_scene_label": {"$nin": [None, ""]}}):
        label = doc.get("manual_scene_label")
        if label in RETIRED_SCENE_LABELS:
            skipped_retired += 1
            continue
        if label not in SCENE_TYPE_SCHEME:
            skipped_unknown += 1
            continue

        thumbnail = doc.get("thumbnail")
        if not thumbnail or not Path(thumbnail).exists():
            skipped_no_frame += 1
            continue
        frame_rel = _relative_frame(thumbnail)
        if not frame_rel:
            skipped_no_frame += 1
            continue

        rows.append({
            "label": label,
            "split": "test",
            "frames": [frame_rel],
            "scene_ref": doc.get("_key"),
            "video": doc.get("video"),
            "scene_id": doc.get("scene_id"),
            "label_source": "manual_scene_label",
            "pipeline_said": doc.get("scene_label_auto") or doc.get("scene_label"),
        })

    out_dir = Path(config.BASE_DIR) / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "annotations.jsonl"
    out_path.write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
    )

    print(f"human-corrected scenes written : {len(rows)}")
    print(f"  skipped, retired label       : {skipped_retired}")
    print(f"  skipped, label off-scheme    : {skipped_unknown}")
    print(f"  skipped, frame not on disk   : {skipped_no_frame}")
    print(f"\nlabel spread: {dict(Counter(r['label'] for r in rows))}")

    agree = sum(1 for r in rows if r["label"] == r["pipeline_said"])
    if rows:
        print(f"\npipeline already agreed on {agree}/{len(rows)} "
              f"({agree / len(rows):.0%}) — expected to be low, these are the "
              f"scenes a human went in and corrected.")
    print(f"\nwritten: {out_path}")

    client.close()


if __name__ == "__main__":
    main()
