# EditEase

**AI-assisted video editing platform for post-production teams.**

EditEase ingests raw footage, runs scene detection and emotion analysis through a background pipeline, and gives reviewers a clip-grid workspace with role-aware controls (admin / reviewer / editor). Tagline: *"Stop sorting footage manually."*

> **Running or evaluating this project?** See **[SETUP.md](SETUP.md)** for a
> step-by-step guide. Quickest check: `pip install -r Requirements.txt && pytest`
> (no MongoDB/Redis/credentials needed — tests use an in-memory database).

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 · Vite · React Router · GSAP + Lenis · Recharts · Lucide React |
| API | Flask (Blueprints) · token-based auth |
| Background jobs | Celery · Redis |
| Database | MongoDB (mongomock in tests) |
| ML pipeline | ResNet-based scene classifier · OpenCV Haar cascade · rule-based fallback |
| Storage | Cloudinary |

---

## Quick start

```bash
# Install
make install          # pip install -e .[dev]

# Run all services (requires Redis + MongoDB running)
make run-api          # Flask on :5000
make run-frontend     # Vite on :5173
make run-celery       # Celery worker

# Process all videos in data/
make run-pipeline

# Health check
make health
```

---

## Environment

Copy `.env.example` → `.env` and fill in values. Key variables:

| Variable | Default | Notes |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | |
| `DB_NAME` | `editease` | |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | |
| `CLASSIFIER_TYPE` | `ml` | `"ml"` or `"rule_based"` |
| `FFMPEG_PATH` | Windows path | Override for non-Windows |
| `CLOUDINARY_CLOUD_NAME` / `API_KEY` / `API_SECRET` | — | Required for upload |
| `CONF_AUTO_HIGH` | `0.85` | ML confidence auto-accept threshold |
| `CONF_FUSE_LOW` | `0.58` | Below this → escalate to reviewer |
| `ML_WEIGHT` | `0.65` | Weight for ML in fusion step |

---

## Testing

```bash
pytest tests/                        # full suite
pytest tests/test_api.py             # single file
pytest tests/ -k "test_name"         # single test
```

Tests use `mongomock` (via `conftest.py`) — no real MongoDB needed. Email and Cloudinary calls are stubbed. The ML model is not required in the test environment.

---

## Project structure

```
editease/
├── api/                    # Flask app — blueprints, templates
│   └── blueprints/         # media, admin, auth, review
├── services/               # Business logic (auth, tasks, email, cloudinary, …)
├── pipeline/               # Video processing pipeline
│   ├── classifiers/        # MLClassifier + RuleBasedClassifier
│   ├── models/             # trained model (scene_classifier*.pth + label_encoder*.json)
│   ├── processing/         # run_pipeline.py, detect_scenes.py, …
│   └── training/           # dataset export + model training scripts
├── database/               # MongoDB ingest + schema helpers
├── frontend/               # React + Vite SPA
│   └── src/
│       ├── components/     # Shared UI primitives
│       ├── hooks/          # Custom React hooks
│       └── lib/api.js      # Single API client for all pages
├── tests/                  # pytest suite
├── ui/                     # Legacy Streamlit UI
├── utils/                  # Logger and shared helpers
├── scripts/                # Maintenance / evaluation scripts
├── Requirements.txt        # Python dependencies
├── pyproject.toml          # Package metadata + dependencies
├── .env.example            # Backend config template (copy → .env)
└── config.py               # Reads all config from .env
```

---

## Architecture

### Upload → pipeline flow

1. `POST /upload` → `api/blueprints/media.py` saves file, creates task in MongoDB
2. `services/task_service.py` dispatches `process_video_task` or `auto_organize_task` to Celery
3. Celery runs `pipeline/processing/run_pipeline.py::process_video()`
4. Pipeline produces `scene_indexes/<video>_scene_index.json` and upserts docs into `scenes` collection
5. `auto_organize_task` additionally writes to `organized_videos` and moves assets in Cloudinary

### Pipeline stages (per video)

1. Cloudinary upload
2. Scene detection — threshold-based cut detection
3. Per-scene: thumbnail extraction → adaptive emotion sampling → face detection → ML classification
4. **Agentic decision layer**: confidence ≥ 0.85 → auto-accept; middle band → weighted fusion with rule-based classifier; fusion < 0.58 → mark `uncertain=True` for reviewer queue

### Classifier fallback chain

`MLClassifier` (ResNet) → `RuleBasedClassifier` (on missing model, import error, low confidence, or retired labels)

### MongoDB collections

| Collection | Notes |
|---|---|
| `scenes` | One doc per detected scene |
| `tasks` | Celery job tracking |
| `organized_videos` | Post-organize records with `file_hash` deduplication |
| `users` | Roles: `admin`, `reviewer`, `editor` |

---

## Design system

Palette, typography, motion, and component rules are previewed under
`frontend/public/design-system/`. The live tokens live in `frontend/src/index.css`.

**TL;DR:** GitHub-Dark base (`#0d1117`), accent blue `#58a6ff`, Inter + JetBrains Mono, `cubic-bezier(0.16, 1, 0.3, 1)` on all motion, Lucide React icons only.
