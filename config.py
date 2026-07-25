import os
from pathlib import Path
from dotenv import load_dotenv

# Base directories
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")
DATA_DIR         = BASE_DIR / "data"
EXPORTS_DIR      = BASE_DIR / "exports"
SCENE_INDEXES_DIR = BASE_DIR / "scene_indexes"

# Ensure important directories exist
DATA_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)
SCENE_INDEXES_DIR.mkdir(exist_ok=True)

# Database Settings
MONGO_URI  = os.getenv("MONGO_URI",  "mongodb://localhost:27017")
DB_NAME    = os.getenv("DB_NAME",    "editease")
COLLECTION = os.getenv("COLLECTION", "scenes")

# API Settings
API_HOST    = os.getenv("API_HOST",    "127.0.0.1")
API_PORT    = int(os.getenv("API_PORT", 5000))
API_DEBUG   = os.getenv("API_DEBUG",   "False").lower() == "true"
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5173")

# Origins permitted to call the API. Defaults to the SPA origin plus the 127.0.0.1
# dev variant, since Vite is reachable under both hostnames locally.
# In production set CORS_ORIGINS explicitly to your deployed frontend origin.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", f"{APP_BASE_URL},http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

# Upload limits — enforced by the API before anything touches disk.
# MAX_UPLOAD_BYTES is wired to Flask's MAX_CONTENT_LENGTH in create_app().
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(2 * 1024 ** 3)))  # 2 GiB
ALLOWED_VIDEO_EXTENSIONS = tuple(
    ext.strip().lower()
    for ext in os.getenv("ALLOWED_VIDEO_EXTENSIONS", ".mp4,.mov,.avi,.mkv").split(",")
    if ext.strip()
)

# Email Settings — Gmail SMTP with App Password
RESEND_API_KEY      = os.environ.get("RESEND_API_KEY",      "")   # kept for transition period
MAIL_FROM           = os.environ.get("MAIL_FROM",           "")   # legacy alias
MAIL_SERVER         = os.getenv("MAIL_SERVER",              "smtp.gmail.com")
MAIL_PORT           = int(os.getenv("MAIL_PORT",            "587"))
MAIL_USE_TLS        = os.getenv("MAIL_USE_TLS",     "True").lower() == "true"
MAIL_USERNAME       = os.getenv("MAIL_USERNAME",            "")
MAIL_PASSWORD       = os.getenv("MAIL_PASSWORD",            "")   # 16-char Gmail App Password
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER",     "")
GOOGLE_CLIENT_ID    = os.environ.get("GOOGLE_CLIENT_ID",   "")

# Celery / Redis Settings
CELERY_BROKER_URL    = os.getenv("CELERY_BROKER_URL",    "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# External tools
# Bare command name by default, resolved via PATH — see SETUP.md. Set
# FFMPEG_PATH to an absolute path only for a non-PATH install. Note ffmpeg is
# optional: the scene pipeline decodes via OpenCV (which bundles its own
# ffmpeg), and only edited-video metadata detection (ffprobe) reads this value.
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

# ---------------------------------------------------------------------------
# Pipeline settings
# ---------------------------------------------------------------------------

SCENE_DETECT_THRESHOLD = float(os.getenv("SCENE_DETECT_THRESHOLD", "27.0"))
CLASSIFIER_TYPE        = os.getenv("CLASSIFIER_TYPE", "ml")  # "ml" | "rule_based"

# Minimum scene duration in seconds — shorter scenes are merged after detection.
# Raise this if you see many artifact micro-cuts; lower it for fast-cut content.
MIN_SCENE_DURATION = float(os.getenv("MIN_SCENE_DURATION", "0.5"))

# Agentic decision layer — confidence bands
# ML confidence >= CONF_AUTO_HIGH   → auto-accept without rule-based check
# ML confidence in [CONF_FUSE_LOW, CONF_AUTO_HIGH) → weighted fusion
# Fused confidence < CONF_FUSE_LOW  → mark as uncertain / escalate
CONF_AUTO_HIGH = float(os.getenv("CONF_AUTO_HIGH", "0.85"))
CONF_FUSE_LOW  = float(os.getenv("CONF_FUSE_LOW",  "0.58"))

# Weight of ML prediction in the fusion step (rule-based gets 1 - ML_WEIGHT).
ML_WEIGHT = float(os.getenv("ML_WEIGHT", "0.65"))

# An `audience_reaction` label requires at least this many visible faces.
AUDIENCE_REACTION_MIN_FACES = int(os.getenv("AUDIENCE_REACTION_MIN_FACES", "3"))

# Face detector used to verify a face before an emotion is trusted.
#
# The default was "opencv", the same Haar family as the cheap pre-filter, so
# enforce_detection=True could never catch what the pre-filter got wrong. Measured
# against 120 human-labelled clips, opencv reported faces on foliage (a hanging
# flower pot scored "sad") and simultaneously missed real faces in wide shots.
# retinaface and mtcnn both got every checked case right; retinaface costs about
# 2.3s per frame against opencv's 0.2s, which is the price of the correctness.
EMOTION_DETECTOR_BACKEND = os.getenv("EMOTION_DETECTOR_BACKEND", "retinaface")

# Which trained scene-classifier version the pipeline serves. Training writes a
# new version rather than overwriting this one, so promoting a retrained model
# is a deliberate switch made after evaluating it, not a side effect of training.
SCENE_MODEL_VERSION = os.getenv("SCENE_MODEL_VERSION", "v2")

# ---------------------------------------------------------------------------
# Cloudinary Settings
# ---------------------------------------------------------------------------

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY    = os.getenv("CLOUDINARY_API_KEY",    "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
