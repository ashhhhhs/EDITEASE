"""
Generate the (real) ROC-curve figure for the EditEase scene classifier v2 and
embed it into the report under section 7.3.

WHY THIS IS A SEPARATE SCRIPT:
A genuine ROC curve needs the model's per-class probability scores swept across
thresholds. That requires running the trained model over the held-out test
split, which needs torch + the v2 checkpoint + OpenCV — available in your
project venv but not in the assistant's sandbox. So run this yourself once:

    # Windows venv:
    .venv\\Scripts\\python.exe scripts\\report\\make_roc.py
    # or any interpreter that has the project deps:
    python scripts/report/make_roc.py

It mirrors scripts/report/eval_test_split.py for data loading, then:
  1. collects the full softmax probability matrix over the test scenes,
  2. computes one-vs-rest ROC + AUC per class, plus micro-average and macro AUC,
  3. writes report_assets/screenshots/figure_7_3a_roc.png (GitHub-dark style),
  4. embeds that PNG into the .docx after the 7.3 ML-evaluation discussion
     (pass --no-embed to skip the embed and only produce the PNG).

The numbers come entirely from your model — nothing is fabricated.
"""
import json, os, sys, argparse, struct, zipfile, shutil, re, html, datetime
from collections import Counter

import numpy as np
import cv2
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize

sys.path.insert(0, "/mnt/d/EDITEASE")
import config  # noqa: E402

BASE = str(config.BASE_DIR)
MODEL_PATH = os.path.join(BASE, "pipeline", "models", "scene_classifier_v2.pth")
MANIFEST_PATH = os.path.join(BASE, "datasets", "scene_type", "v2_full", "annotations.jsonl")
SPLITS_PATH = os.path.join(BASE, "datasets", "scene_type", "v2_full", "splits.json")
OUT_PNG = os.path.join(BASE, "report_assets", "screenshots", "figure_7_3a_roc.png")
DOC = os.path.join(BASE, "2407774_AshreenDangol_EDITEASE_FYP_REPORT_FIXED.docx")

# GitHub-Dark palette (matches the generated design figures)
BG = "#0d1117"; PANEL = "#161b22"; INK = "#e6edf3"; MUTED = "#8b949e"; GRID = "#30363d"
CLASS_COLORS = ["#58a6ff", "#3fb950", "#bc8cff", "#db6d28", "#db61a2"]


def build_model(num_classes, device):
    backbone = models.resnet18(weights=None)
    in_features = backbone.fc.in_features
    backbone.fc = nn.Sequential(
        nn.Linear(in_features, 256), nn.LayerNorm(256), nn.ReLU(),
        nn.Dropout(0.4), nn.Linear(256, num_classes),
    )
    return backbone.to(device)


def midpoint_frame(video_path, t0, t1):
    if not video_path:
        return None
    full = video_path.replace("\\", "/")
    full = full if os.path.isabs(full) else os.path.join(BASE, full)
    if not os.path.exists(full):
        return None
    try:
        cap = cv2.VideoCapture(full)
        if not cap.isOpened():
            return None
        mid = (float(t0) + float(t1)) / 2.0 if (t0 is not None and t1 is not None) else 0.0
        cap.set(cv2.CAP_PROP_POS_MSEC, mid * 1000)
        ok, bgr = cap.read(); cap.release()
        if not ok or bgr is None:
            return None
        return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    except Exception:
        return None


def collect_scores():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(MODEL_PATH, map_location=device, weights_only=True)
    classes = ckpt["classes"]
    label_merge = ckpt.get("label_merge", {})
    model = build_model(ckpt.get("num_classes", len(classes)), device)
    model.load_state_dict(ckpt["model_state_dict"]); model.eval()
    tf = transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    test_videos = set(json.load(open(SPLITS_PATH))["test"])
    label_to_idx = {c: i for i, c in enumerate(classes)}

    y_true, probs_all = [], []
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("video") not in test_videos:
                continue
            true = label_merge.get(rec.get("label", ""), rec.get("label", ""))
            if true not in label_to_idx:
                continue
            frames = [fp.replace("\\", "/") for fp in (rec.get("frames") or [])]
            frames = [fp if os.path.isabs(fp) else os.path.join(BASE, fp) for fp in frames]
            fp = next((p for p in frames if os.path.exists(p)), None)
            img = None
            if fp:
                try:
                    img = Image.open(fp).convert("RGB")
                except Exception:
                    img = None
            if img is None:
                img = midpoint_frame(rec.get("video_path"), rec.get("t0"), rec.get("t1"))
            if img is None:
                continue
            x = tf(img.convert("RGB")).unsqueeze(0).to(device)
            with torch.no_grad():
                p = torch.softmax(model(x), dim=1).cpu().numpy()[0]
            y_true.append(label_to_idx[true]); probs_all.append(p)
    return classes, np.array(y_true), np.array(probs_all)


def plot_roc(classes, y_true, probs):
    n = len(classes)
    present = sorted(set(int(v) for v in y_true))
    Y = label_binarize(y_true, classes=list(range(n)))
    if Y.shape[1] == 1:  # binarize edge-case for 2 classes
        Y = np.hstack([1 - Y, Y])

    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": PANEL, "savefig.facecolor": BG,
        "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED,
        "ytick.color": MUTED, "axes.edgecolor": GRID, "font.size": 11,
    })
    fig, ax = plt.subplots(figsize=(8, 6.2), dpi=170)
    aucs = []
    for i in present:
        fpr, tpr, _ = roc_curve(Y[:, i], probs[:, i])
        a = auc(fpr, tpr); aucs.append(a)
        ax.plot(fpr, tpr, color=CLASS_COLORS[i % len(CLASS_COLORS)], lw=2,
                label=f"{classes[i]}  (AUC = {a:.3f})")
    # micro-average over present classes
    cols = [i for i in present]
    fpr_m, tpr_m, _ = roc_curve(Y[:, cols].ravel(), probs[:, cols].ravel())
    auc_micro = auc(fpr_m, tpr_m)
    ax.plot(fpr_m, tpr_m, color=INK, lw=2, ls="--",
            label=f"micro-average  (AUC = {auc_micro:.3f})")
    ax.plot([0, 1], [0, 1], color=GRID, lw=1, ls=":")
    ax.set_xlim(-0.01, 1.0); ax.set_ylim(0.0, 1.02)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title(f"Figure 7.3a  ROC Curves (one-vs-rest, n={len(y_true)})  |  macro AUC = {np.mean(aucs):.3f}",
                 color=INK, fontsize=12, pad=12)
    leg = ax.legend(loc="lower right", facecolor=PANEL, edgecolor=GRID, fontsize=9)
    for t in leg.get_texts():
        t.set_color(INK)
    ax.grid(color=GRID, lw=0.4, alpha=0.5)
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    fig.savefig(OUT_PNG)
    print(f"wrote {OUT_PNG}  (macro AUC {np.mean(aucs):.3f}, micro AUC {auc_micro:.3f})")


# ---- minimal docx embed (same OOXML pattern as embed_additions.py) ----
def embed_into_doc():
    if not os.path.exists(DOC):
        print("doc not found, skipping embed:", DOC); return
    w, h = struct.unpack(">II", open(OUT_PNG, "rb").read(24)[16:24])
    emu_w = int(6.0 * 914400); emu_h = int(emu_w * h / w)
    z = zipfile.ZipFile(DOC)
    xml = z.read("word/document.xml").decode("utf-8")
    rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    if "figure_7_3a_roc.png" in xml:
        print("ROC already embedded; skipping."); z.close(); return
    nmedia = max(int(m.group(1)) for m in re.finditer(r"media/image(\d+)\.png", rels)) + 1
    nrid = max(int(m.group(1)) for m in re.finditer(r'Id="rId(\d+)"', rels)) + 1
    rid = f"rId{nrid}"; member = f"word/media/image{nmedia}.png"; name = "figure_7_3a_roc.png"
    draw = (
        '<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{emu_w}" cy="{emu_h}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="9050" name="{name}"/><wp:cNvGraphicFramePr>'
        '<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>'
        '</wp:cNvGraphicFramePr><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="9050" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
        '</wp:inline></w:drawing>')
    cap = ("Figure 7.3a – ROC curves (one-vs-rest) for the v2 scene classifier on the held-out test split, "
           "with per-class and micro-averaged AUC.")
    para = ('<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="60"/></w:pPr>'
            f'<w:r>{draw}</w:r></w:p>'
            '<w:p><w:pPr><w:spacing w:after="240"/><w:jc w:val="center"/>'
            '<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr></w:pPr>'
            '<w:r><w:rPr><w:rFonts w:cs="Times New Roman"/><w:i/><w:sz w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{html.escape(cap, quote=False)}</w:t></w:r></w:p>')
    # anchor: after the 7.3 discussion of macro/weighted F1 (body occurrence)
    anchor = "makes the imbalance explicit"
    pos = xml.rfind(anchor)
    if pos == -1:
        anchor = "Macro F1"; pos = xml.rfind(anchor)
    end = xml.find("</w:p>", pos) + len("</w:p>")
    xml = xml[:end] + para + xml[end:]
    rels = rels.replace("</Relationships>",
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
        f'Target="media/image{nmedia}.png"/></Relationships>')
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(DOC, DOC.replace(".docx", f".pre_roc_{stamp}.docx"))
    tmp = DOC + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in z.infolist():
            if it.filename == "word/document.xml":
                zout.writestr(it, xml.encode("utf-8"))
            elif it.filename == "word/_rels/document.xml.rels":
                zout.writestr(it, rels.encode("utf-8"))
            else:
                zout.writestr(it, z.read(it.filename))
        zout.writestr(member, open(OUT_PNG, "rb").read())
    z.close(); os.replace(tmp, DOC)
    print(f"embedded ROC into {DOC}  ({rid}, {member})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-embed", action="store_true", help="only write the PNG")
    args = ap.parse_args()
    classes, y_true, probs = collect_scores()
    print(f"collected {len(y_true)} test scenes; class counts: {Counter(int(v) for v in y_true)}")
    if len(y_true) < 2:
        raise SystemExit("Not enough evaluable test scenes to plot ROC.")
    plot_roc(classes, y_true, probs)
    if not args.no_embed:
        embed_into_doc()


if __name__ == "__main__":
    main()
