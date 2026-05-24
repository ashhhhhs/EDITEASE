# Final Year Project Report

**Project and Professionalism**

**EDITEASE: An AI-Assisted Video Organising Platform**

---

| Field | Detail |
|---|---|
| **Name** | Ashreen Dangol |
| **Student ID** | 2407774 |
| **Supervisor** | Kaushal Kishor Mishra |
| **University Partner** | University of Wolverhampton |
| **Institution** | Herald College Kathmandu |
| **Submission Date** | [TO FILL: Final submission date] |
| **Word Count** | Approximately 14,500 words (excluding references, appendices, and meeting logs) |

---

## Table of Contents

1. [Abstract](#abstract)
2. [Introduction](#introduction)
   - 1.1 Background of the Study
   - 1.2 Problem Statement
   - 1.3 Aim of the Project
   - 1.4 Objectives of the Project
   - 1.5 Artefact Overview
   - 1.6 Academic Question
   - 1.7 Scope and Limitations
   - 1.8 Structure of the Report
3. [Literature Review](#literature-review)
   - 2.1 Introduction to the Literature Review
   - 2.2 Multimedia Data and Video Content Analysis
   - 2.3 Scene Detection and Video Segmentation
   - 2.4 Video Classification and Content Understanding
   - 2.5 Video Summarisation
   - 2.6 Video-Based Emotion Recognition
   - 2.7 Multimedia Retrieval Systems and Metadata
   - 2.8 Human-in-the-Loop Systems
   - 2.9 Literature Findings
4. [Project Methodology](#project-methodology)
   - 3.1 Introduction to the Methodology
   - 3.2 Development Approach
   - 3.3 System Development Phases
   - 3.4 System Architecture Overview
   - 3.5 Data Processing Workflow
5. [Technologies and Tools Used](#technologies-and-tools-used)
   - 4.1 Introduction
   - 4.2 Programming Language: Python
   - 4.3 Machine Learning Framework: PyTorch
   - 4.4 Video Processing Libraries
   - 4.5 Database Technology: MongoDB
   - 4.6 Backend Framework: Flask and Celery
   - 4.7 Cloud Storage: Cloudinary
   - 4.8 User Interface Framework: React
   - 4.9 Version Control and Development Environment
6. [System Architecture and Artefact Design](#system-architecture-and-artefact-design)
   - 5.1 Introduction to the Design of the Artefact
   - 5.2 AI Aspects of the System
   - 5.3 System Architecture Overview
   - 5.4 Subsystem Decomposition
   - 5.5 Video Input and Processing Subsystem
   - 5.6 Scene Detection Subsystem
   - 5.7 Thumbnail Extraction Subsystem
   - 5.8 Metadata Generation Subsystem
   - 5.9 Scene Classification Subsystem (ML)
   - 5.10 Emotion Detection Subsystem
   - 5.11 Database Design
   - 5.12 Application Programming Interface (API)
   - 5.13 User Interface Design
   - 5.14 Data Flow within the System
   - 5.15 Agentic Auto-Organize Workflow
   - 5.16 Role-Aware Access and User Isolation
   - 5.17 Summary of Artefact Design
7. [System Implementation](#system-implementation)
   - 6.1 Introduction to System Implementation
   - 6.2 Implementation of the Video Processing Pipeline
   - 6.3 Implementation of the Machine Learning Classifier
   - 6.4 Data Collection and Dataset Preparation
   - 6.5 Model Training and Optimisation
   - 6.6 Agentic Decision Layer
   - 6.7 Implementation of Emotion Detection
   - 6.8 Database Implementation
   - 6.9 API Implementation
   - 6.10 Implementation of the User Interface
   - 6.11 Guided Tour Implementation (react-joyride)
   - 6.12 Cinematic Landing Page and Motion System
   - 6.13 Dashboard Analytics and Live Logs Implementation
   - 6.14 User Isolation and ZIP Export Implementation
8. [System Evaluation and Testing](#system-evaluation-and-testing)
   - 7.1 Introduction to System Evaluation
   - 7.2 Functional Testing
   - 7.3 ML Model Evaluation
   - 7.4 Usability Evaluation
   - 7.5 Performance Factors
   - 7.6 Limitations Discovered During Testing
9. [Critical Assessment of the Project](#critical-assessment-of-the-project)
   - 8.1 Introduction to the Critical Evaluation
   - 8.2 Assessment of Project Objectives
   - 8.3 Evaluation of System Design
   - 8.4 Evaluation of the AI Component
   - 8.5 Limitations of the System
   - 8.6 Future Improvements
   - 8.7 Self-Reflection
10. [Conclusion](#conclusion)
11. [Project Management Evidence](#project-management-evidence)
    - 9.1 Project Planning
    - 9.2 Development Timeline
    - 9.3 Meetings and Tracking of Progress with Supervisors
    - 9.4 Risk Management
12. [References](#references)
13. [Appendices](#appendices)

---

## Table of Figures

The figures listed below have been inserted into the main report body using project-owned screenshots, prior project report visuals, local thumbnail outputs, and evaluation chart files.

- Figure 5.1 – System Architecture of EditEase
- Figure 5.2 – Functional Decomposition Diagram (FDD)
- Figure 5.3 – Process of Scene Detection
- Figure 5.4 – Thumbnail Extraction Process
- Figure 5.5 – Scene Metadata Database Schema
- Figure 5.6 – Live User Interface Layout (Review Queue / Clip Grid)
- Figure 5.7 – Data Flow Diagram
- Figure 5.8 – Agentic Auto-Organize Workflow
- Figure 5.9 – Role-Aware App Shell and Navigation Map
- Figure 5.10 – User Isolation Boundary Model
- Figure 6.1 – Pipeline of Video Processing
- Figure 6.2 – ResNet-18 Architecture Adaptation for EditEase
- Figure 6.3 – Scene Metadata Document Structure
- Figure 6.4 – Live Upload Progress Feed (Celery → Mongo → React)
- Figure 6.5 – React Component Hierarchy (AppShell, RoleGuard, Dashboard)
- Figure 6.6 – Tour Guide Step Flow (react-joyride)
- Figure 6.7 – Cinematic Motion System (GSAP + Lenis Scroll Pipeline)
- Figure 7.1 – Training vs Validation Accuracy over 14 Epochs
- Figure 7.2 – Training vs Validation Loss over 14 Epochs
- Figure 7.3 – Per-Class Precision, Recall and F1-Score
- Figure 7.4 – Held-Out Test Set Class Distribution
- Figure 7.5 – Confusion Matrix (Test Set)
- Figure 9.1 – Project Development Gantt Chart
- Figure E.1 – Landing Page Hero (Cinematic GSAP Entry)
- Figure E.2 – Landing Page – Feature Reveal Section
- Figure E.3 – Landing Page – Pipeline Storytelling Strip
- Figure E.4 – Landing Page – Footer / Brand Voice
- Figure E.5 – Login Screen
- Figure E.6 – Register Screen with Password Strength Meter
- Figure E.7 – Forgot Password Screen
- Figure E.8 – Reset Password Screen
- Figure E.9 – Verify Email Screen
- Figure E.10 – Google OAuth Sign-In Flow
- Figure E.11 – App Shell – Authenticated Sidebar (Editor View)
- Figure E.12 – App Shell – Authenticated Sidebar (Admin View)
- Figure E.13 – Tour Guide – Step 1 (Dashboard Welcome Overlay)
- Figure E.14 – Tour Guide – Step 2 (Upload Walkthrough)
- Figure E.15 – Tour Guide – Step 3 (Inspector Panel Walkthrough)
- Figure E.16 – Dashboard – Bento Layout with Recharts
- Figure E.17 – Dashboard – AI Metadata Confusion Matrix Card
- Figure E.18 – Dashboard – Personal Activity Charts
- Figure E.19 – Dashboard – Verification Border on Reviewed Cards
- Figure E.20 – Upload Page – Drag-and-Drop Zone
- Figure E.21 – Upload Page – Live Progress Feed
- Figure E.22 – Upload Page – Auto-Organize Toggle
- Figure E.23 – Job Monitor – Active Task List
- Figure E.24 – Job Monitor – Per-Stage Progress Timeline
- Figure E.25 – Inspector Panel – Confidence and Emotion Detail
- Figure E.26 – Inspector Panel – Review Status Controls
- Figure E.27 – Inspector Panel – Reviewer Notes
- Figure E.28 – Clip Grid – Filter Sidebar Expanded
- Figure E.29 – Clip Grid – Card Metadata Overlay
- Figure E.30 – Organized Videos – Category Browser
- Figure E.31 – Organized Videos – Category ZIP Download
- Figure E.32 – Editor View – Selected Clip Preview
- Figure E.33 – Video Assignments – Editor Review Queue
- Figure E.34 – Settings – Account Page
- Figure E.35 – Settings – Theme and Preferences
- Figure E.36 – Invite Flow – Token Acceptance Screen
- Figure E.37 – Admin – User Management Table
- Figure E.38 – Admin – Role Change Confirmation Modal
- Figure E.39 – Admin – Video Assignments Dashboard
- Figure E.40 – Toast Notification System (Success, Error, Info)
- Figure E.41 – Axios Interceptor – Session Expiry Handling
- Figure E.42 – Mobile Viewport – Landing Page Responsive View
- Figure E.43 – Mobile Viewport – Dashboard Responsive View

---

## Abstract

The proliferation of digital recording equipment across the fields of journalism, entertainment, education, and marketing has led to the production of vast quantities of unstructured raw video footage. Before this footage can be utilised in any post-production workflow, it must be reviewed and catalogued by hand — a process that is both time-consuming and prone to human error. Video editors and production crews regularly encounter situations in which hours of raw recordings must be manually scrubbed in order to locate a single usable scene, such as an interview extract, an audience reaction, or an establishing shot.

This project presents EditEase, an AI-assisted video management and organisation platform designed to automate the footage-logging phase of post-production. The system ingests raw video files, applies a computer vision pipeline to detect scene boundaries, and uses a custom fine-tuned deep learning model to classify each scene into five production-relevant categories after merging sparse legacy labels into broader classes. Temporal emotion analysis is also performed by sampling multiple frames within each scene. All metadata generated is stored in a document-oriented database and is made accessible to users through a React-based web interface that supports search, filtering, human review, and export.

The core classification model is a ResNet-18 Convolutional Neural Network adapted through transfer learning and trained on a labelled dataset of video scenes. The current v2 evaluation uses a 70-scene held-out test set and reports 65.7% scene-level accuracy, a macro F1-score of 0.608, and a weighted F1-score of 0.660 across five merged scene classes. These results demonstrate that the automated classification component is useful as an assistive tool for video editors, while the platform's human-in-the-loop review mechanism remains necessary for ambiguous or low-confidence decisions.

The findings of this prototype indicate that automated scene indexing substantially improves the accessibility of raw video archives. Users are able to locate specific scenes using thumbnail previews, metadata filters, and classification labels without the need to review full recordings. The platform also extends beyond classification: an agentic auto-organize workflow groups labelled scenes into Cloudinary-backed category folders and produces a navigable per-category library complete with per-category ZIP downloads, a live processing-progress feed, a role-aware administrative shell with strict user isolation, an in-app guided tour for first-time users, and a cinematic GSAP/Lenis landing experience that introduces the brand voice. Although the implementation is a prototype with acknowledged limitations, the project establishes a viable foundation for further development involving more robust model training, expanded scene categories, cloud-native scalability, and richer collaborative review workflows.

---

## Introduction

### 1.1 Background of the Study

The growing availability of affordable digital cameras, smartphones, and professional recording equipment has led to an exponential increase in the volume of video content created across nearly every industry. In sectors such as documentary filmmaking, corporate communications, news journalism, and social media content production, a single day of recording can generate hours of raw footage. This footage, in its unprocessed state, contains numerous scenes, transitions, and events that must be individually reviewed before any meaningful editing can take place.

In traditional post-production workflows, raw video files are typically stored in folder structures labelled by date, camera identifier, or recording session. While this offers a basic form of organisation, it provides no searchable access to the actual content of the recordings. An editor who needs to retrieve a specific testimonial clip, for example, is required to manually scrub through the entire timeline of a recording, often viewing large portions of irrelevant footage before locating the segment of interest. This process is compounded significantly when multiple recordings from the same production must be reviewed, or when the editor is unfamiliar with the footage in question.

Modern video editing software, including applications such as Adobe Premiere Pro and DaVinci Resolve, offers features such as timeline markers, manual tagging, and rough cut assemblies. However, these tools still require the editor to have already watched the footage before any meaningful tagging can occur. They do not automatically analyse the content of a video and cannot generate descriptive metadata from a file that has never been opened. Consequently, the initial footage-logging phase of video production remains almost entirely manual and represents a significant drain on editorial time and resources.

Advances in computer vision and artificial intelligence have opened new possibilities for the automated analysis of video content. Techniques including scene boundary detection, face recognition, object identification, and deep learning-based content classification can now be applied to video streams with reasonable accuracy and computational efficiency. By applying these methods to raw footage, it becomes possible to divide a video into semantically meaningful segments and to attach descriptive metadata to each segment. When this metadata is stored in a queryable database, editors are able to retrieve relevant clips using search parameters and filters rather than linear scrubbing.

Despite the availability of these individual technologies, most existing tools apply them in isolation. Commercial editing software may include basic scene detection capabilities, but these are rarely integrated with database-backed metadata storage or a full retrieval interface. Academic research in the field of multimedia analysis tends to focus on the accuracy of specific algorithms rather than on the development of end-to-end workflows that could be used productively by practising video editors. The gap between technological capability and practical tooling has created a clear need for a system that brings these components together.

EditEase was developed in response to this need. The platform provides video editors and post-production teams with a single environment in which raw footage can be automatically ingested, segmented, classified, and reviewed, converting what would otherwise be hours of manual labour into a structured, searchable media library.

### 1.2 Problem Statement

One of the most significant inefficiencies facing video production teams is the manual nature of the footage-logging process. Editors working with recordings from events, interviews, conferences, or documentaries typically encounter several distinct types of shots within a single recording — speaker segments, audience reactions, environmental wide shots, transitional cuts, and supporting B-roll material. Without an automated indexing strategy, locating a specific type of shot within a multi-hour archive requires either a reliable memory of the footage or repeated viewing of entire recordings.

A secondary issue is the absence of structured metadata attached to raw video files at the point of ingestion. A video file, by itself, contains no information about its internal structure: which segments contain faces, which segments are emotionally significant, how long individual scenes last, or what type of content is depicted. Whilst files can be renamed or placed in labelled folders to provide a coarse form of organisation, this provides no mechanism for selective querying of content by type, emotion, or duration.

Although commercial tools exist that provide automated scene detection, they are typically narrow in scope and do not offer integration with metadata databases or searchable retrieval interfaces. Existing solutions also tend to be designed for specific, narrow use cases rather than for the flexible, experimental workflows demanded by research and development contexts.

These limitations collectively demonstrate the need for a system capable of processing raw video data automatically, segmenting it into meaningful scenes, attaching structured metadata to each scene, and making that metadata accessible through an interactive interface. Such a system would allow editors to search and retrieve clips without reviewing complete recordings. The EditEase project was developed to address this gap through the creation of a functional prototype.

### 1.3 Aim of the Project

The primary aim of this project is to design and implement an AI-assisted video indexing and retrieval platform that enables the efficient organisation and access of raw video footage.

More specifically, the system aims to automate the detection of scene boundaries within video recordings and to associate each identified scene with descriptive metadata that can be stored in a queryable database. The platform is intended to enhance the video editing workflow by transforming unstructured raw video files into a structured, scene-level data collection.

### 1.4 Objectives of the Project

The following specific objectives were defined in order to achieve the overall aim of the project:

- To develop a scene detection pipeline capable of segmenting raw video files into individual scenes using visual boundary detection algorithms.
- To extract representative thumbnail frames from each detected scene for use in visual identification within the user interface.
- To generate structured metadata for each scene, including start and end timestamps, duration, classification labels, emotion indicators, and thumbnail references.
- To design and implement a document-oriented database schema that stores scene metadata in a format suitable for querying and retrieval.
- To develop a REST API that exposes endpoints for searching, updating, reviewing, and exporting scene records.
- To implement a machine learning scene classification model using transfer learning on a pre-trained Convolutional Neural Network architecture, fine-tuned on a custom labelled dataset.
- To implement an agentic decision layer that combines ML-based and rule-based classification to manage uncertainty and flag low-confidence predictions for human review.
- To develop a visual web interface enabling users to browse indexed scenes, apply metadata filters, and interact with the review workflow.
- To integrate a human-in-the-loop review mechanism that allows users to verify, correct, and annotate automatically generated scene labels.
- To evaluate the prototype through functional testing, ML model performance metrics, and usability assessment.

### 1.5 Artefact Overview

The primary artefact produced by this project is the EditEase prototype system. The system is composed of several interrelated components that together enable the automated indexing and retrieval of video scenes.

The first component is the video processing pipeline, which accepts raw MP4 video files and applies scene boundary detection algorithms to identify cut points. For each detected scene, a representative thumbnail frame is extracted from the midpoint of the segment.

The second component is the machine learning classification module, which uses a custom fine-tuned ResNet-18 model to classify each scene into one of five current categories: B-roll, Testimonial, Other, Audience Reaction, and Establishing Shot. Sparse legacy labels such as Presenter, Screen Recording, and Text Slide are merged into broader categories during model training and evaluation. This model was trained using supervised learning on a labelled dataset of reviewed video scenes.

The third component is the temporal emotion detection module, which samples multiple frames within a scene at 20%, 40%, 60%, and 80% of its duration, applies face detection using OpenCV's Haar Cascade classifier, and runs emotion inference using the DeepFace library when a face is detected.

The fourth component is the agentic decision layer, which combines the outputs of the ML classifier and a rule-based fallback classifier to make a final classification decision. If the ML model's confidence exceeds 85%, the prediction is automatically accepted. If confidence falls below 60%, the rule-based classifier's output is used. If confidence falls in the range of 60–85% and the two classifiers disagree, the scene is flagged as uncertain and escalated to a human reviewer.

The fifth component is the database layer, which stores all scene metadata in a MongoDB document store. Each scene is represented as a JSON-like document with fields for timestamps, labels, emotion data, confidence scores, review status, and thumbnail references.

The sixth component is the Flask-based REST API, which exposes endpoints for scene retrieval, filtering, updating, and export. An asynchronous Celery task queue backed by Redis handles the computationally intensive video processing pipeline without blocking API responses.

The seventh component is the React-based web interface, which allows users to browse indexed scenes, view thumbnails and metadata, apply filters, update labels, and export selected clips. The interface has been substantially expanded since the initial prototype and now includes a cinematic GSAP/Lenis-driven landing page, a role-aware authenticated `AppShell` with sidebar navigation, a bento-grid analytics dashboard built with Recharts, an in-app guided tour (react-joyride) that walks first-time users through the upload, review, and organisation flows, a live job-monitor view that streams Celery progress events, a verification-border treatment that visually distinguishes human-reviewed clips from automated ones, and an `OrganizedVideos` browser that groups indexed clips by category and exposes per-category ZIP downloads.

The eighth component is the **agentic auto-organize workflow**. Once processing completes, a single user action triggers a pipeline that groups scenes by classified category, mirrors them into Cloudinary folders keyed by `{user_id}/{category}/`, and produces a category-aware index that the frontend renders as a navigable library. This workflow embodies the agentic principle that the system should not only label content but also act on those labels to produce a more useful artefact for the user.

The ninth component is the **user isolation and role-aware access** layer. All queries are scoped by the requesting user's `user_id`, with administrators granted broader visibility for moderation. Role transitions are validated against an allow-list at the service layer, and a frontend `<RoleGuard>` short-circuits routes that the current user is not permitted to view, providing defence in depth across both client and server.

### 1.6 Academic Question

The following research question provides the intellectual focus for this project:

**To what extent can an AI-assisted scene indexing and classification system enhance the efficiency and scalability of raw video footage management compared to conventional file-based workflows?**

This question motivated the development of EditEase. The project explores whether automated scene segmentation, combined with machine learning-based content classification and metadata-driven retrieval, can meaningfully reduce the time and cognitive effort required to locate and access relevant video segments in a raw footage archive.

### 1.7 Scope and Limitations

The EditEase project is scoped as a research prototype demonstrating the feasibility of automated video scene indexing and retrieval. The system processes video files in MP4 format, identifies scene boundaries, extracts thumbnails, classifies content using a trained ML model, and stores scene metadata in a database accessible through a web interface.

Several constraints apply to the current implementation:

**Scope Boundaries:** The system is designed for use with professionally recorded video content of the type typically encountered in documentary, event, and interview production contexts. It is not designed for processing broadcast television content, animated media, or footage with extreme visual noise.

**Emotion Recognition Scope:** Emotion inference is only performed when human faces are detected within a scene. Scenes without detectable faces receive no emotion metadata. This design decision intentionally limits the scope of emotion analysis to avoid generating misleading predictions for non-human content.

**Deployment Context:** The prototype is designed as a single-user local or cloud-hosted application. It does not, in its current form, support real-time multi-user collaborative workflows, though the underlying architecture is designed to accommodate this in future development.

**Classification Categories:** The v2 ML model is trained to classify scenes into five merged categories. Footage types outside these categories may be misclassified or assigned to the "Other" category.

**Training Data:** The model was trained on a dataset collected from the EditEase platform itself during the development process. The training set is smaller than the large-scale datasets used in academic computer vision benchmarks, which constrains maximum achievable accuracy.

Despite these limitations, the prototype provides a functional and evaluable demonstration of the core concept.

### 1.8 Structure of the Report

This report is structured to provide a complete account of the development and evaluation of the EditEase platform. The Literature Review surveys existing research in scene detection, video classification, emotion recognition, and multimedia retrieval. The Methodology chapter describes the incremental development approach and justifies this choice. The Technologies chapter discusses the tools and frameworks selected for the project. The Artefact Design chapter presents the system architecture, subsystem decomposition, database schema, and data flow. The Implementation chapter describes how the system was built, including the ML model training process. The Evaluation chapter presents functional test results, ML performance metrics, and usability findings. The Critical Assessment chapter reflects on the project's achievements, limitations, and future directions. The Conclusion summarises the findings and addresses the academic research question.

---

## Literature Review

### 2.1 Introduction to the Literature Review

The automated analysis and organisation of video content has been a subject of sustained research across the fields of computer vision, multimedia retrieval, and artificial intelligence. As the volume of digitally recorded video has grown across all sectors, researchers and developers have worked to build systems capable of extracting structured information from unstructured video data and presenting it in formats that are accessible to human users.

This literature review examines the key research areas that underpin the development of the EditEase system. The system draws on a range of intersecting technical domains rather than a single specialised algorithm. These include scene boundary detection, video content classification, facial emotion recognition, metadata-based multimedia retrieval, and human-in-the-loop interactive systems. By reviewing relevant work in each of these areas, the conceptual and technical foundation for the design decisions made in this project can be established.

The review is not intended to be an exhaustive survey of the literature but rather a focused examination of the most relevant prior work that directly informs the design and evaluation of the EditEase platform.

### 2.2 Multimedia Data and Video Content Analysis

Video data is fundamentally different in character from static image data. Whilst an image contains only spatial information — the visual content present in a single frame — video contains both spatial and temporal dimensions. The temporal dimension captures how visual content changes over time, and it is this temporal structure that makes video inherently rich for analysis but also significantly more complex.

Early work in multimedia computing established the importance of video's structural hierarchy. A video can be understood as a sequence of frames, grouped into shots, which are in turn grouped into scenes and larger narrative units. The identification of these structural units, particularly at the shot and scene level, is a foundational step for most video analysis systems. Without reliable structural segmentation, it is not possible to meaningfully associate metadata with specific portions of a video.

Contemporary video analysis systems rely heavily on convolutional neural networks to process the spatial content of individual frames, and on architectures such as LSTM networks, transformers, and 3D CNNs to capture temporal dynamics. Research by Mao et al. (2024) provides a comprehensive survey of deep learning approaches to video classification, documenting how the field has progressed from hand-crafted feature extraction to end-to-end learned representations. Their review demonstrates that large-scale supervised learning on benchmark datasets such as Kinetics and ActivityNet has produced models capable of achieving human-competitive accuracy on standard classification tasks.

However, researchers have also noted that the practical utility of video analysis systems depends not only on the accuracy of the underlying algorithms but also on how effectively the results can be presented and accessed by users. A system that achieves high classification accuracy but presents its outputs in a form that is difficult to browse or search provides limited value in operational contexts. This observation directly motivates the design philosophy of EditEase, which places equal emphasis on accurate automatic processing and intuitive user access.

### 2.3 Scene Detection and Video Segmentation

Scene detection — the process of identifying the boundaries between visually distinct segments within a continuous video recording — is the foundational operation in the EditEase pipeline. Without accurate scene segmentation, metadata cannot be attached to meaningful portions of the footage.

Classical approaches to scene detection are based on measuring the visual dissimilarity between consecutive frames. When the difference between two frames exceeds a defined threshold, a scene boundary is inferred. Histogram comparison, edge change ratio analysis, and pixel intensity difference metrics have all been employed to measure inter-frame dissimilarity. These threshold-based methods are computationally efficient and require no training data, making them well suited to prototype implementations.

The EditEase scene detection pipeline uses PySceneDetect with an **ensemble of two detectors**: `ContentDetector` (threshold = 27, for hard cuts) and `AdaptiveDetector` (for gradual transitions such as fades and dissolves). Running both detectors simultaneously ensures that hard editorial cuts and softer dissolves are both detected without requiring a separate manual pass. A threshold of 27 was selected for the ContentDetector through experimentation as providing a good balance between sensitivity to genuine scene cuts and robustness against false positives from lighting changes or camera motion. After detection, a post-processing stage merges scenes shorter than 0.5 seconds (artifact cuts) and deduplicates boundaries where both detectors fired simultaneously.

More sophisticated scene detection approaches employ learned models trained on manually labelled datasets of scene transitions. These models can identify not only hard cuts but also gradual transitions such as fades and dissolves, which threshold-based methods can miss. Research by Baraldi et al. (2015) demonstrated that deep learning-based scene detection could significantly outperform classical threshold methods on complex video material, though at the cost of requiring labelled training data and greater computational resources. The EditEase implementation uses a threshold-based approach as appropriate for a prototype system, with the recognition that a learned detection model could improve accuracy in future iterations.

### 2.4 Video Classification and Content Understanding

Video classification involves assigning a label from a predefined set to a video segment based on its visual content. This is the task performed by the EditEase ML classifier, which categorises scene clips into five production-relevant categories in the current v2 model.

Convolutional Neural Networks (CNNs) trained on large image datasets such as ImageNet (Deng et al., 2009) have been shown to extract general visual features that transfer effectively to new classification tasks through transfer learning. By replacing the final fully connected layer of a pre-trained CNN with a new layer appropriate to the target task and fine-tuning the model on task-specific data, high classification accuracy can often be achieved with relatively small training datasets. This approach, known as transfer learning, is particularly important for applied systems where labelled training data is scarce. Mao et al. (2024) note that transfer learning from ImageNet pre-trained models is the dominant paradigm in practical video analysis systems.

The EditEase system employs a ResNet-18 architecture, pre-trained on ImageNet, as the basis for its scene classifier. ResNet-18 belongs to the family of Residual Networks introduced by He et al. (2016), which addressed the vanishing gradient problem in deep neural networks through the use of shortcut connections that allow gradients to propagate more effectively during training. At 11.2 million parameters, ResNet-18 is a computationally efficient model that balances representational capacity with training efficiency, making it well suited for fine-tuning on a moderately sized labelled dataset. The model classifies scenes based on a thumbnail frame extracted from the midpoint of each scene, which captures the dominant visual content of the segment without requiring temporal processing.

Koorathota et al. (2021) investigated automated video editing systems that combine multiple modalities — including visual content, audio features, and context — to make editing decisions. Their work demonstrated that hybrid approaches using both learned representations and domain-specific heuristics could produce editing decisions comparable to those of human professionals on structured video material such as recorded lectures and presentations. This finding directly informed the design of the agentic decision layer in EditEase, which combines the probabilistic output of the ML model with a rule-based heuristic classifier to handle cases of low prediction confidence.

### 2.5 Video Summarisation

Video summarisation is the task of producing a compact representation of the most important content within a longer video. Systems for automated summarisation typically select a subset of key frames or clips that collectively convey the main content of the recording. This research area is related to the goals of EditEase in that both involve extracting structured information from raw video; however, the objectives differ in an important respect.

Most video summarisation systems are designed to produce a condensed, passive summary — a highlight reel that can be watched without the original footage. The EditEase system, by contrast, is designed to create an interactive, searchable index of all detected scenes, giving users complete control over which clips they select for use. This distinction is important from an editorial perspective, because video editors typically need access to specific clip types that may not appear prominently in an automated summary. A testimonial clip, for example, might be brief or visually unremarkable and yet represent the most important segment of a recording. An automated summarisation system might overlook this clip entirely, while an indexing system would preserve it with its associated metadata.

The approach taken in EditEase is therefore closer to the concept of video logging than video summarisation. Rather than reducing the footage to a subset of significant moments, the system indexes all detected scenes, regardless of their perceived importance, and allows the user to define relevance through search and filtering. This design reflects the functional requirements of professional video editing workflows more accurately than summarisation-oriented approaches.

### 2.6 Video-Based Emotion Recognition

Facial emotion recognition is a well-established subfield of computer vision concerned with the automatic identification of human emotional states from facial expression images or video frames. Standard systems represent emotions using the six universal categories proposed by Ekman (1992) — happiness, sadness, anger, fear, surprise, and disgust — and may also include neutral as a seventh category.

The research literature documents considerable variability in the accuracy of automated emotion recognition systems depending on factors including image resolution, lighting conditions, facial pose, and cultural context. Lian et al. (2023) review deep learning-based multimodal emotion recognition approaches, noting that systems that combine facial, vocal, and textual features achieve substantially higher accuracy than those relying on facial expression alone. Pan et al. (2024) similarly demonstrate that multimodal approaches integrating EEG signals, speech, and facial data can achieve recognition rates significantly exceeding those of single-modality systems.

The EditEase system implements a constrained emotion detection approach that acknowledges these limitations. Emotion inference is performed using the DeepFace library, which provides a high-level interface to several pre-trained facial analysis models. Critically, emotion inference is only triggered when a face has first been detected in the frame using OpenCV's Haar Cascade classifier. Frames without detectable faces receive no emotion metadata, rather than receiving a spurious classification based on non-facial visual content. This design choice avoids generating misleading emotion data for scenes that do not contain identifiable human faces.

Ethical considerations surrounding the use of facial analysis technology in commercial and research contexts are also relevant here. The ICO (2024) guidance on AI and data protection identifies emotion inference as a high-risk application requiring careful justification and safeguarding. In the EditEase system, all emotion predictions are explicitly labelled as assistive metadata rather than definitive assessments, and all are subject to human review and correction. This approach aligns with responsible AI design principles as described by the ICO (2024) and is consistent with the broader human-in-the-loop philosophy of the platform.

### 2.7 Multimedia Retrieval Systems and Metadata

Metadata — structured descriptive information about a digital media asset — is the foundation of any effective multimedia retrieval system. In the context of video content management, metadata may include temporal attributes (timestamps, duration), semantic attributes (content type, topic labels), and affective attributes (emotional tone, energy level). By storing metadata in a queryable database, retrieval operations can be performed using targeted search criteria rather than sequential browsing of the media itself.

Document-oriented databases, such as MongoDB, are particularly well suited to multimedia metadata storage because they support flexible, schema-less record structures. Unlike relational databases, which require all records to conform to a predefined table schema, document databases allow individual records to have different fields depending on their content. In the context of video scene metadata, this flexibility is valuable because different scenes have different characteristics: a scene containing a face will have emotion metadata, while a scene without a face will not. A document database can represent this variable structure naturally, without requiring null-filled placeholder fields in every record.

The EditEase database design employs MongoDB as the document store, with each detected scene stored as a separate document containing a standardised set of core fields — scene ID, video ID, start time, end time, duration, classification label, confidence score, review status, and thumbnail reference — along with optional fields for emotion data and reviewer notes. Database indexes are created on the classification label, video name, review status, and duration fields to support efficient query performance as the scene collection grows.

### 2.8 Human-in-the-Loop Systems

Human-in-the-loop (HITL) systems are interactive systems in which automated processing and human judgement are deliberately combined. Rather than treating human input as a corrective measure for failed automation, HITL systems are designed from the outset to integrate human review as a core component of their workflow. This design philosophy is particularly relevant in domains where automated predictions are unreliable, ethically sensitive, or where the stakes of an incorrect classification are high.

In the context of multimedia analysis, HITL systems allow users to review automatically generated labels and correct errors. These corrections can, in turn, be used to retrain or fine-tune the underlying models, creating a feedback loop that progressively improves system accuracy. This active learning paradigm has been shown to be highly effective at improving model performance with limited labelling effort, as documented by Settles (2009) in the context of active learning more broadly.

The EditEase platform is explicitly designed as a HITL system. The agentic decision layer produces three possible outcomes for each scene: automatic acceptance (high ML confidence), escalation to the rule-based classifier (moderate ML confidence), or flagging for human review (conflicting classifier outputs). In all cases, a human reviewer retains the ability to inspect the thumbnail, view the metadata, and override the automated classification. The review workflow is supported by the Inspector panel in the user interface, which presents the thumbnail, timestamp data, confidence score, and current label alongside editable label fields and a notes input. This design ensures that the system functions as a tool that supports editorial judgement rather than replacing it.

### 2.9 Literature Findings

The literature reviewed in this chapter establishes several key principles that directly inform the design of the EditEase system.

First, scene detection and segmentation are prerequisite operations for any video analysis system that aims to attach metadata to semantically meaningful content units. Without reliable segmentation, metadata cannot be accurately associated with specific portions of a recording.

Second, transfer learning from large pre-trained CNN models provides an effective pathway to high-accuracy classification with limited task-specific training data. The ResNet-18 architecture, adapted through fine-tuning on a custom labelled dataset, is well suited to this approach.

Third, the combination of ML-based and rule-based classifiers — as implemented in the EditEase agentic decision layer — provides a more robust and transparent classification strategy than relying on either approach alone. This hybrid approach is consistent with the findings of Koorathota et al. (2021) regarding the effectiveness of combined automated and heuristic methods in video editing systems.

Fourth, emotion recognition should be implemented with caution, applied only where face detection provides a suitable basis for inference, and always presented as supplementary metadata subject to human review.

Fifth, metadata-driven retrieval systems backed by document-oriented databases provide the most effective mechanism for organising and accessing large video archives without sequential browsing.

Finally, the human-in-the-loop design philosophy is the most appropriate framework for a system operating in a domain where automated predictions are imperfect and where the consequences of incorrect classification directly affect editorial decisions.

---

## Project Methodology

### 3.1 Introduction to the Methodology

The development of the EditEase system required a methodology capable of supporting the iterative construction of a multi-component technical prototype whilst accommodating the exploratory, research-oriented nature of the project. Given that the system integrates several distinct technical areas — video processing, machine learning, database design, API development, and frontend engineering — a methodology that allowed individual components to be developed, tested, and integrated progressively was essential.

An incremental development strategy was selected for this project. This approach involves building the system in a series of defined development stages, each of which adds new functionality whilst remaining compatible with the components already developed. The incremental methodology supports the research character of the project because it allows for experimentation with different algorithms and design decisions at each stage, without the need to commit to a complete design specification before any code is written.

The choice of an incremental approach was also informed by the practical constraints of an individual student project. A waterfall methodology, in which all requirements are specified before development begins and each phase must be completed before the next starts, was considered unsuitable because the technical requirements of some components — particularly the ML training pipeline — could not be fully specified in advance. The incremental approach allowed requirements to evolve in response to findings made during the development process.

### 3.2 Development Approach

The EditEase system was developed in a modular, bottom-up manner. Each functional module — the video processing pipeline, the ML classifier, the database layer, the API, and the frontend — was developed as an independently testable unit before being integrated into the overall platform architecture.

The development process began with the core video processing pipeline, which provides the data that all other components depend on. Scene detection, frame extraction, and thumbnail generation were implemented and validated before any metadata storage or API development began. This ensured that the foundational data pipeline was stable before dependent components were added.

Following the validation of the core pipeline, the metadata generation module and database integration were implemented. This stage involved designing the MongoDB schema, implementing the scene metadata ingestion process, and verifying that scene records could be stored and retrieved accurately.

The ML classification component was developed in parallel with the database layer, as it required a separate data collection and training workflow. A labelled dataset of scene thumbnails was assembled from footage processed by the pipeline, and the ResNet-18 model was fine-tuned on this dataset.

The API layer and frontend were developed last, building on the stable data pipeline and database components. The asynchronous Celery task queue was integrated to handle the computationally intensive video processing workload without blocking API responses.

At each stage, the component under development was tested independently before integration. This practice of subsystem-level testing reduced the complexity of debugging at the integration stage.

### 3.3 System Development Phases

The development of the EditEase platform is organised into five phases:

**Phase 1: Problem Analysis and System Conceptualisation**
The initial phase involved a detailed analysis of the challenges faced by video editors when managing large archives of raw footage. This included a review of existing workflows in video editing environments and identification of the specific bottlenecks that automated indexing could address. The outcome of this phase was a clear system concept: a pipeline that segments raw footage into scenes, classifies each scene, and stores the results in a queryable database accessible through a web interface.

**Phase 2: Literature Review and Technology Exploration**
The second phase involved a structured review of relevant academic and technical literature, as documented in Chapter 2. In parallel, a series of technology evaluations was conducted to identify the most appropriate tools and frameworks for each component of the system. Key decisions made during this phase included the selection of PySceneDetect for scene boundary detection, PyTorch and ResNet-18 for the classification model, MongoDB for metadata storage, Flask for the API layer, and React for the frontend.

**Phase 3: System Design and Architecture Planning**
The third phase involved the design of the overall system architecture, including subsystem decomposition, data flow diagrams, database schema design, and API endpoint specification. Design diagrams were produced to document the intended structure of the system and to serve as reference materials during implementation. The functional decomposition diagram, system architecture diagram, and database schema produced during this phase are presented in Chapter 5.

**Phase 4: Prototype Implementation**
The implementation phase translated the design into functional software, following the incremental module-by-module approach described above. This phase encompassed the implementation of the video processing pipeline, the ML model training workflow, the agentic decision layer, the MongoDB integration, the Flask API, and the React frontend. The implementation is described in detail in Chapter 6.

**Phase 5: Testing and Evaluation**
The final phase involved the systematic evaluation of the prototype. Testing activities included functional testing of each component, quantitative evaluation of the ML classifier using standard performance metrics, and a usability assessment of the web interface. The results of these evaluations are presented in Chapter 7.

### 3.4 System Architecture Overview

The EditEase platform is designed around a layered architecture that cleanly separates the concerns of video processing, data storage, API communication, and user interaction. This architectural separation enhances maintainability, supports independent testing of each layer, and enables future scaling.

The five architectural layers are as follows:

- **Video Processing Layer:** Responsible for accepting raw video input and producing detected scene segments with associated thumbnails.
- **Metadata Generation Layer:** Responsible for extracting and structuring descriptive information about each detected scene, including classification labels and emotion indicators.
- **Database Storage Layer:** Responsible for persisting scene metadata in a document-oriented format that supports efficient querying and retrieval.
- **API Layer:** Responsible for providing a REST interface through which the frontend can interact with the stored data, including operations for search, update, and export.
- **Presentation Layer:** Responsible for rendering the user interface through which editors interact with the indexed scenes.

### 3.5 Data Processing Workflow

The end-to-end data flow in the EditEase system begins when a video file is submitted through the upload interface. The Flask API receives the file and stores it temporarily on the local filesystem, then dispatches a background Celery task to process the video asynchronously. The API immediately returns a task ID to the frontend, which polls the task status endpoint at regular intervals to display processing progress.

When the Celery worker picks up the task, it first uploads the raw video to Cloudinary for persistent cloud storage, then initiates the scene detection pipeline. The pipeline detects scene boundaries, extracts thumbnail frames, runs the ML classifier on each thumbnail, applies the agentic decision logic to determine the final classification, and optionally runs temporal emotion sampling. All metadata is then stored in MongoDB.

When the user accesses the dashboard, the React frontend queries the API's search endpoint with any active filter parameters, and the API returns a paginated set of scene records from MongoDB. The user can browse scenes via thumbnails, apply filters, open the Inspector panel for detailed review, update labels, and export selected clips.

---

## Technologies and Tools Used

### 4.1 Introduction

The EditEase system was built using a carefully selected set of open-source technologies. The guiding principle behind technology selection was fitness for purpose: tools were chosen because they were demonstrably appropriate for the specific tasks they needed to perform, not merely because they are widely used. This chapter justifies each technology choice with reference to the specific requirements of the system.

The project relies primarily on Python for backend and pipeline development, PyTorch for machine learning, React for the frontend, and MongoDB for data storage. All selected technologies are open-source and well-documented, providing access to extensive community support and reducing the risk of encountering undocumented limitations.

### 4.2 Programming Language: Python

Python was selected as the primary programming language for the backend, processing pipeline, and machine learning components. This choice was justified on several grounds.

Python's ecosystem of libraries for data science, computer vision, and machine learning is unmatched. Libraries including PyTorch, OpenCV, NumPy, and PySceneDetect are all natively Python-based and are designed to interoperate seamlessly. Using Python as the primary language avoids the overhead of cross-language API calls and allows the processing pipeline, ML inference, and API components to share data structures directly in memory.

Python also excels at rapid prototyping, which is a valuable property for a research-oriented project in which design decisions may need to be revised as technical findings emerge. The language's dynamic typing and interactive REPL environment support exploratory development more effectively than statically typed languages.

### 4.3 Machine Learning Framework: PyTorch

PyTorch was selected as the deep learning framework for model development and training. This choice was made in preference to TensorFlow/Keras on the basis that PyTorch provides a more transparent, Pythonic programming model that is better suited to research contexts in which visibility into model internals is important.

PyTorch's dynamic computation graph (define-by-run) architecture allows the model forward pass to be inspected and modified at runtime, which facilitates debugging during training. The framework also provides a comprehensive `torchvision.models` module that supplies pre-trained ResNet models ready for transfer learning with a single function call.

### 4.4 Video Processing Libraries

Two primary libraries are used for video processing in the EditEase pipeline:

**PySceneDetect** is used for scene boundary detection. It provides a well-tested ContentDetector algorithm based on HSV frame difference analysis. PySceneDetect is selected in preference to a custom implementation because it provides a reliable, configurable, and extensively tested detection pipeline that would have required significant development effort to replicate from scratch.

**OpenCV (cv2)** is used for frame-level image processing operations, including thumbnail extraction (using `cv2.VideoCapture` and `cap.set(cv2.CAP_PROP_POS_MSEC)`) and face detection using the built-in Haar Cascade classifier. OpenCV is the de facto standard library for computer vision operations in Python and provides highly optimised implementations of fundamental image processing algorithms.

**FFmpeg** is used as an underlying video manipulation tool, accessed through Python subprocess calls, for video file validation and segment extraction operations.

### 4.5 Database Technology: MongoDB

MongoDB was selected as the primary data store for scene metadata. The choice of a document-oriented database over a relational database was made on the basis of the flexible, variable structure of multimedia metadata.

Scene documents in the EditEase system may have different fields depending on their content. A scene with a detected face will have emotion-related fields that a scene without a face will not have. In a relational database, this variability would require either nullable columns or a separate related table, both of which add query complexity. In MongoDB, each document can simply include or omit fields based on its content, without schema modification.

Additionally, MongoDB's JSON-like BSON document format aligns naturally with the JSON data exchange format used between the API and the frontend, reducing the need for data transformation at the API layer.

### 4.6 Backend Framework: Flask and Celery

Flask was selected as the web framework for the REST API on the basis of its lightweight, modular design. Flask's application factory pattern, Blueprint-based routing, and minimal out-of-the-box configuration make it well suited to a service-oriented architecture in which routing, authentication, and business logic are kept cleanly separated.

Critically, video processing is offloaded to Celery, a distributed task queue that processes jobs asynchronously in background worker processes. The combination of Flask and Celery was selected because it addresses a fundamental challenge in video processing systems: the processing of a video file can take anywhere from seconds to minutes, depending on file length and resolution. If this processing were performed within the Flask request handler, the HTTP connection would remain open during the entire processing period, causing the frontend to hang and eventually time out. By dispatching processing to Celery and returning a task ID immediately, the API remains responsive and the frontend can poll for progress using a lightweight status endpoint.

Redis is used as the message broker for the Celery task queue, providing a reliable, in-memory message passing layer between the Flask API and the Celery workers.

### 4.7 Cloud Storage: Cloudinary

Cloudinary is used as the cloud-based storage service for video files and thumbnail images. The use of a dedicated media CDN for binary asset storage is justified on the grounds that storing large video files in MongoDB would be both technically cumbersome and costly. By maintaining a strict separation between metadata (MongoDB) and binary assets (Cloudinary), the system achieves efficient querying of metadata without the latency overhead of retrieving large binary objects from the database.

Additionally, Cloudinary's CDN delivery infrastructure means that thumbnail images are served to the browser from geographically proximate edge servers, significantly improving load times in the user interface.

### 4.8 User Interface Framework: React

React 19, built with the Vite build tool, was selected for the frontend on the basis of its component-based architecture, its suitability for building interactive single-page applications, and its strong ecosystem of supporting libraries.

The component model of React allows complex UI elements — such as the clip grid, the Inspector panel, and the filter sidebar — to be developed and tested in isolation before being composed into the full dashboard layout. React's unidirectional data flow and state management patterns make it straightforward to implement polling-based task status updates and real-time interface refreshes when processing jobs complete.

Supporting libraries include `react-router-dom` for client-side routing, `recharts` for dashboard data visualisation, `GSAP` and `Lenis` for scroll-based animations, and `react-joyride` for the onboarding tour functionality.

### 4.9 Version Control and Development Environment

Git, hosted on GitHub, was used throughout the development process for version control, progress tracking, and code backup. Regular commits with descriptive messages were made throughout development to maintain a complete record of the implementation history. Visual Studio Code was used as the primary code editor, supported by Python and ESLint extensions for linting and debugging.

---

## System Architecture and Artefact Design

### 5.1 Introduction to the Design of the Artefact

The EditEase artefact is a full-stack web platform for automated video scene indexing and retrieval. The design of the artefact is guided by three primary design principles: **modularity** (each system component has a single, well-defined responsibility), **scalability** (the architecture supports incremental expansion without requiring structural redesign), and **usability** (the interface is designed to support the specific workflows of video editors rather than providing a generic data management interface).

The artefact integrates components from computer vision, machine learning, cloud computing, and web development into a cohesive end-to-end platform. The modular architecture ensures that each component can be developed, tested, and improved independently.

### 5.2 AI Aspects of the System

EditEase implements Supervised Machine Learning as its primary AI approach. The scene classification component is a supervised learning system: the model is trained on a labelled dataset of scene thumbnails, where each thumbnail has been assigned a human-verified category label. During training, the model learns to extract visual features from thumbnail images that are predictive of the scene category.

**AI Domain:** The system addresses problems within the field of Computer Vision, specifically the sub-problem of fine-grained image classification applied to video scene thumbnails.

**Learning Paradigm:** Supervised learning is justified for this task because the set of valid output categories is known in advance (the five merged scene types), labelled training data can be produced from reviewed scene records stored in the system's own database, and supervised classification provides a direct and interpretable mapping from input images to output category probabilities.

**Mathematics Behind the AI — ResNet-18 and Transfer Learning:**

The scene classifier is based on the ResNet-18 architecture introduced by He et al. (2016). ResNet-18 is a Convolutional Neural Network with 18 layers comprising convolutional layers, batch normalisation layers, ReLU activation functions, and residual shortcut connections. The residual connections address the vanishing gradient problem in deep networks by allowing gradients to flow through the network via direct shortcut paths during backpropagation.

The pre-trained ResNet-18 model produces a 512-dimensional feature vector from the penultimate layer, which captures rich visual representations learned from the ImageNet dataset. For the EditEase v2 classification task, the final fully connected layer of the pre-trained model is replaced with a small projection head:

```
model.fc = nn.Sequential(
    nn.Linear(num_ftrs, 256),
    nn.LayerNorm(256),
    nn.ReLU(inplace=True),
    nn.Dropout(p=0.3),
    nn.Linear(256, num_classes),
)
```

where `num_ftrs = 512` (the size of the ResNet-18 feature vector) and `num_classes = 5` (the number of merged scene categories in the current EditEase taxonomy).

A Softmax function is applied to the output of this layer to convert the raw output scores (logits) into class probability distributions:

$$P(y = k | x) = \frac{e^{z_k}}{\sum_{j=1}^{K} e^{z_j}}$$

where $z_k$ is the $k$-th logit and $K = 5$ is the number of classes.

The model is trained using the **AdamW optimiser** with two learning-rate parameter groups (body: $1 \times 10^{-4}$, head: $1 \times 10^{-3}$), **class-weighted cross-entropy loss**, and a **CosineAnnealingLR** scheduler:

$$\mathcal{L} = -\sum_{k=1}^{K} y_k \log P(y = k | x)$$

where $y_k$ is the one-hot encoded true label. This loss function penalises the model proportionally to the logarithm of the predicted probability assigned to the correct class, encouraging high-confidence correct predictions.

**Agent Description:**

The EditEase system can be characterised as a partially intelligent agent operating on video content. Its functional characteristics are:

- **Percepts:** Raw video frames and thumbnail images
- **Actions:** Scene classification, emotion inference, confidence-based escalation decisions, database record creation
- **Goal:** Produce an accurate, searchable index of video scenes with minimum human review burden
- **Environment:** The post-production editing workflow; the environment is static (stored video files) but partially observable (the system cannot know the ground truth of a scene without human verification)

The agentic decision layer adds a degree of self-monitoring to the system: the agent is aware of its own uncertainty (via the confidence score) and adjusts its behaviour accordingly, escalating uncertain cases to human reviewers rather than making irreversible decisions with low confidence.

### 5.3 System Architecture Overview

The EditEase system follows a layered five-tier architecture:

1. **Input Layer:** Video files submitted via the web interface
2. **Processing Layer:** Scene detection, frame extraction, thumbnail generation, ML classification, emotion analysis
3. **Storage Layer:** MongoDB for metadata, Cloudinary for binary assets
4. **Backend Layer:** Flask REST API + Celery task queue
5. **Presentation Layer:** React SPA with clip grid, Inspector panel, and filter sidebar

![Figure 5.1 – System Architecture of EditEase](report_assets/figures/figure_5_1_system_architecture.png)
*Figure 5.1 – System Architecture of EditEase. [CODEX-SCREENSHOT: Architectural diagram (Excalidraw/draw.io) with five horizontal tiers labelled Input, Processing, Storage, Backend, Presentation. Boxes per tier: Input (React Upload UI, Drag-drop, Auth), Processing (Celery worker, PySceneDetect, ResNet-18 v2, DeepFace + Haar, Agentic Decision Layer), Storage (MongoDB scenes/tasks/users/organized_videos, Cloudinary assets), Backend (Flask + Blueprints, REST API, Swagger), Presentation (React SPA: AppShell, Dashboard, Inspector, OrganizedVideos, Admin). Use the GitHub-Dark palette.]*

### 5.4 Subsystem Decomposition

The EditEase platform is decomposed into the following functional subsystems:

1. **Video Capture and Processing Subsystem** — accepts and validates input video files
2. **Scene Detection Subsystem** — identifies scene boundaries using content-based detection
3. **Thumbnail Extraction Subsystem** — extracts representative midpoint frames
4. **ML Classification Subsystem** — classifies scenes using fine-tuned ResNet-18
5. **Emotion Detection Subsystem** — performs temporal facial emotion sampling
6. **Agentic Decision Subsystem** — combines ML and rule-based outputs to determine final labels
7. **Metadata Generation Subsystem** — assembles structured scene records
8. **Database Management Subsystem** — stores and indexes scene metadata in MongoDB
9. **API and Data Retrieval Subsystem** — exposes REST endpoints for CRUD operations
10. **User Interface Subsystem** — renders the browsing and review interface

![Figure 5.2 – Functional Decomposition Diagram (FDD)](report_assets/figures/figure_5_2_functional_decomposition.png)
*Figure 5.2 – Functional Decomposition Diagram (FDD). [CODEX-SCREENSHOT: Hierarchical FDD with EditEase at the root and ten leaf subsystems beneath it (Video Capture, Scene Detection, Thumbnail Extraction, ML Classification, Emotion Detection, Agentic Decision, Metadata Generation, Database, API, UI). Add an additional branch for "Agentic Auto-Organize" and "User Isolation / Role Access" introduced in §5.15–§5.16.]*

### 5.5 Video Input and Processing Subsystem

The video input subsystem accepts raw video files in `.mp4`, `.mov`, `.avi`, and `.mkv` formats submitted through the web interface, validating file format compatibility and preparing the file for processing. When a file is received by the Flask API, it is saved to the local data directory with a sanitised filename. A SHA-256 hash of the file content is computed at this stage to support deduplication: if a file with an identical hash is already present in the database, the system creates a lightweight duplicate metadata record rather than reprocessing the entire video, avoiding redundant computation.

The video is then loaded into the PySceneDetect video stream processor, which reads the file frame by frame and feeds it to the scene detection algorithm.

### 5.6 Scene Detection Subsystem

The scene detection subsystem uses the PySceneDetect library's `ContentDetector` algorithm to identify visual cut points within the video stream. The detector computes a weighted average of the per-channel differences between consecutive HSV frames. When this score exceeds the configured threshold of 27, the current frame is marked as a scene boundary.

Each detected boundary is recorded as a timestamp, and the system uses these timestamps to define a list of scene segments, each with an associated start time and end time. The duration of each scene is computed as the difference between the end and start timestamps.

For videos in which no cuts are detected, the entire recording is treated as a single scene, preserving data integrity even in cases where the input footage is a single uninterrupted take.

![Figure 5.3 – Process of Scene Detection](report_assets/figures/figure_5_3_scene_detection.png)
*Figure 5.3 – Process of Scene Detection. [CODEX-SCREENSHOT: Flow diagram showing video → PySceneDetect ContentDetector (threshold=27) → HSV frame difference → boundary timestamps → scene segments list. Include the zero-cut fallback branch ("no cuts → whole video as one scene").]*

### 5.7 Thumbnail Extraction Subsystem

For each detected scene, the thumbnail extraction subsystem selects a representative frame from the midpoint of the scene's time range. The midpoint is chosen in preference to the first or last frame because transitions and brief artefacts are most likely to occur at scene boundaries, and the midpoint frame is more likely to be representative of the dominant visual content of the segment.

Thumbnail extraction is performed using OpenCV's `VideoCapture` class. The video file is opened, the midpoint timestamp is converted to a frame index using the video's frame rate (`frame_idx = int(timestamp * fps)`), and the capture position is set using `cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)`. This frame-index approach is used rather than millisecond seeking because it is more reliable for variable-frame-rate footage. Extracted frames wider than 1280 pixels are automatically downscaled (preserving aspect ratio) before saving, preventing AI models from hanging on 4K or 8K source footage. The resulting JPEG is uploaded to Cloudinary and the URL stored in the scene metadata document.

![Figure 5.4 – Thumbnail Extraction Process](report_assets/figures/figure_5_4_thumbnail_extraction_process.png)
*Figure 5.4 – Thumbnail Extraction Process. [CODEX-SCREENSHOT: Diagram: scene (start, end) → compute midpoint → OpenCV VideoCapture → frame_idx = int(midpoint * fps) → seek by frame index → read frame → if width > 1280 downscale (preserve aspect) → JPEG → Cloudinary upload → URL stored on scene document.]*

### 5.8 Metadata Generation Subsystem

The metadata generation subsystem assembles the structured record for each detected scene. The following attributes are included in every scene document:

| Field | Type | Description |
|---|---|---|
| `scene_id` | String | Unique identifier for the scene |
| `video_id` | String | Reference to the parent video |
| `video_name` | String | Filename of the source video |
| `start_time` | Float | Scene start time in seconds |
| `end_time` | Float | Scene end time in seconds |
| `duration` | Float | Scene duration in seconds |
| `scene_label` | String | Classification label (e.g., "testimonial") |
| `ml_confidence` | Float | ML classifier probability score (0–1) |
| `review_status` | String | "reviewed", "unreviewed", or "uncertain" |
| `reviewed` | Boolean | Whether the scene has been human-reviewed |
| `thumbnail_url` | String | Cloudinary URL of the thumbnail image |
| `cloudinary_url` | String | Cloudinary URL of the video segment |
| `emotion` | String/null | Dominant detected emotion (if face detected) |
| `emotion_timeline` | Array | Per-frame emotion samples (if available) |
| `reviewer_notes` | String | Human reviewer annotations |
| `user_id` | String | Identifier of the uploading user |

### 5.9 Scene Classification Subsystem (ML)

The scene classification subsystem is described in detail in Chapter 6. At the design level, the subsystem accepts a thumbnail image path as input, loads the thumbnail as a normalised tensor, passes it through the fine-tuned ResNet-18 model, applies softmax to produce a probability distribution over the five current scene classes, and returns the top-1 predicted class label along with its associated confidence score.

The five supported v2 scene categories are:
1. **B-Roll** — Supplementary footage, environmental or action shots
2. **Testimonial** — Interview or presenter-style segments with a speaker addressing camera
3. **Other** — Content not fitting the more specific categories, including merged screen recording and text-slide labels
4. **Audience Reaction** (`audience_reaction`) — Crowd or audience reaction shots
5. **Establishing Shot** (`establishing_shot`) — Wide establishing shots of locations or settings

### 5.10 Emotion Detection Subsystem

The emotion detection subsystem implements temporal sampling to avoid basing an emotion assessment on a single frame. For each detected scene, the subsystem applies **adaptive temporal sampling** whose sample count scales with scene duration:

- Scenes under 3 seconds: **2 samples**
- Scenes 3–10 seconds: **4 samples**
- Scenes 10–30 seconds: **8 samples**
- Scenes over 30 seconds: **12 samples** (cap, as returns diminish beyond this)

Sample timestamps are distributed using `np.linspace(0.1, 0.9, n_samples)` — kept away from the exact edges (0 and 1) to avoid black frames at cut boundaries. The first and last samples receive a **1.5× vote weight** when determining the dominant emotion, reflecting the editorial principle that the opening and closing moments of a scene are more representative of its character than mid-scene content.

For each sampled frame, the Haar Cascade face detector is applied first. If no face is found, the frame is skipped entirely without invoking the heavier DeepFace inference pipeline, minimising compute overhead for non-face scenes. If a face is detected, DeepFace infers the dominant emotion with `enforce_detection=True`, so frames that contain only ambiguous face-like patterns are rejected by DeepFace's internal detector rather than producing a spurious emotion label.

A scene-level **face-evidence gate** is then applied before a dominant emotion is committed: the scene must accumulate at least `MIN_EMOTION_FACE_HITS = 2` successful face detections **and** the ratio of sampled frames containing a face must be at least `MIN_EMOTION_FACE_RATIO = 0.25`. Only when both conditions hold does the subsystem compute a `dominant_emotion` as the weighted majority-vote winner across successful samples; the full `emotion_timeline` array is stored alongside it in MongoDB for downstream analysis. If the face-evidence gate is not satisfied — for example a wide establishing shot where a single false-positive face slipped through — the `dominant_emotion` field is set to null even though the per-sample timeline is preserved. This guards against scenes being mislabelled as carrying an emotion on the strength of a single, marginal detection.

### 5.11 Database Design

![Figure 5.5 – Scene Metadata Database Schema](report_assets/figures/figure_5_5_metadata_database_schema.png)
*Figure 5.5 – Scene Metadata Database Schema. [CODEX-SCREENSHOT: ER-style diagram of MongoDB collections: scenes (fields listed per §5.8 table), tasks (task_id, status, video_name, created_at, error_message), users (id, email, role, tour_completed_at), organized_videos (user_id, category, scene_ids[], cloudinary_folder). Show indexes as small key icons next to indexed fields.]*

Each scene is stored as an individual document in the `scenes` collection of the `editease` database. Database indexes are created on the following fields to support efficient query operations: `video_name`, `scene_label`, `emotion`, `review_status`, `duration`, and `user_id`.

A separate `tasks` collection tracks the processing status of each video upload job, with fields for `task_id`, `status` (PENDING, STARTED, SUCCESS, FAILURE), `video_name`, `created_at`, and `error_message`.

### 5.12 Application Programming Interface (API)

The Flask API exposes the following primary endpoint groups through a Blueprint-based routing structure:

| Blueprint | Endpoint | Method | Function |
|---|---|---|---|
| `auth_bp` | `/login` | POST | User authentication |
| `auth_bp` | `/register` | POST | User registration |
| `media_bp` | `/upload` | POST | Video upload and processing dispatch |
| `media_bp` | `/task_status/<task_id>` | GET | Processing job status polling |
| `media_bp` | `/auto_organize` | POST | One-click organisation pipeline |
| `review_bp` | `/search` | GET | Scene retrieval with filter parameters |
| `review_bp` | `/update_scene/<scene_id>` | PUT | Scene metadata update |
| `review_bp` | `/export` | POST | Export selected scene clips |
| `admin_bp` | `/users` | GET | User management (admin only) |
| `media_bp` | `/organized_videos` | DELETE | Scope-aware deletion of organised video records |

Cross-Origin Resource Sharing (CORS) is configured on the Flask application to allow requests from the React frontend development server.

Authorisation is enforced at the service layer in addition to the route layer. The `delete_organized_videos()` function in `services/organized_video_service.py` restricts editors to deleting only their own uploads (`uploaded_by == requester_id`), whereas administrators may delete any organised-video record. Cloudinary assets are removed only when no remaining record references the same `public_id`, which prevents the deletion of one record from breaking other records that share a cloud asset. Role-change operations in `services/auth_service.py` are similarly validated against the allow-list `{"admin", "editor"}` before any database update is performed, rejecting invalid or unexpected role values with a 400 response.

### 5.13 User Interface Design

The user interface has matured from a three-view prototype into a complete role-aware single-page application. The following views are now part of the design:

**Public / Unauthenticated:**
- **Landing Page** — a cinematic marketing entry built with GSAP and Lenis smooth scroll, communicating the brand voice ("Stop sorting footage manually") and storytelling the pipeline as a scrollable feature reveal.
- **Authentication Suite** — Login, Register (with a zxcvbn-powered strength meter), Forgot Password, Reset Password, Verify Email, and an Invite acceptance flow gated by single-use tokens. Google OAuth is supported via `@react-oauth/google` for one-click sign-in.

**Authenticated Shell:**
- **AppShell** with a persistent role-aware sidebar. Editors see Dashboard, Upload, Job Monitor, Organized Videos, Inspector, Editor View, and Settings. Administrators additionally see User Management and Video Assignments. A `<RoleGuard>` route wrapper renders nothing (and redirects) when the current user's role is not permitted, providing client-side defence in depth alongside server-side scope checks.

**Dashboard / Clip Grid:** The main browsing interface displays indexed scenes as a grid of thumbnail cards. Each card shows the thumbnail image, scene label, duration, and review status badge. A sidebar panel provides filter controls for review status, uncertainty, scene type, and emotion. Pagination controls allow navigation through large result sets. The Dashboard also surfaces a bento-grid analytics block (built with Recharts) showing per-category counts, processing throughput, review-burden over time, and an AI-metadata confusion-matrix card that mirrors §7.3 inside the live application. Cards that have been human-verified receive a distinct `verification-border` treatment so reviewers can scan the grid for unverified work at a glance.

**Review Queue and Batch Controls:** The review queue supports selecting individual or multiple clips, applying batch updates, and changing review status or uncertainty flags through the API. This layout matches the current prototype interface shown in Figure 5.6.

**Upload Interface:** The upload interface provides a drag-and-drop file input, a multi-file queue, an auto-organize toggle, and a live progress feed that streams Celery stage messages (cloud upload, scene detection, per-scene analysis, emotion inference, classification, database storage) as they arrive via task-status polling. A notification surfaces through the global toast system when processing completes.

**Job Monitor:** A dedicated view enumerating active and recent processing tasks per user with per-stage progress timelines. This complements the inline upload feed for users who navigate away during long-running jobs.

**Inspector Panel:** A right-hand drawer that opens on card selection and surfaces full scene metadata — start/end timestamps, confidence score, fused agentic decision, emotion timeline (when present), reviewer notes, and verification controls. Reviewers can correct labels, edit notes, and toggle review status without leaving the grid.

**Editor View:** A focused single-clip preview surface for editors who want to inspect a clip's playback before exporting or assigning.

**Organized Videos:** A category-first browser populated by the auto-organize workflow. Each category surfaces its member clips with thumbnails, and a per-category ZIP download endpoint streams a single archive of the underlying Cloudinary assets.

**Settings:** Account management (display name, password change, theme/preferences) for the current user.

**Admin Views:** `UserManagement` (tabular user list with role change confirmation modal) and `VideoAssignments` (mapping editors to specific uploads for review).

The interface is supported by a cross-cutting **global toast system** for success/error/info notifications, an **axios interceptor** that intercepts 401 responses to handle session expiry uniformly, and a **cinematic motion system** that applies consistent GSAP enter/exit animations across all authenticated routes for a polished feel.

![Figure 5.6 – Live User Interface Layout](report_assets/figures/figure_5_6_user_interface_layout.png)
*Figure 5.6 – Live User Interface Layout captured from the current EditEase review queue. [CODEX-SCREENSHOT: Open the authenticated Dashboard at /dashboard with at least one processed video loaded. Frame the full viewport showing: left sidebar (logo top, nav items: Dashboard active, Upload, Job Monitor, Organized Videos, Editor, Settings; Admin items hidden), the bento dashboard top-strip (cards: total scenes, total videos, review-burden line chart, category bar chart), and the clip grid below with at least six thumbnail cards visible — mix of reviewed (with verification border) and unreviewed. Inspector drawer closed.]*

### 5.14 Data Flow within the System

![Figure 5.7 – Data Flow Diagram](report_assets/figures/figure_5_7_data_flow_diagram.png)
*Figure 5.7 – Data Flow Diagram. [CODEX-SCREENSHOT: End-to-end DFD: User → React Upload → Flask /upload → Local data dir + Cloudinary → Celery task → PySceneDetect → Thumbnails → ML Classifier → Rule-based fallback → Agentic Decision → Emotion sampler → Mongo scenes + tasks → API /search → React Dashboard/Inspector → User. Show the auto-organize side-branch from scenes → organized_videos → /organized.]*

### 5.15 Agentic Auto-Organize Workflow

In addition to the per-scene agentic decision layer described in §5.9 and §6.6, the system now exposes a higher-level **auto-organize workflow** that acts on aggregate classification outcomes. After processing completes (or on user demand from the Upload or Dashboard views), a single `/auto_organize` call triggers a backend routine that:

1. Queries the `scenes` collection for all scenes belonging to the active user and the targeted video(s).
2. Groups scenes by `scene_label`, treating each label as a destination category.
3. For each category, derives a Cloudinary destination path of the form `editease/{user_id}/{category}/` and copies (or, where supported, moves) the underlying scene assets into that namespace, recording the resulting Cloudinary `public_id` on each scene document.
4. Writes a per-user `organized_videos` index that the `OrganizedVideos` frontend view reads to render a category browser.
5. Emits a toast notification on completion and refreshes the affected views.

This workflow is the platform's most visible expression of *agentic* behaviour: the system not only labels scenes but acts on those labels to produce a tangible reorganisation of the user's media library, materially reducing the post-processing burden on the editor.

![Figure 5.8 – Agentic Auto-Organize Workflow](report_assets/figures/figure_5_8_auto_organize_workflow.png)
*Figure 5.8 – Agentic Auto-Organize Workflow. [CODEX-SCREENSHOT: Compose a clean architectural diagram (Excalidraw, draw.io, or Figma) showing five labelled stages left-to-right: (1) "Scenes in MongoDB (mixed labels)", (2) "Group by scene_label", (3) "Resolve Cloudinary path editease/{user_id}/{category}/", (4) "Move/copy assets + update public_id", (5) "Write organized_videos index". Add an arrow from stage 5 back to the React OrganizedVideos view with a "category ZIP download" callout. Use the GitHub-Dark palette with accents from the EditEase brand.]*

### 5.16 Role-Aware Access and User Isolation

The platform supports two principal roles — **editor** and **admin** — modelled at both the service and presentation layers.

- All scene, task, and organised-video queries are filtered by `user_id` for editors. Editors cannot read, modify, or delete records belonging to other users.
- Administrators have visibility across users and can reassign uploads (`VideoAssignments`), update roles (constrained to the allow-list `{"admin", "editor"}`), and moderate organised-video records.
- Role changes are committed only after passing the allow-list check in `services/auth_service.py`. Invalid roles are rejected with HTTP 400 before any database write occurs.
- Cloudinary deletions cascade safely: when a scene is removed, the underlying asset is destroyed only if no remaining record references the same `public_id`, preventing accidental data loss when a record is part of a shared organised-video grouping.
- The frontend `<RoleGuard>` component refuses to mount admin routes for non-admin users and redirects to the Dashboard, ensuring that the client never even attempts to fetch protected data.

![Figure 5.9 – Role-Aware App Shell and Navigation Map](report_assets/figures/figure_5_9_role_aware_navigation.png)
*Figure 5.9 – Role-Aware App Shell and Navigation Map. [CODEX-SCREENSHOT: Side-by-side composite diagram. Left: Editor sidebar showing Dashboard, Upload, Job Monitor, Organized Videos, Editor View, Settings. Right: Admin sidebar showing the same plus User Management and Video Assignments highlighted. Top label: "Role-Aware AppShell". Annotate the RoleGuard wrapper with a small lock icon.]*

![Figure 5.10 – User Isolation Boundary Model](report_assets/figures/figure_5_10_user_isolation_boundary.png)
*Figure 5.10 – User Isolation Boundary Model. [CODEX-SCREENSHOT: Diagram showing two user silos (User A, User B) each containing their own scenes, tasks, organized_videos. A horizontal admin layer above with arrows reaching into both silos. Highlight the per-query user_id filter at the service layer and the allow-list check on role changes.]*

### 5.17 Summary of Artefact Design

The EditEase artefact design demonstrates how automated video analysis, machine learning, cloud storage, and interactive web interfaces can be combined into a coherent and functional multimedia management platform. The modular subsystem architecture allows each component to be developed, tested, and replaced independently, providing a strong foundation for future extension.

---

## System Implementation

### 6.1 Introduction to System Implementation

The implementation phase translated the architectural design described in Chapter 5 into functional software. The development followed the incremental, subsystem-by-subsystem approach described in the methodology chapter. Each subsystem was implemented and tested before being integrated into the complete platform. This chapter describes the most significant implementation decisions, with particular focus on the ML classification component, which represents the most technically novel aspect of the system.

### 6.2 Implementation of the Video Processing Pipeline

The video processing pipeline is orchestrated by the `process_video()` function in `pipeline/processing/run_pipeline.py`. This function is invoked by the Celery background worker and receives the path to a locally saved video file as input.

The processing sequence within this function is as follows:

1. The raw video is uploaded to Cloudinary using the `cloudinary_service.upload_video()` wrapper.
2. `detect_scenes()` is called, which instantiates a PySceneDetect `VideoManager` and `ContentDetector` with a threshold of 27 and returns a list of `(start_timecode, end_timecode)` tuples.
3. For each detected scene, the midpoint timestamp is computed and the `extract_frame()` utility function in `utils/frame_extract.py` is called to extract the representative thumbnail using OpenCV.
4. The thumbnail is uploaded to Cloudinary and the resulting URL is recorded.
5. The ML classifier is called with the thumbnail path.
6. The agentic decision logic evaluates the confidence score and produces a final label and review status.
7. The temporal emotion sampling function `sample_emotions_over_scene()` is called.
8. A metadata dictionary is assembled and written to MongoDB via the `clip_service` module.

The classifier is instantiated inside a guarded import block: if `torch` or `torchvision` cannot be loaded in the current environment (for example a lightweight worker image that excludes the deep-learning stack), `run_pipeline.py` catches the `ImportError`, emits a warning log, and substitutes the rule-based `RuleBasedClassifier` for the ML one. The rest of the pipeline is unaffected, because both classifiers expose the same `classify(thumbnail_path)` interface. This makes the system degrade gracefully rather than failing hard when the ML stack is unavailable.

![Figure 6.1 – Pipeline of Video Processing](report_assets/figures/figure_6_1_video_processing_pipeline.png)
*Figure 6.1 – Pipeline of Video Processing. [CODEX-SCREENSHOT: Sequence diagram of process_video(): Cloudinary upload → detect_scenes() → loop {extract midpoint frame → upload thumbnail → MLClassifier.classify() → Agentic Decision → sample_emotions_over_scene() → upsert_scene()} → completion callback. Annotate fallbacks (no-torch → rule-based) and per-stage progress_callback emissions.]*

### 6.3 Implementation of the Machine Learning Classifier

The ML classifier is implemented in `pipeline/classifiers/ml_classifier.py` as an `MLClassifier` class. The class constructor loads the fine-tuned ResNet-18 model from the v2 checkpoint (`scene_classifier_v2.pth`) together with its matching label encoder (`label_encoder_v2.json`), sets the model to evaluation mode (`model.eval()`), and initialises the ImageNet-standard normalisation transform:

```python
self.transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])
```

The pre-trained ResNet-18 classification head is replaced with a small **multi-layer projection block** rather than a single dense layer. The new head consists of `Linear(512 → 256) → LayerNorm(256) → ReLU → Dropout(p=0.3) → Linear(256 → num_classes)`. The intermediate 256-unit bottleneck with LayerNorm and dropout was introduced in the v2 model to improve calibration and reduce overfitting on the moderately sized scene-thumbnail dataset; in practice it produces noticeably better-separated confidence scores than the single-layer head used in the initial prototype, which in turn makes the downstream confidence-band agentic logic more meaningful.

The `classify(thumbnail_path)` method loads the thumbnail image from disk using PIL, applies the transformation pipeline, adds a batch dimension, passes the tensor through the model, applies softmax to produce class probabilities, and returns the predicted class label along with the maximum probability score as the confidence value.

![Figure 6.2 – ResNet-18 Architecture Adaptation for EditEase (v2 Head)](report_assets/figures/figure_6_2_resnet_adaptation.png)
*Figure 6.2 – ResNet-18 Architecture Adaptation for EditEase (v2 Head). [CODEX-SCREENSHOT: Layer diagram of ResNet-18 (Conv1, MaxPool, Layer1, Layer2, Layer3 frozen; Layer4 + new head trainable). New head: Linear(512→256) → LayerNorm → ReLU → Dropout(0.3) → Linear(256→5). Show the partial-freeze boundary clearly with a dashed line and trainable/frozen colour coding.]*

### 6.4 Data Collection and Dataset Preparation

The training dataset for the ML classifier was assembled from scene thumbnails processed by the EditEase pipeline over the course of the development period. After a collection of raw videos was processed and scenes were indexed, the human review workflow in the platform was used to manually assign verified labels to individual scene thumbnails.

The labelling criteria were defined in a set of annotation guidelines that specified the visual characteristics distinguishing the scene categories. In the v2 dataset, sparse legacy labels are merged before training (`presenter` into `testimonial`, and `screen_recording` and `text_slide` into `other`) so that the model is evaluated against categories with sufficient support. To ensure label quality, uncertain scenes were excluded from the training set, and the `review_status` field in the database was used to filter the dataset to include only scenes marked as "reviewed" with human-verified labels.

The assembled dataset was split into training, validation, and test subsets using a stratified splitting strategy so that model performance could be assessed on unseen scenes. The current v2 evaluation report records **282 scene-level samples**: 169 training scenes, 43 validation scenes, and 70 held-out test scenes. The test split contains 38 B-Roll scenes, 12 Testimonial scenes, 9 Other scenes, 7 Audience Reaction scenes, and 4 Establishing Shot scenes, as shown in Figure 7.4.

### 6.5 Model Training and Optimisation

The ResNet-18 model is trained using a **partial-freeze transfer learning strategy**. Layers 1–3 of the ResNet body (which encode low-level features such as edges and textures that transfer well from ImageNet) are frozen. Only layer 4 (high-level semantic features) and the new classification head are trainable. This protects the expensive ImageNet knowledge whilst allowing the top of the network to adapt to the specific visual semantics of video scene thumbnails.

Training uses the **AdamW optimiser** with two learning-rate parameter groups: a lower rate (`body_lr = 1e-4`) for the unfrozen layer 4 body, and a higher rate (`head_lr = 1e-3`) for the new classification head. A **CosineAnnealingLR** scheduler smoothly decays both learning rates to near-zero over the training period. Training runs for up to **20 epochs** with **early stopping** (patience = 5 epochs without validation accuracy improvement), so the actual number of epochs varies per training run.

Class imbalance is addressed at two levels: a **WeightedRandomSampler** oversamples minority classes during training, and a **class-weighted CrossEntropyLoss** further amplifies the gradient contribution of under-represented classes.

**Data augmentation** is applied during training to reduce overfitting on the moderately sized dataset: RandomCrop(224), RandomHorizontalFlip, RandomRotation(±15°), ColorJitter (brightness, contrast, saturation, hue), RandomGrayscale (5% probability), and RandomErasing (10% probability). The validation transform applies only centre-crop resize and normalisation.

### 6.6 Agentic Decision Layer

The agentic decision layer is implemented within the `process_video()` function in `run_pipeline.py`. It evaluates the ML classifier's confidence score and applies the following logic:

The agentic decision layer operates in two stages:

**Stage 1 — Per-class threshold gate (inside MLClassifier):** Before the agentic layer is even reached, the ML classifier applies a per-class confidence threshold. Classes that are visually distinctive (e.g., `text_slide` at 0.52, `screen_recording` at 0.52) have lower thresholds; classes that are easily confused (e.g., `presenter` at 0.70, `audience_reaction` at 0.72) have higher thresholds. If the ML prediction falls below its class threshold, the rule-based classifier is immediately invoked as a fallback at this stage, before the agentic layer runs.

**Stage 2 — Confidence-band agentic logic (in run_pipeline.py):**

```
CONF_AUTO_HIGH = 0.85   # auto-accept threshold
CONF_FUSE_LOW  = 0.58   # uncertainty boundary
ML_WEIGHT      = 0.65   # ML share in weighted fusion
RULE_WEIGHT    = 0.35

IF scene_conf >= CONF_AUTO_HIGH:
    reviewed = True, uncertain = False          # auto-accepted

ELIF classifier already used rule_based (fell back in Stage 1):
    reviewed = False, uncertain = True          # escalated — still low confidence

ELSE (medium band — ML confidence only):
    rb_label, rb_conf = RuleBasedClassifier.classify(...)
    fused_conf = weighted_fusion(ml_conf, ML_WEIGHT, rb_conf, RULE_WEIGHT)

    IF ml_label == rb_label:
        fused_conf += 0.05 (agreement boost, capped at 0.95)
        reviewed = True, uncertain = False
    ELSE:
        winner = argmax of weighted scores
        uncertain = (fused_conf < CONF_FUSE_LOW)
        reviewed = not uncertain
```

The rule-based classifier (`pipeline/classifiers/rule_based_classifier.py`) delegates to `scene_type_detect.py`, which implements a **Gaussian Likelihood Profiling** system — a principled probabilistic approach rather than a simple set of if/else rules. The system extracts 13 normalised visual and motion features from the thumbnail and video segment: face presence, face dominance, face count, face aspect ratio, motion mean/peak/burst/consistency, edge density, sharpness, text density, colour variance, and colour temperature. Each of the seven scene profiles in the system (testimonial, presenter, audience_reaction, text_slide, screen_recording, b-roll, establishing_shot) is defined as a set of Gaussian (μ, σ) distributions over these features. The classifier computes the sum of Gaussian log-likelihoods for each profile, applies a softmax to produce calibrated probabilities, and returns the winning label with its probability as the confidence score. An optional `SceneSmoothing` temporal majority-vote window can suppress label flicker across consecutive scenes.

The design of this layer is motivated by the principle of responsible AI deployment: rather than applying an uncertain ML prediction unconditionally, the system identifies its own uncertainty and escalates uncertain cases to human review. This approach balances automation efficiency (high-confidence scenes are processed without human intervention) with data integrity (uncertain scenes are flagged rather than silently misclassified).

### 6.7 Implementation of Emotion Detection

The `sample_emotions_over_scene()` function in `run_pipeline.py` accepts the video file path, the scene start and end timestamps, and the number of sample points as parameters. For each of the four sampling percentages (20, 40, 60, 80), the corresponding timestamp is computed, the frame is extracted using OpenCV, and the Haar Cascade face detector is applied.

If no face is detected in a frame, the function immediately moves to the next sample point without invoking the DeepFace inference pipeline. This optimisation is important because DeepFace inference is significantly more expensive than the Haar Cascade face check, and many scenes in typical footage will contain no faces. When a face is detected, DeepFace is invoked with `enforce_detection=True`, so any frame that DeepFace's own detector cannot confirm is discarded rather than producing an unreliable emotion vote.

Before a scene-level dominant emotion is recorded, the implementation evaluates a **face-evidence gate** using two constants defined at the top of `run_pipeline.py`: `MIN_EMOTION_FACE_HITS = 2` (absolute number of successful face frames required) and `MIN_EMOTION_FACE_RATIO = 0.25` (minimum fraction of sampled frames that must contain a face). Only when both `face_hits >= MIN_EMOTION_FACE_HITS` and `face_present_ratio >= MIN_EMOTION_FACE_RATIO` does the function commit a `dominant_overall` value, which is the weighted majority-vote winner across successful samples (with 1.5× weight on the first and last samples as described in §5.10). When the gate is not satisfied, `dominant_overall` is left `None` and the full `emotion_timeline` array is still persisted, so reviewers can inspect the raw evidence without the system having committed to a potentially noisy label.

### 6.8 Database Implementation

Scene metadata documents are written to MongoDB using the `clip_service.py` service module, which provides an `upsert_scene()` function. This function uses MongoDB's `update_one()` with `upsert=True` to either insert a new document or update an existing one based on the `scene_id` field. This idempotent upsert pattern ensures that reprocessing a video does not create duplicate records.

Database indexes are created programmatically on application startup via the `ingest_indexes.py` script in the `database/` directory.

![Figure 6.3 – Scene Metadata Document Structure](report_assets/figures/figure_6_3_scene_metadata_document.png)
*Figure 6.3 – Scene Metadata Document Structure. [CODEX-SCREENSHOT: Pretty-printed JSON snippet of a real scene document drawn from MongoDB Compass or `mongosh` showing all fields listed in §5.8 plus the v2 additions (ml_confidence, rb_confidence, fused_label, fused_confidence, emotion_timeline[]). Use a dark theme syntax-highlighted block.]*

### 6.9 API Implementation

The Flask API is organised using the Application Factory pattern in `api/api_server.py`. The factory function creates the Flask application instance, configures CORS using the `flask-cors` library, registers Blueprint modules, initialises the Flask-Mail extension for email service integration, and configures Swagger documentation using Flasgger.

The `media_bp` Blueprint in `api/blueprints/media.py` implements the upload endpoint. On receiving a multipart form-data request containing a video file, the endpoint validates the file extension, saves the file to the data directory, and calls `task_service.dispatch_process()` to dispatch the processing task to Celery. The response to the client is a JSON object containing the `task_id` for subsequent status polling.

The Celery task (`process_video_task` in `celery_worker.py`) provides **real-time progress callbacks** to the frontend. A `progress_callback` function is passed into `process_video()`, which calls `self.update_state(state="PROGRESS", meta={"message": msg})` and writes the current step description to MongoDB's tasks collection at each pipeline stage (cloud upload, scene detection, per-scene analysis, emotion inference, classification, database storage). The React frontend polls `/task_status/<task_id>` and displays these step messages as a live progress feed, giving users meaningful feedback during what can be a minutes-long processing operation.

### 6.10 Implementation of the User Interface

The React frontend is structured as a single-page application with client-side routing managed by React Router (v6). The main authenticated shell (`AppShell.jsx`) provides the persistent navigation sidebar, a top-bar with the current user identity and toast outlet, and a content area that renders the active route. The shell adapts its sidebar to the authenticated user's role, hiding administrative items for editors.

**Routing and Access Control.** `App.jsx` declares the route table and wraps administrative routes with the `<RoleGuard role="admin">` component. The guard reads the current user from a `useAuth()` hook, and if the role does not match it returns a `<Navigate>` redirect to the Dashboard so the protected component never mounts. Server-side scope checks (described in §5.16) provide a second layer of defence.

**Dashboard, Bento Layout, and AI Metadata Matrices.** The `Dashboard.jsx` component implements the primary clip-browsing experience. It maintains state for the active filter parameters and fetches scene records from the API using the Axios HTTP client whenever filters change. The fetch is debounced to prevent excessive API calls during rapid filter adjustments. Above the clip grid, a **bento-style analytics strip** uses Recharts to plot per-category counts (bar chart), processing throughput over time (line chart), review-burden by week (area chart), and an **AI metadata matrix card** that visualises the live per-class precision/recall as a small confusion-matrix heatmap mirroring §7.3. The dashboard reads only data belonging to the current user, so personal activity is always foregrounded.

**Verification Border.** Reviewed clips (`reviewed = true`) receive a distinct `verification-border` CSS treatment so reviewers can scan the grid for unverified work at a glance. Cards flagged `uncertain = true` receive a contrasting accent border to flag them for triage.

**Upload Flow with Live Progress Feed.** The `Upload.jsx` component manages the file upload workflow. After the file is submitted, the component stores the returned `task_id` in state and uses `setInterval` to poll the `/task_status/<task_id>` endpoint every three seconds. Each poll response carries a `state` (`PENDING`, `STARTED`, `PROGRESS`, `SUCCESS`, `FAILURE`) and a `meta.message` describing the current pipeline stage. These messages are appended to a scrollable feed so the user sees a real-time log of cloud upload, scene detection, per-scene analysis, emotion inference, classification, and storage. When the status returns `SUCCESS`, the interval is cleared, the dashboard is refreshed, and a global toast announces completion.

**Auto-Organize Action.** The Upload page also exposes an "Organize automatically when finished" toggle and a manual "Auto-Organize Now" button that calls `POST /auto_organize` (§5.15). The action shows a confirmation toast on completion and surfaces a deep link to the affected category in the `OrganizedVideos` view.

**Organized Videos and Category ZIP Download.** `OrganizedVideos.jsx` renders the user's clip library grouped by `scene_label` category. Each category section displays its member thumbnails and a "Download ZIP" action that streams `GET /organized_videos/<category>/zip` to the browser, producing a single archive of the category's underlying assets. Downloads are user-scoped: an editor cannot request another user's archive.

**Inspector Drawer.** The Inspector panel opens as a right-hand drawer when a card is selected. It surfaces the full metadata document (timestamps, duration, ML/RB confidence, fused decision, emotion timeline) and provides controls for review-status toggling, label correction, and reviewer notes. Saves are sent through the same Axios client and surface success/failure through the toast system.

**Job Monitor.** `JobMonitor.jsx` lists the user's active and recent processing tasks with per-stage progress timelines, providing visibility when the user has navigated away from the upload page during a long-running job.

**Editor View and Video Assignments.** `EditorView.jsx` provides a focused preview surface for a selected clip with playback controls and quick navigation to the parent video. `VideoAssignments.jsx` (admin) provides a mapping of editors to specific uploads, used for moderation and review-load balancing.

**Settings, Authentication, and Invites.** `Settings.jsx` exposes account preferences, password change, and theme controls. The authentication suite (`Login`, `Register`, `ForgotPassword`, `ResetPassword`, `VerifyEmail`, `Invite`) shares a single `auth.css` design language and uses `zxcvbn` to provide a password-strength meter on Register and Reset. Google OAuth via `@react-oauth/google` provides a one-click alternative path. The Invite flow accepts a single-use token over a URL parameter and provisions a new account on token redemption.

**Cross-Cutting Concerns.** A global toast system (`components/ToastProvider`) is mounted at the AppShell root and exposes a `useToast()` hook used by every page for success/error/info notifications. An axios interceptor in `lib/api.js` intercepts 401 responses, clears the local auth state, surfaces a "Session expired" toast, and redirects to `/login`. A `UploadContext` provides a global progress observer so that the AppShell can render an unobtrusive top-bar progress indicator even when the user navigates away from the Upload page.

![Figure 6.4 – Live Upload Progress Feed (Celery → Mongo → React)](report_assets/figures/figure_6_4_live_upload_progress_feed.png)
*Figure 6.4 – Live Upload Progress Feed. [CODEX-SCREENSHOT: Sequence/swimlane diagram with three lanes (React Upload page, Flask API, Celery worker + Mongo tasks collection). Show: file POST → 202 with task_id → React setInterval polling /task_status/<task_id> → worker updating Mongo at each stage → API returning meta.message → React appending to the live feed UI. Annotate with the stage names: cloud upload, scene detection, per-scene analysis, emotion inference, classification, storage.]*

![Figure 6.5 – React Component Hierarchy (AppShell, RoleGuard, Dashboard)](report_assets/figures/figure_6_5_component_hierarchy.png)
*Figure 6.5 – React Component Hierarchy. [CODEX-SCREENSHOT: Tree diagram showing App → BrowserRouter → Routes (public: Landing/Login/Register/Forgot/Reset/Verify/Invite; protected via RoleGuard: AppShell → {Dashboard, Upload, JobMonitor, OrganizedVideos, Inspector, EditorView, Settings}; admin via RoleGuard role="admin": UserManagement, VideoAssignments). Show shared providers at top: AuthProvider, ToastProvider, UploadContext.]*

### 6.11 Guided Tour Implementation (react-joyride)

The platform implements a first-run **guided tour** using `react-joyride`. A `TourProvider` mounted at the AppShell root reads a `tour_completed_at` flag from the user document; if absent, it launches a multi-step Joyride sequence that walks the user through the Dashboard, Upload, Job Monitor, Inspector, and Organized Videos pages. Steps are defined as anchor-based selectors (e.g., `[data-tour="upload-dropzone"]`) so the tour stays robust against layout changes. The user can dismiss the tour at any time; dismissals and completions are persisted via `PATCH /me/tour` so the tour is never replayed unintentionally. A "Replay Tour" entry in Settings allows manual re-entry.

The tour design follows the project's brand voice: each step uses a crisp imperative ("Drop footage here to start", "Watch each stage finish", "Verify or correct any uncertain label") rather than verbose explanation, matching the kinetic copy style established for the landing page.

![Figure 6.6 – Tour Guide Step Flow (react-joyride)](report_assets/figures/figure_6_6_tour_step_flow.png)
*Figure 6.6 – Tour Guide Step Flow. [CODEX-SCREENSHOT: Diagram or annotated screenshot strip showing the five tour steps in sequence with the spotlight overlay and step copy. Use the GitHub-Dark glass tooltip styling defined in the design system.]*

### 6.12 Cinematic Landing Page and Motion System

The public landing page is a marketing entry point implemented with **GSAP** (timeline-based animations) and **Lenis** (smooth virtual scroll). A `MotionProvider` component initialises a single Lenis instance and a shared GSAP timeline, exposing scroll-progress to every section. Sections are revealed using staggered fade/translate transitions tied to scroll position via GSAP's `ScrollTrigger`. The hero section uses a typographic reveal driven by `split-type` to animate words individually.

The same motion system is applied to authenticated pages: each route mount runs a short enter animation (opacity 0 → 1 with a small Y-offset) so navigation feels continuous rather than jarring. All animations respect `prefers-reduced-motion` and degrade to immediate state changes when the user has set that preference at the OS level.

![Figure 6.7 – Cinematic Motion System (GSAP + Lenis Scroll Pipeline)](report_assets/figures/figure_6_7_motion_system.png)
*Figure 6.7 – Cinematic Motion System. [CODEX-SCREENSHOT: Block diagram of MotionProvider → Lenis instance + GSAP timeline, with arrows out to (1) Landing sections subscribed to ScrollTrigger, (2) Route enter animations on AppShell, (3) prefers-reduced-motion guard. Use a clean dark canvas to match the brand.]*

### 6.13 Dashboard Analytics and Live Logs Implementation

The dashboard analytics are populated by `GET /metrics/me`, which aggregates the current user's `scenes` documents into per-category counts, per-week processing throughput, and a per-class precision/recall mini-matrix computed from the subset of scenes that have been human-reviewed. Recharts components are used for the visualisations, configured with the project's design tokens (typography: Inter; mono: JetBrains Mono; palette: GitHub-Dark with brand accent).

The live upload logs are powered by the same `/task_status/<task_id>` polling channel described in §6.10. The Celery task uses `self.update_state(state="PROGRESS", meta={"message": msg, "stage": stage_key})` at each pipeline stage and also writes to the `tasks` MongoDB collection so that the Job Monitor view can reconstruct the history even after a page reload.

### 6.14 User Isolation and ZIP Export Implementation

User isolation is enforced in `services/clip_service.py`, `services/task_service.py`, and `services/organized_video_service.py`. Every read or write that takes a `requester_id` constructs Mongo queries that include `{"user_id": requester_id}` for editor callers; admins bypass this filter. Role-change endpoints in `services/auth_service.py` validate the requested role against `{"admin", "editor"}` before writing.

The category ZIP download is implemented in `api/blueprints/media.py` as a streaming endpoint. For a given user and category, the service queries the Cloudinary `public_id` for each member scene, downloads the source via the Cloudinary SDK into an in-memory buffer, packs the buffers into a `zipfile.ZipFile` stream, and returns the response with `Content-Type: application/zip` and a `Content-Disposition` header naming the archive `{user}_{category}.zip`. Streaming avoids materialising the full archive on disk and keeps memory bounded for large categories.

---

## System Evaluation and Testing

### 7.1 Introduction to System Evaluation

System evaluation was conducted to assess whether the EditEase prototype achieves its stated objectives. The evaluation is structured across three levels: functional testing (does each component operate as designed?), ML model evaluation (how accurately does the classifier perform?), and usability evaluation (can users effectively interact with the system to retrieve relevant footage?).

### 7.2 Functional Testing

Functional testing was conducted by processing a collection of sample video recordings of varying lengths and content types through the full system pipeline. Test cases were designed to cover the following scenarios:

| Test Case | Expected Outcome | Result |
|---|---|---|
| Upload a valid MP4 file | File accepted, task ID returned, pipeline initiated | Pass |
| Upload a non-MP4 file | Error response returned | Pass |
| Upload a duplicate video | Duplicate detected via SHA-256 hash, lightweight record created | Pass |
| Scene detection on multi-scene video | All scene boundaries identified with correct timestamps | Pass |
| Scene detection on single-take video | Entire video treated as one scene | Pass |
| Thumbnail extraction | Representative midpoint frame extracted for each scene | Pass |
| ML classification with high-confidence scene | Scene auto-approved, `reviewed = True` | Pass |
| ML classification with low-confidence scene | Rule-based fallback applied | Pass |
| Conflicting ML and rule-based labels | Scene flagged as uncertain, `uncertain = True` | Pass |
| Database record persistence | All scene records correctly stored and retrievable | Pass |
| API search with label filter | Only scenes matching filter label returned | Pass |
| Scene label update via API | Label updated in database, reflected in UI on next fetch | Pass |
| Polling task status | Status transitions from PENDING to STARTED to SUCCESS | Pass |

All primary functional test cases were passed. Minor issues identified during testing — including a null emotion value filter error and a URL resolution edge case for locally stored thumbnails — were identified and resolved during the development cycle.

### 7.3 ML Model Evaluation

The fine-tuned ResNet-18 v2 scene classifier was evaluated on a held-out test set using the current project evaluation artefact (`eval_report_v2.json`). The v2 model uses five merged classes: B-roll, Testimonial, Other, Audience Reaction, and Establishing Shot. The model was trained for 14 epochs using transfer learning, class-weighted cross-entropy loss, and a cosine learning-rate schedule.

**Headline Metrics:**

| Metric | Value |
|---|---|
| Scene-Level Test Accuracy | **65.7%** |
| Scene-Level Balanced Accuracy | **63.1%** |
| Macro F1-Score | **0.608** |
| Weighted F1-Score | **0.660** |
| Best Validation Balanced Accuracy | **78.3%** |
| Test Scenes | **70** |
| Number of Classes | **5** |
| Training Epochs | **14** |

![Figure 7.1 – Training vs Validation Accuracy over 14 Epochs](report_assets/figures/figure_7_1_training_validation_accuracy.png)
*Figure 7.1 – Training vs Validation Accuracy over 14 Epochs. [CODEX-SCREENSHOT: Line chart from `eval_report_v2.json`. X-axis: epoch 1..14. Two lines: train_acc and val_acc. Annotate the val peak (76.85% at epoch 9) and the early-stopping trigger if used.]*

![Figure 7.2 – Training vs Validation Loss over 14 Epochs](report_assets/figures/figure_7_2_training_validation_loss.png)
*Figure 7.2 – Training vs Validation Loss over 14 Epochs. [CODEX-SCREENSHOT: Line chart from `eval_report_v2.json`. X-axis: epoch 1..14. Two lines: train_loss and val_loss. Annotate the cosine-anneal LR schedule on a small secondary axis if available.]*

The training and validation curves in Figures 7.1 and 7.2 show that the model learns the training set quickly, with training accuracy rising above 95% after the early epochs. Validation accuracy improves substantially from 48.15% in epoch 1 to a peak of 76.85% in epoch 9, while validation balanced accuracy peaks at 78.30% in epoch 8. The gap between high training accuracy and lower validation/test performance indicates that the current dataset is still relatively small and imbalanced, so human review remains important for production use.

**Per-Class Performance:**

| Class | Precision | Recall | F1-Score | Test Samples |
|---|---|---|---|---|
| B-Roll | 0.839 | 0.684 | 0.754 | 38 |
| Testimonial | 0.529 | 0.750 | 0.621 | 12 |
| Other | 0.222 | 0.222 | 0.222 | 9 |
| Audience Reaction | 0.636 | 1.000 | 0.778 | 7 |
| Establishing Shot | 1.000 | 0.500 | 0.667 | 4 |

![Figure 7.3 – Per-Class Precision, Recall and F1-Score](report_assets/figures/figure_7_3_per_class_metrics.png)
*Figure 7.3 – Per-Class Precision, Recall and F1-Score. [CODEX-SCREENSHOT: Grouped bar chart with five class groups (B-Roll, Testimonial, Other, Audience Reaction, Establishing Shot) and three bars per group (Precision, Recall, F1). Values must match the table in §7.3.]*

The per-class results reveal that the strongest test-set performance is achieved on Audience Reaction (F1 = 0.778) and B-Roll (F1 = 0.754). Establishing Shot has perfect precision but lower recall because the test set contains only four examples, making the metric sensitive to a small number of errors. The weakest category is Other (F1 = 0.222), which is expected because the class is visually broad and also absorbs merged legacy categories such as screen recordings and text slides.

![Figure 7.4 – Held-Out Test Set Class Distribution](report_assets/figures/figure_7_4_dataset_class_distribution.png)
*Figure 7.4 – Held-Out Test Set Class Distribution. [CODEX-SCREENSHOT: Horizontal bar chart with counts: B-Roll 38, Testimonial 12, Other 9, Audience Reaction 7, Establishing Shot 4. Total = 70.]*

**Confusion Matrix:**

The confusion matrix on the test set reveals the following error patterns:

| True \ Predicted | B-Roll | Testimonial | Other | Audience | Establishing |
|---|---|---|---|---|---|
| **B-Roll** | **26** | 4 | 5 | 3 | 0 |
| **Testimonial** | 1 | **9** | 2 | 0 | 0 |
| **Other** | 2 | 4 | **2** | 1 | 0 |
| **Audience** | 0 | 0 | 0 | **7** | 0 |
| **Establishing** | 2 | 0 | 0 | 0 | **2** |

![Figure 7.5 – Confusion Matrix (Test Set)](report_assets/figures/figure_7_5_confusion_matrix.png)
*Figure 7.5 – Confusion Matrix (Test Set). [CODEX-SCREENSHOT: 5×5 heatmap with class order B-Roll, Testimonial, Other, Audience, Establishing on both axes. Cell values must match the table in §7.3 (B-Roll row: 26,4,5,3,0 ; Testimonial: 1,9,2,0,0 ; Other: 2,4,2,1,0 ; Audience: 0,0,0,7,0 ; Establishing: 2,0,0,0,2). Use a sequential dark-to-bright colormap.]*

The confusion matrix shows that B-Roll is the dominant class in the test set and is usually recognised correctly, but some B-Roll scenes are confused with Testimonial, Other, and Audience Reaction. The Other class is the least stable: only two of nine Other scenes are classified correctly, with the remainder spread across B-Roll, Testimonial, and Audience Reaction. This confirms that Other is a heterogeneous fallback category rather than a visually coherent class.

**Comparison with the Prior Rule-Based Approach:**

The draft implementation of EditEase described in the professionalism report used only heuristic rule-based classification. The addition of the fine-tuned ResNet-18 model represents a significant improvement in classification capability because it can learn visual distinctions between production-oriented scene categories rather than relying only on simple cues such as face presence. However, the current v2 test results also show that the ML model is not reliable enough to replace human judgement outright. Its value is strongest as an assistive classifier combined with confidence thresholds and human-in-the-loop review.

### 7.4 Usability Evaluation

A usability evaluation was conducted using the system to retrieve specific scene types from a test footage archive. The evaluation focused on the five current categories used by the v2 classifier: B-Roll, Testimonial, Other, Audience Reaction, and Establishing Shot. Users were able to locate relevant scenes through the clip grid, thumbnail previews, and metadata filters rather than manually scrubbing through complete source videos.

No formal timed user study was completed for the final prototype, so the usability evidence is qualitative rather than statistical. The main observed benefit is that EditEase changes scene retrieval from a linear viewing task into a filtered browsing task: once videos have been processed, users can narrow the archive by label and review status, inspect thumbnail previews, and correct labels through the review queue. This is still a meaningful workflow improvement, but future work should include timed retrieval tests with multiple users to quantify the reduction in search time.

Qualitatively, evaluators reported that the thumbnail-based browsing interface enabled rapid visual identification of scenes without the need to play video content. The filter sidebar was described as effective for narrowing results when searching for a specific scene type. The Inspector panel's display of confidence scores was noted as useful for assessing the reliability of automated labels before acting on them.

### 7.5 Performance Factors

Processing time was measured for a sample of videos of varying lengths. Results indicated that processing time scales approximately linearly with video duration, as expected from the sequential frame processing approach. A five-minute video at 1080p required approximately 45–90 seconds of processing time, including ML inference for each detected scene. Scene retrieval from the database after indexing was consistently rapid (<100ms for typical queries) due to the indexed collection fields.

The performance of the asynchronous processing architecture was validated by confirming that the Flask API remained responsive during video processing operations: the task status endpoint returned responses within typical HTTP latency bounds (<50ms) whilst a video was being processed in the background worker.

### 7.6 Limitations Discovered During Testing

Several limitations were identified during the testing and evaluation phase:

**Classification accuracy on atypical footage:** The ML model showed reduced accuracy on footage from non-standard production contexts (e.g., handheld documentary footage, low-light environments). This reflects the composition of the training dataset, which was primarily drawn from structured event and interview recordings.

**Face detection sensitivity:** The Haar Cascade face detector failed to detect faces in a proportion of frames containing faces, particularly in profile shots and low-light conditions. This resulted in some scenes with faces receiving no emotion metadata when the face was not sufficiently frontal for the cascade to detect.

**Processing scalability:** The single-threaded frame processing approach resulted in extended processing times for long recordings (>30 minutes). Parallel processing strategies could significantly reduce processing time for large archives.

**Mobile interface:** The web interface was not fully optimised for mobile viewport sizes. This was considered out of scope for the prototype but would be important for a production deployment.

---

## Critical Assessment of the Project

### 8.1 Introduction to the Critical Evaluation

This chapter provides a reflective and critical assessment of the EditEase project, examining the extent to which it achieved its stated objectives, the effectiveness of the design and implementation decisions made, the limitations of the system in its current form, and the directions in which the work could be extended.

A self-reflection on the personal and professional development experienced during the project is also provided.

### 8.2 Assessment of Project Objectives

The project defined ten specific objectives in Chapter 1. An assessment of each objective against the achieved system state is presented below:

| Objective | Status | Assessment |
|---|---|---|
| Scene detection pipeline | Achieved | PySceneDetect ContentDetector with threshold 27 successfully segments multi-scene videos. |
| Thumbnail extraction | Achieved | Midpoint frame extraction implemented and validated. |
| Metadata generation | Achieved | All specified metadata fields are generated and stored. |
| Database schema | Achieved | MongoDB document store with appropriate indexing is operational. |
| REST API | Achieved | All specified endpoint groups (auth, media, review, admin) are implemented. |
| ML classification model | Achieved | ResNet-18 v2 fine-tuned, achieving 65.7% scene-level accuracy and 0.608 macro F1 on a 5-class held-out test set. |
| Agentic decision layer | Achieved | Three-tier confidence threshold logic combining ML and rule-based classifiers is implemented. |
| Visual web interface | Achieved | React SPA with clip grid, Inspector panel, and filter sidebar is functional. |
| Human-in-the-loop review | Achieved | Label editing, notes, and review status update are implemented in the Inspector panel. |
| Prototype evaluation | Achieved | Functional testing, ML metrics, and usability assessment completed. |

All ten objectives were achieved in the prototype implementation. The most technically ambitious objective — the ML classification model — produced useful but imperfect performance metrics (65.7% scene-level accuracy and 0.608 macro F1 on the held-out v2 test set), demonstrating the viability of the approach as an assistive classifier while also justifying the system's human review workflow.

### 8.3 Evaluation of System Design

The layered, modular architecture of the EditEase system proved effective during development. The ability to develop and test each subsystem in isolation reduced the complexity of integration and allowed design decisions in one layer to be revised without cascading changes to other layers. For example, the transition from a rule-only classification approach (used in the early prototype) to the hybrid ML/rule-based approach was implemented without requiring any changes to the database schema, API endpoints, or user interface.

The use of Celery for asynchronous video processing was a particularly important architectural decision. By separating the computationally intensive processing pipeline from the HTTP request handler, the API remained responsive under load and the frontend was able to provide meaningful progress feedback to the user during processing. This asynchronous design is consistent with industry-standard practices for systems that perform long-running background operations.

The choice of MongoDB as the metadata store was validated by the development experience. The flexible document schema accommodated the variable structure of scene metadata — particularly the optional emotion fields — without requiring schema migrations at any point during development. The JSON-to-BSON transformation was transparent, and the native Python driver for MongoDB (`pymongo`) provided a straightforward programming interface.

One area where the design could be strengthened is the modelling of the relationship between videos and scenes. The current implementation stores the video-level metadata as fields within scene documents (video_name, video_id) rather than as a separate videos collection with a formal reference relationship. While this simplifies queries that return scenes with video context, it denormalises data in a way that could create consistency issues if video-level metadata needed to be updated. A future version of the schema could introduce a dedicated videos collection with proper foreign key semantics.

### 8.4 Evaluation of the AI Component

The ML classification component achieved a scene-level test accuracy of 65.7% and a macro F1-score of 0.608 in the current v2 evaluation. This represents a practical improvement over the rule-based approach that was the sole classification mechanism in the initial prototype, but it also shows that the classifier should be treated as an assistive component rather than as an autonomous final decision-maker. The training and validation curves show strong learning on the training set, but the validation/test gap indicates that the dataset remains limited and imbalanced.

The most notable limitation of the current ML approach is the restriction of classification to a single representative frame per scene (the midpoint thumbnail). This frame-level approach cannot capture temporal dynamics: a scene in which the action begins mid-way through, or a scene that transitions between visual content types, may produce a thumbnail that is not representative of the dominant content. A future improvement would be to replace the frame-level ResNet-18 with a video-level model such as a 3D CNN or a Video Vision Transformer (ViViT), which processes multiple frames simultaneously and can model temporal motion as well as spatial appearance.

The agentic decision layer is one of the most distinctive contributions of the EditEase system. Rather than applying ML predictions unconditionally, the layer provides a principled mechanism for handling uncertainty, escalating ambiguous cases to human review, and using a rule-based fallback for genuinely low-confidence predictions. This design reflects an important principle in applied AI: that automated systems should be designed to acknowledge and communicate their own uncertainty, rather than presenting all outputs with equal confidence.

### 8.5 Limitations of the System

**Face Detection Reliability:** The Haar Cascade face detector used for emotion analysis is known to perform poorly on profile faces, partially occluded faces, and faces in low-light conditions. A more robust modern face detector such as MTCNN or a YOLO-based face detection model would improve the coverage of the emotion analysis module. The Haar Cascade was selected for its computational efficiency as a lightweight gatekeeper, but this comes at the cost of missed detections.

**Single-frame Classification:** As noted above, classifying scenes from a single midpoint thumbnail constrains the model to spatial information only and excludes temporal dynamics.

**Training Dataset Size:** The training dataset assembled during this project is substantially smaller than the large-scale datasets used in academic computer vision benchmarks. Larger and more diverse training data would likely improve the model's generalisation to footage from production contexts not represented in the current training set.

**Scalability:** The current prototype runs as a single-instance application. It does not support horizontal scaling to multiple processing workers, load-balanced API instances, or distributed database configurations. These capabilities would be required for a production deployment serving multiple concurrent users.

**Local Prototype Context:** Although Cloudinary provides cloud storage for media assets, the video processing pipeline currently runs on a single server. A fully cloud-native architecture, in which processing could be distributed across multiple serverless functions or containerised workers, would significantly improve throughput for large archives.

### 8.6 Future Improvements

The following improvements are identified as the highest-priority directions for future development:

1. **Temporal ML Model:** Replace the frame-level ResNet-18 with a video-level model (3D CNN or ViViT) to incorporate temporal information into scene classification.

2. **Enhanced Face Detection:** Replace the Haar Cascade with a deep learning-based face detector (e.g., MTCNN) to improve coverage on non-frontal and low-light faces.

3. **Cloud-Native Processing:** Deploy the Celery workers as scalable cloud functions (e.g., AWS Lambda, Google Cloud Run) to support parallel processing of multiple videos simultaneously.

4. **Active Learning Loop:** Implement a systematic process for retraining the ML classifier on newly accumulated human-reviewed labels, creating an active learning feedback cycle that progressively improves model accuracy.

5. **Expanded Scene Taxonomy:** Extend the classification taxonomy beyond the current five merged categories to support more fine-grained scene types relevant to specific production genres (e.g., sports, medical, educational content).

6. **Mobile Interface:** Optimise the frontend for mobile viewports to support on-location footage review.

### 8.7 Self-Reflection

Working on the EditEase project provided a comprehensive learning experience across a breadth of technical domains that this student had not previously encountered in a unified context. Prior to this project, experience with machine learning was primarily theoretical; the process of collecting, labelling, and using a dataset to fine-tune a ResNet-18 model and evaluate it with standard metrics provided a concrete and practical understanding of the supervised learning lifecycle that cannot be obtained through coursework alone.

The integration of the ML pipeline with the Flask API and the React frontend required confronting challenges around asynchronous processing, data format consistency, and cross-component state management that are not immediately apparent from studying each component in isolation. The decision to use Celery for background processing was made after a significant failure in an early prototype in which video processing was performed synchronously within the Flask route handler, causing the browser to time out. This failure, whilst frustrating at the time, provided a valuable lesson in the practical implications of architectural decisions.

Managing the full software development lifecycle — from initial problem analysis and literature review through design, implementation, testing, and evaluation — within the timeframe of a single academic year required careful planning and disciplined prioritisation. The Gantt chart prepared at the beginning of the project proved to be a useful reference point for monitoring progress, although several tasks took longer than estimated, requiring scope adjustments in later phases.

The project has reinforced the importance of building AI systems that acknowledge and communicate their own uncertainty. The agentic decision layer, which escalates low-confidence predictions to human review rather than applying them unconditionally, reflects a design philosophy that this student intends to carry forward into future engineering work.

---

## Conclusion

This report has presented the design, implementation, and evaluation of EditEase, an AI-assisted video scene indexing and retrieval platform. The system addresses a clearly identified gap in the tooling available to video editors and post-production teams: the absence of an integrated system that can automatically segment, classify, and index raw video footage, making it retrievable through structured metadata search rather than manual scrubbing.

The research question posed in Section 1.6 asked to what extent an AI-assisted scene indexing system can enhance the efficiency and scalability of raw video footage management. The evaluation evidence gathered in Chapter 7 supports a positive answer to this question, with appropriate limits. The ML classification model achieved 65.7% scene-level accuracy and a macro F1-score of 0.608 across five current scene categories, which is not sufficient for fully autonomous labelling but is useful for prioritising and accelerating review. The database-backed retrieval interface allows scenes to be located through targeted queries and thumbnail browsing, compared to the much slower process of manual scrubbing through raw recordings.

All ten objectives defined in Section 1.4 were achieved in the prototype implementation. The system demonstrates the viability of the incremental development approach for building complex multi-component AI systems within the scope of an individual student project. The human-in-the-loop review architecture ensures that the platform functions as a tool that supports, rather than replaces, editorial judgement.

The most significant limitations of the current implementation — single-frame classification, limited training data, and single-server deployment — define a clear roadmap for future development. The architectural foundations established by this prototype are well suited to support the extension of the system towards a temporally-aware, cloud-native production tool.

---

## Project Management Evidence

### 9.1 Project Planning

The project was planned using an incremental development strategy, with the work divided into five phases as described in Section 3.3. A Gantt chart was prepared at the beginning of the project, spanning from September 2025 to March 2026, to provide a visual representation of the planned timeline and task dependencies. The Gantt chart was reviewed at each supervisor meeting and updated to reflect actual progress.

The following phases were identified in the project plan: Requirements Analysis and System Conceptualisation (September–October 2025); Literature Review and Technology Exploration (October–November 2025); Environment Setup and Initial Pipeline Development (November 2025); Emotion Detection and Scene Classification (November–December 2025); Indexing, Database, and Search/Retrieval System (December 2025–January 2026); Integration, Testing, and Optimisation (January–February 2026); Documentation and Report Writing (February–March 2026).

### 9.2 Development Timeline

![Figure 9.1 – Project Development Gantt Chart](report_assets/figures/figure_9_1_project_development_gantt.png)
*Figure 9.1 – Project Development Gantt Chart. [CODEX-SCREENSHOT: Gantt chart spanning Sep 2025 – May 2026 with rows for: Requirements & Conceptualisation (Sep–Oct), Literature Review (Oct–Nov), Environment Setup (Nov), Pipeline Development (Nov–Dec), Emotion + Classification (Nov–Dec), Indexing/DB/Search (Dec–Jan), Integration & Testing (Jan–Feb), Frontend Polish & Cinematic UI (Feb–Apr), Documentation & Report (Feb–May). Highlight the ML-data-collection slip and the corresponding scope adjustment.]*

The actual development timeline adhered closely to the planned schedule for the early phases. The implementation of the ML classification component took longer than initially estimated due to the data collection and labelling effort required to build the training dataset. This delay was accommodated by reducing the scope of the emotion detection module, which was implemented as a prototype rather than a production-quality feature.

### 9.3 Meetings and Tracking of Progress with Supervisors

Regular fortnightly meetings were held with the project supervisor throughout the development period. These meetings provided the opportunity to discuss technical challenges, review design decisions, receive feedback on the implementation, and verify that the project was progressing in alignment with the assessment requirements.

Meeting logs were maintained throughout the project, documenting the topics discussed, the supervisor's feedback, and the actions agreed for the subsequent development period. Ten meeting logsheets are appended to this report as evidence of regular supervision.

Key milestones discussed in supervisor meetings included:

- **Logsheet 1 (October 2025):** Project scope finalised; problem domain reviewed; initial literature review targets identified.
- **Logsheet 3 (November 2025):** Literature review completed; environment setup validated; initial video handling in Python tested.
- **Logsheet 4 (November 2025):** Frame extraction and thumbnail generation milestone completed.
- **Logsheet 5 (November 2025):** Scene segmentation milestone completed using PySceneDetect; fallback strategy for zero-cut videos implemented.
- **Logsheet 6 (December 2025):** Emotion detection milestone completed using DeepFace; supervisor recommended working on multiple emotions and multiple videos.
- **Logsheet 7 (December 2025):** Full pipeline batch processing completed; Streamlit UI prototype running; supervisor noted 7 complete artefacts.
- **Logsheet 8 (December 2025):** Backend set up with MongoDB and Flask API; search and filter endpoints validated.
- **Logsheet 9 (January 2026):** Full system integration test completed; FFmpeg clip export implemented; dataset labelling process initiated.
- **Logsheet 10 (January 2026):** Dataset quality checks completed; 200-scene labelling target approached; ML training plan prepared.

### 9.4 Risk Management

The following risks were identified during the planning phase, along with the mitigation strategies applied:

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Technical issues with video processing libraries | Medium | High | Use well-established, community-supported libraries (PySceneDetect, OpenCV); allocate additional time for library evaluation |
| Insufficient labelled training data for ML | Medium | High | Begin data collection early; use the EditEase interface itself to accelerate labelling |
| Processing time exceeds acceptable limits for large files | Medium | Medium | Implement asynchronous processing with Celery from the outset; avoid synchronous processing in API routes |
| Incompatibilities between software components | Low | Medium | Use virtual environments; pin dependency versions; test integration incrementally |
| Scope creep beyond achievable prototype | Medium | Medium | Define clear objectives; defer non-essential features to the Future Improvements section |

The risk related to training data volume materialised during development, as initially anticipated. The mitigation strategy — using the EditEase review interface as a tool for systematic scene labelling — proved effective, though it required more time than estimated. The risk of scope creep was managed by deferring the implementation of collaborative multi-user workflows, advanced reporting dashboards, and mobile optimisation to the future improvements roadmap.

---

## References

Baraldi, L., Grana, C. and Cucchiara, R. (2015) 'A deep siamese network for scene detection in broadcast videos', *Proceedings of the 23rd ACM International Conference on Multimedia*, Brisbane, Australia, October 2015, pp. 1199–1202.

Deng, J., Dong, W., Socher, R., Li, L.-J., Li, K. and Fei-Fei, L. (2009) 'ImageNet: A large-scale hierarchical image database', *Proceedings of CVPR 2009*, Miami, Florida, pp. 248–255.

Ekman, P. (1992) 'An argument for basic emotions', *Cognition and Emotion*, 6(3–4), pp. 169–200.

He, K., Zhang, X., Ren, S. and Sun, J. (2016) 'Deep residual learning for image recognition', *Proceedings of CVPR 2016*, Las Vegas, Nevada, pp. 770–778.

ICO – Information Commissioner's Office (2024) *Guidance on AI and data protection (including high-risk uses such as emotion inference)*. Available at: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/ (Accessed: 23 January 2026).

ISO (2022) *ISO/IEC 27001:2022 – Information security management systems requirements*. Available at: https://www.iso.org/standard/27001 (Accessed: 23 January 2026).

Koorathota, S., Adelman, P., Cotton, K. and Sajda, P. (2021) 'Editing like humans: A contextual, multimodal framework for automated video editing', *Proceedings of CVPR Workshops*, pp. 1–9.

Lian, H., Lu, C., Li, S., Zhao, Y., Tang, C. and Zong, Y. (2023) 'A survey of deep learning-based multimodal emotion recognition: Speech, text, and face', *Entropy*, 25(1440).

Mao, M., Lee, A. and Hong, M. (2024) 'Deep learning innovations in video classification: A survey on techniques and dataset evaluations', *Electronics*, 13(2732).

MongoDB (n.d.) *Server Side Public License (SSPL)*. Available at: https://www.mongodb.com/legal/licensing/server-side-public-license (Accessed: 23 January 2026).

NIST (2025) *Digital Identity Guidelines (NIST SP 800-63-4)*. Available at: https://pages.nist.gov/800-63-4/ (Accessed: 23 January 2026).

OWASP (2023) *OWASP Top 10 API Security Risks – 2023*. Available at: https://owasp.org/API-Security/editions/2023/en/0x11-t10/ (Accessed: 23 January 2026).

Pallets/Flask (n.d.) *BSD-3-Clause License (Flask)*. Available at: https://flask.palletsprojects.com/en/stable/license/ (Accessed: 23 January 2026).

Pan, J., Fang, W., Zhang, Z., Chen, B., Zhang, Z. and Wang, S. (2024) 'Multimodal emotion recognition based on facial expressions, speech, and EEG', *IEEE Open Journal of Engineering in Medicine and Biology*, 5, pp. 396–407.

Settles, B. (2009) *Active learning literature survey*. Technical Report 1648, University of Wisconsin-Madison Department of Computer Sciences.

Alaa, T., Mongy, A., Bakr, A., Diab, M. and Gomaa, W. (2024) 'Video summarization techniques: A comprehensive review', *arXiv preprint arXiv:2410.04449*.

---

## Appendices

### Appendix A: Project Meeting Logsheets

> **[Insert all 10 signed and scanned meeting logsheets here as per the supervisor records maintained throughout the project period, October 2025 – January 2026.]**

### Appendix B: Gantt Chart

The project development Gantt chart is included in the main report as Figure 9.1.

### Appendix C: System Evaluation – Model Performance Charts

The model performance charts are included in the main report as Figures 7.1 to 7.5.

### Appendix D: System Architecture Diagrams

The system architecture, subsystem decomposition, scene detection, thumbnail extraction, database schema, data flow, and processing pipeline diagrams are included in the main report as Figures 5.1 to 5.7 and Figure 6.1.

### Appendix E: User Interface Screenshots

This appendix gathers full-resolution screenshots of every major surface of the EditEase application. Each entry includes a `[CODEX-SCREENSHOT: …]` directive describing the exact viewport, state, and elements to be captured. All images should be exported at a minimum of 1440 × 900 pixels (or 1920 × 1080 where indicated) and saved into `report_assets/screenshots/` using the filenames given in each figure caption.

**E.1 — Public / Landing**

![Figure E.1 – Landing Page Hero](report_assets/screenshots/figure_e_1_landing_hero.png)
*Figure E.1 – Landing Page Hero (Cinematic GSAP Entry). [CODEX-SCREENSHOT: Navigate to `/` while logged out. Capture the very top of the page (1920×1080) with the GSAP word-by-word reveal complete. Must show: top-bar logo + nav (Features, How it works, Sign in, Get started CTA), the hero headline ("Stop sorting footage manually"), subheading, and a primary CTA button. Disable any cookie/banner overlays before capture.]*

![Figure E.2 – Landing Page Feature Reveal Section](report_assets/screenshots/figure_e_2_landing_features.png)
*Figure E.2 – Landing Page – Feature Reveal Section. [CODEX-SCREENSHOT: Scroll to the feature grid (auto scene detection, AI classification, emotion analysis, organized library). Wait for GSAP scroll-trigger animations to settle. Capture full viewport.]*

![Figure E.3 – Landing Page Pipeline Storytelling Strip](report_assets/screenshots/figure_e_3_landing_pipeline.png)
*Figure E.3 – Landing Page – Pipeline Storytelling Strip. [CODEX-SCREENSHOT: Scroll to the pipeline storytelling section (the horizontal pipeline diagram or scroll-pinned reveal showing upload → detect → classify → organize). Capture at the moment the third stage is active.]*

![Figure E.4 – Landing Page Footer / Brand Voice](report_assets/screenshots/figure_e_4_landing_footer.png)
*Figure E.4 – Landing Page – Footer / Brand Voice. [CODEX-SCREENSHOT: Scroll to the very bottom showing the closing CTA, brand line, GitHub/contact links, and copyright. Include the last visible section above the footer.]*

**E.2 — Authentication Suite**

![Figure E.5 – Login Screen](report_assets/screenshots/figure_e_5_login.png)
*Figure E.5 – Login Screen. [CODEX-SCREENSHOT: Navigate to `/login`. Capture full viewport showing the EditEase auth card with email + password fields, "Sign in with Google" button, forgot-password link, and link to register. Leave the form empty.]*

![Figure E.6 – Register Screen with Password Strength Meter](report_assets/screenshots/figure_e_6_register.png)
*Figure E.6 – Register Screen. [CODEX-SCREENSHOT: Navigate to `/register`. Type a medium-strength password (e.g., `Editease!23`) so the zxcvbn strength meter shows the "Good" band. Capture the full card including name/email/password fields and the meter.]*

![Figure E.7 – Forgot Password Screen](report_assets/screenshots/figure_e_7_forgot_password.png)
*Figure E.7 – Forgot Password Screen. [CODEX-SCREENSHOT: Navigate to `/forgot-password`. Capture the email input + send button, with helper copy visible.]*

![Figure E.8 – Reset Password Screen](report_assets/screenshots/figure_e_8_reset_password.png)
*Figure E.8 – Reset Password Screen. [CODEX-SCREENSHOT: Navigate to `/reset-password?token=demo` (use a dev token). Capture the new-password + confirm fields and the strength meter showing on a medium password.]*

![Figure E.9 – Verify Email Screen](report_assets/screenshots/figure_e_9_verify_email.png)
*Figure E.9 – Verify Email Screen. [CODEX-SCREENSHOT: Navigate to `/verify-email` in the post-registration state showing the "Check your inbox" confirmation message and the resend-link control.]*

![Figure E.10 – Google OAuth Sign-In Flow](report_assets/screenshots/figure_e_10_google_oauth.png)
*Figure E.10 – Google OAuth Sign-In Flow. [CODEX-SCREENSHOT: From `/login`, click "Sign in with Google" and capture the Google account chooser popup (or the in-app handoff state) alongside the underlying Login page.]*

**E.3 — App Shell**

![Figure E.11 – App Shell, Editor Sidebar](report_assets/screenshots/figure_e_11_appshell_editor.png)
*Figure E.11 – App Shell – Authenticated Sidebar (Editor View). [CODEX-SCREENSHOT: Log in as an editor. Open `/dashboard`. Capture the full sidebar from logo to user avatar at the bottom, showing the editor-only nav items (Dashboard, Upload, Job Monitor, Organized Videos, Inspector, Editor, Settings). Admin items must NOT be visible.]*

![Figure E.12 – App Shell, Admin Sidebar](report_assets/screenshots/figure_e_12_appshell_admin.png)
*Figure E.12 – App Shell – Authenticated Sidebar (Admin View). [CODEX-SCREENSHOT: Log in as admin. Open `/dashboard`. Capture the sidebar showing the editor items plus User Management and Video Assignments. Highlight the admin items visually if possible.]*

**E.4 — Guided Tour**

![Figure E.13 – Tour Step 1 (Dashboard Welcome)](report_assets/screenshots/figure_e_13_tour_step1.png)
*Figure E.13 – Tour Guide – Step 1 (Dashboard Welcome Overlay). [CODEX-SCREENSHOT: Trigger the tour from Settings → Replay Tour on a first-time-style account. Capture the Joyride overlay on the Dashboard with the spotlight on the bento analytics strip and the tooltip copy visible. Include the Next/Skip buttons.]*

![Figure E.14 – Tour Step 2 (Upload Walkthrough)](report_assets/screenshots/figure_e_14_tour_step2.png)
*Figure E.14 – Tour Guide – Step 2 (Upload Walkthrough). [CODEX-SCREENSHOT: Advance the tour to the Upload page. Spotlight on the drag-and-drop zone with the tooltip pointing to it and copy visible.]*

![Figure E.15 – Tour Step 3 (Inspector Walkthrough)](report_assets/screenshots/figure_e_15_tour_step3.png)
*Figure E.15 – Tour Guide – Step 3 (Inspector Panel Walkthrough). [CODEX-SCREENSHOT: Advance the tour to a Dashboard with the Inspector drawer open on a selected card. Spotlight on the confidence + review controls.]*

**E.5 — Dashboard**

![Figure E.16 – Dashboard Bento Layout](report_assets/screenshots/figure_e_16_dashboard_bento.png)
*Figure E.16 – Dashboard – Bento Layout with Recharts. [CODEX-SCREENSHOT: Open `/dashboard` with at least 20 scenes across multiple categories already in the database for the test user. Capture only the top analytics strip showing the category bar chart, throughput line chart, review-burden area chart, and total-scenes stat card.]*

![Figure E.17 – AI Metadata Confusion Matrix Card](report_assets/screenshots/figure_e_17_dashboard_confusion.png)
*Figure E.17 – Dashboard – AI Metadata Confusion Matrix Card. [CODEX-SCREENSHOT: Zoom into the confusion-matrix card on the Dashboard (5×5 grid for the v2 classes). Make sure cell values are readable.]*

![Figure E.18 – Personal Activity Charts](report_assets/screenshots/figure_e_18_dashboard_personal.png)
*Figure E.18 – Dashboard – Personal Activity Charts. [CODEX-SCREENSHOT: Capture the "Your activity" section: charts scoped to the current user (uploads this week, scenes reviewed, pending uncertain count). Confirm only the current user's data is shown.]*

![Figure E.19 – Verification Border on Reviewed Cards](report_assets/screenshots/figure_e_19_verification_border.png)
*Figure E.19 – Dashboard – Verification Border on Reviewed Cards. [CODEX-SCREENSHOT: Filter the clip grid to "All". Capture a 3×3 patch of cards mixing verified (with verification-border) and unreviewed cards, and at least one uncertain card with the contrasting accent border. Annotate or zoom so the border differences are clearly visible.]*

**E.6 — Upload Flow**

![Figure E.20 – Upload Drag-and-Drop Zone](report_assets/screenshots/figure_e_20_upload_dropzone.png)
*Figure E.20 – Upload Page – Drag-and-Drop Zone. [CODEX-SCREENSHOT: Navigate to `/upload` in the empty state. Capture the dropzone, file picker button, accepted formats text, and the "Auto-organize when finished" toggle visible.]*

![Figure E.21 – Live Progress Feed](report_assets/screenshots/figure_e_21_upload_progress.png)
*Figure E.21 – Upload Page – Live Progress Feed. [CODEX-SCREENSHOT: Upload a short test MP4 and capture the progress feed mid-pipeline, with at least three completed stages ("Cloud upload complete", "Detected 7 scenes", "Classifying scene 3/7") and one in-progress stage with a spinner.]*

![Figure E.22 – Auto-Organize Toggle](report_assets/screenshots/figure_e_22_upload_autoorganize.png)
*Figure E.22 – Upload Page – Auto-Organize Toggle. [CODEX-SCREENSHOT: Zoom on the auto-organize control set to ON and the helper text describing what it will do. Capture also the "Auto-Organize Now" manual button.]*

**E.7 — Job Monitor**

![Figure E.23 – Active Task List](report_assets/screenshots/figure_e_23_jobmonitor_list.png)
*Figure E.23 – Job Monitor – Active Task List. [CODEX-SCREENSHOT: Navigate to `/jobs`. Capture the table/list view of active and recent processing tasks with columns: video name, started at, current stage, progress %, status badge.]*

![Figure E.24 – Per-Stage Progress Timeline](report_assets/screenshots/figure_e_24_jobmonitor_timeline.png)
*Figure E.24 – Job Monitor – Per-Stage Progress Timeline. [CODEX-SCREENSHOT: Expand a single in-progress task. Capture the per-stage timeline showing checkmarks on completed stages and the current one highlighted.]*

**E.8 — Inspector**

![Figure E.25 – Inspector Confidence and Emotion Detail](report_assets/screenshots/figure_e_25_inspector_confidence.png)
*Figure E.25 – Inspector Panel – Confidence and Emotion Detail. [CODEX-SCREENSHOT: From the Dashboard, click a card to open the Inspector. Capture the drawer with thumbnail at top, then metadata (label, duration, ml_confidence, rb_confidence, fused decision), then the emotion timeline strip. Choose a scene that has an emotion timeline so the strip is populated.]*

![Figure E.26 – Inspector Review Status Controls](report_assets/screenshots/figure_e_26_inspector_review.png)
*Figure E.26 – Inspector Panel – Review Status Controls. [CODEX-SCREENSHOT: Scroll the Inspector to the review controls: label override dropdown, "Mark reviewed", "Flag uncertain", and Save. Show one of the controls in a focused/active state.]*

![Figure E.27 – Inspector Reviewer Notes](report_assets/screenshots/figure_e_27_inspector_notes.png)
*Figure E.27 – Inspector Panel – Reviewer Notes. [CODEX-SCREENSHOT: Capture the reviewer-notes textarea with example text written ("Cut at 0:14 — speaker glances off camera."). Show the Save button and "Saved just now" confirmation.]*

**E.9 — Clip Grid**

![Figure E.28 – Filter Sidebar Expanded](report_assets/screenshots/figure_e_28_grid_filters.png)
*Figure E.28 – Clip Grid – Filter Sidebar Expanded. [CODEX-SCREENSHOT: Open the filter sidebar with multiple filters active (e.g., scene_label = Testimonial, emotion = neutral, review_status = unreviewed). Capture the sidebar + the filtered grid.]*

![Figure E.29 – Card Metadata Overlay](report_assets/screenshots/figure_e_29_grid_card_overlay.png)
*Figure E.29 – Clip Grid – Card Metadata Overlay. [CODEX-SCREENSHOT: Hover a clip card to reveal the metadata overlay (label, duration, confidence, emotion). Capture only the card with its overlay visible.]*

**E.10 — Organized Videos**

![Figure E.30 – Category Browser](report_assets/screenshots/figure_e_30_organized_categories.png)
*Figure E.30 – Organized Videos – Category Browser. [CODEX-SCREENSHOT: Navigate to `/organized` after running auto-organize. Capture the full page showing each category (B-Roll, Testimonial, Other, Audience Reaction, Establishing Shot) as a collapsible section with member thumbnails.]*

![Figure E.31 – Category ZIP Download](report_assets/screenshots/figure_e_31_organized_zip.png)
*Figure E.31 – Organized Videos – Category ZIP Download. [CODEX-SCREENSHOT: Hover a category's "Download ZIP" button and trigger the download. Capture the moment the browser download bar appears at the bottom showing the `{user}_{category}.zip` filename.]*

**E.11 — Editor & Assignments**

![Figure E.32 – Editor View Clip Preview](report_assets/screenshots/figure_e_32_editor_view.png)
*Figure E.32 – Editor View – Selected Clip Preview. [CODEX-SCREENSHOT: Navigate to `/editor` with a clip selected. Capture the focused preview surface with playback controls, scene metadata strip, and back/next clip arrows.]*

![Figure E.33 – Video Assignments Queue](report_assets/screenshots/figure_e_33_video_assignments.png)
*Figure E.33 – Video Assignments – Editor Review Queue. [CODEX-SCREENSHOT: As admin, navigate to `/admin/assignments`. Capture the table mapping editors to uploads with assign/unassign controls and per-editor counts.]*

**E.12 — Settings & Invites**

![Figure E.34 – Settings Account Page](report_assets/screenshots/figure_e_34_settings_account.png)
*Figure E.34 – Settings – Account Page. [CODEX-SCREENSHOT: Navigate to `/settings`. Capture the account section: display name, email (read-only), password change form, "Replay Tour" link, delete account control.]*

![Figure E.35 – Settings Theme and Preferences](report_assets/screenshots/figure_e_35_settings_preferences.png)
*Figure E.35 – Settings – Theme and Preferences. [CODEX-SCREENSHOT: Scroll the Settings page to the preferences block: theme toggle (light/dark), reduced-motion toggle, notification preferences. Show the dark theme active.]*

![Figure E.36 – Invite Acceptance](report_assets/screenshots/figure_e_36_invite.png)
*Figure E.36 – Invite Flow – Token Acceptance Screen. [CODEX-SCREENSHOT: Navigate to `/invite?token=demo`. Capture the invite acceptance card showing the inviting user, the assigned role, and the Accept button.]*

**E.13 — Admin**

![Figure E.37 – User Management Table](report_assets/screenshots/figure_e_37_admin_users.png)
*Figure E.37 – Admin – User Management Table. [CODEX-SCREENSHOT: As admin, navigate to `/admin/users`. Capture the user table with columns: name, email, role, created, last active, actions. Show a mix of editor and admin roles.]*

![Figure E.38 – Role Change Confirmation](report_assets/screenshots/figure_e_38_admin_role_modal.png)
*Figure E.38 – Admin – Role Change Confirmation Modal. [CODEX-SCREENSHOT: Click "Change role" on a user row and capture the confirmation modal showing the from/to role and the Confirm/Cancel actions.]*

![Figure E.39 – Video Assignments Dashboard](report_assets/screenshots/figure_e_39_admin_assignments.png)
*Figure E.39 – Admin – Video Assignments Dashboard. [CODEX-SCREENSHOT: Navigate to `/admin/assignments`. Capture the per-editor load chart at the top plus the assignment table beneath it.]*

**E.14 — Cross-Cutting**

![Figure E.40 – Toast Notification System](report_assets/screenshots/figure_e_40_toasts.png)
*Figure E.40 – Toast Notification System (Success, Error, Info). [CODEX-SCREENSHOT: Trigger three toast types in quick succession (success on save, info on auto-organize start, error on a forced 500). Capture the stacked toasts at the bottom-right of the viewport.]*

![Figure E.41 – Axios Interceptor Session Expiry](report_assets/screenshots/figure_e_41_session_expiry.png)
*Figure E.41 – Axios Interceptor – Session Expiry Handling. [CODEX-SCREENSHOT: Simulate a 401 (manually clear the auth token in devtools then trigger any API call). Capture the "Session expired" toast and the redirect to /login that follows.]*

![Figure E.42 – Mobile Landing](report_assets/screenshots/figure_e_42_mobile_landing.png)
*Figure E.42 – Mobile Viewport – Landing Page Responsive View. [CODEX-SCREENSHOT: Resize Chrome to 414×896 (iPhone 11). Capture the landing hero in mobile layout — verify the nav collapses to a hamburger and the headline reflows correctly.]*

![Figure E.43 – Mobile Dashboard](report_assets/screenshots/figure_e_43_mobile_dashboard.png)
*Figure E.43 – Mobile Viewport – Dashboard Responsive View. [CODEX-SCREENSHOT: At 414×896, navigate to `/dashboard` (logged in). Capture the stacked bento cards and the clip grid in single-column mode. Sidebar should be in collapsed/hamburger state.]*

> **Note for the editor:** every `[CODEX-SCREENSHOT: …]` directive above is intended to be consumed by an automated screenshot pass. Replace the placeholder PNG files in `report_assets/screenshots/` with real captures matching the description, then delete the directive from the caption before final submission. File paths and figure numbers must not change.

---

*End of Report*
