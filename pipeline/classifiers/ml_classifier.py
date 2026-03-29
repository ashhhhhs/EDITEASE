from pipeline.classifiers.base_classifier import BaseClassifier
from pipeline.classifiers.rule_based_classifier import RuleBasedClassifier
from utils.logger import setup_logger
import os
import json
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import config

logger = setup_logger("ml_classifier")

class MLClassifier(BaseClassifier):
    """
    PyTorch/ML model classifier. 
    Loads model, runs inference on thumbnail, falls back to rules if failed or low conf.
    """
    def __init__(self):
        logger.info("Initializing ML scene classifier...")
        self.fallback = RuleBasedClassifier()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.idx_to_label = {}
        
        models_dir = os.path.join(config.BASE_DIR, "pipeline", "models")
        model_path = os.path.join(models_dir, "scene_classifier.pth")
        encoder_path = os.path.join(models_dir, "label_encoder.json")
        
        try:
            if os.path.exists(encoder_path):
                with open(encoder_path, "r") as f:
                    self.idx_to_label = json.load(f)
                    
            if os.path.exists(model_path) and self.idx_to_label:
                self.model = models.resnet18(pretrained=False)
                num_ftrs = self.model.fc.in_features
                self.model.fc = nn.Linear(num_ftrs, len(self.idx_to_label))
                self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
                self.model.to(self.device)
                self.model.eval()
                
                self.transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                ])
                logger.info("Successfully loaded PyTorch ML model.")
            else:
                logger.warning("Model paths not found. Ensure train_scene_classifier.py is run.")
                
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            self.model = None

    def classify(self, video_path: str, start_sec: float, end_sec: float, thumbnail_path: str) -> tuple[str, float, dict]:
        if self.model is None or not thumbnail_path or not os.path.exists(thumbnail_path):
            logger.debug("Falling back to RuleBasedClassifier")
            scene_label, conf, debug = self.fallback.classify(video_path, start_sec, end_sec, thumbnail_path)
            debug["classifier_used"] = "rule_based_fallback"
            return scene_label, conf, debug
            
        try:
            image = Image.open(thumbnail_path).convert("RGB")
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                conf, predicted = torch.max(probs, 1)
                
            pred_idx = str(predicted.item())
            scene_label = self.idx_to_label.get(pred_idx, "other")
            
            # Use fallback if confidence is too low
            if conf.item() < 0.6:
                lb, fallback_conf, debug = self.fallback.classify(video_path, start_sec, end_sec, thumbnail_path)
                if fallback_conf > conf.item():
                    debug["classifier_used"] = "rule_based_low_conf_fallback"
                    return lb, fallback_conf, debug
                    
            debug = {"classifier_used": "ml_pytorch", "ml_conf": conf.item()}
            return scene_label, conf.item(), debug
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            scene_label, conf, debug = self.fallback.classify(video_path, start_sec, end_sec, thumbnail_path)
            debug["classifier_used"] = "rule_based_error_fallback"
            return scene_label, conf, debug
