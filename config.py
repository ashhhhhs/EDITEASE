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
API_DEBUG   = os.getenv("API_DEBUG",   "True").lower() == "true"
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5173")

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
FFMPEG_PATH = os.getenv(
    "FFMPEG_PATH",
    r"D:\ffmpeg-2026-02-04-git-627da1111c-full_build\bin\ffmpeg.exe",
)

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

# ---------------------------------------------------------------------------
# Cloudinary Settings
# ---------------------------------------------------------------------------

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY    = os.getenv("CLOUDINARY_API_KEY",    "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
