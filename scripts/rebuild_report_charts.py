from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parents[1]
EVAL_PATH = BASE_DIR / "eval_report_v2.json"
HISTORY_PATH = BASE_DIR / "datasets" / "scene_type" / "v2_full" / "training_history.json"
ANNOTATIONS_PATH = BASE_DIR / "datasets" / "scene_type" / "v2_full" / "annotations.jsonl"
FIGURE_DIR = BASE_DIR / "report_assets" / "figures"

W, H = 1600, 900
BG = "#ffffff"
TEXT = "#172033"
MUTED = "#5b6472"
GRID = "#d9dee8"
AXIS = "#8a94a6"
BLUE = "#2f6fdd"
GREEN = "#168a5b"
ORANGE = "#d9822b"
RED = "#c23b4b"
PURPLE = "#7156d9"


LABEL_NAMES = {
    "b-roll": "B-roll",
    "testimonial": "Testimonial",
    "other": "Other",
    "audience_reaction": "Audience Reaction",
    "establishing_shot": "Establishing",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


FONT_TITLE = font(38, True)
FONT_SUBTITLE = font(24, False)
FONT_LABEL = font(22, False)
FONT_SMALL = font(18, False)
FONT_SMALL_BOLD = font(18, True)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def friendly(label: str) -> str:
    return LABEL_NAMES.get(label, label.replace("_", " ").title())


def new_canvas(title: str, subtitle: str | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.text((70, 46), title, fill=TEXT, font=FONT_TITLE)
    if subtitle:
        draw.text((72, 94), subtitle, fill=MUTED, font=FONT_SUBTITLE)
    return img, draw


def save(img: Image.Image, filename: str):
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    img.save(FIGURE_DIR / filename, "PNG", optimize=True)


def nice_ticks(min_val: float, max_val: float, count: int = 6) -> list[float]:
    if min_val == max_val:
        return [min_val]
    step = (max_val - min_val) / (count - 1)
    return [min_val + i * step for i in range(count)]


def chart_area(top: int = 160) -> tuple[int, int, int, int]:
    return 150, top, W - 90, H - 135


def draw_axes(
    draw: ImageDraw.ImageDraw,
    area: tuple[int, int, int, int],
    x_labels: list[str],
    y_min: float,
    y_max: float,
    y_suffix: str = "",
):
    left, top, right, bottom = area
    draw.line((left, top, left, bottom), fill=AXIS, width=2)
    draw.line((left, bottom, right, bottom), fill=AXIS, width=2)

    for tick in nice_ticks(y_min, y_max):
        y = bottom - (tick - y_min) / (y_max - y_min) * (bottom - top)
        draw.line((left, y, right, y), fill=GRID, width=1)
        label = f"{tick:.0f}{y_suffix}" if y_suffix else f"{tick:.2f}".rstrip("0").rstrip(".")
        tw = draw.textlength(label, font=FONT_SMALL)
        draw.text((left - tw - 14, y - 10), label, fill=MUTED, font=FONT_SMALL)

    if x_labels:
        span = right - left
        n = len(x_labels)
        for i, label in enumerate(x_labels):
            x = left + (i / max(1, n - 1)) * span
            tw = draw.textlength(label, font=FONT_SMALL)
            draw.text((x - tw / 2, bottom + 22), label, fill=MUTED, font=FONT_SMALL)


def value_to_point(
    area: tuple[int, int, int, int],
    idx: int,
    n: int,
    value: float,
    y_min: float,
    y_max: float,
) -> tuple[float, float]:
    left, top, right, bottom = area
    x = left + (idx / max(1, n - 1)) * (right - left)
    y = bottom - (value - y_min) / (y_max - y_min) * (bottom - top)
    return x, y


def draw_legend(draw: ImageDraw.ImageDraw, items: list[tuple[str, str]], x: int, y: int):
    cursor = x
    for label, color in items:
        draw.rounded_rectangle((cursor, y, cursor + 34, y + 18), radius=4, fill=color)
        draw.text((cursor + 44, y - 2), label, fill=TEXT, font=FONT_SMALL)
        cursor += int(draw.textlength(label, font=FONT_SMALL)) + 88


def plot_accuracy(history: list[dict]):
    img, draw = new_canvas(
        "Training and Validation Accuracy (v2)",
        "Current 14-epoch run from datasets/scene_type/v2_full/training_history.json",
    )
    area = chart_area()
    epochs = [str(row["epoch"]) for row in history]
    draw_axes(draw, area, epochs, 40, 100, "%")

    series = [
        ("Training accuracy", [row["train_acc"] for row in history], BLUE),
        ("Validation accuracy", [row["val_acc"] for row in history], GREEN),
        ("Validation balanced accuracy", [row["bal_acc"] for row in history], ORANGE),
    ]
    for _, values, color in series:
        points = [value_to_point(area, i, len(values), v, 40, 100) for i, v in enumerate(values)]
        draw.line(points, fill=color, width=5, joint="curve")
        for x, y in points:
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color, outline=BG, width=2)

    draw_legend(draw, [(name, color) for name, _, color in series], 150, 805)
    save(img, "figure_7_1_training_validation_accuracy.png")


def plot_loss(history: list[dict]):
    img, draw = new_canvas(
        "Training and Validation Loss (v2)",
        "Cross-entropy loss from the current training history",
    )
    area = chart_area()
    epochs = [str(row["epoch"]) for row in history]
    max_loss = max(row["val_loss"] for row in history) + 0.15
    draw_axes(draw, area, epochs, 0, max_loss)

    series = [
        ("Training loss", [row["train_loss"] for row in history], BLUE),
        ("Validation loss", [row["val_loss"] for row in history], RED),
    ]
    for _, values, color in series:
        points = [value_to_point(area, i, len(values), v, 0, max_loss) for i, v in enumerate(values)]
        draw.line(points, fill=color, width=5, joint="curve")
        for x, y in points:
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color, outline=BG, width=2)

    draw_legend(draw, [(name, color) for name, _, color in series], 150, 805)
    save(img, "figure_7_2_training_validation_loss.png")


def plot_per_class(per_class: dict, classes: list[str]):
    img, draw = new_canvas(
        "Per-Class Test Metrics (v2)",
        "Precision, recall, and F1-score from eval_report_v2.json",
    )
    left, top, right, bottom = 150, 160, W - 90, 700
    draw_axes(draw, (left, top, right, bottom), [], 0, 1.0)
    group_w = (right - left) / len(classes)
    bar_w = group_w * 0.22
    metrics = [("precision", "Precision", BLUE), ("recall", "Recall", GREEN), ("f1", "F1-score", ORANGE)]

    for i, cls in enumerate(classes):
        center = left + group_w * (i + 0.5)
        for j, (key, _, color) in enumerate(metrics):
            val = float(per_class[cls][key])
            x0 = center + (j - 1) * bar_w * 1.15 - bar_w / 2
            x1 = x0 + bar_w
            y = bottom - val * (bottom - top)
            draw.rounded_rectangle((x0, y, x1, bottom), radius=6, fill=color)
            label = f"{val:.2f}"
            tw = draw.textlength(label, font=FONT_SMALL)
            draw.text((x0 + (bar_w - tw) / 2, y - 25), label, fill=TEXT, font=FONT_SMALL)
        name = friendly(cls)
        words = name.split()
        if len(words) > 1:
            text = "\n".join(words)
            y_label = bottom + 16
        else:
            text = name
            y_label = bottom + 28
        bbox = draw.multiline_textbbox((0, 0), text, font=FONT_SMALL, spacing=2, align="center")
        draw.multiline_text((center - (bbox[2] - bbox[0]) / 2, y_label), text, fill=MUTED,
                            font=FONT_SMALL, spacing=2, align="center")

    draw_legend(draw, [(label, color) for _, label, color in metrics], 150, 810)
    save(img, "figure_7_3_per_class_metrics.png")


def plot_distribution(per_class: dict, classes: list[str]):
    img, draw = new_canvas(
        "Held-Out Test Set Class Distribution (v2)",
        "Support counts used in eval_report_v2.json",
    )
    left, top, right, bottom = 150, 160, W - 90, 700
    supports = [int(per_class[cls]["support"]) for cls in classes]
    max_count = max(supports)
    y_max = max_count + 15
    draw_axes(draw, (left, top, right, bottom), [], 0, y_max)
    group_w = (right - left) / len(classes)
    bar_w = group_w * 0.36
    for i, cls in enumerate(classes):
        center = left + group_w * (i + 0.5)
        val = int(per_class[cls]["support"])
        x0 = center - bar_w / 2
        x1 = center + bar_w / 2
        y = bottom - (val / y_max) * (bottom - top)
        draw.rounded_rectangle((x0, y, x1, bottom), radius=6, fill=BLUE)
        label = str(val)
        tw = draw.textlength(label, font=FONT_SMALL)
        draw.text((x0 + (bar_w - tw) / 2, y - 25), label, fill=TEXT, font=FONT_SMALL)
        name = friendly(cls)
        bbox = draw.textbbox((0, 0), name, font=FONT_SMALL)
        draw.text((center - (bbox[2] - bbox[0]) / 2, bottom + 28), name, fill=MUTED, font=FONT_SMALL)

    save(img, "figure_7_4_dataset_class_distribution.png")


def blend_blue(value: float, max_value: int) -> tuple[int, int, int]:
    t = 0 if max_value == 0 else value / max_value
    light = (235, 242, 255)
    dark = (47, 111, 221)
    return tuple(int(light[i] + (dark[i] - light[i]) * t) for i in range(3))


def plot_confusion_matrix(confusion: dict):
    classes = confusion["classes"]
    matrix = confusion["matrix"]
    img, draw = new_canvas(
        "Test Confusion Matrix (v2)",
        "Rows are true labels; columns are predicted labels",
    )
    n = len(classes)
    left, top = 380, 235
    cell = 132
    max_value = max(max(row) for row in matrix)

    for j, cls in enumerate(classes):
        label = friendly(cls).replace("Audience Reaction", "Audience\nReaction")
        bbox = draw.multiline_textbbox((0, 0), label, font=FONT_SMALL, spacing=2, align="center")
        draw.multiline_text((left + j * cell + cell / 2 - (bbox[2] - bbox[0]) / 2, top - 72),
                            label, fill=MUTED, font=FONT_SMALL, spacing=2, align="center")
    for i, cls in enumerate(classes):
        label = friendly(cls)
        bbox = draw.textbbox((0, 0), label, font=FONT_SMALL)
        draw.text((left - 32 - (bbox[2] - bbox[0]), top + i * cell + 50),
                  label, fill=MUTED, font=FONT_SMALL)

    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            x0 = left + j * cell
            y0 = top + i * cell
            fill = blend_blue(value, max_value)
            draw.rectangle((x0, y0, x0 + cell, y0 + cell), fill=fill, outline=BG, width=4)
            color = "#ffffff" if value > max_value * 0.55 else TEXT
            text = str(value)
            bbox = draw.textbbox((0, 0), text, font=FONT_SUBTITLE)
            draw.text((x0 + cell / 2 - (bbox[2] - bbox[0]) / 2,
                       y0 + cell / 2 - (bbox[3] - bbox[1]) / 2),
                      text, fill=color, font=FONT_SUBTITLE)

    draw.text((left + n * cell / 2 - 72, top + n * cell + 54), "Predicted label", fill=TEXT, font=FONT_LABEL)
    draw.text((82, top + n * cell / 2 - 20), "True label", fill=TEXT, font=FONT_LABEL)
    save(img, "figure_7_5_confusion_matrix.png")


def main():
    eval_report = load_json(EVAL_PATH)
    history = load_json(HISTORY_PATH)
    classes = eval_report["classes"]
    label_merge = eval_report.get("label_merge", {})

    plot_accuracy(history)
    plot_loss(history)
    plot_per_class(eval_report["per_class"], classes)
    plot_distribution(eval_report["per_class"], classes)
    plot_confusion_matrix(eval_report["confusion_matrix"])

    source_summary = {
        "source_eval_report": str(EVAL_PATH),
        "source_training_history": str(HISTORY_PATH),
        "source_annotations": str(ANNOTATIONS_PATH),
        "generated_from": "Current v2 project evaluation artefacts; no synthetic chart data.",
        "generated_figures": [
            "figure_7_1_training_validation_accuracy.png",
            "figure_7_2_training_validation_loss.png",
            "figure_7_3_per_class_metrics.png",
            "figure_7_4_dataset_class_distribution.png",
            "figure_7_5_confusion_matrix.png",
        ],
    }
    with (FIGURE_DIR / "figure_7_sources.json").open("w", encoding="utf-8") as f:
        json.dump(source_summary, f, indent=2)


if __name__ == "__main__":
    main()
