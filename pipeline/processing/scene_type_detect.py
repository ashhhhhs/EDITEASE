import os
import cv2
import numpy as np

CASCADE_PATH = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")


def detect_faces_info(image_bgr):
    """Return (face_count, largest_face_area_ratio)"""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40)
    )

    h, w = gray.shape
    frame_area = float(h * w)

    if len(faces) == 0:
        return 0, 0.0

    areas = [(fw * fh) for (fx, fy, fw, fh) in faces]
    largest_ratio = max(areas) / frame_area
    return int(len(faces)), float(largest_ratio)


def estimate_motion(video_path, start_sec, end_sec, sample_points=3):
    """
    Estimate motion by sampling a few frames in the segment and measuring frame difference.
    Returns motion_score in [0, ~1+] (higher = more motion)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.0

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if fps <= 0 or total_frames <= 0:
        cap.release()
        return 0.0

    duration = total_frames / fps
    start_sec = max(0.0, min(float(start_sec), float(duration) - 0.05))
    end_sec = max(float(start_sec) + 0.05, min(float(end_sec), float(duration)))

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
            score = float(np.mean(diff)) / 255.0
            diffs.append(score)

        prev = gray

    cap.release()
    if not diffs:
        return 0.0

    return float(np.mean(diffs))


# ---------------- NEW: lightweight screen/text features (no OCR) ----------------
def compute_edge_density(image_bgr):
    """Fraction of edge pixels (Canny) in the frame."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(gray, 60, 160)
    return float(np.mean(edges > 0))


def compute_sharpness(image_bgr):
    """Variance of Laplacian (higher = sharper)."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    return float(lap.var())


def compute_text_component_density(image_bgr):
    """
    Heuristic: binarize + count "small-ish" connected components that resemble glyphs.
    Returns density in [0..~] (higher = more text-like components).
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # Improve contrast for slides/UIs
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    # Adaptive threshold tends to catch text on varying backgrounds
    bw = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 31, 7
    )

    # Remove noise
    bw = cv2.medianBlur(bw, 3)

    # Connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bw, connectivity=8)

    h, w = gray.shape
    frame_area = float(h * w)

    # Count components that look like characters (area bounds are conservative)
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

    # normalize by frame area so it generalizes across resolutions
    density = glyph_like / (frame_area / 100000.0 + 1e-9)
    return float(density)


def classify_scene_type(face_count, largest_face_ratio, motion_score,
                        edge_density=0.0, sharpness=0.0, text_density=0.0):
    """
    Rule-based baseline classifier with added screen/text detection.
    Thresholds are intentionally simple and tunable.
    """

    # 1) Talking head / testimonial (single face, large, very still)
    if face_count == 1 and largest_face_ratio >= 0.08 and motion_score < 0.08:
        return "testimonial", 0.75

    # 2) Presenter (single face, moderate motion — gesturing, walking, presenting)
    if face_count == 1 and largest_face_ratio >= 0.05 and motion_score >= 0.08:
        return "presenter", 0.70

    # 3) Audience reaction / group
    if face_count >= 3 and largest_face_ratio < 0.06:
        return "audience_reaction", 0.70

    # 3) Text slide (no faces, very low motion, strong text-like component density)
    # text_density tends to be high for slides; motion should be near-static.
    if face_count == 0 and motion_score < 0.05 and text_density >= 18.0:
        return "text_slide", 0.70

    # 4) Screen recording (no faces, sharp + edgey frame, low/moderate motion)
    # Screen footage is typically very sharp + many straight edges / UI lines.
    if face_count == 0 and sharpness >= 120.0 and edge_density >= 0.085 and motion_score < 0.12:
        return "screen_recording", 0.65

    # 5) B-roll (no faces + higher motion)
    if face_count == 0 and motion_score >= 0.10:
        return "b-roll", 0.65

    # 6) Establishing shot (no faces + low motion)
    if face_count == 0 and motion_score < 0.06:
        return "establishing_shot", 0.60

    return "other", 0.50


def detect_scene_type(video_path, start_sec, end_sec, thumbnail_path=None):
    """
    Uses thumbnail (if provided) for faces + screen/text heuristics,
    and video segment for motion.
    Returns: (scene_label, scene_confidence, debug_dict)
    """
    face_count, largest_face_ratio = 0, 0.0
    edge_density, sharpness, text_density = 0.0, 0.0, 0.0

    if thumbnail_path and os.path.exists(thumbnail_path):
        img = cv2.imread(thumbnail_path)
        if img is not None:
            face_count, largest_face_ratio = detect_faces_info(img)
            edge_density = compute_edge_density(img)
            sharpness = compute_sharpness(img)
            text_density = compute_text_component_density(img)

    motion_score = estimate_motion(video_path, start_sec, end_sec, sample_points=4)

    label, conf = classify_scene_type(
        face_count, largest_face_ratio, motion_score,
        edge_density=edge_density,
        sharpness=sharpness,
        text_density=text_density
    )

    debug = {
        "face_count": int(face_count),
        "largest_face_ratio": float(largest_face_ratio),
        "motion_score": float(motion_score),
        "edge_density": float(edge_density),
        "sharpness": float(sharpness),
        "text_density": float(text_density),
    }

    return label, float(conf), debug
