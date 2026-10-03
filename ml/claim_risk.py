"""Shared claim-risk (review-triage) model: feature construction + inference.

This module is the SINGLE source of truth for the feature vector used by BOTH
training (ml/train_claim_risk_model.py) and live inference (backend/main.py
via predict_claim_risk). If the two ever drift, holdout metrics would no
longer describe production predictions, so feature logic lives here only.

The trained model is a CALIBRATED binary classifier:
    output  = P(claim is officer-verified INCONSISTENT), in [0, 1]
and the final review category is read from that calibrated probability.
The damage difference is only ONE learned input feature; no hardcoded
difference thresholds decide the final review status.

Purpose guardrails (shared with the training script):
  * Triage for a human officer only.
  * Never used to auto-approve, auto-reject, or calculate a PMFBY payout.
  * If the model/metadata is missing or loading fails, we return an explicit
    MODEL_NOT_READY result - we never pretend an ML result exists and never
    silently fall back to the old rule-based final decision.
"""
import json
import os
import sqlite3
from pathlib import Path

import joblib
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "claims.db"
MODEL_DIR = BASE_DIR / "ml" / "model"
MODEL_PATH = MODEL_DIR / "claim_risk_model.joblib"
FEATURES_PATH = MODEL_DIR / "claim_risk_features.json"
MODEL_NAME = "claim_risk_model"
DEMO_MODEL_PATH = MODEL_DIR / "claim_risk_demo_model.joblib"
DEMO_FEATURES_PATH = MODEL_DIR / "claim_risk_demo_features.json"
DEMO_MODEL_NAME = "claim_risk_demo_model"

MINIMUM_REVIEWED_CLAIMS = 200
MINIMUM_PER_CLASS = 30

# Ordered feature list. Order matters: build_feature_vector and the trained
# model were produced with exactly this ordering.
FEATURE_NAMES = [
    "claimed_loss",              # farmer-claimed loss percentage
    "visual_heuristic_damage",   # colour-based image damage estimate (heuristic, NOT trained severity)
    "loss_difference",           # |claimed - visual heuristic|, used as an INPUT feature only
    "farm_area",                 # reported farm area
    "disease_model_confidence",  # MobileNetV2 softmax confidence for the crop image
    "photo_needs_review",        # 1 if photo-quality heuristics found issues
    "field_location_present",    # 1 if lat/lng or farm polygon provided
    "event_type_present",        # 1 if claim event type provided
    "crop_stage_present",        # 1 if crop stage provided
]

# Interpretation bands applied to the CALIBRATED model probability
# P(officer-verified INCONSISTENT). These are NOT damage-difference
# thresholds; the difference is just one learned input among several.
LOW_RISK_MAX = 0.35
HIGH_RISK_MIN = 0.65

NOT_READY_MESSAGE = (
    "The trained claim-risk model requires sufficient officer-verified claim "
    "records before ML triage can be activated."
)


def _not_ready_result():
    """Structured safe result when no trained model is available."""
    return {
        "review_status": "MODEL_NOT_READY",
        "claim_risk_score": None,
        "model_used": False,
        "model_name": None,
        "risk_model_name": None,
        "decision_type": "model_not_ready",
        "level": None,
        "message": NOT_READY_MESSAGE,
    }


def probability_to_review(probability):
    """Map the calibrated inconsistency probability to a triage category.

    Low/mid/high are interpretation bands on the MODEL output - the model's
    own learned scoring, not a hand-coded rule on claimed-vs-estimated loss.
    """
    probability = float(probability)
    if probability < LOW_RISK_MAX:
        return "NORMAL", "normal"
    if probability > HIGH_RISK_MIN:
        return "HIGH", "high"
    return "MEDIUM", "medium"


def build_feature_vector(source):
    """Build the exact training-time feature vector.

    ``source`` mirrors the claims table columns used during training:
    claimed_loss, estimated_damage, difference, farm_area, model_confidence,
    evidence_json, latitude, farm_polygon, event_type, crop_stage.

    Returns a 1-D float numpy array in FEATURE_NAMES order.
    """
    evidence_raw = source.get("evidence_json") or "{}"
    if isinstance(evidence_raw, str):
        try:
            evidence = json.loads(evidence_raw)
        except (ValueError, TypeError):
            evidence = {}
    else:
        evidence = evidence_raw or {}

    photo_needs_review = int(any(
        item.get("source") == "photo_quality" and item.get("value") == "review"
        for item in evidence.get("factors", [])
    ))
    field_location_present = int(
        source.get("latitude") not in (None, "")
        or bool(source.get("farm_polygon"))
    )

    return np.asarray([
        float(source.get("claimed_loss") or 0.0),
        float(source.get("estimated_damage") or 0.0),
        float(source.get("difference") or 0.0),
        float(source.get("farm_area") or 0.0),
        float(source.get("model_confidence") or 0.0),
        photo_needs_review,
        field_location_present,
        int(bool(source.get("event_type"))),
        int(bool(source.get("crop_stage"))),
    ], dtype=float)


def predict_claim_risk(source):
    """Reusable inference for the trained claim-risk model.

    * Loads the trained model + feature metadata.
    * Builds the exact training features from ``source``.
    * Returns the review category, the calibrated score, and model identity.

    Fails SAFELY: when the model/metadata is missing or cannot be loaded it
    returns MODEL_NOT_READY / model_used=False. It never falls back to the
    old difference-threshold rules as if they were an ML result.
    """
    # Default is deliberately safe: a demo artifact is never selected unless
    # the operator explicitly opts in with CLAIM_RISK_MODE=demo.
    mode = os.getenv("CLAIM_RISK_MODE", "off").strip().lower()
    if mode not in {"real", "demo", "off"}:
        mode = "off"
    if mode == "real":
        model_path, features_path, model_name, decision_type = (
            MODEL_PATH, FEATURES_PATH, MODEL_NAME, "ml"
        )
    elif mode == "demo":
        # Prefer a real verified-label model when one is available, even in a
        # demo environment; it remains the authoritative artifact.
        if MODEL_PATH.exists() and FEATURES_PATH.exists():
            model_path, features_path, model_name, decision_type = (
                MODEL_PATH, FEATURES_PATH, MODEL_NAME, "ml"
            )
        else:
            model_path, features_path, model_name, decision_type = (
                DEMO_MODEL_PATH, DEMO_FEATURES_PATH, DEMO_MODEL_NAME, "demo_ml"
            )
    else:
        return _not_ready_result()

    if not model_path.exists() or not features_path.exists():
        print("[claim-risk] Model not trained yet - returning MODEL_NOT_READY "
              "(no fabrication of ML results).")
        return _not_ready_result()

    try:
        metadata = json.loads(features_path.read_text(encoding="utf-8"))
        trained_features = metadata.get("feature_names")
        if trained_features is not None and list(trained_features) != FEATURE_NAMES:
            print(f"[claim-risk] Metadata feature mismatch: {trained_features}")
            return _not_ready_result()
        model = joblib.load(model_path)
        vector = build_feature_vector(source).reshape(1, -1)
        probability = float(model.predict_proba(vector)[0][1])
        review, level = probability_to_review(probability)
        print(f"[claim-risk] Model used: {model_name} score={probability:.4f} -> {review}")
        return {
            "review_status": review,
            "claim_risk_score": round(probability, 4),
            "model_used": True,
            "model_name": metadata.get("model_name", model_name),
            "risk_model_name": metadata.get("model_name", model_name),
            "decision_type": decision_type,
            "level": level,
            "message": None,
        }
    except Exception as error:  # never let inference break claim submission
        print(f"[claim-risk] Inference failed -> MODEL_NOT_READY (not rules): {error}")
        return _not_ready_result()


def get_claim_risk_readiness():
    """Aggregate, non-sensitive readiness info for GET /model-readiness."""
    empty = {
        "reviewed_claim_count": 0,
        "trainable_claim_count": 0,
        "class_counts": {"supported": 0, "inconsistent": 0, "inconclusive": 0},
        "model_exists": False,
        "model_active": False,
        "ready_to_train": False,
    }
    if not DB_PATH.exists():
        return empty

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM claim_review_labels"
        ).fetchone()["n"]
        count_by_label = {
            key: conn.execute(
                "SELECT COUNT(*) AS n FROM claim_review_labels WHERE consistency_label = ?",
                (label,),
            ).fetchone()["n"]
            for key, label in (
                ("supported", "SUPPORTED"),
                ("inconsistent", "INCONSISTENT"),
                ("inconclusive", "INCONCLUSIVE"),
            )
        }
    except sqlite3.OperationalError:
        # claim_review_labels is created by the app's auto-migration on first
        # startup; a freshly seeded DB may not have it yet.
        total = 0
        count_by_label = {"supported": 0, "inconsistent": 0, "inconclusive": 0}
    finally:
        conn.close()

    model_exists = MODEL_PATH.exists() and FEATURES_PATH.exists()
    model_active = False
    if model_exists:
        try:
            joblib.load(MODEL_PATH)
            model_active = True
        except Exception:
            model_active = False

    ready_to_train = (
        # INCONCLUSIVE records remain valuable audit data, but cannot be
        # used to train this binary supported-vs-inconsistent classifier.
        # Match the training script's actual eligible-row guard exactly.
        (count_by_label["supported"] + count_by_label["inconsistent"])
        >= MINIMUM_REVIEWED_CLAIMS
        and count_by_label.get("supported", 0) >= MINIMUM_PER_CLASS
        and count_by_label.get("inconsistent", 0) >= MINIMUM_PER_CLASS
    )

    return {
        "reviewed_claim_count": total,
        "trainable_claim_count": (
            count_by_label["supported"] + count_by_label["inconsistent"]
        ),
        "minimum_required": MINIMUM_REVIEWED_CLAIMS,
        "class_counts": count_by_label,
        "model_exists": model_exists,
        "model_active": model_active,
        "ready_to_train": ready_to_train,
    }
