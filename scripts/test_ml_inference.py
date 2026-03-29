import os
import sys

# Ensure d:\EDITEASE is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.classifiers.ml_classifier import MLClassifier
from utils.logger import setup_logger
import config

logger = setup_logger("test_ml_inference")

def main():
    logger.info("Initializing MLClassifier for test...")
    classifier = MLClassifier()
    
    if classifier.model is None:
        logger.error("ML model failed to load. Are the .pth and label_encoder.json present?")
        return
        
    logger.info(f"Model loaded successfully with {len(classifier.idx_to_label)} labels.")
    
    # Let's find a thumbnail to test on
    data_dir = os.path.join(config.BASE_DIR, "datasets", "scene_type", "v1")
    annotations_file = os.path.join(data_dir, "annotations.jsonl")
    
    if not os.path.exists(annotations_file):
        logger.error(f"Cannot find annotations at {annotations_file}")
        return
        
    import json
    test_image = None
    with open(annotations_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            frames = data.get("frames", [])
            if frames and data.get("split") == "test":
                test_image = os.path.join(config.BASE_DIR, frames[0])
                break
                
    if not test_image or not os.path.exists(test_image):
        logger.warning("No valid test image found in annotations to run inference on.")
        return
        
    logger.info(f"Running inference on test image: {test_image}")
    scene_label, conf, debug = classifier.classify("dummy_video.mp4", 0.0, 5.0, test_image)
    
    logger.info(f"Predicted Scene Label: {scene_label}")
    logger.info(f"Confidence: {conf:.4f}")
    logger.info(f"Debug info: {debug}")
    
    if debug.get("classifier_used") == "ml_pytorch":
        logger.info("✅ ML inference succeeded without falling back.")
    else:
        logger.warning(f"⚠️ Inference fell back to rule-based: {debug.get('classifier_used')}")

if __name__ == "__main__":
    main()
