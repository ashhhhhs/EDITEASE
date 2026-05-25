# EditEase Final Defense Prep - May 31

Generated on May 25, 2026.

## 1. Your One-Minute Project Story

EditEase is an AI-assisted video indexing and organising platform for post-production teams. The problem is that raw footage is usually reviewed manually: editors scrub through long videos just to find interviews, audience reactions, B-roll, or establishing shots. EditEase automates the first logging step.

The system accepts a raw video, detects scene boundaries, extracts representative thumbnails, classifies each scene using a fine-tuned ResNet-18 model with rule-based fallback, samples emotions only when faces are detected, stores scene metadata in MongoDB, and exposes the result through a React review workspace. The important design decision is that the AI is assistive, not fully autonomous: uncertain predictions are flagged for human review.

## 2. The System From Inside Out

Core flow:

1. User uploads a video from the React frontend.
2. Flask API receives the file and dispatches a Celery background task.
3. Celery runs the processing pipeline so the HTTP request does not timeout.
4. The pipeline uploads the video to Cloudinary as a backup/source asset.
5. PySceneDetect detects hard cuts and gradual transitions.
6. OpenCV extracts a midpoint thumbnail per scene.
7. Emotion sampling checks multiple timestamps, uses Haar Cascade for face detection, and only calls DeepFace if a face is present.
8. ResNet-18 predicts one of five merged labels: `b-roll`, `testimonial`, `other`, `audience_reaction`, `establishing_shot`.
9. The rule-based classifier extracts visual/motion features and acts as fallback or fusion partner.
10. The agentic decision layer auto-accepts high-confidence scenes and escalates uncertain scenes.
11. MongoDB stores scene-level metadata.
12. React shows dashboards, review queue, organized videos, exports, admin controls, and job progress.

Key code map:

- Backend app factory: `api/api_server.py`
- Auth routes: `api/blueprints/auth.py`
- Upload, task, export, organized video routes: `api/blueprints/media.py`
- Review/search routes: `api/blueprints/review.py`
- Main pipeline: `pipeline/processing/run_pipeline.py`
- Scene detection: `pipeline/processing/detect_scenes.py`
- Rule classifier: `pipeline/processing/scene_type_detect.py`
- ML classifier: `pipeline/classifiers/ml_classifier.py`
- Background tasks: `api/celery_worker.py`
- Frontend routing: `frontend/src/App.jsx`
- Upload UI: `frontend/src/Upload.jsx`
- Review UI: `frontend/src/Inspector.jsx`
- Organized videos UI: `frontend/src/OrganizedVideos.jsx`

## 3. Metrics You Should Say Carefully

Use this exact framing:

"The headline held-out v2 test result is 92.5% scene-level accuracy, macro F1 of 0.919, and weighted F1 of 0.922 on 40 evaluable test scenes from 42 test videos. I treat that as encouraging prototype evidence, not production proof, because the split is small and class-imbalanced."

If asked why other artifacts show different numbers:

"Different artifacts evaluate different scopes. The held-out split report evaluates 40 evaluable test scenes and is the one used in the final report. The real/full evaluation artifact covers a broader local manifest and reports 84.75% overall accuracy across 282 evaluated scenes. An older/alternate evaluation artifact reports lower results because it used a different split/evaluation setup. The correct defense answer is not to hide that variation, but to explain that model performance depends on dataset composition, and that is why the system keeps a human review workflow."

Strongest class story:

- Good: `testimonial`, `audience_reaction`, `other`, and most `b-roll`.
- Weakest boundary: `b-roll` vs `establishing_shot`.
- Reason: both can be wide, natural, face-free footage; the semantic boundary is fuzzy.

## 4. Supervisor Push Areas

Expect questions in these areas:

1. Why is this AI, not just file management?
Answer: The system performs automated scene boundary detection, visual classification using a fine-tuned CNN, emotion inference, confidence scoring, and automated organization. The file management UI is the delivery layer for AI-generated metadata.

2. Why ResNet-18?
Answer: It is lightweight, well understood, works well with transfer learning, and is realistic for an individual prototype. A larger video model would need more labelled data and compute.

3. Why classify from a thumbnail instead of the full video segment?
Answer: It reduces compute cost and makes the prototype feasible. The limitation is that temporal information can be missed, so future work should use multi-frame or video-level models such as 3D CNNs or Video Transformers.

4. Why combine ML with rules?
Answer: The ML model learns visual patterns, while the rules provide transparent fallback when confidence is low. This improves trust and gives a clear path for handling uncertainty.

5. What is the agentic part?
Answer: The system does not only predict labels; it acts on them by auto-organizing videos into categories, storing metadata, preparing exports, and deciding whether to auto-accept or escalate cases based on confidence.

6. What are the limitations?
Answer: Small and imbalanced dataset, single-frame classification, emotion detection depends on visible faces and lighting, local/single-server processing, and prototype-scale evaluation.

7. What ethical concerns exist?
Answer: Emotion recognition can be sensitive and unreliable. EditEase treats emotion as assistive metadata, only runs emotion detection when faces are detected, and allows human correction.

8. How do you prevent wrong AI outputs from harming workflow?
Answer: Confidence thresholds, rule fallback, uncertainty flags, review status, manual override, and reviewer notes.

9. Why MongoDB?
Answer: Scene metadata is semi-structured. Some scenes have emotion timelines and face data, others do not. MongoDB stores that flexible document structure naturally.

10. Why Celery?
Answer: Video processing is slow. Celery keeps the API responsive and lets the frontend poll task progress instead of waiting for a long synchronous request.

11. What would you improve next?
Answer: More labelled data, active learning from reviewed corrections, video-level classification, scalable cloud workers, better emotion safeguards, and richer collaboration.

## 5. Demo Script

Keep the demo simple and rehearsed:

1. Open landing page: explain problem and target users.
2. Login as verified editor/admin.
3. Show dashboard: analytics and system state.
4. Upload or use existing processed video: explain Celery background task and live progress.
5. Open review queue: show thumbnail, label, confidence, emotion timeline, reviewed/uncertain status.
6. Correct a label or add a note: show human-in-the-loop.
7. Open organized videos: show categories, search/filter, and download/export.
8. If admin account is available, show user management/job monitor briefly.
9. End with limitations and future work before they ask.

Do not let the demo depend on a huge fresh upload unless you have tested timing. Keep at least one already-processed video ready.

## 6. Six-Day Prep Plan

May 25:

- Read this file once.
- Make a 10-slide defense deck skeleton.
- Memorize the one-minute project story.
- Prepare one reliable demo dataset/video.

May 26:

- Study architecture: Flask, Celery, MongoDB, Cloudinary, React.
- Be able to draw the pipeline from memory.
- Practice explaining why each technology was chosen.

May 27:

- Study AI details: ResNet-18, label merge, confidence thresholds, rule fallback, agentic layer.
- Practice explaining the metric differences honestly.
- Prepare answers for dataset size and class imbalance.

May 28:

- Study testing and evaluation.
- Know functional testing, ML evaluation, usability evaluation, and limitations.
- Run the app and rehearse the demo once.

May 29:

- Full mock defense: 8-10 minute presentation plus 10 minute Q&A.
- Record yourself once if possible.
- Fix weak explanations, not just slides.

May 30:

- Final demo rehearsal.
- Prepare backup screenshots/video in case live services fail.
- Do not make risky project changes unless absolutely necessary.

May 31:

- Only light review.
- Open the app early, verify login/demo data, keep terminal commands ready.
- During Q&A, answer directly first, then explain.

## 7. Current Readiness Checks

Verified on May 25:

- Python full test suite: `44 passed`.
- Focused AI/pipeline tests: `14 passed`.
- Frontend production build: passed with Vite.
- Frontend warning: Node.js is `20.14.0`; Vite recommends `20.19+` or `22.12+`. Since the build works, avoid changing Node immediately before defense unless needed.

Test commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
```

## 8. Questions To Practice Out Loud

1. What exact problem does EditEase solve?
2. What makes your solution different from manual folder organization?
3. Why did you choose these five scene classes?
4. What happens when the model is wrong?
5. How does the system decide whether to auto-accept or escalate?
6. Why is the test set small, and how does that affect confidence?
7. What is the difference between scene detection and scene classification?
8. Why is emotion detection optional and face-gated?
9. How does user isolation work?
10. What would break first if 100 users uploaded large videos at once?
11. What part of the project are you most proud of?
12. What would you do differently if you had another semester?

## 9. Best Closing Statement

"The main contribution of EditEase is not claiming that AI can fully replace editorial judgement. It shows that AI can remove the first layer of repetitive footage logging by producing searchable scene metadata, while keeping humans in control for uncertain or important decisions."
