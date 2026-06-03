# EditEase — Setup & Run Guide

A step-by-step guide for running and evaluating EditEase. Two paths are provided:

- **Path A — Verify the test suite** (fastest, **no MongoDB/Redis/credentials needed**).
- **Path B — Run the full application** (API + frontend + background pipeline).

> Tested on Python 3.12 (works on 3.9+). The trained ML model is included under
> `pipeline/models/`, so no retraining is required.

---

## Prerequisites

| Tool | Needed for | Notes |
|------|-----------|-------|
| **Python 3.9+** | everything | `python --version` |
| **pip** | install deps | bundled with Python |
| **Node.js 18+ & npm** | frontend (Path B) | `node --version` |
| **MongoDB** | full app (Path B) | local `mongodb://localhost:27017` is fine |
| **Redis** | background jobs (Path B) | for Celery |
| **ffmpeg** | video pipeline (Path B) | `ffmpeg` on PATH, or set `FFMPEG_PATH` |

> **Path A (tests) needs only Python + pip.** Everything else is for running the live app.

---

## Path A — Verify the test suite (recommended first step)

The tests use an in-memory database (`mongomock`); email and Cloudinary calls are
stubbed. **No external services or credentials are required.**

```bash
# 1. (recommended) create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r Requirements.txt    # or:  pip install -e .[dev]

# 3. run the tests
pytest
```

**Expected result:**

```
68 passed, 3 skipped
```

The 3 skips are intentional: 2 ML-quality tests that need an optional labelled
dataset (not shipped), and 1 test for a removed endpoint (documented in the test).

---

## Path B — Run the full application

### 1. Install dependencies

```bash
# Python (in a venv, as above)
pip install -r Requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### 2. Configure environment

```bash
cp .env.example .env                       # backend config
cp frontend/.env.example frontend/.env     # frontend config (Google client ID)
```

Then edit `.env` and fill in the values you have. Minimum to boot the API locally:

| Variable | Example | Required for |
|----------|---------|--------------|
| `MONGO_URI` | `mongodb://localhost:27017` | API to start |
| `DB_NAME` | `editease` | API to start |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | background jobs |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | background jobs |
| `FFMPEG_PATH` | `ffmpeg` | video pipeline |
| `CLOUDINARY_CLOUD_NAME` / `_API_KEY` / `_API_SECRET` | — | uploads/storage |
| `MAIL_*` | — | sending email (optional) |
| `GOOGLE_CLIENT_ID` (+ `VITE_GOOGLE_CLIENT_ID` in `frontend/.env`) | — | Google sign-in (optional) |

> The app starts with just `MONGO_URI` set. Cloudinary/email/Google features are
> only exercised when used.

### 3. Start the services

Make sure **MongoDB** and **Redis** are running, then in separate terminals:

```bash
make run-api          # Flask API   → http://localhost:5000
make run-frontend     # Vite dev UI → http://localhost:5173
make run-celery       # Celery worker (background video processing)
```

On Windows without `make`, run the underlying commands directly:

```bash
python -m api.api_server
cd frontend && npm run dev
python -m celery -A api.celery_worker.celery_app worker --loglevel=info --pool=solo
```

### 4. Use it

Open **http://localhost:5173**, register an account, upload footage, and watch the
pipeline organise it into the clip-grid workspace.

### 5. (Optional) Process videos directly

Drop video files into `data/` and run the pipeline without the UI:

```bash
make run-pipeline      # python -m pipeline.processing.run_pipeline
```

### Health check

```bash
make health            # python api/health_check.py
```

---

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| `ModuleNotFoundError: No module named 'dotenv'` (or any package) | Run `pip install -r Requirements.txt` inside your activated venv |
| API fails with a MongoDB connection error | Start MongoDB, or set `MONGO_URI` to a reachable instance |
| Celery won't start / jobs never run | Start Redis and confirm `CELERY_BROKER_URL` |
| `ffmpeg not found` during pipeline | Install ffmpeg and set `FFMPEG_PATH` (use `ffmpeg` if it's on PATH) |
| Emotion detection warnings | `deepface` is optional; the pipeline degrades gracefully. Enable with `pip install -e .[full]` |
| Frontend can't reach API | Confirm API is on `:5000` and `APP_BASE_URL` matches the frontend origin |

---

## What's included

- Full backend (`api/`, `services/`, `pipeline/`, `database/`, `utils/`, `ui/`)
- Frontend SPA (`frontend/`)
- Trained ML model (`pipeline/models/`) — no training needed
- Test suite (`tests/`) — runs green with zero external setup

Not included (by design): virtual environments, `node_modules`, generated media,
and real credentials. Copy the `.env.example` files and add your own values.
