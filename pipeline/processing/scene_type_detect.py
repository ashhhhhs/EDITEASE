import os
from collections import Counter, deque

import cv2
import numpy as np

CASCADE_PATH = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")  # type: ignore


# ---------------------------------------------------------------------------
# Frame-level feature extractors
# ---------------------------------------------------------------------------

def detect_faces_info(image_bgr):
    """Return (face_count, largest_face_area_ratio)."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40),
    )

    h, w = gray.shape
    frame_area = float(h * w)

    if len(faces) == 0:
        return 0, 0.0

    areas = [fw * fh for (fx, fy, fw, fh) in faces]
    largest_ratio = max(areas) / frame_area
    return int(len(faces)), float(largest_ratio)


def compute_edge_density(image_bgr):
    """Fraction of edge pixels (Canny) in the frame."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(gray, 60, 160)
    return float(np.mean(edges > 0))


def compute_sharpness(image_bgr):
    """Variance of Laplacian — higher means sharper."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    return float(lap.var())


def compute_text_component_density(image_bgr):
    """
    Heuristic: binarize + count small connected components that resemble glyphs.
    Returns density in [0..~] — higher means more text-like content.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)  # type: ignore

    bw = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 31, 7,
    )
    bw = cv2.medianBlur(bw, 3)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bw, connectivity=8)

    h, w = gray.shape
    frame_area = float(h * w)

    glyph_like = 0
    for i in range(1, num_labels):  # skip background
        x, y, cw, ch, area = stats[i]
        if area < 15 or area > 2500:
            continue
        if cw < 3 or ch < 6:
            continue
        if cw > 120 or ch > 120:
            continue
        glyph_like += 1

    density = glyph_like / (frame_area / 100_000.0 + 1e-9)
    return float(density)


def compute_color_variance(image_bgr):
    """
    Normalized color variance — high for natural scenes, low for slides / UIs.
    Combines saturation std-dev and value std-dev from HSV space.
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32) / 255.0
    val = hsv[:, :, 2].astype(np.float32) / 255.0
    return float(np.std(sat) * 0.5 + np.std(val) * 0.5)


# ---------------------------------------------------------------------------
# Motion estimation
# ---------------------------------------------------------------------------

def estimate_motion(video_path, start_sec, end_sec, sample_points=6):
    """
    Sample frames across the segment and measure inter-frame difference.

    Returns:
        mean_motion  – average motion score in [0, ~1+]
        peak_motion  – maximum single-step motion score (catches action bursts)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.0, 0.0

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1
    duration = total_frames / fps

    start_sec = max(0.0, min(float(start_sec), duration - 0.1))
    end_sec   = max(start_sec + 0.1, min(float(end_sec), duration))

    times = np.linspace(start_sec, end_sec, num=int(sample_points))

    prev = None
    diffs = []

    for t in times:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (320, 180))

        if prev is not None:
            diff = cv2.absdiff(prev, gray)
            diffs.append(float(np.mean(diff)) / 255.0)

        prev = gray

    cap.release()

    if not diffs:
        return 0.0, 0.0

    return float(np.mean(diffs)), float(np.max(diffs))


# ---------------------------------------------------------------------------
# Scored candidate classifier
# ---------------------------------------------------------------------------

def classify_scene_type(
    face_count,
    largest_face_ratio,
    motion_score,
    peak_motion=0.0,
    edge_density=0.0,
    sharpness=0.0,
    text_density=0.0,
    color_variance=0.0,
):
    """
    Scored candidate classifier — every applicable scene gets a continuous
    score; the highest-scoring label wins.  This eliminates the threshold
    gaps and overlapping-rule problems of the original if/elif chain.

    Scene labels (unchanged from original):
        testimonial, presenter, audience_reaction,
        text_slide, screen_recording, b-roll, establishing_shot, other
    """
    candidates = []  # list of (label, score 0-1)

    # ------------------------------------------------------------------
    # Face-based scenes
    # ------------------------------------------------------------------
    if face_count >= 1:
        face_size_score = min(largest_face_ratio / 0.12, 1.0)
        stillness       = max(0.0, 1.0 - motion_score / 0.10)

        # Testimonial — single large face, very still
        if face_count == 1:
            candidates.append((
                "testimonial",
                face_size_score * 0.60 + stillness * 0.40,
            ))

        # Presenter — single face + motion (gesturing / walking)
        if face_count == 1:
            dynamism = min(motion_score / 0.15, 1.0)
            candidates.append((
                "presenter",
                face_size_score * 0.50 + dynamism * 0.50,
            ))

        # Audience reaction — many faces, each relatively small
        if face_count >= 3:
            crowd_score   = min(face_count / 6.0, 1.0)
            small_faces   = max(0.0, 1.0 - largest_face_ratio / 0.06)
            candidates.append((
                "audience_reaction",
                crowd_score * 0.55 + small_faces * 0.45,
            ))

    # ------------------------------------------------------------------
    # No-face scenes
    # ------------------------------------------------------------------
    if face_count == 0:
        # Text slide — static, text-heavy
        text_score     = min(text_density / 30.0, 1.0)
        slide_stillness = max(0.0, 1.0 - motion_score / 0.05)
        flat_colors    = max(0.0, 1.0 - color_variance / 0.20)
        candidates.append((
            "text_slide",
            text_score * 0.50 + slide_stillness * 0.35 + flat_colors * 0.15,
        ))

        # Screen recording — sharp, edge-rich, low-moderate motion
        screen_score = (
            min(sharpness / 300.0, 1.0)   * 0.40
            + min(edge_density / 0.15, 1.0) * 0.35
            + max(0.0, 1.0 - motion_score / 0.12) * 0.25
        )
        candidates.append(("screen_recording", screen_score))

        # B-roll — higher motion + natural color variance
        broll_score = (
            min(motion_score / 0.20, 1.0)  * 0.60
            + min(peak_motion / 0.30, 1.0) * 0.20
            + min(color_variance / 0.25, 1.0) * 0.20
        )
        candidates.append(("b-roll", broll_score))

        # Establishing shot — static, no notable text/screen features
        static_score = (
            max(0.0, 1.0 - motion_score / 0.06) * 0.55
            + min(color_variance / 0.20, 1.0)    * 0.25   # natural scene
            + max(0.0, 1.0 - text_score)          * 0.20   # low text
        )
        candidates.append(("establishing_shot", static_score))

    if not candidates:
        return "other", 0.50

    label, raw_score = max(candidates, key=lambda x: x[1])
    confidence = round(min(max(raw_score, 0.40), 0.95), 3)
    return label, confidence


# ---------------------------------------------------------------------------
# Temporal smoother
# ---------------------------------------------------------------------------

class SceneSmoothing:
    """
    Majority-vote smoothing over a sliding window of recent labels.
    Prevents a single anomalous frame from flipping the scene label.
    """

    def __init__(self, window: int = 3):
        self._window: deque = deque(maxlen=window)

    def smooth(self, raw_label: str, confidence: float):
        """
        Feed in the raw label for the current segment.
        Returns (smoothed_label, adjusted_confidence).
        """
        self._window.append(raw_label)
        smoothed = Counter(self._window).most_common(1)[0][0]

        # Penalise confidence slightly when smoothing overrides the raw label
        if smoothed != raw_label:
            confidence = max(0.40, confidence - 0.10)

        return smoothed, round(confidence, 3)

    def reset(self):
        self._window.clear()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def detect_scene_type(video_path, start_sec, end_sec, thumbnail_path=None, smoother=None):
    """
    Classify the scene type for a video segment.

    Args:
        video_path     : path to the video file
        start_sec      : segment start time in seconds
        end_sec        : segment end time in seconds
        thumbnail_path : optional path to a representative frame image
        smoother       : optional SceneSmoothing instance for temporal smoothing

    Returns:
        (scene_label, scene_confidence, debug_dict)
    """
    face_count, largest_face_ratio = 0, 0.0
    edge_density = sharpness = text_density = color_variance = 0.0

    if thumbnail_path and os.path.exists(thumbnail_path):
        img = cv2.imread(thumbnail_path)
        if img is not None:
            face_count, largest_face_ratio = detect_faces_info(img)
            edge_density    = compute_edge_density(img)
            sharpness       = compute_sharpness(img)
            text_density    = compute_text_component_density(img)
            color_variance  = compute_color_variance(img)

    mean_motion, peak_motion = estimate_motion(video_path, start_sec, end_sec, sample_points=6)

    label, confidence = classify_scene_type(
        face_count        = face_count,
        largest_face_ratio= largest_face_ratio,
        motion_score      = mean_motion,
        peak_motion       = peak_motion,
        edge_density      = edge_density,
        sharpness         = sharpness,
        text_density      = text_density,
        color_variance    = color_variance,
    )

    # Optional temporal smoothing
    if smoother is not None:
        label, confidence = smoother.smooth(label, confidence)

    debug = {
        "face_count"         : int(face_count),
        "largest_face_ratio" : float(largest_face_ratio),
        "mean_motion"        : float(mean_motion),
        "peak_motion"        : float(peak_motion),
        "edge_density"       : float(edge_density),
        "sharpness"          : float(sharpness),
        "text_density"       : float(text_density),
        "color_variance"     : float(color_variance),
    }

    return label, float(confidence), debug