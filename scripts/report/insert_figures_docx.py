"""
Rebuild Final_Project_Report.docx with new image files swapped in.
Works at the ZIP level — no XML manipulation — guaranteed MS Word compatible.
"""

import os, shutil, zipfile

SRC = "Final_Project_Report_backup.docx"
DST = "Final_Project_Report.docx"
FIG = "report_assets/figures"

# image1..image16 (in zip) → generated figure PNG
# Mapping derived from rId order in document.xml (rId9..rId24)
IMAGE_TO_FIGURE = {
    "word/media/image1.png":  "figure_5_1_system_architecture.png",
    "word/media/image2.png":  "figure_5_2_functional_decomposition.png",
    "word/media/image3.png":  "figure_5_3_scene_detection.png",
    "word/media/image4.png":  "figure_5_4_thumbnail_extraction_process.png",
    "word/media/image5.png":  "figure_5_5_metadata_database_schema.png",
    "word/media/image6.png":  "figure_5_6_user_interface_layout.png",
    "word/media/image7.png":  "figure_5_7_data_flow_diagram.png",
    "word/media/image8.png":  "figure_6_1_video_processing_pipeline.png",
    "word/media/image9.png":  "figure_6_2_resnet_adaptation.png",
    "word/media/image10.png": "figure_6_3_scene_metadata_document.png",
    "word/media/image11.png": "figure_7_1_training_validation_accuracy.png",
    "word/media/image12.png": "figure_7_2_training_validation_loss.png",
    "word/media/image13.png": "figure_7_3_per_class_metrics.png",
    "word/media/image14.png": "figure_7_4_dataset_class_distribution.png",
    "word/media/image15.png": "figure_7_5_confusion_matrix.png",
    "word/media/image16.png": "figure_9_1_project_development_gantt.png",
}

if not os.path.exists(SRC):
    raise SystemExit(f"Backup {SRC} not found")

# Read replacement bytes
new_bytes = {}
for member, fig in IMAGE_TO_FIGURE.items():
    path = os.path.join(FIG, fig)
    if not os.path.exists(path):
        print(f"  [MISS] {fig} not found — keeping original {member}")
        continue
    with open(path, "rb") as f:
        new_bytes[member] = f.read()
    print(f"  [LOAD] {member:30s} ← {fig} ({len(new_bytes[member])//1024} KB)")

# Rebuild the zip
TMP = DST + ".tmp"
with zipfile.ZipFile(SRC, 'r') as zin:
    with zipfile.ZipFile(TMP, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename in new_bytes:
                zout.writestr(item, new_bytes[item.filename])
                print(f"  [SWAP] {item.filename}")
            else:
                # Copy verbatim, preserving original compression/metadata
                data = zin.read(item.filename)
                zout.writestr(item, data)

os.replace(TMP, DST)
print(f"\nWrote {DST}  ({os.path.getsize(DST)//1024} KB)")
