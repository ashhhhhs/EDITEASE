"""Move downloaded label files into the dataset directories.

The labelling page can only hand you a file in your Downloads folder. Putting the
wrong one in the wrong directory silently produces a dataset that scores nothing
(the scene-type test filters on labels it does not recognise, so a mixed-up file
looks like "no samples found" rather than an error). This does the move for you.

Usage:
    python -m scripts.install_annotations
    python -m scripts.install_annotations --downloads "D:/some/other/folder"
"""
import argparse
import json
from pathlib import Path

import config

# downloaded name -> destination template, and the key every record must contain
TRANSFERS = [
    ("editease-emotion-labels.jsonl", "datasets/emotion/{batch}/annotations.jsonl", "human_emotion"),
    ("editease-scene-type-labels.jsonl", "datasets/scene_type/{batch}/annotations.jsonl", "label"),
]


def _validate(path: Path, required_key: str) -> tuple[list[dict], str | None]:
    """Return (records, error). Catches a swapped pair before it lands.

    Read as utf-8-sig so a byte-order mark is stripped transparently. Notepad and
    PowerShell's Out-File both add one on Windows, and json.loads rejects it.
    """
    records: list[dict] = []
    for lineno, line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            return records, f"line {lineno} is not valid JSON: {exc}"
        if required_key not in record:
            return records, (
                f"line {lineno} has no '{required_key}' key — this looks like the "
                f"other label file. Check which download you are pointing where."
            )
        records.append(record)
    if not records:
        return [], "file contains no records"
    return records, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--downloads",
        default=str(Path.home() / "Downloads"),
        help="folder the browser saved the files into",
    )
    parser.add_argument(
        "--batch", default="v1",
        help="which batch these labels belong to; must match the --batch used "
             "when the labelling page was generated",
    )
    args = parser.parse_args()

    downloads = Path(args.downloads)
    if not downloads.is_dir():
        raise SystemExit(f"Downloads folder not found: {downloads}")

    moved = 0
    for filename, destination_template, required_key in TRANSFERS:
        destination = destination_template.format(batch=args.batch)
        source = downloads / filename
        if not source.exists():
            print(f"  skip    {filename} — not in {downloads}")
            continue

        records, error = _validate(source, required_key)
        if error:
            print(f"  REFUSED {filename} — {error}")
            continue

        target = Path(config.BASE_DIR) / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        # Rewrite rather than byte-copy, so the installed file is always clean
        # UTF-8 with newline endings regardless of what the browser or an editor
        # produced. A copied BOM would break every downstream reader instead.
        target.write_text(
            "".join(json.dumps(r) + "\n" for r in records), encoding="utf-8"
        )
        print(f"  ok      {filename} -> {destination}  ({len(records)} records)")
        moved += 1

    if not moved:
        raise SystemExit(
            "\nNothing installed. Label some clips first:\n"
            "  1. python -m scripts.export_eval_set\n"
            "  2. open datasets/label_eval.html\n"
            "  3. download both files, then re-run this"
        )

    print(f"\ninstalled {moved} file(s). Next:")
    print("  python -m scripts.evaluate_emotion")
    print("  python -m pytest tests/test_emotion_quality.py tests/test_ml_classifier_quality.py -v")


if __name__ == "__main__":
    main()
