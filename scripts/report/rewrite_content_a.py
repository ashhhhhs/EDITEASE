"""Batch A condensation: Chapters 1-4 + Agile reframing + Requirements (3.6/3.7)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rewrite_engine import para, lead_para, heading, table, bullet, apply

R = {}

# ---------------- Chapter 1 ----------------
R["1.1 Background of the Study"] = [para(
 "The volume of recorded video has grown rapidly across documentary, event, corporate and social-media "
 "production, where a single shoot can yield hours of raw footage. In conventional workflows this footage is "
 "stored in date- or camera-named folders that record nothing about its content, so an editor searching for a "
 "specific shot — an interview answer, an audience reaction, an establishing wide — must scrub linearly through "
 "entire recordings. Editing suites such as Adobe Premiere Pro and DaVinci Resolve provide markers and manual "
 "tagging, but they assume the editor has already watched the material and cannot describe a file that has never "
 "been opened. Advances in computer vision now make it possible to segment a video into scenes and attach "
 "descriptive metadata automatically, yet most tools apply these techniques in isolation and rarely connect them "
 "to a searchable, database-backed retrieval interface. EditEase closes that gap by combining automated scene "
 "detection, deep-learning classification and metadata-driven retrieval in a single platform that turns raw "
 "footage into a structured, searchable library.")]

R["1.2 Problem Statement"] = [para(
 "A single event, interview or documentary recording contains many distinct shot types — speaker segments, "
 "audience reactions, wide environment shots, cutaways and B-roll. Without automated indexing, locating a "
 "particular shot in a multi-hour archive depends on memory or repeated viewing. A raw file also carries no "
 "structured metadata: nothing records which segments contain faces, which are emotionally significant, how long "
 "each scene lasts, or what type of content it shows. Renaming files or sorting them into folders gives only "
 "coarse organisation and no way to query footage by type, emotion or duration, and existing commercial "
 "scene-detection tools are narrow and seldom integrate with a metadata database or retrieval interface. EditEase "
 "addresses this by processing raw video automatically, segmenting it into scenes, attaching structured metadata, "
 "and exposing the result through an interactive review interface.")]

R["1.3 Aim of the Project"] = [para(
 "The aim of this project is to design and implement an AI-assisted video indexing and retrieval platform that "
 "lets editors organise and access raw footage efficiently. The system automatically detects scene boundaries, "
 "associates each scene with descriptive metadata in a queryable database, and so transforms unstructured raw "
 "video into a structured, scene-level collection that can be searched and filtered rather than scrubbed.")]

R["1.4 Objectives of the Project"] = [
 para("The following objectives were defined to achieve this aim:"),
 bullet("Build a scene-detection pipeline that segments raw video using visual boundary detection."),
 bullet("Extract a representative thumbnail per scene for visual identification in the interface."),
 bullet("Generate structured per-scene metadata (timestamps, duration, label, emotion, thumbnail)."),
 bullet("Design a document-oriented (MongoDB) schema for storing and querying scene metadata."),
 bullet("Expose a REST API for searching, updating, reviewing and exporting scene records."),
 bullet("Implement an ML scene classifier via transfer learning on a pre-trained CNN, fine-tuned on a custom dataset."),
 bullet("Add an agentic decision layer that fuses ML and rule-based outputs and flags low-confidence scenes for review."),
 bullet("Build a web interface for browsing, filtering and reviewing indexed scenes."),
 bullet("Integrate a human-in-the-loop workflow for verifying and correcting automatic labels."),
 bullet("Evaluate the prototype through functional testing, ML performance metrics and usability assessment."),
]

R["1.5 Artefact Overview"] = [
 para("The artefact is the EditEase prototype, composed of several integrated components. A video-processing "
 "pipeline accepts raw video, detects scene boundaries and extracts a midpoint thumbnail per scene. A machine "
 "learning module classifies each thumbnail with a fine-tuned ResNet-18 model into five categories (B-roll, "
 "Testimonial, Other, Audience Reaction, Establishing Shot), merging sparse legacy labels during training. A "
 "temporal emotion module samples frames within a scene, detects faces with OpenCV's Haar cascade and infers "
 "emotion with DeepFace only when a face is present."),
 para("An agentic decision layer fuses the ML prediction with a rule-based classifier: high-confidence predictions "
 "are accepted automatically, low-confidence ones fall back to the rule-based result, and conflicting mid-confidence "
 "cases are flagged as uncertain for human review. Scene metadata is stored in MongoDB and served by a Flask REST "
 "API, with an asynchronous Celery/Redis queue running the heavy pipeline off the request path. A React interface "
 "provides a clip-grid workspace, filters, an Inspector review panel, a live job monitor and a guided tour. Finally, "
 "an auto-organize workflow groups labelled scenes into Cloudinary category folders ({user_id}/{category}/) with "
 "per-category ZIP export, and a role-aware access layer scopes all data by user with administrator oversight.")]

R["1.6 Academic Question"] = [para(
 "The research question is: to what extent can an AI-assisted scene indexing and classification system enhance "
 "the efficiency and scalability of raw video footage management compared with conventional file-based workflows? "
 "The project explores whether automated segmentation, ML-based classification and metadata-driven retrieval can "
 "meaningfully reduce the time and effort required to locate relevant segments in a raw archive.")]

R["1.7 Scope and Limitations"] = [
 para("EditEase is a research prototype demonstrating automated video scene indexing and retrieval. It targets "
 "professionally recorded footage of the kind found in documentary, event and interview production, rather than "
 "broadcast television, animation or extremely noisy material."),
 bullet("Emotion inference runs only when a face is detected; face-free scenes receive no emotion metadata."),
 bullet("The prototype is a single-user local or cloud-hosted application; real-time multi-user collaboration is future work."),
 bullet("The v2 classifier supports five merged categories; footage outside these may fall into “Other”."),
 bullet("The model is trained on a modest dataset collected from the platform, which bounds achievable accuracy."),
]

R["1.8 Structure of the Report"] = [para(
 "The remainder of the report is organised as follows. Chapter 2 reviews related work in scene detection, video "
 "classification, emotion recognition, retrieval and human-in-the-loop systems. Chapter 3 explains and justifies "
 "the Agile methodology and states the system requirements. Chapter 4 covers the technologies chosen. Chapter 5 "
 "presents the architecture and design; Chapter 6 the implementation. Chapter 7 reports functional testing, ML "
 "evaluation and usability findings. Chapter 8 critically assesses the project, and the Conclusion answers the "
 "academic question.")]

# ---------------- Chapter 2 (Literature Review) ----------------
R["2.1 Introduction to the Literature Review"] = [para(
 "This review examines the technical domains underpinning EditEase: scene boundary detection, video content "
 "classification, facial emotion recognition, metadata-based retrieval and human-in-the-loop systems. It is a "
 "focused survey of work that directly informs the design and evaluation decisions made in later chapters.")]

R["2.2 Multimedia Data and Video Content Analysis"] = [para(
 "Video differs from still imagery in carrying both spatial and temporal information, and is conventionally "
 "structured as frames grouped into shots and scenes. Reliable structural segmentation is therefore a prerequisite "
 "for attaching metadata to meaningful units. Mao et al. (2024) survey deep-learning video classification and show "
 "the field moving from hand-crafted features to learned representations, with CNNs handling spatial content and "
 "architectures such as 3D CNNs and transformers capturing temporal dynamics. They also note that practical value "
 "depends as much on how results are presented and searched as on raw accuracy — a principle central to EditEase.")]

R["2.3 Scene Detection and Video Segmentation"] = [para(
 "Classical scene detection measures visual dissimilarity between consecutive frames (histogram, edge-change or "
 "intensity differences) and marks a boundary when it exceeds a threshold; such methods are efficient and need no "
 "training data, suiting a prototype. Baraldi et al. (2015) show learned detectors can outperform threshold methods "
 "on complex material, especially for gradual transitions, at the cost of labelled data and compute. EditEase uses "
 "PySceneDetect with an ensemble of ContentDetector (HSV frame difference, threshold 27) for hard cuts and "
 "AdaptiveDetector for fades and dissolves, with a learned detector noted as future work.")]

R["2.4 Video Classification and Content Understanding"] = [para(
 "CNNs pre-trained on large datasets such as ImageNet (Deng et al., 2009) extract general visual features that "
 "transfer to new tasks through fine-tuning, enabling high accuracy from modest task-specific data. EditEase uses "
 "ResNet-18 (He et al., 2016), whose residual connections ease training of deep networks; at about 11 million "
 "parameters it balances capacity and efficiency for fine-tuning on a midpoint thumbnail per scene. Koorathota et "
 "al. (2021) show that hybrid systems combining learned representations with domain heuristics produce strong "
 "editing decisions on structured material — directly motivating the agentic layer that fuses the ML model with a "
 "rule-based classifier for low-confidence cases.")]

R["2.5 Video Summarisation"] = [para(
 "Video summarisation selects key frames or clips to convey a recording's main content as a condensed, passive "
 "highlight reel. EditEase instead performs video logging: it indexes all detected scenes and lets the user define "
 "relevance through search and filtering. This matters editorially because important shots — a brief testimonial, "
 "for example — may be visually unremarkable and would be omitted by a summariser but are preserved with metadata "
 "by an indexer.")]

R["2.6 Video-Based Emotion Recognition"] = [para(
 "Facial emotion recognition typically classifies expressions into Ekman's (1992) basic categories plus neutral, "
 "but accuracy varies with resolution, lighting and pose. Lian et al. (2023) and Pan et al. (2024) show multimodal "
 "approaches (combining facial, vocal, textual or physiological signals) substantially outperform facial-only "
 "methods. EditEase adopts a deliberately constrained approach: emotion is inferred with DeepFace only after a face "
 "is detected, so face-free frames receive no spurious label. The ICO (2024) guidance flags emotion inference as "
 "high-risk, so all emotion outputs are treated as assistive metadata subject to human review.")]

R["2.7 Multimedia Retrieval Systems and Metadata"] = [para(
 "Structured metadata is the foundation of retrieval: temporal, semantic and affective attributes stored in a "
 "queryable database allow targeted search rather than sequential browsing. Document databases such as MongoDB "
 "suit multimedia metadata because records can include or omit fields by content — a scene with a face carries "
 "emotion fields while one without does not — avoiding the null-filled columns a relational schema would require. "
 "EditEase indexes scene_label, video_name, review_status, emotion, duration and user_id for efficient queries as "
 "the collection grows.")]

R["2.8 Human-in-the-Loop Systems"] = [para(
 "Human-in-the-loop (HITL) systems integrate human judgement as a core part of the workflow rather than a fallback, "
 "which is valuable where automated predictions are unreliable or ethically sensitive. Corrections can also feed "
 "back into model retraining, an active-learning loop shown by Settles (2009) to improve accuracy with limited "
 "labelling. EditEase is explicitly HITL: the agentic layer accepts, escalates or flags each scene, and a reviewer "
 "can always inspect the thumbnail and metadata in the Inspector panel and override the label, so the system "
 "supports rather than replaces editorial judgement.")]

R["2.9 Literature Findings"] = [para(
 "The review establishes the foundations EditEase builds on: segmentation is a prerequisite for meaningful "
 "metadata; transfer learning from pre-trained CNNs gives high accuracy from limited data; combining ML and "
 "rule-based classification is more robust and transparent than either alone; emotion recognition should be applied "
 "cautiously and only with face evidence; document databases best support metadata retrieval; and a "
 "human-in-the-loop design is the appropriate framework where misclassification directly affects editorial "
 "decisions.")]

# ---------------- Chapter 3 (Methodology -> Agile/Scrum) ----------------
R["3.1 Introduction to the Methodology"] = [para(
 "EditEase integrates several distinct areas — video processing, machine learning, database design, API and "
 "frontend engineering — whose requirements could not be fully fixed in advance, particularly the ML training "
 "pipeline. An Agile approach was therefore chosen over a plan-driven Waterfall process, allowing the system to be "
 "built and validated in short, incremental cycles in which design decisions could be revised as technical "
 "findings emerged.")]

R["3.2 Development Approach"] = [
 para("Development followed an Agile, Scrum-inspired process organised into short sprints, each delivering a "
 "working, independently testable increment of a single subsystem before integration. A lightweight backlog of "
 "features was prioritised by dependency, so the foundational video pipeline was built first, followed by metadata "
 "storage, the ML classifier, the API and finally the frontend. Each sprint ended with a review against the "
 "objectives and informal supervisor feedback that shaped the next iteration."),
 para("Scrum was preferred to a rigid Waterfall plan because the project was exploratory and single-developer: "
 "requirements for the ML and agentic components genuinely emerged from experimentation, and the iterative cadence "
 "let those findings feed back into the design without a costly up-front specification. Subsystem-level testing "
 "within each sprint reduced integration complexity later.")]

R["3.3 System Development Phases"] = [
 para("Work progressed through five phases, run iteratively rather than strictly sequentially:"),
 bullet("Problem analysis and conceptualisation — defining the indexing concept and the bottlenecks it addresses."),
 bullet("Literature review and technology selection — choosing PySceneDetect, PyTorch/ResNet-18, MongoDB, Flask and React."),
 bullet("Design and architecture — subsystem decomposition, data-flow, database schema and API specification."),
 bullet("Incremental implementation — pipeline, ML training, agentic layer, MongoDB integration, API and React UI."),
 bullet("Testing and evaluation — functional tests, ML performance metrics and usability assessment."),
]

R["3.4 System Architecture Overview"] = [para(
 "The platform uses a layered architecture that separates video processing, metadata generation, database "
 "storage, the API and the presentation layer. This separation aids maintainability, allows each layer to be "
 "tested independently and supports future scaling. The detailed architecture and subsystem decomposition are "
 "presented in Chapter 5.")]

R["3.5 Data Processing Workflow"] = [para(
 "A video submitted through the upload interface is saved by the Flask API, which dispatches a background Celery "
 "task and immediately returns a task ID that the frontend polls for progress. The worker uploads the raw file to "
 "Cloudinary, detects scenes, extracts thumbnails, classifies each scene, applies the agentic decision logic, "
 "optionally samples emotion, and writes metadata to MongoDB. The dashboard then queries the API's search endpoint "
 "with active filters and renders the returned scene records as a clip grid.")]

# ---------------- Chapter 4 (Technologies) ----------------
R["4.1 Introduction"] = [para(
 "Technologies were chosen for fitness to purpose rather than popularity. The stack centres on Python for the "
 "backend and pipeline, PyTorch for machine learning, MongoDB for storage and React for the interface — all "
 "open-source and well documented.")]
R["4.2 Programming Language: Python"] = [para(
 "Python was chosen for the backend, pipeline and ML components because its computer-vision and machine-learning "
 "ecosystem (PyTorch, OpenCV, NumPy, PySceneDetect) is mature and interoperable, letting these stages share data "
 "in memory without cross-language overhead, and because it supports the rapid, exploratory development this "
 "project required.")]
R["4.3 Machine Learning Framework: PyTorch"] = [para(
 "PyTorch was preferred to TensorFlow/Keras for its transparent, Pythonic, define-by-run model that eases "
 "inspection and debugging during training, and for torchvision.models, which supplies pre-trained ResNet models "
 "ready for transfer learning.")]
R["4.4 Video Processing Libraries"] = [para(
 "PySceneDetect provides well-tested ContentDetector and AdaptiveDetector algorithms for scene boundaries. OpenCV "
 "(cv2) handles frame-level operations including thumbnail extraction and Haar-cascade face detection, and FFmpeg "
 "is used through subprocess calls for video validation and segment extraction.")]
R["4.5 Database Technology: MongoDB"] = [para(
 "MongoDB was chosen because scene documents have variable structure — a scene with a face carries emotion fields "
 "that a face-free scene omits — which a document store represents naturally without nullable columns, and because "
 "its JSON-like BSON aligns with the JSON exchanged between API and frontend.")]
R["4.6 Backend Framework: Flask and Celery"] = [para(
 "Flask provides a lightweight REST API using the application-factory pattern with Blueprints, CORS, Flask-Mail and "
 "Swagger documentation. Because scene processing is computationally heavy, it is offloaded to a Celery task queue "
 "backed by Redis, so uploads return immediately with a task ID while processing runs asynchronously and reports "
 "progress.")]
R["4.7 Cloud Storage: Cloudinary"] = [para(
 "Cloudinary stores raw videos, thumbnails and organised category folders, returning URLs that are persisted in "
 "the scene metadata. Offloading binary assets to a managed CDN keeps the database lightweight and serves media "
 "efficiently to the frontend.")]
R["4.8 User Interface Framework: React"] = [para(
 "The interface is built with React (with Vite and React Router), chosen for its component model and ecosystem. It "
 "uses GSAP and Lenis for the landing-page motion, Recharts for the analytics dashboard, react-joyride for the "
 "guided tour and Lucide icons, within a role-aware authenticated shell.")]
R["4.9 Version Control and Development Environment"] = [para(
 "Development used Git for version control with VS Code as the primary IDE. The backend ran in a Python virtual "
 "environment and the frontend through the Vite dev server, with MongoDB and Redis running locally during "
 "development.")]

# ---------------- Requirements (inserted at end of Methodology) ----------------
func_reqs = table(
 ["ID", "Functional Requirement", "Priority"],
 [["F1", "Users can register, log in and access a role-aware dashboard.", "High"],
  ["F2", "Users can upload raw video files (MP4/MOV/AVI/MKV) for processing.", "High"],
  ["F3", "The pipeline detects scene boundaries and extracts a thumbnail per scene.", "High"],
  ["F4", "Each scene is classified into one of five categories with a confidence score.", "High"],
  ["F5", "Low-confidence or conflicting scenes are flagged as uncertain for review.", "High"],
  ["F6", "Emotion is inferred for scenes containing detectable faces.", "Medium"],
  ["F7", "Users can browse, search and filter scenes by label, emotion, status and duration.", "High"],
  ["F8", "Users can review, correct and annotate labels in an Inspector panel.", "High"],
  ["F9", "Users can auto-organize scenes into category folders and download per-category ZIPs.", "Medium"],
  ["F10", "Administrators can manage users and monitor processing jobs.", "Medium"]],
 widths=[700, 6800, 1200])

nf_reqs = table(
 ["ID", "Non-Functional / Usability Requirement"],
 [["NF1", "Heavy processing runs asynchronously so the UI stays responsive during uploads."],
  ["NF2", "All data is scoped by user_id; users see only their own footage (admins have oversight)."],
  ["NF3", "The system degrades gracefully if the ML stack is unavailable, falling back to rule-based classification."],
  ["NF4", "Reprocessing a video is idempotent (SHA-256 dedup, upsert by scene_id)."],
  ["UR1", "Thumbnails and labels let users identify clips without playing full footage."],
  ["UR2", "Live progress feedback is shown during minutes-long processing jobs."],
  ["UR3", "A first-run guided tour introduces the upload, review and organise workflows."],
  ["UR4", "Human-reviewed clips are visually distinguished from automatically labelled ones."]],
 widths=[700, 8000])

requirements_block = (
 heading("3.6 Functional Requirements", 3)
 + para("The functional requirements (F) define what the system must do. They are summarised below and were used "
        "as acceptance criteria during the functional testing reported in Chapter 7.")
 + func_reqs
 + heading("3.7 Non-Functional and Usability Requirements", 3)
 + para("Non-functional (NF) and usability (UR) requirements define quality attributes and the user experience the "
        "system must support.")
 + nf_reqs)

INSERTS = [("Technologies and Tools Used", requirements_block)]

if __name__ == "__main__":
    apply(R, INSERTS, strip_codex=True, dry=("--apply" not in sys.argv))
