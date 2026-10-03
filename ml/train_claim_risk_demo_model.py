"""Train the strictly separate synthetic/research claim-risk demo model."""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_recall_fscore_support,
                             roc_auc_score)
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from ml.claim_risk import (DEMO_FEATURES_PATH, DEMO_MODEL_NAME, DEMO_MODEL_PATH,
                           FEATURE_NAMES, HIGH_RISK_MIN, LOW_RISK_MAX, MODEL_DIR,
                           build_feature_vector)

DATASET_PATH = BASE_DIR / "ml" / "data" / "claim_risk_demo_dataset.csv"
REPORT_PATH = MODEL_DIR / "claim_risk_demo_training_report.json"
NOTICE = "These labels are synthetic/research demonstration labels and are NOT officer-verified PMFBY claim labels."


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Missing demo dataset: {DATASET_PATH}. Run generate_claim_risk_demo_dataset.py first.")
    with DATASET_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    labels = np.asarray([int(r["consistency_label"] == "INCONSISTENT") for r in rows])
    x = np.asarray([build_feature_vector(r) for r in rows])
    counts = {"SUPPORTED": int((labels == 0).sum()), "INCONSISTENT": int((labels == 1).sum())}
    if min(counts.values()) < 150:
        raise ValueError(f"Demo dataset needs at least 150 rows per class: {counts}")
    x_train, x_test, y_train, y_test = train_test_split(x, labels, test_size=.20, random_state=42, stratify=labels)
    model = CalibratedClassifierCV(HistGradientBoostingClassifier(max_depth=3, learning_rate=.05, random_state=42), method="isotonic", cv=5)
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    predicted = (probabilities >= .5).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, predicted, average="binary", zero_division=0)
    metrics = {
        "precision": round(float(precision), 4), "recall": round(float(recall), 4),
        "f1": round(float(f1), 4), "accuracy": round(float(accuracy_score(y_test, predicted)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "confusion_matrix": confusion_matrix(y_test, predicted).tolist(),
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, DEMO_MODEL_PATH)
    metadata = {"model_name": DEMO_MODEL_NAME, "dataset_type": "synthetic/research demonstration",
                "dataset_notice": NOTICE, "feature_names": FEATURE_NAMES, "training_rows": len(rows),
                "class_counts": counts, "algorithm": "CalibratedClassifierCV(HistGradientBoostingClassifier, isotonic)", "metrics": metrics,
                "score_meaning": f"calibrated research-demo P(inconsistency); <{LOW_RISK_MAX} NORMAL, >{HIGH_RISK_MIN} HIGH, otherwise MEDIUM",
                "purpose": "human-review triage only; never approve, reject, or calculate a payout"}
    DEMO_FEATURES_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    report = {**metadata, "train_test_split": {"train_rows": len(y_train), "test_rows": len(y_test), "test_size": .2, "random_state": 42}, "training_timestamp": datetime.now(timezone.utc).isoformat()}
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"training_rows": len(rows), "class_counts": counts, "metrics": metrics, "saved_model": str(DEMO_MODEL_PATH)}, indent=2))
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
