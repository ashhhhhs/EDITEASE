import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = BASE_DIR / "exports"
SCENE_INDEXES_DIR = BASE_DIR / "scene_indexes"

# Ensure important directories exist
DATA_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)
SCENE_INDEXES_DIR.mkdir(exist_ok=True)

# Database Settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "editease")
COLLECTION = os.getenv("COLLECTION", "scenes")

# API Settings
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 5000))
API_DEBUG = os.getenv("API_DEBUG", "True").lower() == "true"

# Celery / Redis Settings
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# External tools
FFMPEG_PATH = os.getenv(
    "FFMPEG_PATH", 
    r"D:\ffmpeg-2026-02-04-git-627da1111c-full_build\bin\ffmpeg.exe"
)

# Pipeline settings
SCENE_DETECT_THRESHOLD = float(os.getenv("SCENE_DETECT_THRESHOLD", "27.0"))
CLASSIFIER_TYPE = os.getenv("CLASSIFIER_TYPE", "rule_based")
