"""Batch B condensation: Chapters 5-8, Conclusion, Chapter 9 + Testing tables."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rewrite_engine import para, lead_para, heading, table, bullet, apply

R = {}

# ---------------- Chapter 5 (Design) ----------------
R["System Architecture and Artefact Design"] = [para(
 "This chapter presents the design of the artefact: the AI approach, the layered architecture, the decomposition "
 "into subsystems, the database schema, the API and the user interface.")]

R["5.1 Introduction to the Design of the Artefact"] = [para(
 "The design separates concerns into clear layers and subsystems so that each can be developed and tested "
 "independently. The following sections describe the AI component first, then the architecture, subsystems, data "
 "model, API and interface.")]

R["5.2 AI Aspects of the System"] = [
 para("EditEase applies supervised machine learning within computer vision: the scene classifier learns to map a "
 "thumbnail image to one of five production categories from a dataset of human-verified labels. Supervised "
 "learning is justified because the output categories are known in advance and labelled data can be produced from "
 "reviewed scenes in the platform's own database."),
 para("The classifier is a ResNet-18 CNN (He et al., 2016) pre-trained on ImageNet. Its residual connections ease "
 "gradient flow in deep networks, and its ~11M parameters suit fine-tuning on a modest dataset. The 512-dimensional "
 "feature vector feeds a small projection head — Linear(512→256) → LayerNorm → ReLU → Dropout(0.3) → Linear(256→5) "
 "— and a softmax converts the logits into a class probability distribution, P(y=k|x) = e^{z_k} / Σ e^{z_j}. "
 "Training minimises class-weighted cross-entropy."),
 para("The system behaves as a partially intelligent agent: its percepts are video frames and thumbnails; its "
 "actions are classification, emotion inference, confidence-based escalation and database writes; its goal is an "
 "accurate, searchable index with minimal review burden. Crucially, the agent monitors its own uncertainty through "
 "the confidence score and escalates doubtful scenes to a human rather than committing low-confidence labels.")]

R["5.3 System Architecture Overview"] = [para(
 "The architecture has five tiers: an input layer (React upload and authentication); a processing layer (Celery "
 "worker running scene detection, classification and emotion analysis); a storage layer (MongoDB for metadata, "
 "Cloudinary for binary assets); a backend layer (Flask REST API with Blueprints and Swagger); and a presentation "
 "layer (the React single-page application). Figure 5.1 shows these tiers and the components within each.")]

R["5.4 Subsystem Decomposition"] = [
 para("The platform decomposes into the following functional subsystems, shown in the functional decomposition "
 "diagram (Figure 5.2) and related design diagrams:"),
 bullet("Video capture and processing — accepts and validates input video."),
 bullet("Scene detection — identifies boundaries with content-based detection."),
 bullet("Thumbnail extraction — extracts a representative midpoint frame."),
 bullet("ML classification — classifies each scene with the fine-tuned ResNet-18."),
 bullet("Emotion detection — temporal facial emotion sampling where faces are present."),
 bullet("Agentic decision — fuses ML and rule-based outputs to set the final label."),
 bullet("Metadata, database, API and user-interface subsystems — assemble, store, expose and present scene records."),
]

R["5.5 Video Input and Processing Subsystem"] = [para(
 "The input subsystem accepts .mp4, .mov, .avi and .mkv files. On receipt the Flask API saves the file with a "
 "sanitised name and computes a SHA-256 hash for deduplication: if an identical file already exists, a lightweight "
 "duplicate record is created instead of reprocessing. The file is then passed to the PySceneDetect stream "
 "processor for boundary detection.")]

R["5.6 Scene Detection Subsystem"] = [para(
 "Scene detection uses PySceneDetect with an ensemble of ContentDetector (a weighted HSV frame-difference score, "
 "threshold 27, for hard cuts) and AdaptiveDetector (for fades and dissolves). Each boundary becomes a timestamp, "
 "and consecutive boundaries define scene segments with start, end and duration. Scenes shorter than 0.5 s are "
 "merged as artefacts, and if no cuts are found the whole recording is treated as a single scene (Figure 5.3).")]

R["5.7 Thumbnail Extraction Subsystem"] = [para(
 "For each scene a representative frame is taken from the midpoint, which is less likely than the boundaries to "
 "contain transition artefacts. Extraction uses OpenCV's VideoCapture: the midpoint is converted to a frame index "
 "(frame_idx = int(timestamp × fps)) and seeked by index, which is more reliable than millisecond seeking on "
 "variable-frame-rate footage. Frames wider than 1280 px are downscaled to prevent the AI models from stalling on "
 "4K/8K source, and the resulting JPEG is uploaded to Cloudinary with its URL stored on the scene (Figure 5.4).")]

R["5.8 Metadata Generation Subsystem"] = [para(
 "The metadata subsystem assembles a structured document per scene. Core fields include scene_id, video_id, "
 "video_name, start_time, end_time, duration, scene_label, ml_confidence, review_status, reviewed, thumbnail_url, "
 "cloudinary_url, user_id, and optional emotion, emotion_timeline and reviewer_notes, as summarised in the table "
 "below.")]

R["5.9 Scene Classification Subsystem (ML)"] = [para(
 "The classification subsystem takes a thumbnail path, loads it as a normalised tensor, passes it through the "
 "fine-tuned ResNet-18 and applies softmax to produce a probability distribution over the five v2 categories — "
 "B-Roll, Testimonial, Other, Audience Reaction and Establishing Shot — returning the top-1 label and its "
 "confidence. Sparse legacy labels (presenter, screen_recording, text_slide) are merged into these classes during "
 "training and evaluation.")]

R["5.10 Emotion Detection Subsystem"] = [
 para("Emotion detection samples several frames per scene rather than relying on one. The sample count scales with "
 "duration (2 for very short scenes up to a cap of 12 for long ones) and the sample points are spread with "
 "np.linspace(0.1, 0.9, n) to avoid black frames at cut boundaries; the first and last samples carry 1.5× vote "
 "weight. Each sampled frame is first checked with OpenCV's Haar cascade; only if a face is present is the heavier "
 "DeepFace inference run (with enforce_detection=True)."),
 para("Before a dominant emotion is committed, a face-evidence gate requires at least MIN_EMOTION_FACE_HITS = 2 "
 "successful detections and a face ratio of at least MIN_EMOTION_FACE_RATIO = 0.40. When satisfied, the dominant "
 "emotion is the weighted majority vote and the full timeline is stored; otherwise the dominant emotion is left "
 "null while the per-sample timeline is preserved, preventing a single marginal detection from mislabelling a "
 "scene.")]

R["5.11 Database Design"] = [para(
 "Each scene is stored as a document in the scenes collection of the editease MongoDB database, with indexes on "
 "video_name, scene_label, emotion, review_status, duration and user_id for efficient queries. Separate "
 "collections track tasks (task_id, status, video_name, created_at, error_message), users (id, email, role, "
 "tour_completed_at) and organized_videos (user_id, category, scene_ids, cloudinary_folder). The schema and entity "
 "relationships are shown in Figures 5.5 and 5.5a.")]

R["5.12 Application Programming Interface (API)"] = [para(
 "The Flask API uses the application-factory pattern and Blueprints: auth (register, login, me), media (upload, "
 "thumbnail, task_status, auto_organize), review (search, update_scene, bulk update) and admin (user and job "
 "management). Uploads dispatch a Celery task and return a task_id; the frontend polls task_status for progress. "
 "Endpoints are documented with Swagger (Flasgger), and all data-access endpoints scope results by the requesting "
 "user.")]

R["5.13 User Interface Design"] = [
 para("The interface is a React single-page application built around a role-aware AppShell with a persistent "
 "sidebar, a top bar showing the current user, and a routed content area. Editors and administrators see different "
 "navigation, and a <RoleGuard> component blocks routes the current role may not view (Figure 5.6a)."),
 para("The core workspace is a clip grid of scene thumbnails, each card showing the label and confidence and a "
 "verification border that distinguishes human-reviewed clips from automatic ones. A filter rail narrows scenes by "
 "label, emotion, status and duration, and an Inspector panel presents the thumbnail, timestamps, confidence and "
 "an editable label with a notes field for review. A bento-grid dashboard (Recharts) summarises the library, a job "
 "monitor streams Celery progress, and an OrganizedVideos view groups clips by category with ZIP export.")]

R["5.14 Data Flow within the System"] = [para(
 "Data flows from upload, through asynchronous processing and metadata storage, to filtered retrieval in the "
 "dashboard, as shown in the data-flow diagram (Figure 5.7). The end-to-end interaction between the client, API, "
 "worker, pipeline, Cloudinary and MongoDB is detailed in the sequence diagram (Figure 6.1b).")]

R["5.15 Agentic Auto-Organize Workflow"] = [para(
 "After processing, a single user action triggers the auto-organize workflow: scenes are grouped by classified "
 "category and mirrored into Cloudinary folders keyed by {user_id}/{category}/, and a category-aware index is "
 "produced that the frontend renders as a navigable library with per-category ZIP downloads (Figure 5.8). This "
 "embodies the agentic principle that the system should not only label content but act on those labels to produce "
 "a more useful artefact.")]

R["5.16 Role-Aware Access and User Isolation"] = [para(
 "All queries are scoped by the requesting user's user_id, with administrators granted broader visibility for "
 "moderation. Role transitions are validated against an allow-list at the service layer, and the frontend "
 "<RoleGuard> short-circuits routes the current user may not access, providing defence in depth across client and "
 "server (Figures 5.9 and 5.10).")]

R["5.17 Summary of Artefact Design"] = [para(
 "The design delivers a layered, subsystem-based architecture in which an agentic ML pipeline produces "
 "human-reviewable scene metadata, stored in MongoDB and presented through a role-aware React interface.")]

# ---------------- Chapter 6 (Implementation) ----------------
R["6.1 Introduction to System Implementation"] = [para(
 "This chapter describes the most significant implementation decisions, focusing on the pipeline, the ML "
 "classifier, the agentic layer and the interface.")]

R["6.2 Implementation of the Video Processing Pipeline"] = [para(
 "The pipeline is orchestrated by process_video() in pipeline/processing/run_pipeline.py, invoked by the Celery "
 "worker with a local file path. It uploads the raw video to Cloudinary, calls detect_scenes() (PySceneDetect), "
 "and for each scene extracts a midpoint thumbnail, uploads it, runs the ML classifier, applies the agentic "
 "decision logic, optionally samples emotion, and writes the record to MongoDB via clip_service (Figures 6.1, "
 "6.1a, 6.1b). The classifier is imported in a guarded block: if torch is unavailable, the rule-based classifier "
 "is substituted behind the same classify() interface, so the pipeline degrades gracefully.")]

R["6.3 Implementation of the Machine Learning Classifier"] = [para(
 "The classifier is implemented as MLClassifier in pipeline/classifiers/ml_classifier.py. The constructor loads "
 "the v2 checkpoint (scene_classifier_v2.pth) and label encoder (label_encoder_v2.json), sets eval mode and builds "
 "the ImageNet normalisation transform (resize 224×224, normalise to ImageNet mean/std). The ResNet-18 head is "
 "replaced by Linear(512→256) → LayerNorm → ReLU → Dropout(0.3) → Linear(256→5); the intermediate bottleneck "
 "improves calibration and produces better-separated confidence scores than a single dense layer, which makes the "
 "downstream confidence bands more meaningful. classify() loads the thumbnail, applies the transform, runs the "
 "model and returns the softmax top-1 label and confidence.")]

R["6.4 Data Collection and Dataset Preparation"] = [para(
 "The training set was assembled from thumbnails processed by the platform and labelled through its review "
 "workflow, keeping only scenes marked reviewed. Sparse legacy labels were merged before training (presenter → "
 "testimonial; screen_recording and text_slide → other). The data was split at the video level (70/15/15) so no "
 "scene from a training video appears in test — 193 training, 41 validation and 42 test videos (315 annotated "
 "scenes), recorded in datasets/scene_type/v2_full/splits.json. The held-out test split contains 51 scenes, of "
 "which 40 were evaluable after excluding 11 with missing thumbnail frames.")]

R["6.5 Model Training and Optimisation"] = [para(
 "Training uses a partial-freeze transfer-learning strategy: ResNet layers 1–3 are frozen and only layer 4 and the "
 "new head are trained, protecting transferable ImageNet features while adapting the top of the network. The "
 "AdamW optimiser uses two learning-rate groups (body 1e-4, head 1e-3) with a CosineAnnealingLR schedule, up to 20 "
 "epochs with early stopping (patience 5). Class imbalance is addressed with a WeightedRandomSampler and "
 "class-weighted cross-entropy, and augmentation (random crop, horizontal flip, rotation, colour jitter, grayscale "
 "and random erasing) reduces overfitting on the modest dataset.")]

R["6.6 Agentic Decision Layer"] = [
 para("The agentic layer operates in two stages. First, inside the classifier, a per-class confidence threshold "
 "(audience_reaction 0.72; testimonial 0.65; b-roll and establishing_shot 0.60; default 0.62) gates the ML "
 "prediction; if confidence falls below the class threshold the rule-based classifier is used as a fallback."),
 para("Second, in run_pipeline.py, confidence bands decide the outcome (CONF_AUTO_HIGH = 0.85, CONF_FUSE_LOW = "
 "0.58, ML_WEIGHT = 0.65, RULE_WEIGHT = 0.35). At or above 0.85 the prediction is auto-accepted; if the classifier "
 "had already fallen back, the scene is flagged uncertain; otherwise the ML and rule-based outputs are fused by "
 "weighted scores, with an agreement boost when they concur and an uncertain flag when the fused confidence stays "
 "below 0.58. The rule-based classifier (scene_type_detect.py) uses Gaussian likelihood profiling over twelve "
 "normalised visual and motion features across four scene profiles, returning a softmax-calibrated label. This "
 "lets the system surface its own uncertainty for human review rather than silently committing weak labels.")]

R["6.7 Implementation of Emotion Detection"] = [para(
 "sample_emotions_over_scene() in run_pipeline.py samples frames across the scene (count scaling with duration), "
 "extracts each with OpenCV and applies the Haar cascade first; frames without a face are skipped before the "
 "expensive DeepFace call. When a face is found, DeepFace runs with enforce_detection=True so ambiguous frames are "
 "rejected. A scene-level face-evidence gate (MIN_EMOTION_FACE_HITS = 2, MIN_EMOTION_FACE_RATIO = 0.40) must hold "
 "before a weighted majority-vote dominant emotion is committed; otherwise it is left null while the timeline is "
 "still stored.")]

R["6.8 Database Implementation"] = [para(
 "Scene documents are written through clip_service.upsert_scene(), which uses MongoDB update_one with upsert=True "
 "keyed on scene_id, making reprocessing idempotent. Indexes are created programmatically at startup via "
 "database/ingest_indexes.py.")]

R["6.9 API Implementation"] = [para(
 "The API is built with the application-factory pattern (CORS, Flask-Mail, Swagger). The media Blueprint's upload "
 "endpoint validates the extension, saves the file and calls task_service.dispatch_process(), returning a task_id. "
 "The Celery task passes a progress_callback into process_video() that updates task state at each stage (upload, "
 "detection, per-scene analysis, classification, storage); the frontend polls /task_status/<id> and renders these "
 "messages as a live feed.")]

R["6.10 Implementation of the User Interface"] = [
 para("The frontend is a React SPA with client-side routing. AppShell.jsx provides the sidebar, top bar and routed "
 "content area, adapting navigation to the user's role. App.jsx declares the routes and wraps administrative ones "
 "in <RoleGuard>, which reads the current user from a useAuth() hook and redirects unauthorised roles before the "
 "protected component mounts, complementing the server-side scope checks."),
 para("The dashboard renders the clip grid and a Recharts analytics summary; the Inspector panel supports label "
 "correction and notes; the JobMonitor view streams processing progress; and OrganizedVideos presents the "
 "category library with ZIP export. A verification border visually marks reviewed clips, reinforcing the "
 "human-in-the-loop workflow.")]

R["6.11 Guided Tour Implementation (react-joyride)"] = [para(
 "A first-run guided tour built with react-joyride walks new users through the upload, review and organise flows. "
 "Completion is persisted (tour_completed_at on the user) so the tour does not repeat, and it can be restarted on "
 "demand.")]

R["6.12 Cinematic Landing Page and Motion System"] = [para(
 "The public landing page uses GSAP and Lenis for smooth scroll-driven animation that introduces the brand voice "
 "and core value proposition, with scroll-triggered reveals across hero, features and pipeline-storytelling "
 "sections (Figure 6.7).")]

R["6.13 Dashboard Analytics and Live Logs Implementation"] = [para(
 "The dashboard aggregates library statistics — scene counts by category, review status and emotion distribution "
 "— into Recharts visualisations, and a live log/job feed surfaces Celery progress so users have continuous "
 "feedback during processing.")]

R["6.14 User Isolation and ZIP Export Implementation"] = [para(
 "Every data query is filtered by user_id at the service layer so users see only their own scenes, with "
 "administrators granted oversight. Per-category ZIP export streams the organised clips for a category to the user "
 "on demand, built from the Cloudinary-backed category index.")]

# ---------------- Chapter 7 (Evaluation and Testing) ----------------
func_test_table = table(
 ["TC", "Requirement", "Test", "Expected", "Result"],
 [["T1", "F1", "Register and log in as editor.", "Role-aware dashboard loads.", "Pass"],
  ["T2", "F2", "Upload an MP4 file.", "Task accepted; task_id returned.", "Pass"],
  ["T3", "F3", "Process a multi-scene video.", "Scenes detected with thumbnails.", "Pass"],
  ["T4", "F4", "Inspect classified scenes.", "Each has a label and confidence.", "Pass"],
  ["T5", "F5", "Process ambiguous footage.", "Low-confidence scenes flagged uncertain.", "Pass"],
  ["T6", "F6", "Process footage with faces.", "Emotion recorded only for face scenes.", "Pass"],
  ["T7", "F7", "Filter by label/emotion/status.", "Clip grid updates correctly.", "Pass"],
  ["T8", "F8", "Correct a label in Inspector.", "Label updated; marked reviewed.", "Pass"],
  ["T9", "F9", "Run auto-organize; download ZIP.", "Category folders and ZIP produced.", "Pass"],
  ["T10", "F10", "Access admin views as editor.", "RoleGuard blocks and redirects.", "Pass"]],
 widths=[600, 900, 3200, 2700, 800])

api_test_table = table(
 ["Endpoint", "Method", "Check (Postman/pytest)", "Result"],
 [["/register, /login", "POST", "Auth succeeds; session/role returned.", "Pass"],
  ["/upload", "POST", "Valid file accepted; invalid rejected (400).", "Pass"],
  ["/task_status/<id>", "GET", "Returns PROGRESS then SUCCESS.", "Pass"],
  ["/search", "GET", "Filters return only the user's scenes.", "Pass"],
  ["/update_scene", "POST", "Label/notes persisted; review_status set.", "Pass"],
  ["/auto_organize", "POST", "Category index and folders created.", "Pass"],
  ["/admin/*", "GET", "Rejected for non-admin (403).", "Pass"]],
 widths=[2100, 900, 4400, 800])

R["7.1 Introduction to System Evaluation"] = [para(
 "The prototype was evaluated through functional testing against the requirements, quantitative evaluation of the "
 "ML classifier, and a usability assessment of the interface.")]

R["7.2 Functional Testing"] = [
 para("Functional testing checked each functional requirement from Chapter 3 through the interface, with backend "
 "behaviour verified using pytest and the API exercised with Postman. Table 7.1 summarises the functional test "
 "cases and Table 7.2 the API tests; all defined cases passed in the final build."),
 func_test_table,
 lead_para("Table 7.2 — API endpoint tests. ", "Endpoint behaviour was checked for success and failure paths, "
 "including authentication, validation and user-scoping."),
 api_test_table,
]

R["7.3 ML Model Evaluation"] = [
 para("The v2 classifier was evaluated on the held-out test split (42 videos; 40 evaluable scenes after excluding "
 "11 with missing thumbnail frames). It achieved 92.5% scene-level accuracy, a macro F1 of 0.919 and a weighted "
 "F1 of 0.922 across the five merged classes, with a balanced accuracy of 0.91 (eval_report_v2_test.json). "
 "Per-class results were strong for Testimonial, Other and Audience Reaction (F1 = 1.0 on small support) and for "
 "B-Roll (F1 = 0.93); the weakest was Establishing Shot (F1 = 0.67), where two of five examples were confused with "
 "B-Roll — the expected fuzzy boundary between wide B-roll and establishing shots."),
 para("These results are encouraging but rest on a small, imbalanced split (several classes have only four to six "
 "test examples), so they should be read as evidence of viability rather than a guarantee of production-scale "
 "performance. The confusion matrix and per-class metrics are shown in Figures 7.3–7.5, the training/validation "
 "curves in Figures 7.1–7.2, and the ROC curves in Figure 7.3a. The small test size is exactly why the "
 "human-in-the-loop review queue and agentic confidence thresholds are retained.")]

R["7.4 Usability Evaluation"] = [para(
 "Usability was assessed informally by walking through the core tasks — upload, monitor, browse, filter, review "
 "and organise — and checking the supporting features. The clip grid and thumbnails let users identify content "
 "without playing footage; the live progress feed addressed the uncertainty of minutes-long processing; the guided "
 "tour eased first use; and the verification border made review state obvious. These observations indicate the "
 "interface meets the usability requirements (UR1–UR4), though a formal study with external participants remains "
 "future work.")]

R["7.5 Performance Factors"] = [para(
 "Processing time is dominated by scene detection and per-scene inference and scales with video length and scene "
 "count; offloading work to Celery keeps the interface responsive, and skipping DeepFace on face-free frames "
 "avoids unnecessary computation. Downscaling large frames to 1280 px prevents stalls on 4K/8K source.")]

R["7.6 Limitations Discovered During Testing"] = [para(
 "Testing surfaced several limitations: a few test scenes had missing thumbnail frames and were excluded from "
 "evaluation; the small, imbalanced dataset limits achievable accuracy and makes per-class metrics sensitive to "
 "individual errors; and the B-Roll/Establishing-Shot boundary remains the main source of error. Emotion "
 "inference is also limited to scenes with detectable faces, by design.")]

# ---------------- Chapter 8 (Critical Assessment) ----------------
obj_table = table(
 ["Objective", "Status", "Evidence"],
 [["Scene-detection pipeline", "Achieved", "PySceneDetect ensemble with merge/zero-cut handling."],
  ["Thumbnail extraction", "Achieved", "Midpoint frame, frame-index seek, downscaling."],
  ["Structured metadata", "Achieved", "Scene documents with full field set in MongoDB."],
  ["Document database schema", "Achieved", "Indexed scenes/tasks/users/organized_videos."],
  ["REST API", "Achieved", "Flask Blueprints for search/update/review/export."],
  ["ML classifier", "Achieved", "ResNet-18 v2, 92.5% accuracy, 0.919 macro F1 (n=40)."],
  ["Agentic decision layer", "Achieved", "Two-stage threshold + weighted fusion with review flags."],
  ["Web interface", "Achieved", "React AppShell, clip grid, Inspector, dashboard."],
  ["Human-in-the-loop review", "Achieved", "Inspector edit/annotate; verification border."],
  ["Evaluation", "Achieved", "Functional tests, ML metrics, usability walkthrough."]],
 widths=[2600, 1200, 5400])

R["8.1 Introduction to the Critical Evaluation"] = [para(
 "This chapter assesses the project against its objectives, evaluates the design and AI component, and reflects on "
 "limitations, future work and the development experience.")]

R["8.2 Assessment of Project Objectives"] = [
 para("All ten objectives were met in the prototype, as summarised in Table 8.1. The most ambitious — the ML "
 "classifier — produced strong metrics on the held-out split, while the human-in-the-loop workflow guards against "
 "the limits of a small dataset."),
 obj_table,
]

R["8.3 Evaluation of System Design"] = [para(
 "The layered, subsystem-based design met its goals: separating processing, storage, API and presentation made "
 "the system testable and allowed the ML stack to be swapped for a rule-based fallback without affecting the rest "
 "of the pipeline. The asynchronous Celery design kept the interface responsive, and the document database "
 "accommodated the variable structure of scene metadata cleanly. The main design trade-off — classifying from a "
 "single midpoint thumbnail rather than full temporal content — favours efficiency and suits the prototype, but "
 "limits discrimination between visually similar categories.")]

R["8.4 Evaluation of the AI Component"] = [para(
 "The ML classifier achieved 92.5% accuracy and 0.919 macro F1 on the held-out test set, a clear improvement over "
 "the rule-based heuristic that was the original prototype's only classifier. The agentic layer adds robustness by "
 "fusing ML and rule-based outputs and surfacing uncertainty for review. However, the small, imbalanced dataset "
 "means the headline figures are evidence of viability rather than proof of production performance, and the "
 "remaining errors concentrate on the inherently fuzzy B-Roll/Establishing-Shot boundary. Classifying from a "
 "single frame and inferring emotion from facial cues alone are the principal model-level limitations.")]

R["8.5 Limitations of the System"] = [para(
 "Key limitations are the modest, imbalanced training set; single-frame classification; face-only emotion "
 "inference; a threshold-based rather than learned scene detector; and a single-user deployment model without "
 "real-time collaboration. None undermines the core concept, but each bounds the prototype's generality.")]

R["8.6 Future Improvements"] = [para(
 "Future work includes collecting a larger, more balanced dataset and adding active learning from reviewer "
 "corrections; multi-frame or short-clip classification for better temporal discrimination; a learned scene "
 "detector for gradual transitions; multimodal emotion analysis; and multi-user collaboration with cloud-native "
 "scaling.")]

R["8.7 Self-Reflection"] = [para(
 "The project developed my skills in computer vision, transfer learning and full-stack engineering, and in "
 "integrating these into a coherent system. The Agile, incremental approach was valuable: building and testing "
 "subsystems independently kept the work manageable and let ML findings reshape the design. The hardest lessons "
 "concerned data — assembling and labelling a quality dataset proved more demanding than model training, which "
 "reinforced why the human-in-the-loop workflow matters. With more time I would prioritise dataset size and a "
 "formal usability study. Overall the project met its aim and gave me practical experience of building a "
 "responsible, AI-assisted application end to end.")]

# ---------------- Conclusion ----------------
R["Conclusion"] = [para(
 "EditEase set out to determine to what extent an AI-assisted scene indexing and classification system can improve "
 "the efficiency and scalability of raw video management compared with file-based workflows. The completed "
 "prototype detects scenes, classifies them with a fine-tuned ResNet-18 reaching 92.5% accuracy and 0.919 macro "
 "F1 on a held-out split, infers emotion where faces are present, and exposes a searchable, filterable, "
 "human-reviewable library through a role-aware React interface, with an agentic layer that escalates uncertain "
 "cases and an auto-organize workflow that acts on the labels it produces. Together these let editors locate "
 "specific shots through thumbnails, labels and filters rather than linear scrubbing, supporting an affirmative "
 "answer to the research question within the prototype's scope. The main constraints — a small dataset and "
 "single-frame classification — define clear next steps, but the project establishes a viable foundation for "
 "AI-assisted footage management and demonstrates a responsible, human-in-the-loop design.")]

# ---------------- Chapter 9 (Project Management) ----------------
R["9.1 Project Planning"] = [para(
 "The project was planned around incremental sprints aligned to the development phases, with a backlog "
 "prioritised by dependency so foundational components were delivered first. Milestones and deliverables were "
 "tracked against the objectives throughout.")]
R["9.2 Development Timeline"] = [para(
 "Development proceeded from the core pipeline through metadata storage, the ML classifier, the API and the "
 "frontend, followed by the agentic and auto-organize features and evaluation. The timeline and major milestones "
 "are shown in the Gantt chart (Figure 9.1 / Appendix B).")]
R["9.3 Meetings and Tracking of Progress with Supervisors"] = [para(
 "Progress was reviewed in regular supervisor meetings, recorded in signed logsheets (Appendix A). These sessions "
 "guided priorities at the end of each sprint — for example focusing effort on the dataset and the agentic "
 "decision logic — and kept the work aligned with the assessment criteria.")]
R["9.4 Risk Management"] = [para(
 "Key risks were managed pragmatically: limited and imbalanced training data was mitigated by label merging, "
 "augmentation and the human-in-the-loop review queue; dependency on the ML stack was mitigated by the rule-based "
 "fallback; long processing times were mitigated by asynchronous Celery execution; and data loss risk was reduced "
 "by Cloudinary storage and idempotent, deduplicated processing.")]

if __name__ == "__main__":
    apply(R, [], strip_codex=True, dry=("--apply" not in sys.argv))
