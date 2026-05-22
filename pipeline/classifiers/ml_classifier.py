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

# ---------------------------------------------------------------------------
# Per-class confidence thresholds
#
# Why: a single global threshold (0.60) is too blunt. Some scene types are
# inherently hard to separate (presenter vs testimonial) and need a tighter
# gate; others (text_slide, screen_recording) are visually distinct and can
# afford a looser gate.
#
# Tune these values as you accumulate labelled data. Start conservative and
# relax when you see that a class rarely needs rule-based correction.
# ---------------------------------------------------------------------------
CLASS_THRESHOLDS = {
    "testimonial"      : 0.65,
    "presenter"        : 0.70,   # easily confused with testimonial
    "audience_reaction": 0.72,
    "text_slide"       : 0.52,   # highly distinctive visually
    "screen_recording" : 0.52,
    "b-roll"           : 0.60,
    "establishing_shot": 0.60,
}
# Fallback threshold for any label not listed above (e.g. if the model was
# retrained with new classes that haven't been tuned yet).
DEFAULT_THRESHOLD = 0.62


class MLClassifier(BaseClassifier):
    """
    PyTorch/ML model classifier.
    Loads model, runs inference on thumbnail.
    Falls back to RuleBasedClassifier when:
      - model file is missing
      - inference throws an exception
      - per-class confidence threshold is not met (and rule-based is more confident)
    """

    def __init__(self):
        logger.info("Initializing ML scene classifier…")
        self.fallback = RuleBasedClassifier()
        self.device   = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model    = None
        self.transform = None
        self.idx_to_label: dict[str, str] = {}

        models_dir    = os.path.join(config.BASE_DIR, "pipeline", "models")
        model_path    = os.path.join(models_dir, "scene_classifier.pth")
        encoder_path  = os.path.join(models_dir, "label_encoder.json")

        try:
            if os.path.exists(encoder_path):
                with open(encoder_path, "r") as f:
                    self.idx_to_label = json.load(f)

            if os.path.exists(model_path) and self.idx_to_label:
                self.model = models.resnet18(weights=None)
                num_ftrs   = self.model.fc.in_features
                self.model.fc = nn.Linear(num_ftrs, len(self.idx_to_label))
                self.model.load_state_dict(
                    torch.load(model_path, map_location=self.device, weights_only=True)
                )
                self.model.to(self.device)
                self.model.eval()

                self.transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std =[0.229, 0.224, 0.225],
                    ),
                ])
                logger.info("ML model loaded successfully (device=%s).", self.device)
            else:
                logger.warning(
                    "Model or encoder not found at %s — run train_scene_classifier.py first.",
                    models_dir,
                )

        except Exception as exc:
            logger.error("Failed to load ML model: %s", exc)
            self.model = None

    # ------------------------------------------------------------------
    def prepare_image_tensor(self, thumbnail_path: str) -> torch.Tensor:
        """Load and transform a thumbnail into the model input tensor."""
        if self.transform is None:
            raise RuntimeError("ML transform is unavailable because the model did not load")
        if not thumbnail_path or not os.path.exists(thumbnail_path):
            raise FileNotFoundError(f"Thumbnail not found: {thumbnail_path}")

        image = Image.open(thumbnail_path).convert("RGB")
        return self.transform(image).unsqueeze(0).to(self.device)  # type: ignore[operator]

    # ------------------------------------------------------------------
    def predict_thumbnail(self, thumbnail_path: str) -> tuple[str, float, dict]:
        """
        Run raw ML inference for a thumbnail without rule-based fallback.

        This keeps model-quality tests focused on the PyTorch classifier rather
        than blending model predictions with the rule-based fallback path.
        """
        if self.model is None:
            raise RuntimeError("ML model is unavailable")

        input_tensor = self.prepare_image_tensor(thumbnail_path)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probs   = torch.nn.functional.softmax(outputs, dim=1)
            conf_t, predicted = torch.max(probs, 1)

        pred_idx    = str(predicted.item())
        scene_label = self.idx_to_label.get(pred_idx, "other")
        ml_conf     = float(conf_t.item())
        all_probs = {
            self.idx_to_label.get(str(i), str(i)): round(float(probs[0][i].item()), 4)
            for i in range(probs.shape[1])
        }

        return scene_label, ml_conf, {
            "ml_conf"        : round(ml_conf, 4),
            "all_class_probs": all_probs,
        }

    # ------------------------------------------------------------------
    def classify(
        self,
        video_path: str,
        start_sec: float,
        end_sec: float,
        thumbnail_path: str,
    ) -> tuple[str, float, dict]:

        # ── No model available ──────────────────────────────────────────
        if self.model is None or not thumbnail_path or not os.path.exists(thumbnail_path):
            logger.debug("ML model unavailable — falling back to RuleBasedClassifier.")
            label, conf, debug = self.fallback.classify(video_path, start_sec, end_sec, thumbnail_path)
            debug["classifier_used"] = "rule_based_no_model"
            return label, conf, debug

        # ── Run inference ───────────────────────────────────────────────
        try:
            scene_label, ml_conf, ml_debug = self.predict_thumbnail(thumbnail_path)

            # ── Per-class threshold check ────────────────────────────────
            threshold = CLASS_THRESHOLDS.get(scene_label, DEFAULT_THRESHOLD)

            if ml_conf < threshold:
                rb_label, rb_conf, rb_debug = self.fallback.classify(
                    video_path, start_sec, end_sec, thumbnail_path
                )
                rb_debug["classifier_used"] = "rule_based_low_conf_fallback"
                rb_debug["ml_label"]        = scene_label
                rb_debug["ml_conf"]         = round(ml_conf, 4)
                rb_debug["ml_threshold"]    = threshold
                logger.debug(
                    "ML conf %.3f < threshold %.2f for '%s' — using rule-based (%.3f).",
                    ml_conf, threshold, scene_label, rb_conf,
                )
                return rb_label, rb_conf, rb_debug

            # ── ML wins ─────────────────────────────────────────────────
            debug = {
                "classifier_used" : "ml_pytorch",
                "ml_conf"         : round(ml_conf, 4),
                "ml_threshold"    : threshold,
                "all_class_probs" : ml_debug["all_class_probs"],
            }
            return scene_label, ml_conf, debug

        except Exception as exc:
            logger.error("Inference error: %s", exc)
            label, conf, debug = self.fallback.classify(video_path, start_sec, end_sec, thumbnail_path)
            debug["classifier_used"] = "rule_based_error_fallback"
            return label, conf, debug
