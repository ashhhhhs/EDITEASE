# EditEase — Technical Audit

**Date:** 2026-07-23
**Commit audited:** `9783ef5f` (branch `main`, clean tree)
**Scope:** full codebase — Flask API, React SPA, Celery pipeline, MongoDB layer, test suite

---

## 1. Executive summary

EditEase is a **Flask + React + Celery video-organization platform**, not a plain web app. Raw
footage is uploaded, a background pipeline detects scenes, classifies them with a ResNet model
(with a rule-based fallback), and surfaces uncertain clips in a role-aware review queue.

The codebase is in **good structural shape**: clean blueprint/service separation, no dead
credentials in git, a passing test suite, and an unusually thoughtful "agentic decision layer"
in the pipeline. It reads like a project that has been deliberately tidied.

The problems are concentrated in three places:

| Area | Assessment |
|---|---|
| Structure & layering | **Strong** — blueprints → services → database is consistently applied |
| Test suite | **Good for its size** — 68 passing, zero external deps needed |
| Upload security | **Weak** — arbitrary file write, no size cap, no type check |
| Authorization consistency | **Weak** — admin scoping contradicts itself between endpoints |
| Production readiness | **Not ready** — hardcoded API URL, debug on by default, open CORS |

**Verified during this audit (actually executed, not inferred):**

- `pytest` → **68 passed, 3 skipped** in 31.5s, exactly as `SETUP.md` documents.
- `npm run lint` → **27 errors, 9 warnings**.
- Werkzeug 3.1.5 returns upload filenames **completely unsanitized** (probe script confirmed
  `../../evil.mp4` arrives verbatim) — so finding S1 below is real, not theoretical.
- The production bundle contains **no `process.env` references**, so the `ErrorBoundary` lint
  errors are noise, not a runtime crash.

---

## 2. Architecture

### 2.1 Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 7, React Router 6, Axios, GSAP + Lenis, Recharts, Lucide |
| API | Flask + Blueprints, Flask-CORS, Flask-Mail, Flasgger (Swagger) |
| Background jobs | Celery + Redis |
| Database | MongoDB (`pymongo`); `mongomock` in tests |
| ML | PyTorch ResNet scene classifier + OpenCV Haar cascade + rule-based fallback |
| Storage | Cloudinary (video, thumbnails, avatars, signed ZIP downloads) |

### 2.2 Backend layout

```
config.py                 Single source of config — loads .env at import time
api/
  api_server.py           create_app() factory; registers 4 blueprints + /health
  api_app.py              Back-compat shim → re-exports the same app
  decorators.py           login_required / role_required / require_verified_email
  celery_worker.py        Celery app + process_video_task + auto_organize_task
  blueprints/
    auth.py    (17 routes)  register, login, OAuth, invites, profile, password
    admin.py   (10 routes)  overview, users, jobs, assignments   [url_prefix=/admin]
    media.py   (16 routes)  upload, organize, download, thumbnails
    review.py   (9 routes)  search, clip updates, review requests
services/                 Business logic — 11 modules, no Flask imports in most
database/                 Mongo schema helpers + ingest
pipeline/                 classifiers/ processing/ training/
utils/                    logger, exceptions, frame/segment helpers
```

**53 HTTP routes total** (52 blueprint + `/health`).

### 2.3 Authentication model

Custom, token-based — no JWT, no Flask session:

1. `POST /login` → `secrets.token_hex(32)` written to the user's **`users.token` field**.
2. SPA stores it in `localStorage`; an Axios interceptor attaches `Authorization: Bearer <t>`.
3. `login_required` looks the token up in Mongo on every request and populates `g.user`.

Consequences of the one-token-per-user design (see finding **A3**):
- **No expiry.** A token is valid forever until an explicit logout or password change.
- **Single session.** Logging in on a second device silently invalidates the first.
- **Stored in plaintext** — a DB read exposes live sessions. (Contrast: reset, verification,
  and invite tokens are all correctly stored as SHA-256 hashes. Only session tokens are not.)

Roles are `admin`, `reviewer`, `editor`. Self-serve signup is always `editor`; elevation happens
only through an admin invite or an admin role change, and the last active admin cannot be
demoted or deactivated — that guard is properly implemented.

### 2.4 Frontend

`App.jsx` is the whole router. All 14 views are `React.lazy` code-split behind a `Suspense`
fallback, and `vite.config.js` splits vendor chunks manually. Auth state lives in `App.jsx`
(`token` + `currentUser`) and flows down via props — **no Redux/Zustand/Context for auth**; the
only Context is `UploadContext` for in-flight upload progress.

Two guard components wrap protected routes:
- `RoleGuard` — redirects to `/app/dashboard` if the role isn't allowed.
- `VerifiedGuard` — redirects to `/login` if `email_verified` is false.

Styling is plain CSS with a design-token layer in `index.css` (GitHub-Dark base `#0d1117`,
accent `#58a6ff`). No CSS framework, no CSS-in-JS — though several components use large inline
`style={{...}}` objects instead of the token classes.

### 2.5 Pipeline

`upload → Celery → process_video() → scene_indexes/*.json + Mongo upsert`

Per scene: thumbnail extract → adaptive emotion sampling (2–12 frames, scaled to scene length,
edges weighted 1.5×) → Haar face detection → ML classification. Then the **agentic decision
layer**:

| ML confidence | Action |
|---|---|
| ≥ 0.85 | auto-accept, `reviewed=True` |
| 0.58 – 0.85 | weighted fusion with rule-based (ML 0.65 / rule 0.35) |
| < 0.58 fused | `uncertain=True` → escalate to reviewer queue |

There's also a face gate that blocks an `audience_reaction` label unless ≥3 faces are visible —
a nice guard against a confident-but-wrong ML prediction.

---

## 3. Feature map

| Route | View | Access |
|---|---|---|
| `/` | Landing (GSAP marketing page) | public |
| `/login`, `/register` | Auth + Google OAuth | public |
| `/forgot-password`, `/reset-password/:token` | Password recovery | public |
| `/verify-email/:token` | Email verification | public |
| `/invite/:token` | Accept team invite | authed |
| `/app/dashboard` | Stats, charts, activity | all roles, verified |
| `/app/review` | Inspector — clip grid, bulk edit, review requests | all roles |
| `/app/uploads` | Upload + live task progress | admin, editor |
| `/app/organized-videos` | Browse/filter/download organized output | admin, editor |
| `/app/settings` | Profile, password, sessions | all roles |
| `/app/admin/users` | User management | admin |
| `/app/admin/jobs` | Celery job monitor, retry/cancel | admin |

### Primary user flows

1. **Register → verify → upload → organize.** Register (editor) → verification email → upload
   in `/app/uploads` → `POST /auto_organize` → Celery → poll `GET /task_status/:id` → appears
   in `/app/organized-videos` under its dominant label.
2. **Review escalation.** Pipeline marks a clip `uncertain` → editor/reviewer opens
   `/app/review` → requests admin or peer review with a reason → admin resolves/dismisses or
   assigns → requester sees the resolution and acknowledges it. Every step appends to
   `audit_trail` and `review_history` on the clip document.
3. **Team growth.** Admin invites by email with a role → invitee registers/signs in → accepting
   the invite sets the role and implicitly verifies the email.

---

## 4. Running it locally

### Fast path — tests only (no MongoDB, Redis, or credentials)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows;  source .venv/bin/activate elsewhere
pip install -r Requirements.txt
pytest
```

Expect `68 passed, 3 skipped`. The 3 skips are intentional (2 need an unshipped labelled
dataset, 1 covers a removed endpoint). Tests use `mongomock`; email and Cloudinary are stubbed.

### Full app

Prerequisites: Python 3.9+, Node 18+, MongoDB, Redis, ffmpeg.

```bash
pip install -r Requirements.txt
cd frontend && npm install && cd ..
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Then three terminals:

```bash
python -m api.api_server                                                    # :5000
cd frontend && npm run dev                                                  # :5173
python -m celery -A api.celery_worker.celery_app worker --loglevel=info --pool=solo
```

Only `MONGO_URI` is needed to boot the API. Cloudinary/email/Google are exercised lazily.

**Gotchas found during this audit:**
- `make health` reports ffmpeg as **failing** if you follow `SETUP.md` and set `FFMPEG_PATH=ffmpeg`
  — see finding **B1**.
- `config.py` ships a **hardcoded Windows ffmpeg path** as the default. Non-Windows users must
  set `FFMPEG_PATH` or the pipeline breaks.
- The Makefile's `.PHONY` line omits `run-frontend` and `run-celery`.

---

## 5. Findings

Severity: **High** = exploitable or data-corrupting · **Medium** = wrong behaviour users will hit
· **Low** = hygiene.

### 5.1 Security

#### S1 — Arbitrary file write via upload filename · **High**
`api/blueprints/media.py:98` and `:115`

```python
file_path = config.DATA_DIR / file.filename
file.save(str(file_path))
```

`file.filename` is attacker-controlled and **never sanitized**. I confirmed empirically that
Werkzeug 3.1.5 passes `../../evil.mp4` through verbatim, so `DATA_DIR / "../../evil.mp4"`
resolves outside the data directory and `save()` writes there. On this Windows checkout that
means writing to `D:\`. Overwriting a `.py` file on the import path turns this into code
execution under the API process.

Requires an authenticated, email-verified editor or admin — so it's privilege escalation rather
than an unauthenticated hole, but it should not be reachable at all.

**Fix:** `werkzeug.utils.secure_filename()`, then verify the resolved path is still inside
`DATA_DIR`:
```python
from werkzeug.utils import secure_filename
name = secure_filename(file.filename)
if not name:
    return jsonify({'error': 'Invalid filename'}), 400
dest = (config.DATA_DIR / name).resolve()
if not dest.is_relative_to(config.DATA_DIR.resolve()):
    return jsonify({'error': 'Invalid filename'}), 400
```
Also collision-suffix the name — two users uploading `interview.mp4` currently clobber each other.

#### S2 — No upload size or type limit · **High**
`MAX_CONTENT_LENGTH` is never set (grepped: zero occurrences), and neither upload endpoint checks
the extension or MIME type. Any authenticated editor can exhaust the API server's disk with a
single request, or upload a non-video that fails deep inside the Celery worker.

**Fix:** `app.config['MAX_CONTENT_LENGTH'] = 2 * 1024**3` plus an allowlist checked against
`VIDEO_EXTENSIONS` (already defined in `run_pipeline.py:29` — reuse it).

#### S3 — Unauthenticated media endpoints · **Medium**
`media.py:64` (`/thumbnail/<clip_id>`) and `:74` (`/video_clip/<clip_id>`) carry **no decorator
at all**. Anyone who knows or guesses a clip `ObjectId` gets the thumbnail or a redirect to the
video. ObjectIds embed a timestamp and a counter, so they're partially predictable.

This is load-bearing, not an oversight: `Inspector.jsx:261` renders thumbnails via a plain
`<img src>`, which cannot send an `Authorization` header. Note `/video_clip` is **not called by
the SPA at all** and can simply be deleted.

**Fix:** delete `/video_clip`; for `/thumbnail`, issue short-lived signed URLs, or serve the
Cloudinary URL directly from the already-authenticated `/search` payload.

#### S4 — Wide-open CORS · **Medium**
`api_server.py:19` is a bare `CORS(app)` — every origin, every route. Combined with
`localStorage` token storage, any XSS on any origin the user visits can read the token and call
the API. **Fix:** `CORS(app, origins=[config.APP_BASE_URL], supports_credentials=True)`.

#### S5 — Debug mode defaults to on · **Medium**
`config.py:27` — `API_DEBUG = os.getenv("API_DEBUG", "True")`. A deploy that forgets to set the
variable gets the Werkzeug debugger and its interactive console. **Default should be `False`.**

#### S6 — No rate limiting on login · **Medium**
`POST /login` has no throttle, lockout, or backoff. Password reset (3/hour), verification
(3/hour), and password OTP (3/hour) are all correctly rate-limited — login is the gap.
`reset_token_service.py` already notes Flask-Limiter as the intended production answer.

#### S7 — `/open_folder` runs `os.startfile` on a client-supplied path · **Low**
`media.py:136`. Admin-only and existence-checked, but it opens an arbitrary server-side path in
Explorer — a desktop-era affordance in a client-server app. The SPA calls it, but it can only
ever act on the machine running the API. Note `services/export_service.py:130` has a safer
`open_local_folder()` that is never used. **Recommend deleting the endpoint.**

#### S8 — Unused endpoints widening the attack surface · **Low**
`/upload`, `/export`, `/export_batch`, `/update_scene`, `/video_clip` are **never called by the
SPA** (verified by grep). They remain live and authenticated. `/export` and `/export_batch` are
also unscoped — see **A4**.

**Good news:** `.env` is correctly gitignored and **not tracked** (only `.env.example` is).
Password hashing uses `werkzeug.security`. Reset/verification/invite tokens are SHA-256 hashed,
one-time-use, and expiring. Login returns a single non-enumerating error, and `/forgot-password`
always returns 200. Mongo `$regex` searches are `re.escape`d in `organized_video_service.py:33`.
This is careful work — the gaps above are the exceptions, not the pattern.

### 5.2 Authorization consistency

#### A1 — Admins see their own uploads only, but stats count everyone's · **High**
`media.py:164-191`. `list_organized_videos` passes `uploader=user_id` **unconditionally** and
hardcodes `is_admin=False`:

```python
user_id = g.user.get('id')
result = svc_list(..., uploader=user_id, requester_id=user_id, is_admin=False, ...)
```

But the docstring on the very next line says *"Admins see all."* And `/organized-videos/stats`
directly above it (`:158`) does the opposite — `None if role == 'admin' else id`, so admins get
unscoped counts.

**User-visible symptom:** an admin's dashboard reads "42 organized videos" while the list below
shows only the 3 they personally uploaded. `is_admin=False` also forces `can_delete: false` on
every row, so the admin's delete buttons disappear.

#### A2 — Admin ownership checks with no admin bypass · **High**
Three endpoints 404 for admins on other users' records:
- `media.py:203` — `GET /organized-videos/<id>`
- `media.py:263` — `POST /organized-videos/download`
- `media.py:222` — `DELETE /organized-videos` (hardcoded `is_admin=False`)

All three use a bare `doc.get('uploaded_by') != g.user.get('id')`. Meanwhile
`/organized-videos/download-batch` (`:300`) and `/download-category` (`:353`) **do** have the
bypass (`if g.user.get('role') != 'admin'`). So an admin can batch-download ten videos they
don't own but gets a 404 downloading any one of them individually.

`organized_video_service.delete_organized_videos` even documents "Admins can delete any organized
video record" — the service supports it; the blueprint never passes `is_admin=True`.

**Fix:** compute `is_admin = g.user.get('role') == 'admin'` once and thread it through all five
endpoints consistently. This is one small change that resolves A1 and A2 together.

#### A3 — Session tokens never expire · **Medium**
Discussed in §2.3. A stolen token from `localStorage` is valid indefinitely. Add an
`expires_at`, or move to short-lived JWTs with a refresh token, and store a token *hash* rather
than the token — the codebase already does exactly this for every other token type.

#### A4 — `/export` and `/export_batch` are not ownership-scoped · **Medium**
`export_service.py:27` and `:68` filter only on `video`/`scene_label`/`emotion` — never on the
caller. Any editor can export any other user's clips and receive their Cloudinary URLs. Currently
unreachable from the SPA (**S8**), which caps real-world impact, but the endpoints are live.

### 5.3 Correctness bugs

#### B1 — `check_ffmpeg` fails when ffmpeg is on PATH · **Medium**
`api/health_check.py:64` — `os.path.exists(config.FFMPEG_PATH)`. `SETUP.md` explicitly tells
users to set `FFMPEG_PATH=ffmpeg`, for which `os.path.exists("ffmpeg")` is `False`. `make health`
then reports ffmpeg broken and exits 1 on a perfectly working install.
**Fix:** fall back to `shutil.which(config.FFMPEG_PATH)` when the literal path doesn't exist.

#### B2 — Pipeline reads config twice, from two sources · **Medium**
`run_pipeline.py:34-36` re-reads `CONF_AUTO_HIGH`, `CONF_FUSE_LOW`, and `ML_WEIGHT` via
`os.getenv` even though `config.py:66-70` already defines all three. They agree today only
because both read the same env vars with the same defaults. Anyone who changes a default in
`config.py` will silently not change pipeline behaviour. **Fix:** import from `config`.

#### B3 — `ffprobe` invoked bare, ignoring `FFMPEG_PATH` · **Medium**
`celery_worker.py:66` hardcodes `'ffprobe'`. The whole call is wrapped in
`except Exception: return False`, so on a machine where ffmpeg lives at a custom path — which is
this project's *documented default* — edited-video metadata detection silently always returns
`False`, and no one finds out. **Fix:** derive the ffprobe path from `config.FFMPEG_PATH`.

#### B4 — Whole video file read into memory for hashing · **Medium**
`celery_worker.py:228` — `hashlib.sha256(fh.read()).hexdigest()`. A 4 GB upload becomes a 4 GB
resident allocation in the worker. **Fix:** chunked read (`for chunk in iter(lambda: fh.read(1<<20), b'')`).

#### B5 — `validate_batch_request` miscounts duplicate IDs · **Low**
`organized_video_service.py:347` compares `count_documents(...)` against `len(ids)`. Passing the
same ID twice yields `found=1, len=2` → "One or more video IDs were not found." **Fix:** dedupe
`ids` first.

#### B6 — `_reconcile_completed_review_requests` writes on a GET · **Low**
`clip_service.py:378` — `GET /search` triggers `update_many` calls that rewrite review status.
A read endpoint mutating data makes `/search` non-idempotent, unsafe to retry, and racy under
concurrent reviewers. **Fix:** move reconciliation into the write paths that create the
inconsistency, or into a periodic Celery beat task.

#### B7 — `datetime.utcnow()` is deprecated · **Low**
~40 call sites across services. Deprecated in Python 3.12 and slated for removal; emits
`DeprecationWarning` on the project's own documented test platform.
**Fix:** `datetime.now(datetime.UTC)`. Note all timestamps are stored as **ISO strings** and
compared lexically (e.g. `invitation_service.py:83`) — correct for UTC ISO-8601, but fragile if
a tz-aware value ever enters the mix, since `"...+00:00"` breaks the ordering assumption.

### 5.4 Performance

#### P1 — `MongoClient` constructed per call · **High impact, trivial fix**
`reset_token_service.py:29` and `:43`, and `organized_video_service.py:381` build a **new
`MongoClient` on every invocation**. Each one spins up its own connection pool and monitor
threads that are never closed. Under load this exhausts connections. Every other module in the
codebase correctly caches a module-level `_client` singleton — these three are the outliers.

#### P2 — Haar cascade reloaded from disk per frame · **High impact**
`run_pipeline.py:50` constructs `cv2.CascadeClassifier(...)` **inside `has_face()`**, which runs
once per emotion sample — up to 12 times per scene, times every scene in the video. The XML is
re-parsed from disk each time. **Fix:** hoist to a module-level constant. This is likely the
single biggest pipeline speedup available.

#### P3 — N+1 queries in processing logs · **Medium**
`organized_video_service.py:415` runs one `tasks_col.find_one` per log row (30 rows/page → 31
round trips). **Fix:** collect `batch_id`s and issue one `$in` query.

#### P4 — Up to 200 regexes in a single `$or` · **Medium**
`organized_video_service.py:53-61` builds one regex condition per accessible video name, capped
at 200, and ORs them together. None can use an index. This runs on **every** organized-video
list and stats call for non-admins. **Fix:** store a normalized `safe_name` on the scene
documents and query it with a single indexed `$in`.

#### P5 — `_get_dominant_scene_type` re-queries per document · **Medium**
`export_service.py:98` calls it inside the `export_batch` loop; each call is a full
`col.find({"video": ...})`. **Fix:** memoize per video name.

#### P6 — Frontend polls task status per file · **Low**
`Upload.jsx` / `UploadContext.jsx` poll `GET /task_status/:id` per in-flight upload. Fine at
current scale; a batched status endpoint or SSE would scale better.

### 5.5 Code quality

#### Q1 — 619 lines of dead frontend code
`EditorView.jsx` (283 lines) and `VideoAssignments.jsx` (336 lines) are **imported by nothing**
(verified by grep). `VideoAssignments` appears to be the UI for `/admin/assignments`, which the
API still serves. Either wire it into the router or delete both.

#### Q2 — 27 ESLint errors, 9 warnings
Notable ones:
- `App.jsx:40` — `handleLogout` used in a `useEffect` before its `const` declaration. Works only
  because the effect runs after the render body completes; it's a TDZ hazard one refactor away
  from a crash.
- `ErrorBoundary.jsx:20,93` — `process is not defined`. **Not a runtime bug** — I confirmed Vite
  statically replaces `process.env.NODE_ENV` and no reference survives into `dist/`. Still worth
  switching to `import.meta.env.DEV` for correctness.
- `vite.config.js:17,18` — `__dirname` undefined under the ESM config; needs an eslint env fix.
- Several `react-hooks/set-state-in-effect` errors (`Dashboard.jsx:117`, `VerifyEmail.jsx:15`).

#### Q3 — Hardcoded API base URL · blocks any deploy
`frontend/src/config.js` is one line: `export const API_BASE = "http://127.0.0.1:5000";`

There is no env-var fallback, so **a production build can only ever talk to localhost**. Every
other frontend config value uses `import.meta.env`. **Fix:**
`export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";`

#### Q4 — Inconsistent import placement
Blueprints mix top-level imports with function-local ones (`from flask import g` appears inside
~10 handlers in `media.py` despite `g` already being imported at line 4). Harmless, but it
obscures the real dependency graph.

#### Q5 — Test coverage gaps
7 test files cover auth, API surface, the rule system, and an end-to-end pipeline path. Not
covered: the authorization-scoping logic in `clip_service._apply_review_scope` /
`_can_review_doc` (the most security-sensitive code in the project), the media blueprint's
ownership checks, and the Cloudinary service. A regression test on scoping would have caught
**A1** and **A2**.

#### Q6 — Stale packaging metadata
`pyproject.toml:10-11` still reads `Your Name` / `your.email@example.com`.

---

## 6. Recommended roadmap

### Phase 1 — Security & correctness (do first)

1. **S1** Sanitize upload filenames + confine to `DATA_DIR`.
2. **S2** Set `MAX_CONTENT_LENGTH` and an extension allowlist.
3. **A1 + A2** Thread a real `is_admin` through all organized-video endpoints. *One change,
   fixes the most user-visible bugs in the app.*
4. **S5** Default `API_DEBUG` to `False`.
5. **S4** Restrict CORS to `APP_BASE_URL`.
6. **S8** Delete unused endpoints (`/video_clip`, `/export`, `/export_batch`, `/open_folder`)
   — removes **A4** and **S7** for free.
7. **Q3** Make `API_BASE` env-driven.

### Phase 2 — Reliability

8. **P1** Cache the three stray `MongoClient` instances.
9. **P2** Hoist the Haar cascade to module level.
10. **B1** Fix `check_ffmpeg` to honour a PATH-based ffmpeg.
11. **B3** Route `ffprobe` through `FFMPEG_PATH`; **B4** chunk the file hash.
12. **S6** Add Flask-Limiter to `/login`.
13. **Q5** Add authorization-scoping tests for `clip_service` and the media blueprint.

### Phase 3 — Hardening & scale

14. **A3** Token expiry + hashed storage (multi-session support falls out of this).
15. **P3, P4, P5** Fix the N+1s and the 200-regex `$or`.
16. **B6** Move review reconciliation out of `GET /search`.
17. **B2** Single-source the pipeline confidence thresholds from `config.py`.
18. **B7** Migrate off `datetime.utcnow()`.

### Phase 4 — Cleanup & polish

19. **Q1** Delete or wire up `EditorView` / `VideoAssignments`.
20. **Q2** Clear the ESLint errors; add lint to CI.
21. **Q6** Fix `pyproject.toml` metadata; add `run-frontend`/`run-celery` to `.PHONY`.
22. Add CI running `pytest` + `npm run lint` on every push.
23. Consider structured logging + an error reporting hook (the `ErrorBoundary` has a TODO for it).

---

## 7. What's genuinely good

Worth stating plainly, because it's the context for everything above:

- **Layering is consistent.** Blueprints stay thin; services hold the logic; the database layer
  is isolated. Very few projects this size hold that line.
- **Token hygiene is well above average** for reset, verification, and invite flows — hashed,
  expiring, one-time-use, rate-limited, with non-enumerating error messages.
- **The tests run green with zero external setup.** The `conftest.py` `mongomock` patching —
  including resetting lazy `_client` singletons — is genuinely thoughtful.
- **The pipeline's fallback chain is well-designed.** ML → rule-based → escalate-to-human, with
  an explicit face gate to stop confident-but-wrong predictions. The confidence bands are
  documented and tunable.
- **The audit trail is real.** Every clip mutation appends actor, old/new values, and timestamps
  to `audit_trail` and `review_history` — the accountability story is stronger than the
  authorization story.
- **`.env` is correctly gitignored and untracked**, and the `.gitignore` is unusually thorough.
