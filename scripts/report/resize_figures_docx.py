"""
Resize each inline shape in Final_Project_Report.docx to match the actual
aspect ratio of its replaced image.
"""

import os
from docx import Document
from docx.shared import Inches
from PIL import Image

DOCX = "Final_Project_Report.docx"
FIG  = "report_assets/figures"

# Per-figure target width in inches.  Word's printable area = ~6.5"
FIGURES = [
    ("figure_5_1_system_architecture.png",         6.5),
    ("figure_5_2_functional_decomposition.png",    6.5),
    ("figure_5_3_scene_detection.png",             6.5),
    ("figure_5_4_thumbnail_extraction_process.png",6.5),
    ("figure_5_5_metadata_database_schema.png",    6.5),
    ("figure_5_6_user_interface_layout.png",       6.0),
    ("figure_5_7_data_flow_diagram.png",           6.5),
    ("figure_6_1_video_processing_pipeline.png",   6.5),
    ("figure_6_2_resnet_adaptation.png",           6.5),
    ("figure_6_3_scene_metadata_document.png",     5.5),
    ("figure_7_1_training_validation_accuracy.png",6.0),
    ("figure_7_2_training_validation_loss.png",    6.0),
    ("figure_7_3_per_class_metrics.png",           6.5),
    ("figure_7_4_dataset_class_distribution.png",  6.0),
    ("figure_7_5_confusion_matrix.png",            5.0),
    ("figure_9_1_project_development_gantt.png",   6.5),
]

doc = Document(DOCX)
shapes = doc.inline_shapes

if len(shapes) != len(FIGURES):
    raise SystemExit(f"Shape/figure count mismatch: {len(shapes)} vs {len(FIGURES)}")

for i, (shape, (fname, target_w)) in enumerate(zip(shapes, FIGURES)):
    path = os.path.join(FIG, fname)
    if not os.path.exists(path):
        print(f"  [SKIP] {fname} missing")
        continue
    with Image.open(path) as im:
        w_px, h_px = im.size

    aspect = h_px / w_px
    new_h = target_w * aspect

    # Cap height so it fits on a page (~8 inches)
    if new_h > 8.0:
        new_h = 8.0
        target_w = new_h / aspect

    shape.width  = Inches(target_w)
    shape.height = Inches(new_h)
    print(f"  Shape {i}: {fname:50s} → {target_w:.2f}\" × {new_h:.2f}\"")

doc.save(DOCX)
print(f"\nSaved → {DOCX}")
