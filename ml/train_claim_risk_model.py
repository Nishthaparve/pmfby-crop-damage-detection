"""Train a calibrated *triage* model from officer-verified claim labels.

This script deliberately refuses to train on unreviewed claims or synthetic
scores.  Its output prioritises work for an officer; it must never approve,
reject, or calculate a PMFBY payout.

Training guards (unchanged production policy):
  * at least MINIMUM_REVIEWED_CLAIMS (200) reviewed claims, and
  * at least MINIMUM_PER_CLASS (30) labels in each of SUPPORTED/INCONSISTENT.

The feature vector is built by ml.claim_risk.build_feature_vector - the SAME
code path used by backend inference - so training and live prediction can
never drift apart.

Outputs written under ml/model/:
  * claim_risk_model.joblib        - calibrated HistGradientBoosting classifier
  * claim_risk_features.json       - metadata + the exact feature
Run from the project root:
    python ml/train_claim_risk_model.py
"""
import json
import argparse
import sqlite3
import sys
from pathlib import Path
import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Shared feature code: the exact same vector is used at inference time.
from ml.claim_risk import (  # noqa: E402
    FEATURES_PATH, FEATURE_NAMES, HIGH_RISK_MIN, LOW_RISK_MAX,
    MINIMUM_PER_CLASS, MINIMUM_REVIEWED_CLAIMS, MODEL_DIR,
    MODEL_NAME, MODEL_PATH, build_feature_vector,
)

DB_PATH = BASE_DIR / "backend" / "claims.db"


def rows_to_features(rows):
    features, labels = [], []
    for row in rows:
        # dict(row): sqlite3.Row -> plain dict so the shared builder sees the
        # same field names that live inference passes in.
        features.append(build_feature_vector(dict(row)))
        labels.append(int(row["consistency_label"] == "INCONSISTENT"))
    return np.asarray(features), np.asarray(labels)


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"No claim database found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
        SELECT c.*, l.consistency_label FROM claims c
        JOIN claim_review_labels l ON l.claim_id = c.id
        WHERE l.consistency_label IN ('SUPPORTED', 'INCONSISTENT')
    """).fetchall()
    except sqlite3.OperationalError as error:
        # claim_review_labels does not exist yet: the backend's auto-migration
        # creates it on first startup, so a fresh database has zero labels -
        # refuse to train rather than crash.
        print(f"[train] No verified labels yet ({error}). Nothing to train on.")
        rows = []
    conn.close()
    x, y = rows_to_features(rows)
    class_counts = {"supported": int((y == 0).sum()), "inconsistent": int((y == 1).sum())}
    if len(y) < MINIMUM_REVIEWED_CLAIMS or min(class_counts.values()) < MINIMUM_PER_CLASS:
        # Insufficient verified labels is an expected, safe state—not a
        # training failure that should emit a traceback or create artifacts.
        print(
            "Refusing to train: need at least "
            f"{MINIMUM_REVIEWED_CLAIMS} reviewed claims and {MINIMUM_PER_CLASS} labels "
            f"per class; found {len(y)} ({class_counts})."
        )
        return False
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.20, random_state=42, stratify=y
    )
    # Calibration makes scores interpretable as a likelihood estimate only
    # after independent evaluation; it does not make them payout decisions.
    model = CalibratedClassifierCV(
        HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, random_state=42),
        method="isotonic", cv=5
    )
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    predicted = (probabilities >= 0.5).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, predicted, average="binary", zero_division=0)
    metrics = {
        "holdout_pr_auc": round(float(average_precision_score(y_test, probabilities)), 4),
        "holdout_precision_at_0_5": round(float(precision), 4),
        "holdout_recall_at_0_5": round(float(recall), 4),
        "holdout_f1_at_0_5": round(float(f1), 4),
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    FEATURES_PATH.write_text(json.dumps({
        "model_name": MODEL_NAME,
        "feature_names": FEATURE_NAMES,
        "training_rows": len(y),
        "class_counts": class_counts,
        "metrics": metrics,
        "score_meaning": (
            "calibrated P(claim is officer-verified INCONSISTENT); "
            f"review bands on the model score: <{LOW_RISK_MAX} NORMAL, "
            f">{HIGH_RISK_MIN} HIGH, between -> MEDIUM"
        ),
        "purpose": "human-review triage only; never use for automated approval, rejection, or payout"
    }, indent=2), encoding="utf-8")
    print(json.dumps({
        "saved_model": str(MODEL_PATH),
        "saved_features_metadata": str(FEATURES_PATH),
        "training_rows": len(y),
        "class_counts": class_counts,
        "metrics": metrics,
    }, indent=2))
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train real verified-label or separate research/demo claim-risk model.")
    parser.add_argument("--mode", choices=("real", "demo"), default="real")
    args = parser.parse_args()
    if args.mode == "demo":
        from ml.train_claim_risk_demo_model import main as demo_main
        sys.exit(0 if demo_main() else 1)
    sys.exit(0 if main() else 1)
