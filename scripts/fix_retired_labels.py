"""
One-time cleanup for organized_videos documents whose `dominant_label` is a
retired class (`screen_recording`, `presenter`, `text_slide`).

For each affected document:
  1. If `ai_metadata.dominant_label` is a currently-valid label, use that.
  2. Otherwise fall back to "other".
  3. Preserve the old value in `legacy_dominant_label` for audit / rollback.

Cloudinary paths and the `cloudinary_public_id` field are NOT modified — those
point at real uploaded assets and would require re-uploading to rename. The
UI filters / displays by `dominant_label`, so updating that field is enough
to make stale records show the correct category.

Run:
    python -m scripts.fix_retired_labels          # apply the fix
    python -m scripts.fix_retired_labels --dry    # preview, no writes
"""

import sys
from pymongo import MongoClient

import config

RETIRED_LABELS = {"screen_recording", "presenter", "text_slide"}
VALID_LABELS   = {"testimonial", "b-roll", "audience_reaction",
                  "establishing_shot", "other", "edited"}


def main(dry_run: bool) -> None:
    client = MongoClient(config.MONGO_URI)
    col = client[config.DB_NAME]["organized_videos"]

    stale = list(col.find({"dominant_label": {"$in": list(RETIRED_LABELS)}}))
    if not stale:
        print("No stale documents found. Nothing to do.")
        return

    print(f"Found {len(stale)} stale document(s):")
    summary = {"to_label": {}, "skipped": 0}
    updates = []

    for doc in stale:
        old = doc.get("dominant_label")
        ai_label = (doc.get("ai_metadata") or {}).get("dominant_label")
        new = ai_label if ai_label in VALID_LABELS else "other"

        updates.append((doc["_id"], old, new))
        summary["to_label"][new] = summary["to_label"].get(new, 0) + 1

        print(f"  {doc['_id']}  {old:>17s}  →  {new}"
              f"   (video={doc.get('original_filename', '?')})")

    print(f"\nRemap summary: {summary['to_label']}")

    if dry_run:
        print("\n[dry-run] No changes written. Re-run without --dry to apply.")
        return

    for _id, old, new in updates:
        # Clear any emotion data on the same docs — those values came from
        # the old Haar-cascade false-positive era and are not trustworthy.
        col.update_one(
            {"_id": _id},
            {
                "$set": {
                    "dominant_label": new,
                    "legacy_dominant_label": old,
                    "ai_metadata.dominant_emotion": "none",
                    "ai_metadata.dominant_emotion_confidence": None,
                },
            },
        )

    print(f"\nUpdated {len(updates)} document(s).")
    print("Each doc now carries `legacy_dominant_label` for audit.")
    print("Stale emotion fields on those docs were cleared.")


if __name__ == "__main__":
    main(dry_run="--dry" in sys.argv)
