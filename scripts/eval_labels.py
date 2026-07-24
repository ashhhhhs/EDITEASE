"""Shared label vocabulary for the evaluation datasets.

One definition, imported by the exporter, the scorers and the pytest gates, so a
change to the scheme cannot leave two files silently disagreeing about what a
label means.
"""

# ---------------------------------------------------------------------------
# Emotion
# ---------------------------------------------------------------------------
# DeepFace's `disgust` / `fear` / `surprise` are folded into `other`: across 475
# scenes disgust fired once and surprise eight times, and a human cannot reliably
# tell them apart from a still frame anyway. Keeping them as separate classes
# would add noise to every metric without adding editorial meaning.
EMOTION_SCHEME = ["sad", "happy", "neutral", "other", "none"]

EMOTION_PREDICTION_TO_BUCKET = {
    "sad": "sad",
    "happy": "happy",
    "neutral": "neutral",
    "angry": "other",
    "fear": "other",
    "disgust": "other",
    "surprise": "other",
    None: "none",
    "": "none",
}

# ---------------------------------------------------------------------------
# Scene type
# ---------------------------------------------------------------------------
# Must match pipeline/models/label_encoder_v2.json, or test_ml_classifier_quality
# silently drops every annotation whose label the encoder does not know.
SCENE_TYPE_SCHEME = [
    "testimonial",
    "b-roll",
    "audience_reaction",
    "establishing_shot",
    "other",
]

# Labels the model may still emit from an older training run but that are no
# longer supported. Mirrors RETIRED_LABELS in pipeline/classifiers/ml_classifier.py.
RETIRED_SCENE_LABELS = {"presenter", "text_slide", "screen_recording"}

# Short definitions shown in the labelling UI. Without them scene-type labels
# drift between sessions and the eval set measures inconsistency, not accuracy.
SCENE_TYPE_HELP = {
    "testimonial": "One person talking to camera",
    "b-roll": "Supporting footage, movement, no one addressing camera",
    "audience_reaction": "Several people reacting — a crowd or panel",
    "establishing_shot": "Wide, static scene-setting shot",
    "other": "None of the above",
}


# Display text for the labelling UI, and the keyboard key bound to each option.
EMOTION_OPTIONS = [
    {"key": "1", "value": "sad", "label": "Sad"},
    {"key": "2", "value": "happy", "label": "Happy"},
    {"key": "3", "value": "neutral", "label": "Neutral"},
    {"key": "4", "value": "other", "label": "Other emotion"},
    {"key": "5", "value": "none", "label": "No face / can't tell"},
]

SCENE_TYPE_KEYS = ["q", "w", "e", "r", "t"]

SCENE_TYPE_OPTIONS = [
    {
        "key": SCENE_TYPE_KEYS[i],
        "value": label,
        "label": label.replace("_", " ").replace("-", "-").title(),
        "help": SCENE_TYPE_HELP[label],
    }
    for i, label in enumerate(SCENE_TYPE_SCHEME)
]


def emotion_bucket(prediction):
    """Map a raw DeepFace emotion (or None) into the labelling scheme."""
    return EMOTION_PREDICTION_TO_BUCKET.get(prediction, "other")


def scene_type_bucket(prediction):
    """Map a raw scene label into the scheme; retired labels collapse to `other`."""
    if not prediction or prediction in RETIRED_SCENE_LABELS:
        return "other"
    return prediction if prediction in SCENE_TYPE_SCHEME else "other"
