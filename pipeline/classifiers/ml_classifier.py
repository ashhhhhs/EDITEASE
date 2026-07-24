from pipeline.classifiers.base_classifier import BaseClassifier
from pipeline.classifiers.rule_based_classifier import RuleBasedClassifier
from utils.logger import setup_logger
import os
import json
import torch
from PIL import Image
import config
from pipeline.classifiers.scene_model import (
    MODELS_DIR,
    build_scene_model,
    inference_transform,
    model_paths,
)

logger = setup_logger("ml_classifier")

# ---------------------------------------------------------------------------
# Per-class confidence thresholds
#
# Why: a single global threshold (0.60) is too blunt. Audience reactions are
# easily confused with b-roll group shots, so they get a tighter gate;
# testimonial / b-roll / establishing_shot are distinctive enough to use a
# looser threshold. Tune as labelled data accumulates.
# ---------------------------------------------------------------------------
CLASS_THRESHOLDS = {
    "testimonial"      : 0.65,
    "audience_reaction": 0.72,
    "b-roll"           : 0.60,
    "establishing_shot": 0.60,
    "other"            : 0.62,
}
# Fallback threshold for any label not listed above (e.g. if the model was
# retrained with new classes that haven't been tuned yet).
DEFAULT_THRESHOLD = 0.62

# Classes the ML model may still emit because it was trained on the old label
# set, but that we no longer support. When the ML predicts one of these, skip
# it entirely and fall back to the rule-based classifier.
RETIRED_LABELS = {"presenter", "text_slide", "screen_recording"}


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

        # Architecture, label order and file layout all come from scene_model so
        # training and inference cannot drift apart. They previously had, badly:
        # a freshly trained checkpoint would not load at all.
        model_path, encoder_path = model_paths(config.SCENE_MODEL_VERSION)
        models_dir = MODELS_DIR

        try:
            if os.path.exists(encoder_path):
                with open(encoder_path, "r") as f:
                    self.idx_to_label = json.load(f)

            if os.path.exists(model_path) and self.idx_to_label:
                self.model = build_scene_model(len(self.idx_to_label), pretrained=False)
                ckpt = torch.load(model_path, map_location=self.device, weights_only=False)
                state_dict = ckpt.get("model_state_dict", ckpt)
                self.model.load_state_dict(state_dict)
                self.model.to(self.device)
                self.model.eval()

                self.transform = inference_transform()
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
        features: dict | None = None,
        raw_signals: dict | None = None,
    ) -> tuple[str, float, dict]:

        # ── No model available ──────────────────────────────────────────
        if self.model is None or not thumbnail_path or not os.path.exists(thumbnail_path):
            logger.debug("ML model unavailable — falling back to RuleBasedClassifier.")
            label, conf, debug = self.fallback.classify(
                video_path, start_sec, end_sec, thumbnail_path,
                features=features, raw_signals=raw_signals,
            )
            debug["classifier_used"] = "rule_based_no_model"
            return label, conf, debug

        # ── Run inference ───────────────────────────────────────────────
        try:
            scene_label, ml_conf, ml_debug = self.predict_thumbnail(thumbnail_path)

            # ── Retired-label override ───────────────────────────────────
            # The ML model still predicts the old class set; ignore any
            # prediction that maps to a class we no longer support.
            if scene_label in RETIRED_LABELS:
                rb_label, rb_conf, rb_debug = self.fallback.classify(
                    video_path, start_sec, end_sec, thumbnail_path,
                    features=features, raw_signals=raw_signals,
                )
                rb_debug["classifier_used"] = "rule_based_retired_label"
                rb_debug["ml_label"]        = scene_label
                rb_debug["ml_conf"]         = round(ml_conf, 4)
                logger.debug(
                    "ML predicted retired label '%s' (%.3f) — using rule-based (%s, %.3f).",
                    scene_label, ml_conf, rb_label, rb_conf,
                )
                return rb_label, rb_conf, rb_debug

            # ── Per-class threshold check ────────────────────────────────
            threshold = CLASS_THRESHOLDS.get(scene_label, DEFAULT_THRESHOLD)

            if ml_conf < threshold:
                rb_label, rb_conf, rb_debug = self.fallback.classify(
                    video_path, start_sec, end_sec, thumbnail_path,
                    features=features, raw_signals=raw_signals,
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
            # Carry the scene's feature vector even though the rule-based path did
            # not run. Without this the retraining fields stay empty for exactly
            # the scenes the model is most confident about, so a later human
            # correction on one of them contributes nothing to recalibration.
            if features:
                debug["normalised_features"] = {k: round(float(v), 4) for k, v in features.items()}
                debug["feature_vector_for_training"] = {
                    k: round(float(v), 6) for k, v in features.items()
                }
            if raw_signals:
                debug["raw_signals"] = raw_signals
            return scene_label, ml_conf, debug

        except Exception as exc:
            logger.error("Inference error: %s", exc)
            label, conf, debug = self.fallback.classify(
                video_path, start_sec, end_sec, thumbnail_path,
                features=features, raw_signals=raw_signals,
            )
            debug["classifier_used"] = "rule_based_error_fallback"
            return label, conf, debug
