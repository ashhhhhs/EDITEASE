"""
Rebuild Figures 7.1 .. 7.5 of the FYP report from the fresh held-out test
evaluation (artifacts/eval_report_v2_test.json) and the trainer's
training_history.json. Overwrites the PNGs in
_archive/reports/report_assets/figures/.

Run with:
    /mnt/d/EDITEASE/venv/bin/python scripts/report/rebuild_eval_figures.py
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

BASE = "/mnt/d/EDITEASE"
EVAL = os.path.join(BASE, "artifacts", "eval_report_v2_test.json")
FIGURES = os.path.join(BASE, "_archive", "reports", "report_assets", "figures")
os.makedirs(FIGURES, exist_ok=True)

BG = "#0d1117"; BG2 = "#161b22"; BG3 = "#21262d"; BORDER = "#30363d"
TEXT = "#e6edf3"; TEXT2 = "#8b949e"
BLUE = "#58a6ff"; GREEN = "#3fb950"; ORANGE = "#d29922"; RED = "#f85149"
PURPLE = "#bc8cff"; TEAL = "#39d3f2"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG2, "axes.edgecolor": BORDER,
    "text.color": TEXT, "axes.labelcolor": TEXT,
    "xtick.color": TEXT2, "ytick.color": TEXT2,
    "grid.color": BORDER, "grid.alpha": 0.5,
    "font.family": "monospace", "font.size": 10,
})

DISPLAY = {
    "b-roll": "B-Roll",
    "testimonial": "Testimonial",
    "other": "Other",
    "audience_reaction": "Audience\nReaction",
    "establishing_shot": "Establishing\nShot",
}
SHORT = {
    "b-roll": "B-Roll", "testimonial": "Testimonial", "other": "Other",
    "audience_reaction": "Audience", "establishing_shot": "Establishing",
}


def save(fig, name):
    p = os.path.join(FIGURES, name)
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  saved {p}")


def fig_7_1(data):
    hist = data["history"]
    epochs = [h["epoch"] for h in hist]
    train = [h["train_acc"] for h in hist]
    val = [h["val_acc"] for h in hist]

    peak_i = int(np.argmax(val))
    peak_e = epochs[peak_i]; peak_v = val[peak_i]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG2)
    ax.plot(epochs, train, color=BLUE, marker="o", ms=5, lw=2, label="Train Accuracy")
    ax.plot(epochs, val, color=GREEN, marker="s", ms=5, lw=2, label="Val Accuracy")
    ax.annotate(f"Peak val\n{peak_v:.2f}% @ epoch {peak_e}",
                xy=(peak_e, peak_v), xytext=(peak_e + 1.5, peak_v - 12),
                arrowprops=dict(arrowstyle="-|>", color=TEXT2, lw=1),
                color=TEXT2, fontsize=8)
    ax.set_xlabel("Epoch"); ax.set_ylabel("Accuracy (%)")
    ax.set_title(f"Training vs Validation Accuracy over {len(epochs)} Epochs",
                 color=TEXT, fontsize=12, fontweight="bold")
    ax.set_xlim(0.5, len(epochs) + 0.5); ax.set_ylim(40, 105)
    ax.set_xticks(epochs)
    ax.legend(facecolor=BG3, edgecolor=BORDER, labelcolor=TEXT)
    ax.grid(True, alpha=0.3)
    for sp in ax.spines.values(): sp.set_color(BORDER)
    fig.tight_layout()
    save(fig, "figure_7_1_training_validation_accuracy.png")


def fig_7_2(data):
    hist = data["history"]
    epochs = [h["epoch"] for h in hist]
    train = [h["train_loss"] for h in hist]
    val = [h["val_loss"] for h in hist]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG2)
    ax.plot(epochs, train, color=ORANGE, marker="o", ms=5, lw=2, label="Train Loss")
    ax.plot(epochs, val, color=RED, marker="s", ms=5, lw=2, label="Val Loss")
    ax.set_xlabel("Epoch"); ax.set_ylabel("Cross-Entropy Loss")
    ax.set_title(f"Training vs Validation Loss over {len(epochs)} Epochs",
                 color=TEXT, fontsize=12, fontweight="bold")
    ax.set_xlim(0.5, len(epochs) + 0.5)
    ax.set_xticks(epochs)
    ax.legend(facecolor=BG3, edgecolor=BORDER, labelcolor=TEXT)
    ax.grid(True, alpha=0.3)
    for sp in ax.spines.values(): sp.set_color(BORDER)
    fig.tight_layout()
    save(fig, "figure_7_2_training_validation_loss.png")


def fig_7_3(data):
    classes = data["classes"]
    labels = [DISPLAY[c] for c in classes]
    prec = [data["per_class"][c]["precision"] for c in classes]
    rec = [data["per_class"][c]["recall"] for c in classes]
    f1 = [data["per_class"][c]["f1"] for c in classes]

    x = np.arange(len(classes)); w = 0.25
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG2)
    b1 = ax.bar(x - w, prec, w, label="Precision", color=BLUE, alpha=0.85)
    b2 = ax.bar(x, rec, w, label="Recall", color=GREEN, alpha=0.85)
    b3 = ax.bar(x + w, f1, w, label="F1-Score", color=PURPLE, alpha=0.85)
    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01, f"{h:.2f}",
                    ha="center", va="bottom", color=TEXT2, fontsize=7.5)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 1.15); ax.set_ylabel("Score")
    ax.set_title("Per-Class Precision, Recall and F1-Score (held-out test set)",
                 color=TEXT, fontsize=12, fontweight="bold")
    ax.legend(facecolor=BG3, edgecolor=BORDER, labelcolor=TEXT)
    ax.grid(True, axis="y", alpha=0.3)
    for sp in ax.spines.values(): sp.set_color(BORDER)
    fig.tight_layout()
    save(fig, "figure_7_3_per_class_metrics.png")


def fig_7_4(data):
    classes = data["classes"]
    labels = [DISPLAY[c] for c in classes]
    counts = [data["per_class"][c]["support"] for c in classes]
    colors = [BLUE, GREEN, ORANGE, PURPLE, TEAL][: len(classes)]
    total = sum(counts)

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG2)
    bars = ax.barh(labels, counts, color=colors, alpha=0.85, height=0.55)
    for bar, cnt in zip(bars, counts):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                str(cnt), va="center", color=TEXT, fontsize=10)
    ax.set_xlabel("Number of Scenes")
    ax.set_title(f"Held-Out Test Set Class Distribution (n={total})",
                 color=TEXT, fontsize=12, fontweight="bold")
    ax.set_xlim(0, max(counts) * 1.2)
    for sp in ax.spines.values(): sp.set_color(BORDER)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    save(fig, "figure_7_4_dataset_class_distribution.png")


def fig_7_5(data):
    classes = data["confusion_matrix"]["classes"]
    cm = np.array(data["confusion_matrix"]["matrix"])
    labels = [SHORT[c] for c in classes]
    n = sum(data["per_class"][c]["support"] for c in classes)

    cmap = LinearSegmentedColormap.from_list("gh_dark", [BG2, BLUE], N=256)
    fig, ax = plt.subplots(figsize=(8, 7))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG2)
    im = ax.imshow(cm, cmap=cmap, interpolation="nearest")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9, rotation=20, ha="right")
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix (held-out test set, n={n})",
                 color=TEXT, fontsize=12, fontweight="bold")
    thresh = cm.max() / 2 if cm.max() > 0 else 1
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(int(cm[i, j])), ha="center", va="center",
                    color=TEXT if cm[i, j] < thresh else BG,
                    fontsize=12, fontweight="bold")
    for sp in ax.spines.values(): sp.set_color(BORDER)
    fig.tight_layout()
    save(fig, "figure_7_5_confusion_matrix.png")


def main():
    data = json.load(open(EVAL))
    print(f"Rebuilding figures from {EVAL}")
    print(f"  test_accuracy={data['test_accuracy']}  macro_f1={data['test_macro_f1']}  weighted_f1={data['test_weighted_f1']}")
    fig_7_1(data)
    fig_7_2(data)
    fig_7_3(data)
    fig_7_4(data)
    fig_7_5(data)


if __name__ == "__main__":
    main()
