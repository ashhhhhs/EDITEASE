"""
Generate EditEase report design figures (Use Case, Class, Activity, ERD,
Wireframe) as PNGs using the dependency-free figlib canvas.

All content is derived from the actual codebase:
  - pipeline/classifiers/{base,ml,rule_based}_classifier.py
  - pipeline/processing/run_pipeline.py  (agentic + emotion flow)
  - database collections (scenes/tasks/users/organized_videos)
  - frontend AppShell / Dashboard / Inspector / OrganizedVideos

Output dir: report_assets/screenshots/
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from figlib import *

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "report_assets", "screenshots")
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)


def titlebar(c, title, sub=None):
    c.rect(0, 0, c.w, 64, fill=PANEL2)
    c.hline(0, c.w, 64, ACCENT, t=3)
    c.text(28, 20, title, INK, scale=3)
    if sub:
        c.text(c.w - c.text_w(sub, 2) - 24, 26, sub, MUTED, scale=2)


def panel(c, x, y, w, h, title, lines, accent=ACCENT, fill=PANEL, tscale=2):
    c.rect(x, y, w, h, fill=fill, border=BORDER, bw=2)
    c.rect(x, y, w, 34, fill=PANEL2)
    c.hline(x, x + w, y + 34, accent, t=2)
    c.text(x + 12, y + 10, title, accent, scale=tscale)
    yy = y + 46
    for ln, col in lines:
        c.text(x + 12, yy, ln, col, scale=2)
        yy += 24
    return x, y, w, h


def pill(c, cx, cy, w, h, text, accent=ACCENT):
    x = cx - w // 2; y = cy - h // 2
    c.rect(x, y, w, h, fill=PANEL, border=accent, bw=2)
    # rounded corners (knock out)
    for (ox, oy) in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]:
        c._set(x+ox, y+oy, BG)
    c.text_center(cx, cy - 7, text, INK, scale=2)


def actor(c, cx, cy, label):
    col = INK
    # head
    for a in range(360):
        import math
        c._set(int(cx + 10*math.cos(math.radians(a))), int(cy - 22 + 10*math.sin(math.radians(a))), col)
    c.vline(cx, cy - 12, cy + 12, col, 2)          # body
    c.hline(cx - 14, cx + 14, cy - 4, col, 2)      # arms
    c.line(cx, cy + 12, cx - 12, cy + 30, col, 2)  # legs
    c.line(cx, cy + 12, cx + 12, cy + 30, col, 2)
    c.text_center(cx, cy + 36, label, ACCENT, scale=2)


# ---------------------------------------------------------------- Use Case
def use_case():
    c = Canvas(1500, 980)
    titlebar(c, "Figure 5.2a  Use Case Diagram", "EditEase")
    # system boundary
    bx, by, bw, bh = 470, 110, 560, 830
    c.rect(bx, by, bw, bh, border=BORDER, bw=2)
    c.text_center(bx + bw//2, by + 10, "EditEase System", MUTED, scale=2)
    cases = [
        "Register / Login", "Upload Raw Video", "Browse Clip Grid",
        "Filter & Search Scenes", "Review & Correct Labels", "Run Auto-Organize",
        "Download Category ZIP", "Monitor Processing Jobs", "Manage Users / Roles",
    ]
    ys = [180 + i*84 for i in range(len(cases))]
    cxc = bx + bw//2
    for t, y in zip(cases, ys):
        pill(c, cxc, y, 360, 50, t)
    actor(c, 120, 470, "Editor")
    actor(c, 1380, 470, "Admin")
    # editor -> first 7 cases ; admin -> all 9
    for y in ys[:7]:
        c.line(150, 470, cxc - 182, y, MUTED, 1)
    for y in ys:
        c.line(1350, 470, cxc + 182, y, ORANGE, 1)
    c.text(120, 900, "Editor: upload, browse, filter, review, organize, export", MUTED, scale=2)
    c.text(120, 928, "Admin: all editor cases + job monitor + user management", ORANGE, scale=2)
    c.save(os.path.join(OUT, "figure_5_2a_use_case.png"))


# ---------------------------------------------------------------- Class
def class_diagram():
    c = Canvas(1560, 1000)
    titlebar(c, "Figure 5.2b  Class / Module Diagram", "classifiers + pipeline + services")
    base = panel(c, 600, 110, 360, 130, "BaseClassifier  <<abstract>>", [
        ("# classify(thumbnail_path)", MUTED),
        ("  -> (label, confidence)", MUTED),
        ("base_classifier.py", PURPLE),
    ], accent=PURPLE)
    ml = panel(c, 320, 330, 380, 180, "MLClassifier", [
        ("- model: ResNet-18 (v2)", INK),
        ("- transform / idx_to_label", INK),
        ("- CLASS_THRESHOLDS", INK),
        ("+ classify(): softmax top-1", INK),
        ("ml_classifier.py", GREEN),
    ], accent=GREEN)
    rb = panel(c, 860, 330, 400, 180, "RuleBasedClassifier", [
        ("+ classify() -> Gaussian", INK),
        ("  likelihood profiling", INK),
        ("delegates scene_type_detect", INK),
        ("12 features / 4 profiles", INK),
        ("rule_based_classifier.py", ORANGE),
    ], accent=ORANGE)
    # inheritance (hollow arrow up to base)
    c.arrow(510, 330, 700, 240, PURPLE, t=2, head=12)
    c.arrow(1060, 330, 840, 240, PURPLE, t=2, head=12)
    c.text(545, 285, "extends", MUTED, scale=2)
    pipe = panel(c, 320, 580, 940, 150, "Pipeline  (run_pipeline.process_video)", [
        ("agentic decision: CONF_AUTO_HIGH=0.85  CONF_FUSE_LOW=0.58  ML_WEIGHT=0.65", INK),
        ("sample_emotions_over_scene()  - Haar + DeepFace, face-evidence gate", INK),
        ("uses Classifier.classify() then fuses ML + rule-based outputs", ACCENT),
    ], accent=ACCENT)
    c.arrow(510, 580, 510, 510, ACCENT, t=2)   # pipe -> ml (uses)
    c.arrow(1000, 580, 1000, 510, ACCENT, t=2) # pipe -> rb (uses)
    c.text(515, 545, "uses", MUTED, scale=2)
    svc = panel(c, 320, 780, 460, 170, "Services", [
        ("clip_service.upsert_scene()", INK),
        ("task_service.dispatch_process()", INK),
        ("cloudinary_service.upload_video()", INK),
        ("-> MongoDB / Cloudinary", GREEN),
    ], accent=GREEN)
    model = panel(c, 820, 780, 440, 170, "Scene  <<document>>", [
        ("scene_id, video_id, user_id", INK),
        ("start/end/duration, scene_label", INK),
        ("ml_confidence, review_status", INK),
        ("thumbnail_url, emotion[]", INK),
    ], accent=PINK)
    c.arrow(700, 780, 700, 730, ACCENT, t=2)   # pipe -> services
    c.arrow(900, 780, 1000, 730, ACCENT, t=2)  # pipe -> model
    c.arrow(780, 865, 820, 865, PINK, t=2)     # services -> model
    c.save(os.path.join(OUT, "figure_5_2b_class_diagram.png"))


# ---------------------------------------------------------------- Activity
def activity():
    c = Canvas(1180, 1500)
    titlebar(c, "Figure 6.1a  Activity Diagram", "process_video() pipeline")
    cx = 590

    def node(y, w, h, text, fill=PANEL, border=BORDER, col=INK, lines=None):
        x = cx - w//2
        c.rect(x, y, w, h, fill=fill, border=border, bw=2)
        if lines:
            yy = y + 12
            for ln in lines:
                c.text_center(cx, yy, ln, col, scale=2); yy += 24
        else:
            c.text_center(cx, y + h//2 - 7, text, col, scale=2)
        return y + h

    def diamond(y, h, text):
        w = 360
        x = cx
        pts = [(x, y), (x + w//2, y + h//2), (x, y + h), (x - w//2, y + h//2)]
        for i in range(4):
            c.line(*pts[i], *pts[(i+1) % 4], ACCENT, 2)
        c.text_center(cx, y + h//2 - 7, text, ACCENT, scale=2)
        return y + h

    def conn(y0, y1, label=None, col=MUTED):
        c.arrow(cx, y0, cx, y1, col, t=2)
        if label:
            c.text(cx + 12, (y0 + y1)//2 - 8, label, col, scale=2)

    y = 90
    # start
    c.rect(cx-60, y, 120, 40, fill=GREEN, border=GREEN); c.text_center(cx, y+12, "START", BG, 2); y2=y+40
    conn(y2, y2+30); y = y2+30
    y = node(y, 360, 44, "Upload video (Flask API)"); conn(y, y+26); y+=26
    y = node(y, 360, 44, "Save file + SHA-256 dedup"); conn(y, y+26); y+=26
    y = node(y, 360, 44, "Dispatch Celery task"); conn(y, y+26); y+=26
    y = node(y, 360, 44, "Upload raw to Cloudinary"); conn(y, y+26); y+=26
    y = node(y, 420, 44, "Detect scenes (PySceneDetect)"); conn(y, y+26); y+=26
    loop_top = y
    y = node(y, 460, 44, "FOR each scene: extract midpoint thumb", fill=PANEL2); conn(y, y+26); y+=26
    y = node(y, 360, 44, "ML classify (ResNet-18 v2)"); conn(y, y+30); y+=30
    d1 = y; y = diamond(y, 90, "conf >= 0.85 ?");
    # yes branch (right)
    c.arrow(cx+180, d1+45, cx+360, d1+45, GREEN, 2); c.text(cx+200, d1+18, "yes", GREEN, 2)
    c.rect(cx+360, d1+20, 200, 50, fill=PANEL, border=GREEN, bw=2); c.text_center(cx+460, d1+34, "accept", GREEN, 2)
    conn(y, y+24, "no"); y+=24
    d2 = y; y = diamond(y, 90, "rule-based used ?")
    c.arrow(cx+180, d2+45, cx+360, d2+45, ORANGE, 2); c.text(cx+200, d2+18, "yes", ORANGE, 2)
    c.rect(cx+360, d2+20, 200, 50, fill=PANEL, border=ORANGE, bw=2); c.text_center(cx+460, d2+34, "uncertain", ORANGE, 2)
    conn(y, y+24, "no"); y+=24
    y = node(y, 460, 44, "Fuse ML + rule (0.65 / 0.35)"); conn(y, y+30); y+=30
    d3 = y; y = diamond(y, 90, "fused < 0.58 ?")
    c.arrow(cx+180, d3+45, cx+360, d3+45, ORANGE, 2); c.text(cx+200, d3+18, "yes", ORANGE, 2)
    c.rect(cx+360, d3+20, 200, 50, fill=PANEL, border=ORANGE, bw=2); c.text_center(cx+460, d3+34, "uncertain", ORANGE, 2)
    conn(y, y+24, "no -> reviewed"); y+=24
    y = node(y, 460, 44, "Sample emotions (face-evidence gate)"); conn(y, y+24); y+=24
    y = node(y, 360, 44, "Store scene -> MongoDB");
    # loop back
    c.arrow(cx-230-30, y-22, cx-230-30, loop_top+22, PURPLE, 2)
    c.line(cx-230, y-22, cx-260, y-22, PURPLE, 2)
    c.line(cx-230, loop_top+22, cx-260, loop_top+22, PURPLE, 2)
    c.text(cx-420, (y+loop_top)//2, "next scene", PURPLE, 2)
    conn(y, y+30); y+=30
    c.rect(cx-70, y, 140, 40, fill=ACCENT, border=ACCENT); c.text_center(cx, y+12, "COMPLETE", BG, 2)
    c.save(os.path.join(OUT, "figure_6_1a_activity.png"))


# ---------------------------------------------------------------- ERD
def erd():
    c = Canvas(1560, 1000)
    titlebar(c, "Figure 5.5a  Entity Relationship (MongoDB)", "editease database")
    users = panel(c, 80, 120, 380, 200, "users", [
        ("PK  _id", ACCENT),
        ("    email", INK),
        ("    role  (admin / editor)", INK),
        ("    tour_completed_at", INK),
        ("    verified", INK),
    ], accent=ACCENT)
    scenes = panel(c, 600, 120, 420, 360, "scenes", [
        ("PK  scene_id", ACCENT),
        ("FK  user_id  -> users", PINK),
        ("    video_id, video_name", INK),
        ("    start_time, end_time", INK),
        ("    duration", INK),
        ("    scene_label", GREEN),
        ("    ml_confidence", INK),
        ("    review_status, reviewed", INK),
        ("    thumbnail_url, cloudinary_url", INK),
        ("    emotion, emotion_timeline[]", INK),
        ("    reviewer_notes", INK),
    ], accent=GREEN)
    tasks = panel(c, 1120, 120, 380, 200, "tasks", [
        ("PK  task_id", ACCENT),
        ("FK  user_id  -> users", PINK),
        ("    status (PENDING..SUCCESS)", INK),
        ("    video_name, created_at", INK),
        ("    error_message", INK),
    ], accent=ORANGE)
    org = panel(c, 600, 600, 420, 220, "organized_videos", [
        ("PK  _id", ACCENT),
        ("FK  user_id  -> users", PINK),
        ("    category", GREEN),
        ("    scene_ids[]  -> scenes", PINK),
        ("    cloudinary_folder", INK),
        ("    (user_id)/(category)/", MUTED),
    ], accent=PURPLE)
    # relationships with 1..* labels
    c.arrow(460, 200, 600, 200, PINK, 2); c.text(480, 175, "1..*", PINK, 2)
    c.arrow(1120, 200, 1020, 200, PINK, 2); c.text(1035, 175, "1..*", PINK, 2)
    c.arrow(270, 320, 700, 600, PINK, 2); c.text(360, 470, "1..* organizes", PINK, 2)
    c.arrow(810, 600, 810, 480, PINK, 2); c.text(820, 540, "references", PINK, 2)
    c.save(os.path.join(OUT, "figure_5_5a_erd.png"))


# ---------------------------------------------------------------- Wireframe
def wireframe():
    c = Canvas(1560, 940)
    titlebar(c, "Figure 5.6a  Dashboard Wireframe", "AppShell + clip grid + Inspector")
    # top bar
    c.rect(0, 64, c.w, 50, fill=PANEL2)
    c.text(28, 78, "EditEase", ACCENT, 3)
    c.rect(360, 74, 400, 30, fill=PANEL, border=BORDER, bw=1); c.text(372, 80, "search scenes...", MUTED, 2)
    c.rect(c.w-160, 74, 130, 30, fill=PANEL, border=BORDER, bw=1); c.text(c.w-150, 80, "user / role", MUTED, 2)
    # sidebar
    c.rect(0, 114, 230, c.h-114, fill=PANEL)
    for i, item in enumerate(["Dashboard","Uploads","Review","Organized","Admin: Users","Admin: Jobs"]):
        col = ACCENT if i == 0 else MUTED
        c.rect(16, 140 + i*48, 198, 36, fill=PANEL2 if i==0 else PANEL, border=BORDER, bw=1)
        c.text(28, 150 + i*48, item, col, 2)
    # filter rail
    fx = 250
    c.rect(fx, 130, 230, c.h-150, fill=PANEL, border=BORDER, bw=1)
    c.text(fx+12, 142, "Filters", INK, 2)
    for i, f in enumerate(["Label","Emotion","Status","Duration"]):
        c.rect(fx+12, 178 + i*70, 206, 46, fill=PANEL2, border=BORDER, bw=1)
        c.text(fx+22, 190 + i*70, f, MUTED, 2)
    # clip grid
    gx, gy = 500, 130
    c.text(gx, 138, "Clip Grid", INK, 2)
    for r in range(3):
        for col in range(3):
            x = gx + col*200; y = gy + 30 + r*150
            verified = (r+col) % 3 == 0
            c.rect(x, y, 180, 130, fill=PANEL2, border=(GREEN if verified else BORDER), bw=(3 if verified else 1))
            c.rect(x+10, y+10, 160, 78, fill=PANEL, border=BORDER, bw=1)
            c.text(x+16, y+18, "thumbnail", MUTED, 2)
            c.text(x+12, y+96, "b-roll  0.92", INK, 2)
            c.text(x+12, y+116, ("reviewed" if verified else "auto"), (GREEN if verified else MUTED), 2)
    # inspector
    ix = 1180
    c.rect(ix, 130, 360, c.h-150, fill=PANEL, border=ACCENT, bw=2)
    c.text(ix+14, 142, "Inspector", ACCENT, 2)
    c.rect(ix+14, 176, 332, 170, fill=PANEL2, border=BORDER, bw=1); c.text(ix+24, 184, "selected thumbnail", MUTED, 2)
    rows = ["start 00:12  end 00:19","duration 7.0s","ml_confidence 0.74","emotion: neutral"]
    for i, t in enumerate(rows):
        c.text(ix+18, 360 + i*30, t, INK, 2)
    c.rect(ix+14, 500, 332, 40, fill=PANEL2, border=BORDER, bw=1); c.text(ix+24, 510, "label  [ testimonial v ]", INK, 2)
    c.rect(ix+14, 552, 332, 90, fill=PANEL2, border=BORDER, bw=1); c.text(ix+24, 560, "reviewer notes...", MUTED, 2)
    c.rect(ix+14, 656, 150, 44, fill=GREEN, border=GREEN); c.text(ix+40, 668, "Save", BG, 2)
    c.rect(ix+178, 656, 168, 44, fill=PANEL, border=ACCENT, bw=2); c.text(ix+196, 668, "Next clip", ACCENT, 2)
    c.save(os.path.join(OUT, "figure_5_6a_wireframe.png"))


if __name__ == "__main__":
    use_case(); class_diagram(); activity(); erd(); wireframe()
    print("figures written to", OUT)
