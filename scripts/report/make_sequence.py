"""Sequence diagram for the EditEase upload->process->review flow (figlib)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from figlib import *

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                   "report_assets", "screenshots", "figure_6_1b_sequence.png"))


def sequence():
    c = Canvas(1640, 1180)
    # title bar
    c.rect(0, 0, c.w, 64, fill=PANEL2); c.hline(0, c.w, 64, ACCENT, t=3)
    c.text(28, 20, "Figure 6.1b  Sequence Diagram", INK, scale=3)
    c.text(c.w - c.text_w("upload -> process -> review", 2) - 24, 26,
           "upload -> process -> review", MUTED, scale=2)

    lanes = ["User (React)", "Flask API", "Celery Worker", "Pipeline", "Cloudinary", "MongoDB"]
    cols = [150, 410, 690, 950, 1230, 1500]
    top, bottom = 130, 1140
    accents = [ACCENT, GREEN, ORANGE, PURPLE, PINK, ACCENT]
    for x, name, ac in zip(cols, lanes, accents):
        c.rect(x - 110, top - 36, 220, 34, fill=PANEL, border=ac, bw=2)
        c.text_center(x, top - 30, name, INK, scale=2)
        # lifeline (dashed)
        yy = top
        while yy < bottom:
            c.vline(x, yy, min(yy + 10, bottom), BORDER, 1); yy += 18

    def msg(y, a, b, label, col=INK, dashed=False, ret=False):
        xa, xb = cols[a], cols[b]
        d = 1 if xb > xa else -1
        if dashed:
            x = xa
            while (x - xb) * d < 0:
                c.hline(x, x + 8 * d, y, col, 1); x += 16 * d
            c.arrow(xb - 12 * d, y, xb, y, col, t=1, head=8)
        else:
            c.arrow(xa, y, xb, y, col, t=2, head=10)
        tx = min(xa, xb) + 8
        c.text(tx, y - 20, label, col, scale=2)

    def selfmsg(y, a, label, col=PURPLE):
        x = cols[a]
        c.rect(x, y - 8, 60, 26, border=col, bw=1)
        c.text(x + 70, y - 6, label, col, scale=2)

    y = top + 30
    msg(y, 0, 1, "1: POST /upload (video)", ACCENT); y += 58
    selfmsg(y, 1, "2: save file + SHA-256 dedup", GREEN); y += 58
    msg(y, 1, 2, "3: dispatch_process(task)", GREEN); y += 48
    msg(y, 1, 0, "4: 202 Accepted (task_id)", MUTED, dashed=True); y += 58
    msg(y, 2, 4, "5: upload_video()", ORANGE); y += 48
    msg(y, 2, 3, "6: process_video()", ORANGE); y += 56
    selfmsg(y, 3, "7: detect_scenes (PySceneDetect)", PURPLE); y += 70
    # loop box (label first, then messages below so they do not overlap)
    ly0 = y - 30
    c.text(cols[3] - 18, ly0 + 4, "loop  [per scene]", GREEN, scale=2)
    selfmsg(y, 3, "8: extract thumbnail + ML classify", PURPLE); y += 50
    selfmsg(y, 3, "9: agentic decide + sample emotion", PURPLE); y += 50
    msg(y, 3, 4, "10: upload thumbnail", ORANGE); y += 48
    msg(y, 3, 5, "11: upsert_scene()", PINK); y += 44
    c.rect(cols[3] - 24, ly0, cols[5] - cols[3] + 60, y - ly0 - 14, border=GREEN, bw=1)
    y += 22
    msg(y, 2, 5, "12: update task status", ORANGE); y += 58
    msg(y, 0, 1, "13: GET /task_status (poll)", ACCENT); y += 44
    msg(y, 1, 5, "14: read status", GREEN); y += 44
    msg(y, 1, 0, "15: progress / SUCCESS", MUTED, dashed=True); y += 58
    msg(y, 0, 1, "16: GET /search (filters)", ACCENT); y += 44
    msg(y, 1, 5, "17: query scenes", GREEN); y += 44
    msg(y, 1, 0, "18: scene records -> clip grid", MUTED, dashed=True)
    c.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    sequence()
