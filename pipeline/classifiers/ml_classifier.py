from pipeline.classifiers.base_classifier import BaseClassifier
from pipeline.classifiers.rule_based_classifier import RuleBasedClassifier
from utils.logger import setup_logger

logger = setup_logger("ml_classifier")

class MLClassifier(BaseClassifier):
    """
    Future PyTorch/ML model classifier. 
    Currently Acts as a stub that loads empty model and falls back to rules.
    """
    def __init__(self):
        # TODO: Load PyTorch model, transforms, and class labels here
        logger.info("Initializing ML scene classifier stub...")
        self.fallback = RuleBasedClassifier()

    def classify(self, video_path: str, start_sec: float, end_sec: float, thumbnail_path: str) -> tuple[str, float, dict]:
        # TODO: Run frame through ResNet/ViT and get logits
        # For now, fallback to heuristics
        logger.debug("ML Classifier not yet trained -> falling back to RuleBasedClassifier")
        
        scene_label, conf, debug = self.fallback.classify(video_path, start_sec, end_sec, thumbnail_path)
        debug["classifier_used"] = "ml_stub_fallback"
        return scene_label, conf, debug
