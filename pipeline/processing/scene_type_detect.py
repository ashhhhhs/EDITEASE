"""
Scene detection via Gaussian Likelihood Profiling.

Architecture overview
---------------------
1. Raw signals  →  extract_features()  →  normalised feature dict  (all values in [0, 1])
2. Feature dict →  classify_scene()    →  Gaussian log-likelihood per scene
3. Log-likelihoods  →  softmax  →  true probability distribution over scene labels
4. Winner + softmax probability  →  (label, confidence)
5. Optional SceneSmoothing for temporal stability across segments

Why this beats a rule-based or scored-candidate approach
---------------------------------------------------------
* No threshold gaps   – every scene always gets a continuous likelihood score.
* No hand-crafted weights per scene – the Gaussian sigma encodes how
  discriminative each feature is for each scene (tight sigma = must be close
  to mu; wide sigma = "don't care much").
* Confidence is a true probability (softmax over all scenes), not a hardcoded
  constant or a hand-tuned linear sum.
* New signals can be added by extending FEATURE_RANGES and SCENE_PROFILES
  alone — no rule rewriting required.
* All scenes compete simultaneously; the best statistical match wins.
"""

import os
from collections import Counter, deque

import cv2
import numpy as np

CASCADE_PATH = os.path.join(
    cv2.data.haarcascades, "haarcascade_frontalface_default.xml"  # type: ignore
)


# ---------------------------------------------------------------------------
# Feature normalisation ceilings
# Tune upper bounds here if your footage has different dynamic ranges.
# ---------------------------------------------------------------------------
FEATURE_RANGES = {
    "face_dominance"     : 0.25,   # largest_face_area / frame_area
    "face_count_norm"    : 6.0,    # raw face count
    "motion_mean"        : 0.30,
    "motion_peak"        : 0.40,
    "motion_burst"       : 3.0,    # peak / (mean + ε) — how spikey motion is
    "motion_consistency" : 0.12,   # std-dev of per-frame diffs (inverted later)
    "edge_density"       : 0.20,
    "sharpness"          : 500.0,
    "text_density"       : 40.0,
    "color_variance"     : 0.30,
}


# ---------------------------------------------------------------------------
# Scene profiles
#
# Each entry is  feature_name: (mu, sigma)
#   mu    – ideal normalised value for this scene  [0, 1]
#   sigma – tolerance; small = feature must match closely;
#           large = feature is less discriminative for this scene
#
# Features NOT listed for a scene contribute zero log-likelihood — they
# neither help nor hurt that scene's score.
# ---------------------------------------------------------------------------
SCENE_PROFILES = {

    "testimonial": {
        # Single large face, camera nearly static
        "face_presence"      : (1.00, 0.05),
        "face_dominance"     : (0.80, 0.18),
        "face_count_norm"    : (0.17, 0.08),   # 1 face → 1/6 ≈ 0.17
        "motion_mean"        : (0.05, 0.07),
        "motion_peak"        : (0.08, 0.09),
        "motion_consistency" : (0.90, 0.12),   # very consistent (inverted std)
        "text_density"       : (0.08, 0.15),
        "color_variance"     : (0.18, 0.12),
    },

    "presenter": {
        # Single face, gesturing / walking, more dynamic
        "face_presence"      : (1.00, 0.05),
        "face_dominance"     : (0.35, 0.25),
        "face_count_norm"    : (0.17, 0.10),
        "motion_mean"        : (0.50, 0.22),
        "motion_peak"        : (0.55, 0.25),
        "motion_consistency" : (0.55, 0.25),
        "color_variance"     : (0.22, 0.14),
    },

    "audience_reaction": {
        # Many small faces (crowd, panel, audience shot)
        "face_presence"      : (1.00, 0.05),
        "face_count_norm"    : (0.65, 0.25),   # 4+ faces → ~0.65
        "face_dominance"     : (0.10, 0.08),   # each face is small
        "motion_mean"        : (0.25, 0.25),
        "color_variance"     : (0.28, 0.18),
    },

    "text_slide": {
        # No faces, static, text-heavy, flat colours
        "face_presence"      : (0.00, 0.05),
        "motion_mean"        : (0.04, 0.06),
        "motion_peak"        : (0.06, 0.08),
        "text_density"       : (0.82, 0.18),
        "color_variance"     : (0.07, 0.09),   # flat palette
        "sharpness"          : (0.40, 0.30),
        "edge_density"       : (0.45, 0.30),
    },

    "screen_recording": {
        # No faces, pixel-sharp UI, dense edges, low-moderate motion
        "face_presence"      : (0.00, 0.05),
        "sharpness"          : (0.85, 0.15),
        "edge_density"       : (0.75, 0.18),
        "motion_mean"        : (0.18, 0.18),
        "color_variance"     : (0.12, 0.14),
        "text_density"       : (0.40, 0.30),
    },

    "b-roll": {
        # No faces, dynamic natural footage, rich colour
        "face_presence"      : (0.00, 0.05),
        "motion_mean"        : (0.72, 0.22),
        "motion_peak"        : (0.75, 0.22),
        "motion_burst"       : (0.45, 0.35),
        "color_variance"     : (0.72, 0.18),
        "text_density"       : (0.05, 0.12),
        "sharpness"          : (0.35, 0.28),
    },

    "establishing_shot": {
        # No faces, slow / static wide scene, natural colour, no text
        "face_presence"      : (0.00, 0.05),
        "motion_mean"        : (0.07, 0.09),
        "motion_peak"        : (0.10, 0.12),
        "motion_consistency" : (0.75, 0.20),
        "color_variance"     : (0.50, 0.22),
        "text_density"       : (0.05, 0.10),
        "sharpness"          : (0.28, 0.24),
    },
}


# ---------------------------------------------------------------------------
# Low-level signal extractors
# ---------------------------------------------------------------------------

def detect_faces_info(image_bgr):
    """Return (face_count, largest_face_area_ratio)."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
    )
    h, w = gray.shape
    frame_area = float(h * w)
    if len(faces) == 0:
        return 0, 0.0
    areas = [fw * fh for (_, _, fw, fh) in faces]
    return int(len(faces)), float(max(areas) / frame_area)


def compute_edge_density(image_bgr):
    """Fraction of Canny edge pixels in the frame."""
    gray = cv2.GaussianBlur(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY), (3, 3), 0)
    return float(np.mean(cv2.Canny(gray, 60, 160) > 0))


def compute_sharpness(image_bgr):
    """Variance of Laplacian — higher = sharper."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_text_density(image_bgr):
    """
    Count glyph-like connected components as a proxy for on-screen text.
    Normalised by frame area so it generalises across resolutions.
    """
    gray = cv2.normalize(
        cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY),
        None, 0, 255, cv2.NORM_MINMAX,  # type: ignore
    )
    bw = cv2.medianBlur(
        cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 31, 7,
        ), 3,
    )
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    h, w = gray.shape
    glyph_like = sum(
        1 for i in range(1, num_labels)
        if 15 <= stats[i][4] <= 2500
        and 3 <= stats[i][2] <= 120
        and 6 <= stats[i][3] <= 120
    )
    return float(glyph_like / (float(h * w) / 100_000.0 + 1e-9))


def compute_color_variance(image_bgr):
    """
    Blend of saturation and value std-dev in HSV.
    High = rich natural scene; low = flat slide / UI.
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32) / 255.0
    val = hsv[:, :, 2].astype(np.float32) / 255.0
    return float(np.std(sat) * 0.5 + np.std(val) * 0.5)


def estimate_motion(video_path, start_sec, end_sec, sample_points=8):
    """
    Sample frames across the segment and measure inter-frame differences.

    Returns:
        mean_motion  – average frame-diff score  [0, ~1]
        peak_motion  – maximum single-step score (catches burst action)
        motion_std   – std-dev of scores (low = smooth, high = erratic)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.0, 0.0, 0.0

    fps          = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1
    duration     = total_frames / fps

    start_sec = max(0.0, min(float(start_sec), duration - 0.1))
    end_sec   = max(start_sec + 0.1, min(float(end_sec), duration))

    times = np.linspace(start_sec, end_sec, num=int(sample_points))
    prev, diffs = None, []

    for t in times:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (320, 180))
        if prev is not None:
            diffs.append(float(np.mean(cv2.absdiff(prev, gray))) / 255.0)
        prev = gray

    cap.release()

    if not diffs:
        return 0.0, 0.0, 0.0

    arr = np.array(diffs)
    return float(arr.mean()), float(arr.max()), float(arr.std())


# ---------------------------------------------------------------------------
# Feature normalisation — all values → [0, 1]
# ---------------------------------------------------------------------------

def extract_features(
    face_count, largest_face_ratio,
    mean_motion, peak_motion, motion_std,
    edge_density, sharpness, text_density, color_variance,
):
    """Convert raw signals into a unified normalised feature dict."""
    def norm(value, ceiling):
        return float(min(value / (ceiling + 1e-9), 1.0))

    burst       = peak_motion / (mean_motion + 0.01)
    consistency = max(0.0, 1.0 - norm(motion_std, FEATURE_RANGES["motion_consistency"]))

    return {
        "face_presence"      : 1.0 if face_count > 0 else 0.0,
        "face_dominance"     : norm(largest_face_ratio, FEATURE_RANGES["face_dominance"]),
        "face_count_norm"    : norm(face_count,         FEATURE_RANGES["face_count_norm"]),
        "motion_mean"        : norm(mean_motion,        FEATURE_RANGES["motion_mean"]),
        "motion_peak"        : norm(peak_motion,        FEATURE_RANGES["motion_peak"]),
        "motion_burst"       : norm(burst,              FEATURE_RANGES["motion_burst"]),
        "motion_consistency" : consistency,
        "edge_density"       : norm(edge_density,       FEATURE_RANGES["edge_density"]),
        "sharpness"          : norm(sharpness,          FEATURE_RANGES["sharpness"]),
        "text_density"       : norm(text_density,       FEATURE_RANGES["text_density"]),
        "color_variance"     : norm(color_variance,     FEATURE_RANGES["color_variance"]),
    }


# ---------------------------------------------------------------------------
# Gaussian Likelihood Profiling classifier
# ---------------------------------------------------------------------------

def _gaussian_log_likelihood(value, mu, sigma):
    """Unnormalised log N(value | mu, sigma). Constant term omitted."""
    return -0.5 * ((value - mu) / (sigma + 1e-9)) ** 2


def classify_scene(features):
    """
    Score every scene profile against the feature dict using Gaussian
    log-likelihoods, then apply softmax to get a calibrated probability.

    Returns:
        label      – winning scene label
        confidence – softmax probability clamped to [0.40, 0.95]
        all_probs  – {label: probability} for every scene
    """
    log_scores = {
        scene: sum(
            _gaussian_log_likelihood(features[feat], mu, sigma)
            for feat, (mu, sigma) in profile.items()
            if feat in features
        )
        for scene, profile in SCENE_PROFILES.items()
    }

    labels = list(log_scores.keys())
    raw    = np.array([log_scores[l] for l in labels], dtype=np.float64)
    raw   -= raw.max()                  # numerical stability before exp
    probs  = np.exp(raw)
    probs /= probs.sum()

    best_idx   = int(np.argmax(probs))
    label      = labels[best_idx]
    confidence = float(np.clip(probs[best_idx], 0.40, 0.95))
    all_probs  = {l: round(float(p), 4) for l, p in zip(labels, probs)}

    return label, round(confidence, 3), all_probs


# ---------------------------------------------------------------------------
# Temporal smoother
# ---------------------------------------------------------------------------

class SceneSmoothing:
    """
    Majority-vote over a sliding window of recent raw labels.
    Prevents a single anomalous frame from flipping the output.
    Confidence is penalised slightly when smoothing overrides the raw label.
    """

    def __init__(self, window: int = 3):
        self._window: deque = deque(maxlen=window)

    def smooth(self, raw_label: str, confidence: float):
        self._window.append(raw_label)
        smoothed = Counter(self._window).most_common(1)[0][0]
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
        start_sec      : segment start in seconds
        end_sec        : segment end in seconds
        thumbnail_path : optional representative frame for vision signals
        smoother       : optional SceneSmoothing instance

    Returns:
        label       – scene label string
        confidence  – probability in [0.40, 0.95]
        debug       – raw signals, normalised features, and per-scene probabilities
    """
    face_count = largest_face_ratio = 0
    edge_density = sharpness = text_density = color_variance = 0.0

    if thumbnail_path and os.path.exists(thumbnail_path):
        img = cv2.imread(thumbnail_path)
        if img is not None:
            face_count, largest_face_ratio = detect_faces_info(img)
            edge_density                   = compute_edge_density(img)
            sharpness                      = compute_sharpness(img)
            text_density                   = compute_text_density(img)
            color_variance                 = compute_color_variance(img)

    mean_motion, peak_motion, motion_std = estimate_motion(
        video_path, start_sec, end_sec, sample_points=8
    )

    features = extract_features(
        face_count, largest_face_ratio,
        mean_motion, peak_motion, motion_std,
        edge_density, sharpness, text_density, color_variance,
    )

    label, confidence, all_probs = classify_scene(features)

    if smoother is not None:
        label, confidence = smoother.smooth(label, confidence)

    debug = {
        "raw_signals": {
            "face_count"         : int(face_count),
            "largest_face_ratio" : round(float(largest_face_ratio), 4),
            "mean_motion"        : round(float(mean_motion), 4),
            "peak_motion"        : round(float(peak_motion), 4),
            "motion_std"         : round(float(motion_std), 4),
            "edge_density"       : round(float(edge_density), 4),
            "sharpness"          : round(float(sharpness), 2),
            "text_density"       : round(float(text_density), 2),
            "color_variance"     : round(float(color_variance), 4),
        },
        "normalised_features" : {k: round(v, 4) for k, v in features.items()},
        "scene_probabilities" : all_probs,
    }

    return label, float(confidence), debug