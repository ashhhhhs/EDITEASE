"""Score the emotion track against human labels.

Answers the question the pipeline currently cannot: when EditEase says a clip is
sad, is it sad — and when it is wrong, what is it confusing sad *with*?

Reads `datasets/emotion/v1/annotations.jsonl` (produced by label_emotions.html),
looks up what the pipeline actually predicted for each labelled scene, and prints
accuracy, per-class precision/recall, a confusion matrix, and the worst misses.

It scores the **scene-level** result (`dominant_emotion_overall`) because that is
what a reviewer sees — not raw per-frame DeepFace output.

Usage:
    python -m scripts.evaluate_emotion
    python -m scripts.evaluate_emotion --annotations datasets/emotion/v2/annotations.jsonl
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from pymongo import MongoClient

import config
from scripts.export_emotion_eval_set import LABEL_SCHEME, bucket_for


def load_annotations(path: Path) -> dict:
    """scene_ref -> human label. Later lines win, so re-labelling a scene is fine."""
    if not path.exists():
        raise SystemExit(
            f"No annotations at {path}\n"
            "Label some clips first:\n"
            "  1. python -m scripts.export_emotion_eval_set\n"
            "  2. open datasets/emotion/v1/label_emotions.html\n"
            "  3. save the downloaded annotations.jsonl into that folder"
        )
    labels = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        ref, human = rec.get("scene_ref"), rec.get("human_emotion")
        if ref and human:
            labels[ref] = human
    return labels


def fetch_predictions(scene_refs):
    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
    col = client[config.DB_NAME][config.COLLECTION]
    preds = {}
    for doc in col.find(
        {"_key": {"$in": list(scene_refs)}},
        {"_key": 1, "dominant_emotion_overall": 1, "faces": 1, "video": 1, "scene_id": 1},
    ):
        preds[doc["_key"]] = {
            "raw": doc.get("dominant_emotion_overall") or None,
            "face_present": bool((doc.get("faces") or {}).get("face_present_any")),
            "video": doc.get("video"),
            "scene_id": doc.get("scene_id"),
        }
    client.close()
    return preds


def confusion_matrix(pairs, labels):
    matrix = {t: Counter() for t in labels}
    for truth, pred in pairs:
        matrix[truth][pred] += 1
    return matrix


def print_matrix(matrix, labels):
    width = max(len(l) for l in labels) + 2
    header = " " * (width + 2) + "".join(f"{l[:7]:>9}" for l in labels)
    print("\n  Confusion matrix  (rows = your label, cols = pipeline said)")
    print("  " + header)
    for truth in labels:
        row = matrix[truth]
        total = sum(row.values())
        cells = ""
        for pred in labels:
            n = row.get(pred, 0)
            cells += f"{(str(n) if n else '·'):>9}"
        print(f"  {truth:<{width}}{cells}   ({total})")


def per_class_stats(pairs, labels):
    tp = Counter(); fp = Counter(); fn = Counter()
    for truth, pred in pairs:
        if truth == pred:
            tp[truth] += 1
        else:
            fn[truth] += 1
            fp[pred] += 1
    print("\n  Per-class precision / recall")
    print(f"  {'label':<10}{'precision':>11}{'recall':>9}{'support':>9}")
    for l in labels:
        support = tp[l] + fn[l]
        if support == 0 and fp[l] == 0:
            continue
        precision = tp[l] / (tp[l] + fp[l]) if (tp[l] + fp[l]) else 0.0
        recall = tp[l] / support if support else 0.0
        print(f"  {l:<10}{precision:>11.2f}{recall:>9.2f}{support:>9}")
    return tp, fp, fn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", default="datasets/emotion/v1/annotations.jsonl")
    parser.add_argument("--show-misses", type=int, default=15)
    args = parser.parse_args()

    path = Path(config.BASE_DIR) / args.annotations
    human = load_annotations(path)
    preds = fetch_predictions(human.keys())

    pairs = []
    missing = []
    misses = []
    for ref, truth in human.items():
        p = preds.get(ref)
        if not p:
            missing.append(ref)
            continue
        pred_bucket = bucket_for(p["raw"])
        pairs.append((truth, pred_bucket))
        if truth != pred_bucket:
            misses.append((ref, truth, pred_bucket, p["raw"], p["face_present"]))

    if not pairs:
        raise SystemExit("No labelled scenes matched anything in MongoDB.")

    correct = sum(1 for t, p in pairs if t == p)
    accuracy = correct / len(pairs)

    print("=" * 68)
    print("  EMOTION TRACK — accuracy against human labels")
    print("=" * 68)
    print(f"  labelled scenes scored : {len(pairs)}")
    if missing:
        print(f"  skipped (not in Mongo) : {len(missing)}")
    print(f"  overall accuracy       : {accuracy:.1%}  ({correct}/{len(pairs)})")

    print_matrix(confusion_matrix(pairs, LABEL_SCHEME), LABEL_SCHEME)
    per_class_stats(pairs, LABEL_SCHEME)

    # The headline question.
    sad_pred = [(t, p) for t, p in pairs if p == "sad"]
    sad_true = [(t, p) for t, p in pairs if t == "sad"]
    print("\n  The question you actually asked")
    if sad_pred:
        hit = sum(1 for t, _ in sad_pred if t == "sad")
        print(f"    when it says SAD, it is right {hit}/{len(sad_pred)} "
              f"({hit / len(sad_pred):.0%})")
    else:
        print("    it never predicted SAD on this sample")
    if sad_true:
        found = sum(1 for _, p in sad_true if p == "sad")
        print(f"    of genuinely SAD clips, it found {found}/{len(sad_true)} "
              f"({found / len(sad_true):.0%})")
        confused = Counter(p for t, p in sad_true if p != "sad")
        if confused:
            print("    real sad clips were called: " +
                  ", ".join(f"{k} x{v}" for k, v in confused.most_common()))
    else:
        print("    no clips were labelled SAD, so recall cannot be measured")

    if misses:
        print(f"\n  Worst misses (showing {min(args.show_misses, len(misses))} of {len(misses)})")
        for ref, truth, pred, raw, face in misses[:args.show_misses]:
            print(f"    {ref:<34} you={truth:<8} pipeline={pred:<8} "
                  f"(raw={raw or 'none'}, face={'y' if face else 'n'})")

    by_truth = defaultdict(Counter)
    for t, p in pairs:
        by_truth[t][p] += 1
    print("\n" + "=" * 68)


if __name__ == "__main__":
    main()
