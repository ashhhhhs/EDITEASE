"""
Generate all architectural diagrams and charts for the EditEase Final Report.
Outputs to report_assets/figures/ and report_assets/screenshots/ where applicable.
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as mpatch
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.patches import ConnectionPatch
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap

# ── Colour palette (GitHub-Dark)
BG     = "#0d1117"
BG2    = "#161b22"
BG3    = "#21262d"
BORDER = "#30363d"
TEXT   = "#e6edf3"
TEXT2  = "#8b949e"
BLUE   = "#58a6ff"
GREEN  = "#3fb950"
ORANGE = "#d29922"
RED    = "#f85149"
PURPLE = "#bc8cff"
TEAL   = "#39d3f2"
YELLOW = "#e3b341"

FIGURES = "report_assets/figures"
os.makedirs(FIGURES, exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   BG2,
    "axes.edgecolor":   BORDER,
    "text.color":       TEXT,
    "axes.labelcolor":  TEXT,
    "xtick.color":      TEXT2,
    "ytick.color":      TEXT2,
    "grid.color":       BORDER,
    "grid.alpha":       0.5,
    "font.family":      "monospace",
    "font.size":        10,
})

# ─── helpers ─────────────────────────────────────────────────────────────────

def save(fig, name):
    path = os.path.join(FIGURES, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  saved {path}")

def diagram_fig(w=14, h=8):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor(BG)
    return fig, ax

def box(ax, x, y, w, h, label, color=BG3, textcolor=TEXT, fontsize=9,
        sublabel=None, radius=0.01, bold=False):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle=f"round,pad=0.5", linewidth=1,
                           edgecolor=BORDER, facecolor=color)
    ax.add_patch(rect)
    weight = "bold" if bold else "normal"
    ax.text(x, y + (1 if sublabel else 0), label, ha="center", va="center",
            color=textcolor, fontsize=fontsize, fontweight=weight)
    if sublabel:
        ax.text(x, y - 2, sublabel, ha="center", va="center",
                color=TEXT2, fontsize=7)

def arrow(ax, x1, y1, x2, y2, color=BORDER, lw=1.2, arrowstyle="-|>"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=arrowstyle, color=color,
                                lw=lw, mutation_scale=12))

def title_label(ax, text, x=50, y=97, fontsize=12):
    ax.text(x, y, text, ha="center", va="center", color=TEXT,
            fontsize=fontsize, fontweight="bold")

# ─── Figure 7.1 – Training vs Validation Accuracy ────────────────────────────
def fig_7_1():
    with open("eval_report_v2.json") as f:
        data = json.load(f)
    epochs = [h["epoch"] for h in data["history"]]
    train  = [h["train_acc"] for h in data["history"]]
    val    = [h["val_acc"]   for h in data["history"]]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG2)
    ax.plot(epochs, train, color=BLUE,  marker="o", ms=5, lw=2, label="Train Accuracy")
    ax.plot(epochs, val,   color=GREEN, marker="s", ms=5, lw=2, label="Val Accuracy")
    # annotate peak
    peak_epoch = 9; peak_val = 76.85
    ax.annotate(f"Peak val\n{peak_val}% @ epoch {peak_epoch}",
                xy=(peak_epoch, peak_val), xytext=(peak_epoch+1.5, peak_val-12),
                arrowprops=dict(arrowstyle="-|>", color=TEXT2, lw=1),
                color=TEXT2, fontsize=8)
    ax.set_xlabel("Epoch"); ax.set_ylabel("Accuracy (%)")
    ax.set_title("Training vs Validation Accuracy over 14 Epochs", color=TEXT, fontsize=12, fontweight="bold")
    ax.set_xlim(0.5, 14.5); ax.set_ylim(40, 105)
    ax.set_xticks(epochs)
    ax.legend(facecolor=BG3, edgecolor=BORDER, labelcolor=TEXT)
    ax.grid(True, alpha=0.3)
    for sp in ax.spines.values(): sp.set_color(BORDER)
    fig.tight_layout()
    save(fig, "figure_7_1_training_validation_accuracy.png")

# ─── Figure 7.2 – Training vs Validation Loss ────────────────────────────────
def fig_7_2():
    with open("eval_report_v2.json") as f:
        data = json.load(f)
    epochs = [h["epoch"] for h in data["history"]]
    train  = [h["train_loss"] for h in data["history"]]
    val    = [h["val_loss"]   for h in data["history"]]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG2)
    ax.plot(epochs, train, color=ORANGE, marker="o", ms=5, lw=2, label="Train Loss")
    ax.plot(epochs, val,   color=RED,    marker="s", ms=5, lw=2, label="Val Loss")
    ax.set_xlabel("Epoch"); ax.set_ylabel("Cross-Entropy Loss")
    ax.set_title("Training vs Validation Loss over 14 Epochs", color=TEXT, fontsize=12, fontweight="bold")
    ax.set_xlim(0.5, 14.5)
    ax.set_xticks(epochs)
    ax.legend(facecolor=BG3, edgecolor=BORDER, labelcolor=TEXT)
    ax.grid(True, alpha=0.3)
    for sp in ax.spines.values(): sp.set_color(BORDER)
    fig.tight_layout()
    save(fig, "figure_7_2_training_validation_loss.png")

# ─── Figure 7.3 – Per-Class Precision, Recall, F1 ────────────────────────────
def fig_7_3():
    with open("eval_report_v2.json") as f:
        data = json.load(f)
    classes  = ["B-Roll", "Testimonial", "Other", "Audience\nReaction", "Establishing\nShot"]
    keys     = ["b-roll", "testimonial", "other", "audience_reaction", "establishing_shot"]
    prec = [data["per_class"][k]["precision"] for k in keys]
    rec  = [data["per_class"][k]["recall"]    for k in keys]
    f1   = [data["per_class"][k]["f1"]        for k in keys]

    x   = np.arange(len(classes))
    w   = 0.25
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG2)

    b1 = ax.bar(x - w, prec, w, label="Precision", color=BLUE,   alpha=0.85)
    b2 = ax.bar(x,     rec,  w, label="Recall",    color=GREEN,  alpha=0.85)
    b3 = ax.bar(x + w, f1,   w, label="F1-Score",  color=PURPLE, alpha=0.85)

    for bars in [b1, b2, b3]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.01, f"{h:.2f}",
                    ha="center", va="bottom", color=TEXT2, fontsize=7.5)

    ax.set_xticks(x); ax.set_xticklabels(classes, fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score")
    ax.set_title("Per-Class Precision, Recall and F1-Score (v2 Model)", color=TEXT, fontsize=12, fontweight="bold")
    ax.legend(facecolor=BG3, edgecolor=BORDER, labelcolor=TEXT)
    ax.grid(True, axis="y", alpha=0.3)
    for sp in ax.spines.values(): sp.set_color(BORDER)
    fig.tight_layout()
    save(fig, "figure_7_3_per_class_metrics.png")

# ─── Figure 7.4 – Class Distribution ─────────────────────────────────────────
def fig_7_4():
    classes = ["B-Roll", "Testimonial", "Other", "Audience\nReaction", "Establishing\nShot"]
    counts  = [38, 12, 9, 7, 4]
    colors  = [BLUE, GREEN, ORANGE, PURPLE, TEAL]

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG2)

    bars = ax.barh(classes, counts, color=colors, alpha=0.85, height=0.55)
    for bar, cnt in zip(bars, counts):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                str(cnt), va="center", color=TEXT, fontsize=10)

    ax.set_xlabel("Number of Scenes")
    ax.set_title("Held-Out Test Set Class Distribution (n=70)", color=TEXT, fontsize=12, fontweight="bold")
    ax.set_xlim(0, 46)
    for sp in ax.spines.values(): sp.set_color(BORDER)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    save(fig, "figure_7_4_dataset_class_distribution.png")

# ─── Figure 7.5 – Confusion Matrix ───────────────────────────────────────────
def fig_7_5():
    with open("eval_report_v2.json") as f:
        data = json.load(f)
    cm      = np.array(data["confusion_matrix"]["matrix"])
    labels  = ["B-Roll", "Testimonial", "Other", "Audience", "Establishing"]

    cmap = LinearSegmentedColormap.from_list("gh_dark", [BG2, BLUE], N=256)

    fig, ax = plt.subplots(figsize=(8, 7))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG2)

    im = ax.imshow(cm, cmap=cmap, interpolation="nearest")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9, rotation=20, ha="right")
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix (Test Set, n=70)", color=TEXT, fontsize=12, fontweight="bold")

    thresh = cm.max() / 2
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color=TEXT if cm[i, j] < thresh else BG, fontsize=12, fontweight="bold")

    for sp in ax.spines.values(): sp.set_color(BORDER)
    fig.tight_layout()
    save(fig, "figure_7_5_confusion_matrix.png")

# ─── Figure 5.1 – System Architecture ────────────────────────────────────────
def fig_5_1():
    fig, ax = diagram_fig(16, 10)
    title_label(ax, "Figure 5.1 – EditEase System Architecture")

    tiers = [
        ("INPUT",        93, [("React Upload UI", BLUE),   ("Drag-and-Drop", BLUE), ("Auth (JWT/OAuth)", BLUE)]),
        ("PROCESSING",   76, [("Celery Worker", ORANGE),   ("PySceneDetect", ORANGE), ("ResNet-18 v2", ORANGE), ("DeepFace + Haar", ORANGE), ("Agentic Layer", ORANGE)]),
        ("STORAGE",      57, [("MongoDB\nscenes/tasks/users", GREEN), ("Cloudinary\nAssets CDN", GREEN), ("organized_videos", GREEN)]),
        ("BACKEND",      38, [("Flask + Blueprints", PURPLE), ("REST API", PURPLE), ("Celery Broker\n(Redis)", PURPLE)]),
        ("PRESENTATION", 18, [("Dashboard", TEAL), ("Inspector", TEAL), ("OrganizedVideos", TEAL), ("Admin Shell", TEAL), ("Landing Page", TEAL)]),
    ]

    for tier_name, y, items in tiers:
        # tier label on left
        ax.text(2, y, tier_name, ha="center", va="center", color=TEXT2, fontsize=8,
                fontweight="bold", rotation=0)
        # horizontal divider
        ax.axhline(y=y - 9, color=BORDER, lw=0.8, xmin=0.04, xmax=0.98)
        # boxes
        n = len(items); spacing = 78 / (n + 1)
        for i, (label, color) in enumerate(items):
            bx = 12 + spacing * (i + 1)
            bw = min(spacing - 2, 16)
            box(ax, bx, y, bw, 10, label, color=color+"22", textcolor=color, fontsize=7.5)

    # vertical arrows between tiers
    for ya, yb in [(84, 69), (66, 50), (48, 31), (29, 12)]:
        arrow(ax, 50, ya, 50, yb, color=BORDER, lw=1)

    save(fig, "figure_5_1_system_architecture.png")

# ─── Figure 5.2 – Functional Decomposition Diagram ───────────────────────────
def fig_5_2():
    fig, ax = diagram_fig(18, 11)
    title_label(ax, "Figure 5.2 – Functional Decomposition Diagram (FDD)")

    root_y = 88; root_x = 50
    box(ax, root_x, root_y, 22, 8, "EditEase", color=BLUE+"33", textcolor=BLUE, fontsize=12, bold=True)

    branches = [
        ("Video\nCapture", 10), ("Scene\nDetection", 21), ("Thumbnail\nExtraction", 32),
        ("ML\nClassification", 43), ("Emotion\nDetection", 54),
        ("Agentic\nDecision", 65), ("Metadata\nGeneration", 76),
        ("Database", 87), ("API", 93), ("UI", 99),
    ]
    mid_y = 65
    for label, bx in branches:
        box(ax, bx, mid_y, 8, 9, label, color=BG3, fontsize=7.5)
        arrow(ax, root_x, root_y - 4, bx, mid_y + 4.5, color=BORDER)

    # sub-branches for Agentic Decision and UI
    sub_agentic = [("Auto-Organize", 58), ("User Isolation", 72)]
    sub_y = 48
    for label, bx in sub_agentic:
        box(ax, bx, sub_y, 11, 7, label, color=GREEN+"22", textcolor=GREEN, fontsize=7)
        arrow(ax, 65, mid_y - 4.5, bx, sub_y + 3.5, color=GREEN+"88")

    sub_ui = [("Role-Aware\nAppShell", 88), ("Tour Guide", 100)]
    for label, bx in sub_ui:
        box(ax, bx, sub_y, 10, 7, label, color=PURPLE+"22", textcolor=PURPLE, fontsize=7)
        arrow(ax, 99, mid_y - 4.5, bx, sub_y + 3.5, color=PURPLE+"88")

    save(fig, "figure_5_2_functional_decomposition.png")

# ─── Figure 5.3 – Scene Detection Process ─────────────────────────────────────
def fig_5_3():
    fig, ax = diagram_fig(14, 7)
    title_label(ax, "Figure 5.3 – Process of Scene Detection")

    steps = [
        ("Raw\nVideo\nFile", 10),
        ("PySceneDetect\nContentDetector\n(threshold=27)", 28),
        ("HSV Frame\nDifference\nComputation", 46),
        ("Boundary\nTimestamps\nList", 64),
        ("Scene\nSegments\nList", 82),
    ]
    y = 55
    for label, x in steps:
        color = BLUE if x in [10, 82] else BG3
        tc    = BLUE if x in [10, 82] else TEXT
        box(ax, x, y, 14, 18, label, color=color+"22" if x in [10,82] else BG3, textcolor=tc, fontsize=8)

    for i in range(len(steps) - 1):
        arrow(ax, steps[i][1] + 7, y, steps[i+1][1] - 7, y, color=BORDER, lw=1.5)

    # fallback branch
    box(ax, 64, 22, 22, 10, "Zero-cut Fallback:\nWhole video → 1 scene", color=ORANGE+"22", textcolor=ORANGE, fontsize=7.5)
    ax.annotate("", xy=(64, 26), xytext=(64, 46),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE+"aa", lw=1.2,
                                connectionstyle="arc3,rad=0"))
    ax.text(68, 36, "no cuts\ndetected", color=ORANGE, fontsize=7.5, ha="left")

    save(fig, "figure_5_3_scene_detection.png")

# ─── Figure 5.4 – Thumbnail Extraction ───────────────────────────────────────
def fig_5_4():
    fig, ax = diagram_fig(16, 6)
    title_label(ax, "Figure 5.4 – Thumbnail Extraction Process")

    steps = [
        ("Scene\n(start, end)", 7),
        ("Compute\nMidpoint\nt = (s+e)/2", 20),
        ("OpenCV\nVideoCapture\n+ seek", 33),
        ("frame_idx =\nint(mid × fps)", 46),
        ("Read\nFrame", 59),
        ("Resize if\nwidth > 1280\n(aspect kept)", 72),
        ("JPEG\nEncode", 83),
        ("Cloudinary\nUpload", 93),
    ]
    y = 50
    for label, x in steps:
        c = BLUE if x in [7, 93] else BG3
        tc = BLUE if x in [7, 93] else TEXT
        box(ax, x, y, 11, 20, label, color=c+"22" if x in [7,93] else BG3, textcolor=tc, fontsize=7.5)

    for i in range(len(steps)-1):
        arrow(ax, steps[i][1]+5.5, y, steps[i+1][1]-5.5, y, color=BORDER)

    ax.text(93, 34, "URL stored\non scene doc", color=GREEN, fontsize=8, ha="center", va="center")
    arrow(ax, 93, 40, 93, 43, color=GREEN)

    save(fig, "figure_5_4_thumbnail_extraction_process.png")

# ─── Figure 5.5 – Database Schema ─────────────────────────────────────────────
def fig_5_5():
    fig, ax = diagram_fig(18, 12)
    title_label(ax, "Figure 5.5 – Scene Metadata Database Schema (MongoDB)")

    collections = {
        "scenes": (20, 62, [
            "[PK] _id (ObjectId)",
            "video_name (str)",
            "scene_label (str)",
            "ml_confidence (float)",
            "fused_label (str)",
            "thumbnail_url (str)",
            "start_time / end_time",
            "emotion_timeline []",
            "review_status (str)",
            "reviewer_notes (str)",
            "user_id (str) [idx]",
        ]),
        "tasks": (50, 62, [
            "[PK] task_id (str)",
            "status (str)",
            "video_name (str)",
            "created_at (datetime)",
            "meta.message (str)",
            "error_message (str)",
            "user_id (str) [idx]",
        ]),
        "users": (76, 62, [
            "[PK] _id (ObjectId)",
            "email (str)",
            "role (str)",
            "password_hash (str)",
            "tour_completed_at",
            "google_id (str)",
        ]),
        "organized_videos": (96, 62, [   # shifted right
            "[PK] _id (ObjectId)",
            "user_id (str) [idx]",
            "category (str)",
            "scene_ids [] [idx]",
            "cloudinary_folder",
        ]),
    }

    colors = [BLUE, ORANGE, GREEN, PURPLE]
    for (cname, (cx, cy, fields)), color in zip(collections.items(), colors):
        h = len(fields) * 4.5 + 8
        bx = cx; by = cy
        # header
        ax.add_patch(FancyBboxPatch((bx-13, by - h/2), 26, h,
                                    boxstyle="round,pad=0.5", lw=1,
                                    edgecolor=color+"88", facecolor=BG3))
        ax.text(bx, by + h/2 - 4, cname, ha="center", va="center",
                color=color, fontsize=9, fontweight="bold")
        ax.axhline(y=by + h/2 - 8, color=color+"44", lw=0.8,
                   xmin=(bx-13)/100, xmax=(bx+13)/100)
        for fi, field in enumerate(fields):
            ax.text(bx - 11, by + h/2 - 12 - fi * 4.5, field,
                    ha="left", va="center", color=TEXT2, fontsize=7)

    # index legend
    ax.text(50, 6, "[idx] = indexed field    [PK] = primary key", ha="center", va="center",
            color=TEXT2, fontsize=8)

    save(fig, "figure_5_5_metadata_database_schema.png")

# ─── Figure 5.7 – Data Flow Diagram ──────────────────────────────────────────
def fig_5_7():
    fig, ax = diagram_fig(16, 10)
    title_label(ax, "Figure 5.7 – End-to-End Data Flow Diagram")

    nodes = [
        ("User",            8,  50, TEAL),
        ("React\nUpload",   20, 50, BLUE),
        ("Flask\n/upload",  32, 50, PURPLE),
        ("Cloudinary\n+ Local", 44, 65, GREEN),
        ("Celery\nWorker",  56, 50, ORANGE),
        ("PyScene\nDetect", 68, 65, ORANGE),
        ("ML\nClassifier",  68, 35, ORANGE),
        ("Emotion\nSampler",80, 50, ORANGE),
        ("MongoDB",         88, 50, GREEN),
        ("React\nDashboard",76, 20, BLUE),
    ]

    for label, x, y, color in nodes:
        box(ax, x, y, 10, 11, label, color=color+"22", textcolor=color, fontsize=7.5)

    edges = [
        (8, 50, 20, 50), (20, 50, 32, 50), (32, 50, 44, 65),
        (44, 65, 56, 50), (56, 50, 68, 65), (56, 50, 68, 35),
        (68, 65, 80, 50), (68, 35, 80, 50), (80, 50, 88, 50),
        (88, 50, 76, 20),
    ]
    for x1,y1,x2,y2 in edges:
        arrow(ax, x1, y1, x2, y2, color=BORDER)

    # organized_videos side-branch
    box(ax, 92, 30, 14, 9, "organized_videos\n(Cloudinary folders)", color=GREEN+"22", textcolor=GREEN, fontsize=7)
    arrow(ax, 88, 46, 92, 34, color=GREEN+"88")
    arrow(ax, 92, 25, 76, 24, color=GREEN+"88")
    ax.text(86, 20, "/organized\nroute", color=GREEN, fontsize=7, ha="center")

    save(fig, "figure_5_7_data_flow_diagram.png")

# ─── Figure 5.8 – Auto-Organize Workflow ──────────────────────────────────────
def fig_5_8():
    fig, ax = diagram_fig(16, 7)
    title_label(ax, "Figure 5.8 – Agentic Auto-Organize Workflow")

    stages = [
        ("[1] Scenes in\nMongoDB\n(mixed labels)", 10),
        ("[2] Group by\nscene_label", 28),
        ("[3] Resolve\nCloudinary path\neditease/{uid}/{cat}/", 46),
        ("[4] Move/copy\nassets + update\npublic_id", 64),
        ("[5] Write\norganized_videos\nindex", 82),
    ]
    y = 55
    colors_s = [BLUE, ORANGE, PURPLE, ORANGE, GREEN]
    for (label, x), color in zip(stages, colors_s):
        box(ax, x, y, 14, 22, label, color=color+"22", textcolor=color, fontsize=8)

    for i in range(len(stages)-1):
        arrow(ax, stages[i][1]+7, y, stages[i+1][1]-7, y, color=BORDER, lw=2)

    # return arrow to UI
    box(ax, 82, 22, 16, 10, "React OrganizedVideos\n+ Category ZIP Download", color=TEAL+"22", textcolor=TEAL, fontsize=7.5)
    arrow(ax, 82, 44, 82, 27, color=TEAL, lw=1.5)
    ax.text(72, 35, "category\nZIP ↓", color=TEAL, fontsize=8, ha="center")

    save(fig, "figure_5_8_auto_organize_workflow.png")

# ─── Figure 5.9 – Role-Aware Navigation ───────────────────────────────────────
def fig_5_9():
    fig, ax = diagram_fig(14, 10)
    title_label(ax, "Figure 5.9 – Role-Aware App Shell and Navigation Map")

    # Editor sidebar
    ax.text(28, 88, "Editor View", ha="center", color=BLUE, fontsize=10, fontweight="bold")
    editor_items = ["Dashboard", "Upload", "Job Monitor", "Organized Videos", "Inspector / Editor", "Settings"]
    for i, item in enumerate(editor_items):
        y = 80 - i * 10
        box(ax, 28, y, 30, 8, item, color=BG3, fontsize=9)

    # Admin sidebar
    ax.text(72, 88, "Admin View", ha="center", color=PURPLE, fontsize=10, fontweight="bold")
    admin_extra = ["User Management", "Video Assignments"]
    for i, item in enumerate(editor_items):
        y = 80 - i * 10
        box(ax, 72, y, 30, 8, item, color=BG3, fontsize=9)
    for i, item in enumerate(admin_extra):
        y = 20 - i * 10
        box(ax, 72, y, 30, 8, item, color=PURPLE+"33", textcolor=PURPLE, fontsize=9)
        ax.text(60, y, "[lock]", fontsize=7, ha="center", va="center", color=PURPLE)

    # RoleGuard label
    box(ax, 50, 5, 22, 6, "RoleGuard wrapper", color=ORANGE+"22", textcolor=ORANGE, fontsize=8.5)

    save(fig, "figure_5_9_role_aware_navigation.png")

# ─── Figure 5.10 – User Isolation ────────────────────────────────────────────
def fig_5_10():
    fig, ax = diagram_fig(14, 10)
    title_label(ax, "Figure 5.10 – User Isolation Boundary Model")

    # Silo A
    ax.add_patch(FancyBboxPatch((5, 20), 35, 60, boxstyle="round,pad=1",
                                 lw=1.5, edgecolor=BLUE+"88", facecolor=BLUE+"11"))
    ax.text(22.5, 78, "User A", ha="center", color=BLUE, fontsize=10, fontweight="bold")
    for i, item in enumerate(["scenes (user_id=A)", "tasks (user_id=A)", "organized_videos (A)"]):
        box(ax, 22.5, 65 - i*14, 28, 9, item, color=BG3, fontsize=8)

    # Silo B
    ax.add_patch(FancyBboxPatch((58, 20), 35, 60, boxstyle="round,pad=1",
                                 lw=1.5, edgecolor=GREEN+"88", facecolor=GREEN+"11"))
    ax.text(75.5, 78, "User B", ha="center", color=GREEN, fontsize=10, fontweight="bold")
    for i, item in enumerate(["scenes (user_id=B)", "tasks (user_id=B)", "organized_videos (B)"]):
        box(ax, 75.5, 65 - i*14, 28, 9, item, color=BG3, fontsize=8)

    # Admin layer
    ax.add_patch(FancyBboxPatch((5, 84), 88, 12, boxstyle="round,pad=1",
                                 lw=1.5, edgecolor=PURPLE+"88", facecolor=PURPLE+"11"))
    ax.text(49, 90, "Admin Layer  (role='admin'  →  cross-user access)", ha="center",
            color=PURPLE, fontsize=9.5, fontweight="bold")
    arrow(ax, 22.5, 84, 22.5, 80, color=PURPLE+"88")
    arrow(ax, 75.5, 84, 75.5, 80, color=PURPLE+"88")

    # per-query filter note
    ax.text(49, 13, "Service layer enforces user_id filter on every query",
            ha="center", color=ORANGE, fontsize=8.5)
    arrow(ax, 22.5, 20, 22.5, 16, color=ORANGE+"88")
    arrow(ax, 75.5, 20, 75.5, 16, color=ORANGE+"88")

    save(fig, "figure_5_10_user_isolation_boundary.png")

# ─── Figure 6.1 – Video Processing Pipeline ──────────────────────────────────
def fig_6_1():
    fig, ax = diagram_fig(18, 10)
    title_label(ax, "Figure 6.1 – Pipeline of Video Processing (process_video)")

    stages = [
        ("Cloudinary\nUpload", 8, 70),
        ("detect_scenes()\nPySceneDetect", 22, 70),
        ("Extract\nMidpoint Frame", 36, 70),
        ("Upload\nThumbnail", 50, 70),
        ("MLClassifier\n.classify()", 64, 70),
        ("Agentic\nDecision\nLayer", 78, 70),
        ("sample_emotions\n_over_scene()", 64, 40),
        ("upsert_scene()\nMongoDB", 50, 40),
        ("Completion\nCallback", 36, 40),
    ]
    colors_p = [BLUE,BLUE,ORANGE,ORANGE,PURPLE,PURPLE,ORANGE,GREEN,GREEN]
    for (label, x, y), color in zip(stages, colors_p):
        box(ax, x, y, 11, 14, label, color=color+"22", textcolor=color, fontsize=7.5)

    # forward path arrows
    arrow(ax, 8+5.5, 70, 22-5.5, 70, color=BORDER)
    arrow(ax, 22+5.5, 70, 36-5.5, 70, color=BORDER)
    arrow(ax, 36+5.5, 70, 50-5.5, 70, color=BORDER)
    arrow(ax, 50+5.5, 70, 64-5.5, 70, color=BORDER)
    arrow(ax, 64+5.5, 70, 78-5.5, 70, color=BORDER)

    # loop back
    arrow(ax, 78, 63, 64, 47, color=ORANGE)
    arrow(ax, 64, 33, 50, 47, color=GREEN)
    arrow(ax, 50-5.5, 40, 36+5.5, 40, color=BORDER)
    # loop label
    ax.text(72, 55, "per-scene\nloop", color=TEXT2, fontsize=7.5, ha="center")

    # fallback note
    box(ax, 64, 17, 18, 8, "Fallback: rule-based\nif torch unavailable", color=RED+"22", textcolor=RED, fontsize=7.5)
    arrow(ax, 64, 63, 64, 21, color=RED+"55", lw=0.8)

    # progress_callback
    ax.text(8, 45, "progress_callback()\nemitted at each stage", color=TEAL, fontsize=7.5, ha="center")
    arrow(ax, 22, 63, 22, 50, color=TEAL+"55")

    save(fig, "figure_6_1_video_processing_pipeline.png")

# ─── Figure 6.2 – ResNet-18 Architecture ─────────────────────────────────────
def fig_6_2():
    fig, ax = diagram_fig(16, 7)
    title_label(ax, "Figure 6.2 – ResNet-18 Architecture Adaptation for EditEase (v2 Head)")

    layers = [
        ("Conv1\n7×7, 64", 7,   BORDER, "frozen"),
        ("MaxPool\n3×3", 16,    BORDER, "frozen"),
        ("Layer 1\nRes Blocks", 25, BORDER, "frozen"),
        ("Layer 2\nRes Blocks", 34, BORDER, "frozen"),
        ("Layer 3\nRes Blocks", 43, BORDER, "frozen"),
        ("Layer 4\nRes Blocks", 54, BLUE+"44", "trainable"),
        ("Linear\n512→256",     64, GREEN+"44", "trainable"),
        ("LayerNorm\n+ ReLU",   73, GREEN+"44", "trainable"),
        ("Dropout\n(0.3)",      82, ORANGE+"44", "trainable"),
        ("Linear\n256→5",       91, PURPLE+"44", "trainable"),
    ]
    y = 55
    for label, x, color, state in layers:
        tc = TEXT2 if state == "frozen" else TEXT
        box(ax, x, y, 7.5, 16, label, color=color, textcolor=tc, fontsize=7)

    for i in range(len(layers)-1):
        arrow(ax, layers[i][1]+3.75, y, layers[i+1][1]-3.75, y, color=BORDER)

    # freeze boundary dashed line
    ax.axvline(x=48.5, color=ORANGE, lw=1.5, linestyle="--", alpha=0.7)
    ax.text(48.5, 76, "Partial Freeze\nBoundary", ha="center", color=ORANGE, fontsize=8)

    # legend
    legend_handles = [
        mpatches.Patch(color=BORDER,       label="Frozen (ImageNet weights)"),
        mpatches.Patch(color=BLUE+"44",    label="Trainable (Layer 4)"),
        mpatches.Patch(color=GREEN+"44",   label="New classification head"),
    ]
    ax.legend(handles=legend_handles, loc="lower center", facecolor=BG3, edgecolor=BORDER,
              labelcolor=TEXT, fontsize=7.5, ncol=3)

    save(fig, "figure_6_2_resnet_adaptation.png")

# ─── Figure 6.3 – Scene Metadata Document ─────────────────────────────────────
def fig_6_3():
    fig, ax = diagram_fig(14, 10)
    title_label(ax, "Figure 6.3 – Scene Metadata Document Structure (MongoDB)")

    json_lines = [
        ('{',                                                  TEXT),
        ('  "_id":      ObjectId("66f3a12b..."),',              TEXT2),
        ('  "video_name":      "C0039.MP4",',                 BLUE),
        ('  "start_time":      12.44,',                       BLUE),
        ('  "end_time":        19.72,',                       BLUE),
        ('  "scene_label":     "testimonial",',               GREEN),
        ('  "ml_confidence":   0.847,',                       GREEN),
        ('  "rb_confidence":   0.0,',                         TEXT2),
        ('  "fused_label":     "testimonial",',               GREEN),
        ('  "fused_confidence": 0.847,',                      GREEN),
        ('  "thumbnail_url":   "https://res.cloudinary..."',  TEAL),
        ('  "emotion_timeline": [',                           ORANGE),
        ('    {"time": 13.1, "emotion": "neutral", "conf": 0.89},', ORANGE),
        ('    {"time": 15.8, "emotion": "happy",   "conf": 0.72}',  ORANGE),
        ('  ],',                                              ORANGE),
        ('  "review_status":  "reviewed",',                  PURPLE),
        ('  "reviewer_notes": "Strong quote, keep.",',        PURPLE),
        ('  "user_id":        "usr_abc123"',                 RED),
        ('}',                                                  TEXT),
    ]

    ax.add_patch(FancyBboxPatch((4, 5), 92, 88, boxstyle="round,pad=1",
                                 lw=1, edgecolor=BORDER, facecolor="#0d1117"))
    for i, (line, color) in enumerate(json_lines):
        ax.text(7, 88 - i*4.5, line, ha="left", va="center",
                color=color, fontsize=8, fontfamily="monospace")

    save(fig, "figure_6_3_scene_metadata_document.png")

# ─── Figure 6.4 – Live Upload Progress Feed ───────────────────────────────────
def fig_6_4():
    fig, ax = diagram_fig(16, 10)
    title_label(ax, "Figure 6.4 – Live Upload Progress Feed (Celery → Mongo → React)")

    lanes = [("React\nUpload Page", 18, BLUE), ("Flask\nAPI", 50, PURPLE), ("Celery Worker\n+ MongoDB", 82, ORANGE)]
    for label, x, color in lanes:
        ax.add_patch(FancyBboxPatch((x-13, 5), 26, 88, boxstyle="square,pad=0",
                                    lw=1, edgecolor=color+"44", facecolor=color+"08"))
        ax.text(x, 92, label, ha="center", color=color, fontsize=9, fontweight="bold")

    events = [
        (80, "POST /upload (file)", 18, 50, BLUE),
        (70, "202 Accepted + task_id", 50, 18, PURPLE),
        (60, "poll /task_status/<id>\n(every 2s)", 18, 50, BLUE),
        (50, "Update Mongo stage", 82, 50, ORANGE),
        (40, "Return meta.message", 50, 18, PURPLE),
        (30, "Append to live feed UI", 18, 18, BLUE),
    ]
    for ey, label, x1, x2, color in events:
        arrow(ax, x1, ey, x2, ey, color=color, lw=1.2)
        mid = (x1 + x2) / 2
        ax.text(mid, ey + 3, label, ha="center", va="center", color=TEXT2, fontsize=7)

    # stage names
    stages = ["cloud upload", "scene detection", "per-scene analysis", "emotion inference", "classification", "storage"]
    for i, s in enumerate(stages):
        ax.text(82, 25 - i * 3, f"• {s}", ha="center", color=ORANGE, fontsize=6.5)

    save(fig, "figure_6_4_live_upload_progress_feed.png")

# ─── Figure 6.5 – Component Hierarchy ────────────────────────────────────────
def fig_6_5():
    fig, ax = diagram_fig(18, 12)
    title_label(ax, "Figure 6.5 – React Component Hierarchy")

    # Providers
    for i, p in enumerate(["AuthProvider", "ToastProvider", "UploadContext"]):
        box(ax, 20 + i*25, 90, 20, 7, p, color=TEAL+"22", textcolor=TEAL, fontsize=8)

    box(ax, 50, 78, 20, 7, "App\nBrowserRouter", color=BG3, fontsize=8.5, bold=True)

    # Public routes
    public = ["Landing", "Login", "Register", "Forgot", "Reset", "Verify", "Invite"]
    for i, r in enumerate(public):
        x = 5 + i * 13
        box(ax, x, 62, 10, 7, r, color=BLUE+"22", textcolor=BLUE, fontsize=7)
        arrow(ax, 50, 74.5, x, 65.5, color=BLUE+"55")

    # Protected (RoleGuard)
    box(ax, 50, 48, 22, 7, "RoleGuard\n(auth required)", color=ORANGE+"22", textcolor=ORANGE, fontsize=8)
    box(ax, 50, 36, 20, 7, "AppShell", color=PURPLE+"22", textcolor=PURPLE, fontsize=8.5, bold=True)
    arrow(ax, 50, 74.5, 50, 51.5, color=ORANGE)
    arrow(ax, 50, 44.5, 50, 39.5, color=PURPLE)

    protected = ["Dashboard", "Upload", "JobMonitor", "OrganizedVideos", "Inspector", "EditorView", "Settings"]
    for i, r in enumerate(protected):
        x = 10 + i * 13
        box(ax, x, 22, 11, 7, r, color=BG3, fontsize=7.5)
        arrow(ax, 50, 32.5, x, 25.5, color=BORDER)

    # Admin RoleGuard
    box(ax, 80, 28, 22, 7, "RoleGuard\n(role='admin')", color=RED+"22", textcolor=RED, fontsize=7.5)
    arrow(ax, 50, 74.5, 80, 31.5, color=RED+"55")
    for i, r in enumerate(["UserManagement", "VideoAssignments"]):
        x = 74 + i * 14
        box(ax, x, 16, 12, 7, r, color=RED+"11", textcolor=RED, fontsize=7)
        arrow(ax, 80, 24.5, x, 19.5, color=RED+"55")

    save(fig, "figure_6_5_component_hierarchy.png")

# ─── Figure 6.6 – Tour Guide Step Flow ───────────────────────────────────────
def fig_6_6():
    fig, ax = diagram_fig(16, 7)
    title_label(ax, "Figure 6.6 – Tour Guide Step Flow (react-joyride)")

    steps = [
        ("Step 1\nDashboard\nWelcome", 10),
        ("Step 2\nUpload Zone\nWalkthrough", 28),
        ("Step 3\nInspector\nPanel", 46),
        ("Step 4\nJob Monitor\nOverview", 64),
        ("Step 5\nSettings /\nReplay Tour", 82),
    ]
    y = 55
    for label, x in steps:
        box(ax, x, y, 14, 22, label, color=PURPLE+"22", textcolor=PURPLE, fontsize=8.5)
        # spotlight indicator
        ax.add_patch(plt.Circle((x, y-16), 4, color=YELLOW+"33", linewidth=1.5,
                                edgecolor=YELLOW, fill=True))
        ax.text(x, y-16, "*", ha="center", va="center", color=YELLOW, fontsize=8)

    for i in range(len(steps)-1):
        arrow(ax, steps[i][1]+7, y, steps[i+1][1]-7, y, color=BORDER, lw=1.5)

    # trigger
    box(ax, 10, 22, 18, 9, "Trigger:\nSettings → Replay Tour", color=BG3, fontsize=7.5)
    arrow(ax, 10, 26.5, 10, 44, color=TEXT2)

    # completion
    box(ax, 82, 22, 16, 9, "tour_completed_at\nsaved to MongoDB", color=GREEN+"22", textcolor=GREEN, fontsize=7.5)
    arrow(ax, 82, 44, 82, 26.5, color=GREEN)

    save(fig, "figure_6_6_tour_step_flow.png")

# ─── Figure 6.7 – Motion System ───────────────────────────────────────────────
def fig_6_7():
    fig, ax = diagram_fig(14, 8)
    title_label(ax, "Figure 6.7 – Cinematic Motion System (GSAP + Lenis)")

    box(ax, 50, 78, 24, 9, "MotionProvider", color=BLUE+"33", textcolor=BLUE, fontsize=10, bold=True)

    box(ax, 30, 60, 20, 8, "Lenis Instance\n(smooth scroll)", color=BG3, fontsize=8.5)
    box(ax, 70, 60, 20, 8, "GSAP Timeline\n(entry anims)", color=BG3, fontsize=8.5)

    arrow(ax, 43, 74, 30, 64, color=BLUE)
    arrow(ax, 57, 74, 70, 64, color=BLUE)

    outputs = [
        (15, 38, "Landing Sections\n(ScrollTrigger\nsubscribers)"),
        (50, 38, "Route Enter\nAnimations\n(AppShell)"),
        (82, 38, "prefers-reduced-\nmotion guard\n(a11y)"),
    ]
    for x, y, label in outputs:
        box(ax, x, y, 22, 14, label, color=BG3, fontsize=8)

    arrow(ax, 30, 56, 15, 45, color=ORANGE)
    arrow(ax, 70, 56, 50, 45, color=ORANGE)
    arrow(ax, 70, 56, 82, 45, color=GREEN)

    ax.text(50, 14, "Scroll-pinned pipeline: upload → detect → classify → organize", ha="center",
            color=TEXT2, fontsize=8.5, style="italic")

    save(fig, "figure_6_7_motion_system.png")

# ─── Figure 9.1 – Gantt Chart ─────────────────────────────────────────────────
def fig_9_1():
    tasks = [
        ("Requirements &\nConceptualisation",  "2025-09", "2025-10", BLUE),
        ("Literature Review",                   "2025-10", "2025-11", GREEN),
        ("Environment Setup",                   "2025-11", "2025-11", TEXT2),
        ("Pipeline Development",                "2025-11", "2025-12", ORANGE),
        ("Emotion + ML Classification",         "2025-11", "2025-12", ORANGE),
        ("Indexing / DB / Search",              "2025-12", "2026-01", PURPLE),
        ("Integration & Testing",               "2026-01", "2026-02", RED),
        ("Frontend Polish & Cinematic UI",      "2026-02", "2026-04", TEAL),
        ("Documentation & Report Writing",      "2026-02", "2026-05", YELLOW),
    ]

    months = ["Sep\n2025","Oct","Nov","Dec","Jan\n2026","Feb","Mar","Apr","May"]
    month_idx = {"2025-09":0,"2025-10":1,"2025-11":2,"2025-12":3,
                 "2026-01":4,"2026-02":5,"2026-03":6,"2026-04":7,"2026-05":8}

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG2)

    for i, (label, start, end, color) in enumerate(tasks):
        s = month_idx[start]; e = month_idx[end] + 1
        ax.barh(i, e - s, left=s, height=0.55, color=color, alpha=0.8)
        ax.text(s + 0.1, i, label.replace("\n", " "), va="center", ha="left",
                color=TEXT, fontsize=8.5, style="italic")

    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([""] * len(tasks))
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, fontsize=9)
    ax.set_xlim(0, len(months))
    ax.invert_yaxis()
    ax.set_title("Figure 9.1 – Project Development Gantt Chart  (Sep 2025 – May 2026)",
                 color=TEXT, fontsize=12, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)
    for sp in ax.spines.values(): sp.set_color(BORDER)

    # annotate ML data slip
    ax.annotate("ML data-collection slip\n→ scope adjusted", xy=(3.5, 4),
                xytext=(5, 6.5), color=RED,
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1), fontsize=8)

    fig.tight_layout()
    save(fig, "figure_9_1_project_development_gantt.png")

# ─── run all ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating report figures...")
    fig_7_1()
    fig_7_2()
    fig_7_3()
    fig_7_4()
    fig_7_5()
    fig_5_1()
    fig_5_2()
    fig_5_3()
    fig_5_4()
    fig_5_5()
    fig_5_7()
    fig_5_8()
    fig_5_9()
    fig_5_10()
    fig_6_1()
    fig_6_2()
    fig_6_3()
    fig_6_4()
    fig_6_5()
    fig_6_6()
    fig_6_7()
    fig_9_1()
    print("\nDone. All figures saved to report_assets/figures/")
