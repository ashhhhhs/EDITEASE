"""Build a scene-type TRAINING set from human labels only.

The rule this enforces
----------------------
Nothing in datasets/scene_type/v1 (the held-out evaluation set) may appear in
the training set. Training on your benchmark is exactly the mistake that
produced the current model: datasets/scene_type/v2_full is 252/315
machine-labelled, so v2 largely learned to reproduce the pipeline's own output,
and its "test" split measured self-consistency rather than correctness.

Sources, in order of preference:
  1. Human labels from later labelling passes (datasets/scene_type/batch*/)
  2. manual_scene_label corrections in MongoDB

Both are human judgements. Machine labels are never used.

Usage:
    python -m scripts.export_training_set
    python -m scripts.export_training_set --val-fraction 0.2
"""
import argparse
import json
import random
from collections import Counter
from pathlib import Path

from pymongo import MongoClient

import config
from scripts.eval_labels import RETIRED_SCENE_LABELS, SCENE_TYPE_SCHEME

EVAL_SET = Path("datasets/scene_type/v1/annotations.jsonl")


def _relative_frame(thumbnail: str) -> str | None:
    try:
        return str(Path(thumbnail).resolve().relative_to(Path(config.BASE_DIR).resolve()))
    except ValueError:
        return None


def _read_refs(path: Path) -> set[str]:
    if not path.exists():
        return set()
    refs = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            ref = json.loads(line).get("scene_ref")
            if ref:
                refs.add(ref)
    return refs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="datasets/scene_type/train")
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=20260725)
    args = parser.parse_args()

    random.seed(args.seed)

    held_out = _read_refs(Path(config.BASE_DIR) / EVAL_SET)
    print(f"held-out evaluation scenes (never trained on): {len(held_out)}")

    rows: dict[str, dict] = {}

    # ── Source 1: human labels from later labelling batches ────────────────
    for path in sorted(Path(config.BASE_DIR).glob("datasets/scene_type/batch*/annotations.jsonl")):
        n = 0
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ref, label = rec.get("scene_ref"), rec.get("label")
            if not ref or ref in held_out or label not in SCENE_TYPE_SCHEME:
                continue
            if not rec.get("frames"):
                continue
            rows[ref] = {"label": label, "frames": rec["frames"], "scene_ref": ref,
                         "source": path.parent.name}
            n += 1
        print(f"  {path.parent.name}: {n} usable human labels")

    # ── Source 2: manual_scene_label corrections in MongoDB ────────────────
    try:
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        col = client[config.DB_NAME][config.COLLECTION]
        n = 0
        for doc in col.find({"manual_scene_label": {"$nin": [None, ""]}}):
            ref = doc.get("_key")
            label = doc.get("manual_scene_label")
            if not ref or ref in held_out or ref in rows:
                continue
            if label in RETIRED_SCENE_LABELS or label not in SCENE_TYPE_SCHEME:
                continue
            thumbnail = doc.get("thumbnail")
            if not thumbnail or not Path(thumbnail).exists():
                continue
            frame_rel = _relative_frame(thumbnail)
            if not frame_rel:
                continue
            rows[ref] = {"label": label, "frames": [frame_rel], "scene_ref": ref,
                         "source": "manual_scene_label"}
            n += 1
        print(f"  mongo manual_scene_label: {n} usable corrections")
        client.close()
    except Exception as exc:
        print(f"  mongo unavailable, skipping corrections ({exc})")

    records = list(rows.values())
    if not records:
        raise SystemExit(
            "\nNo training data.\n"
            "Label another batch first:\n"
            "  python -m scripts.export_eval_set --exclude-labelled\n"
            "  open datasets/label_eval.html\n"
            "then save the scene-type file to datasets/scene_type/batch2/annotations.jsonl"
        )

    # Stratified split so a rare class does not land entirely in one side.
    by_label: dict[str, list] = {}
    for r in records:
        by_label.setdefault(r["label"], []).append(r)

    train, val = [], []
    for label, group in by_label.items():
        random.shuffle(group)
        n_val = max(1, round(len(group) * args.val_fraction)) if len(group) > 1 else 0
        val.extend(group[:n_val])
        train.extend(group[n_val:])

    out_dir = Path(config.BASE_DIR) / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "annotations.jsonl"
    with out_path.open("w", encoding="utf-8") as handle:
        for split, group in (("train", train), ("val", val)):
            for r in group:
                handle.write(json.dumps({
                    "label": r["label"], "split": split, "frames": r["frames"],
                    "scene_ref": r["scene_ref"], "label_source": r["source"],
                }) + "\n")

    # Belt and braces: prove the two sets are disjoint before anyone trains.
    written = _read_refs(out_path)
    overlap = written & held_out
    if overlap:
        raise SystemExit(f"ABORT: {len(overlap)} training scenes are in the eval set: "
                         f"{sorted(overlap)[:5]}")

    print(f"\ntrain: {len(train)}   val: {len(val)}")
    print(f"  train labels: {dict(Counter(r['label'] for r in train))}")
    print(f"  val labels  : {dict(Counter(r['label'] for r in val))}")
    print(f"\noverlap with evaluation set: 0  (verified)")
    print(f"written: {out_path}")
    print("\nNext:")
    print("  python -m pipeline.training.train_scene_classifier   # writes v3")
    print("  # then evaluate v3 before promoting it via SCENE_MODEL_VERSION")


if __name__ == "__main__":
    main()
