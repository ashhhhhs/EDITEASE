"""
Patches all factual inaccuracies in Final_Project_Report.md.
Run with: /mnt/d/EDITEASE/venv/bin/python patch_report.py
"""

PATH = "/mnt/d/EDITEASE/Final_Project_Report.md"

with open(PATH, "r", encoding="utf-8") as f:
    text = f.read()

original = text  # keep for diff check

# ─────────────────────────────────────────────────────────────────────────────
# FIX 1  Scene detection: ContentDetector only → ContentDetector + AdaptiveDetector ensemble
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    "The scene detection subsystem uses the PySceneDetect library's `ContentDetector` algorithm to identify visual cut points within the video stream. The detector computes a weighted average of the per-channel HSV frame differences. When this score exceeds the configured threshold of 27, the current frame is marked as a scene boundary.\n\nEach detected boundary is recorded as a timestamp, and the system uses these timestamps to define a list of scene segments, each with an associated start time and end time. The duration of each scene is computed as the difference between the end and start timestamps.\n\nFor videos in which no cuts are detected, the entire recording is treated as a single scene, preserving data integrity even in cases where the input footage is a single uninterrupted take.",

    """The scene detection subsystem uses an **ensemble of two PySceneDetect detectors** running simultaneously on the same video stream. The `ContentDetector` (threshold = 27, configurable via `SCENE_DETECT_THRESHOLD`) handles hard cuts by computing a weighted average of per-channel HSV frame differences. The `AdaptiveDetector` runs in parallel to catch gradual transitions — fades and dissolves — that a pure threshold-based approach would miss. Using both detectors ensures reliable boundary detection across footage types ranging from fast-cut event coverage to slow-dissolve documentary material.

After detection, two post-processing steps clean the raw boundary list. First, duplicate boundaries are removed (both detectors can fire at the same frame). Second, scenes shorter than `MIN_SCENE_DURATION = 0.5` seconds are merged into the following scene to eliminate artifact micro-cuts from camera flashes or compression artefacts. If no scenes remain after filtering, the entire video is treated as a single scene, ensuring the pipeline always produces at least one indexable record."""
)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 2  Thumbnail extraction: CAP_PROP_POS_MSEC → CAP_PROP_POS_FRAMES + frame_idx; add 1280px cap
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    "Thumbnail extraction is performed using OpenCV's `VideoCapture` class. The video file is opened, and the capture position is set to the midpoint timestamp in milliseconds using `cap.set(cv2.CAP_PROP_POS_MSEC, midpoint_ms)`. The resulting frame is saved as a JPEG image and uploaded to Cloudinary, with the resulting URL stored in the scene metadata document.",

    """Thumbnail extraction is performed using OpenCV's `VideoCapture` class. The video file is opened, the midpoint timestamp is converted to a frame index using the video's frame rate (`frame_idx = int(timestamp * fps)`), and the capture position is set using `cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)`. This frame-index approach is used rather than millisecond seeking because it is more reliable for variable-frame-rate footage. Extracted frames wider than 1280 pixels are automatically downscaled (preserving aspect ratio) before saving, preventing AI models from hanging on 4K or 8K source footage. The resulting JPEG is uploaded to Cloudinary and the URL stored in the scene metadata document."""
)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 3  Emotion sampling: fixed 20/40/60/80% → adaptive linspace with edge weighting
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    "For each detected scene, the subsystem samples frames at four evenly spaced intervals: 20%, 40%, 60%, and 80% of the scene's total duration. For each sampled frame, the subsystem first applies the OpenCV Haar Cascade face detector (`haarcascade_frontalface_default.xml`). If no face is detected, the frame is skipped and no inference is performed. If one or more faces are detected, the DeepFace library is used to infer the dominant emotion from the facial region.\n\nAfter sampling all four frames, the dominant emotion for the scene is determined by majority vote across the samples where faces were present. If fewer than two valid samples are obtained, the emotion field is set to null.\n\nThis multi-frame sampling approach avoids the single-frame bias problem, where a momentary facial expression that does not represent the emotional character of the scene could dominate the classification. By sampling across the temporal extent of the scene, the system produces a more representative emotion estimate.",

    """For each detected scene, the subsystem applies **adaptive temporal sampling** whose sample count scales with scene duration:

- Scenes under 3 seconds: **2 samples**
- Scenes 3–10 seconds: **4 samples**
- Scenes 10–30 seconds: **8 samples**
- Scenes over 30 seconds: **12 samples** (cap, as returns diminish beyond this)

Sample timestamps are distributed using `np.linspace(0.1, 0.9, n_samples)` — kept away from the exact edges (0 and 1) to avoid black frames at cut boundaries. The first and last samples receive a **1.5× vote weight** when determining the dominant emotion, reflecting the editorial principle that the opening and closing moments of a scene are more representative of its character than mid-scene content.

For each sampled frame, the Haar Cascade face detector is applied first. If no face is found, the frame is skipped entirely without invoking the heavier DeepFace inference pipeline, minimising compute overhead for non-face scenes. If a face is detected, DeepFace infers the dominant emotion. The scene's final `dominant_emotion` is the weighted majority-vote winner across all successful samples; the full `emotion_timeline` array is also stored in MongoDB for downstream analysis. If no valid samples produce a face detection, the emotion field is set to null."""
)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 4  Agentic decision thresholds: <0.60 → per-class; CONF_FUSE_LOW = 0.58 not 0.60
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    """```
IF confidence >= 0.85:
    scene_label = ml_label
    reviewed = True
    uncertain = False

ELSE IF confidence < 0.60:
    scene_label = rule_classifier.classify(thumbnail_path)
    reviewed = False
    uncertain = False

ELSE (0.60 <= confidence < 0.85):
    rule_label = rule_classifier.classify(thumbnail_path)
    IF rule_label == ml_label:
        scene_label = ml_label
        reviewed = True
        uncertain = False
    ELSE:
        scene_label = ml_label
        reviewed = False
        uncertain = True
```""",

    """The agentic decision layer operates in two stages:

**Stage 1 — Per-class threshold gate (inside MLClassifier):** Before the agentic layer is even reached, the ML classifier applies a per-class confidence threshold. Classes that are visually distinctive (e.g., `text_slide` at 0.52, `screen_recording` at 0.52) have lower thresholds; classes that are easily confused (e.g., `presenter` at 0.70, `audience_reaction` at 0.72) have higher thresholds. If the ML prediction falls below its class threshold, the rule-based classifier is immediately invoked as a fallback at this stage, before the agentic layer runs.

**Stage 2 — Confidence-band agentic logic (in run_pipeline.py):**

```
CONF_AUTO_HIGH = 0.85   # auto-accept threshold
CONF_FUSE_LOW  = 0.58   # uncertainty boundary
ML_WEIGHT      = 0.65   # ML share in weighted fusion
RULE_WEIGHT    = 0.35

IF scene_conf >= CONF_AUTO_HIGH:
    reviewed = True, uncertain = False          # auto-accepted

ELIF classifier already used rule_based (fell back in Stage 1):
    reviewed = False, uncertain = True          # escalated — still low confidence

ELSE (medium band — ML confidence only):
    rb_label, rb_conf = RuleBasedClassifier.classify(...)
    fused_conf = weighted_fusion(ml_conf, ML_WEIGHT, rb_conf, RULE_WEIGHT)

    IF ml_label == rb_label:
        fused_conf += 0.05 (agreement boost, capped at 0.95)
        reviewed = True, uncertain = False
    ELSE:
        winner = argmax of weighted scores
        uncertain = (fused_conf < CONF_FUSE_LOW)
        reviewed = not uncertain
```"""
)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 5  Rule-based description: "heuristic rules" → Gaussian Likelihood Profiling
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    "The rule-based classifier (`pipeline/classifiers/rule_based_classifier.py`) applies heuristic rules based on visual features including the presence of faces, motion level estimates, and colour histogram characteristics to assign a class label without relying on trained parameters.",

    """The rule-based classifier (`pipeline/classifiers/rule_based_classifier.py`) delegates to `scene_type_detect.py`, which implements a **Gaussian Likelihood Profiling** system — a principled probabilistic approach rather than a simple set of if/else rules. The system extracts 13 normalised visual and motion features from the thumbnail and video segment: face presence, face dominance, face count, face aspect ratio, motion mean/peak/burst/consistency, edge density, sharpness, text density, colour variance, and colour temperature. Each of the seven scene profiles in the system (testimonial, presenter, audience_reaction, text_slide, screen_recording, b-roll, establishing_shot) is defined as a set of Gaussian (μ, σ) distributions over these features. The classifier computes the sum of Gaussian log-likelihoods for each profile, applies a softmax to produce calibrated probabilities, and returns the winning label with its probability as the confidence score. An optional `SceneSmoothing` temporal majority-vote window can suppress label flicker across consecutive scenes."""
)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 6  Training: Adam → AdamW; 10 epochs → 20 with early stopping; all layers → partial freeze
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    "The ResNet-18 model was trained for 10 epochs using the Adam optimiser with a learning rate of $1 \\times 10^{-4}$ and a batch size of 32. The cross-entropy loss function was used throughout training. Training was performed on the full fine-tuning strategy, in which all layers of the network were allowed to update their weights (as opposed to feature extraction, in which only the final layer is trained). This approach was selected because the target domain — video scene thumbnails — is sufficiently different from ImageNet that updating the convolutional feature extractors, not only the classification head, was expected to improve performance.\n\nLearning rate scheduling and dropout regularisation were not applied in this prototype implementation, as the model demonstrated stable convergence over 10 epochs without significant overfitting.",

    """The ResNet-18 model is trained using a **partial-freeze transfer learning strategy**. Layers 1–3 of the ResNet body (which encode low-level features such as edges and textures that transfer well from ImageNet) are frozen. Only layer 4 (high-level semantic features) and the new classification head are trainable. This protects the expensive ImageNet knowledge whilst allowing the top of the network to adapt to the specific visual semantics of video scene thumbnails.

Training uses the **AdamW optimiser** with two learning-rate parameter groups: a lower rate (`body_lr = 1e-4`) for the unfrozen layer 4 body, and a higher rate (`head_lr = 1e-3`) for the new classification head. A **CosineAnnealingLR** scheduler smoothly decays both learning rates to near-zero over the training period. Training runs for up to **20 epochs** with **early stopping** (patience = 5 epochs without validation accuracy improvement), so the actual number of epochs varies per training run.

Class imbalance is addressed at two levels: a **WeightedRandomSampler** oversamples minority classes during training, and a **class-weighted CrossEntropyLoss** further amplifies the gradient contribution of under-represented classes.

**Data augmentation** is applied during training to reduce overfitting on the moderately sized dataset: RandomCrop(224), RandomHorizontalFlip, RandomRotation(±15°), ColorJitter (brightness, contrast, saturation, hue), RandomGrayscale (5% probability), and RandomErasing (10% probability). The validation transform applies only centre-crop resize and normalisation."""
)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 7  Supported formats: "MP4 only" → .mp4, .mov, .avi, .mkv
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    "The video input subsystem is responsible for accepting raw MP4 video files submitted through the web interface, validating file format compatibility, and preparing the file for processing.",
    "The video input subsystem accepts raw video files in `.mp4`, `.mov`, `.avi`, and `.mkv` formats submitted through the web interface, validating file format compatibility and preparing the file for processing."
)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 8  Class name: "Audience" → "audience_reaction"
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    "4. **Audience** — Crowd or audience reaction shots",
    "4. **Audience Reaction** (`audience_reaction`) — Crowd or audience reaction shots"
)
text = text.replace(
    "| Audience | ~0.88 | ~0.78 | ~0.83 | 100 |",
    "| Audience Reaction | ~0.88 | ~0.78 | ~0.83 | 100 |"
)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 9  Model training description in Section 5.2 (AI section) — epochs & optimiser
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    "The model is trained using the **Adam optimiser** with a learning rate of $1 \\times 10^{-4}$ and **categorical cross-entropy loss**:",
    "The model is trained using the **AdamW optimiser** with two learning-rate parameter groups (body: $1 \\times 10^{-4}$, head: $1 \\times 10^{-3}$), **class-weighted cross-entropy loss**, and a **CosineAnnealingLR** scheduler:"
)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 10  Progress callback system — add to Celery implementation description
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    "The `media_bp` Blueprint in `api/blueprints/media.py` implements the upload endpoint. On receiving a multipart form-data request containing a video file, the endpoint validates the file extension, saves the file to the data directory, and calls `task_service.dispatch_process()` to dispatch the processing task to Celery. The response to the client is a JSON object containing the `task_id` for subsequent status polling.",

    """The `media_bp` Blueprint in `api/blueprints/media.py` implements the upload endpoint. On receiving a multipart form-data request containing a video file, the endpoint validates the file extension, saves the file to the data directory, and calls `task_service.dispatch_process()` to dispatch the processing task to Celery. The response to the client is a JSON object containing the `task_id` for subsequent status polling.

The Celery task (`process_video_task` in `celery_worker.py`) provides **real-time progress callbacks** to the frontend. A `progress_callback` function is passed into `process_video()`, which calls `self.update_state(state="PROGRESS", meta={"message": msg})` and writes the current step description to MongoDB's tasks collection at each pipeline stage (cloud upload, scene detection, per-scene analysis, emotion inference, classification, database storage). The React frontend polls `/task_status/<task_id>` and displays these step messages as a live progress feed, giving users meaningful feedback during what can be a minutes-long processing operation."""
)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 11  Section 3 (scene detection description) — also fix the informal description
# ─────────────────────────────────────────────────────────────────────────────
text = text.replace(
    "The PySceneDetect library, which is used in the EditEase system, implements a content-based detection strategy using a weighted average of frame-to-frame HSV (Hue, Saturation, Value) differences. The ContentDetector algorithm within this library compares consecutive frames and flags boundaries where the content score exceeds a configurable threshold. In the EditEase implementation, a threshold of 27 was selected through experimentation as providing an appropriate balance between sensitivity to genuine scene cuts and robustness against false positives caused by lighting changes or camera motion.",

    """The EditEase scene detection pipeline uses PySceneDetect with an **ensemble of two detectors**: `ContentDetector` (threshold = 27, for hard cuts) and `AdaptiveDetector` (for gradual transitions such as fades and dissolves). Running both detectors simultaneously ensures that hard editorial cuts and softer dissolves are both detected without requiring a separate manual pass. A threshold of 27 was selected for the ContentDetector through experimentation as providing a good balance between sensitivity to genuine scene cuts and robustness against false positives from lighting changes or camera motion. After detection, a post-processing stage merges scenes shorter than 0.5 seconds (artifact cuts) and deduplicates boundaries where both detectors fired simultaneously."""
)

# Verify changes were applied
changes = sum(1 for a, b in zip(original, text) if a != b)
print(f"Characters changed: {changes}")
print(f"Original length: {len(original)}, New length: {len(text)}")

if text == original:
    print("WARNING: No changes were made — check the search strings match exactly.")
else:
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(text)
    print("Report successfully patched and saved.")
