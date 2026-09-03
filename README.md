# PMFBY crop damage 

## Claim-risk review triage

The real claim-risk model is trained only from authorized, officer-verified
PMFBY claim labels. Public PMFBY material is aggregate statistics and does not
provide the complete individual claim labels needed for this model.

For a college demonstration, `ml/data/claim_risk_demo_dataset.csv` and its
separate `claim_risk_demo_model` are synthetic/research data. Their labels are
not officer-verified PMFBY labels and demo results are not PMFBY fraud
determinations. Use `python ml/train_claim_risk_model.py --mode demo` to train
only the demo artifact. Set `CLAIM_RISK_MODE=demo` explicitly to use it; the
safe default is `off`. `real` selects only `claim_risk_model`, which still
requires 200 reviewed claims and at least 30 of each eligible class.

All outputs are human-review triage recommendations. They never automatically
approve or deny a claim, calculate a payout, or classify a farmer as fraudulent.
Production deployment must replace demo data with authorized verified records.
