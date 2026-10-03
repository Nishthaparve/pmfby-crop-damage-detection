"""Create non-PII synthetic/research data for the claim-risk demo only.

These labels are synthetic/research demonstration labels and are NOT
officer-verified PMFBY claim labels.  This generator must never be used to
augment the real verified-label training path.
"""
import csv
import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "claim_risk_demo_dataset.csv"


def main():
    rng = random.Random(20260903)
    rows = []
    # Controlled overlap makes this a demonstrable classification task rather
    # than a dataset of duplicated or trivially separable examples.
    for label, n in (("SUPPORTED", 190), ("INCONSISTENT", 190)):
        for _ in range(n):
            inconsistent = label == "INCONSISTENT"
            claimed = rng.uniform(15, 92)
            disagreement = max(0.5, rng.gauss(30 if inconsistent else 7, 10 if inconsistent else 6))
            estimated = max(0, min(100, claimed + (rng.choice((-1, 1)) * disagreement)))
            photo_review = rng.random() < (0.64 if inconsistent else 0.16)
            location = rng.random() < (0.62 if inconsistent else 0.91)
            event = rng.random() < (0.66 if inconsistent else 0.94)
            stage = rng.random() < (0.60 if inconsistent else 0.92)
            evidence = {"factors": ([{"source": "photo_quality", "value": "review"}]
                       if photo_review else [{"source": "photo_quality", "value": "acceptable"}])}
            rows.append({
                "claimed_loss": round(claimed, 2),
                "estimated_damage": round(estimated, 2),
                "difference": round(abs(claimed - estimated), 2),
                "farm_area": round(rng.uniform(0.4, 12.0), 2),
                "model_confidence": round(rng.uniform(0.42, 0.99), 4),
                "evidence_json": json.dumps(evidence),
                "latitude": round(rng.uniform(18.0, 22.5), 6) if location else "",
                "farm_polygon": "" if location else "",
                "event_type": rng.choice(["Drought", "Flood", "Pest", "Hailstorm"]) if event else "",
                "crop_stage": rng.choice(["Vegetative", "Flowering", "Maturity"]) if stage else "",
                "consistency_label": label,
                "dataset_notice": "synthetic/research demonstration; NOT officer-verified PMFBY claim labels",
            })
    rng.shuffle(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic/research rows to {OUT}")


if __name__ == "__main__":
    main()
