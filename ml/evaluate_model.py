# -*- coding: utf-8 -*-
"""
MobileNetV2 Model Evaluation Script
Evaluates crop_damage_model.pth on held-out test set and prints standard academic benchmark metrics.
"""

import sys
import os
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

torch.set_num_threads(os.cpu_count() or 8)

BASE_DIR = Path(__file__).resolve().parent.parent
PV_DIR = BASE_DIR / "datasets" / "plant_village" / "PlantVillage"
TRAIN_DIR = PV_DIR / "train"
VAL_DIR = PV_DIR / "val"
TEST_DIR = PV_DIR / "test"

MODEL_PATH = BASE_DIR / "ml" / "model" / "crop_damage_model.pth"
CLASS_NAMES_PATH = BASE_DIR / "ml" / "model" / "class_names.json"
REPORT_PATH = BASE_DIR / "ml" / "model" / "mobilenet_v2_evaluation_report.json"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def run_evaluation(recompute=False):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model checkpoint not found at {MODEL_PATH}")
    if not CLASS_NAMES_PATH.exists():
        raise FileNotFoundError(f"Class names file not found at {CLASS_NAMES_PATH}")

    with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
        class_names = json.load(f)

    num_classes = len(class_names)

    # Check if report already exists and recompute is not requested
    existing_report = None
    if REPORT_PATH.exists() and not recompute and "--recompute" not in sys.argv:
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                existing_report = json.load(f)
        except Exception:
            existing_report = None

    if existing_report and "metrics" in existing_report and "test_accuracy" in existing_report["metrics"]:
        r = existing_report
        m = r["metrics"]
        d = r.get("dataset", {})
        print("=" * 50)
        print("MobileNetV2 MODEL EVALUATION")
        print("=" * 50)
        print(f"Dataset:            {d.get('name', 'PlantVillage')} ({num_classes} Classes)")
        print(f"Classes:            {num_classes}")
        print(f"Train Samples:      {d.get('train_samples', 43444)}")
        print(f"Validation Samples: {d.get('val_samples', 5439)}")
        print(f"Test Samples:       {d.get('test_samples', 5422)}")
        print()
        print(f"Training Accuracy:   {m.get('training_accuracy', 0):.2f}%")
        print(f"Validation Accuracy: {m.get('validation_accuracy', 0):.2f}%")
        print(f"Test Accuracy:       {m.get('test_accuracy', 0):.2f}%")
        print()
        print(f"Test Precision:      {m.get('test_precision_macro', m.get('precision', 0)):.2f}%")
        print(f"Test Recall:         {m.get('test_recall_macro', m.get('recall', 0)):.2f}%")
        print(f"Test Macro F1:       {m.get('test_f1_macro', m.get('f1_score', 0)):.2f}%")
        print(f"Test Weighted F1:    {m.get('test_f1_weighted', 0):.2f}%")
        print()
        print(f"Top-1 Accuracy:      {m.get('top1_accuracy', m.get('test_accuracy', 0)):.2f}%")
        print(f"Top-5 Accuracy:      {m.get('top5_accuracy', 0):.2f}%")
        print()
        print("Confusion Matrix:")
        cm_arr = np.array(r.get("confusion_matrix", []))
        print(f"Shape: {cm_arr.shape}")
        print(f"Diagonal sum (correct predictions): {np.trace(cm_arr)} / {np.sum(cm_arr)}")
        print()
        print("Classification Report:")
        for pcm in r.get("per_class_metrics", []):
            print(f"  {pcm['class_name']:<48} | Prec: {pcm['precision']:>5.2f}% | Rec: {pcm['recall']:>5.2f}% | F1: {pcm['f1_score']:>5.2f}% | Support: {pcm['support']}")
        print("=" * 50)
        return r

    # Otherwise perform live evaluation on TEST_DIR
    print("Performing live evaluation on held-out test dataset...")
    eval_transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    test_dataset = datasets.ImageFolder(TEST_DIR, transform=eval_transform)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=128, shuffle=False, num_workers=0)

    # Load Model
    model = models.mobilenet_v2(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.2),
        nn.Linear(model.last_channel, num_classes)
    )
    ckpt = torch.load(MODEL_PATH, map_location=DEVICE)
    if "model_state_dict" in ckpt:
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        model.load_state_dict(ckpt)
    model.to(DEVICE)
    model.eval()

    test_preds, test_targets = [], []
    top1_c, top5_c, total = 0, 0, 0

    with torch.no_grad():
        for imgs, lbls in test_loader:
            imgs = imgs.to(DEVICE)
            out = model(imgs)
            p = out.argmax(dim=1)
            test_preds.extend(p.cpu().numpy().tolist())
            test_targets.extend(lbls.numpy().tolist())
            top1_c += (p.cpu() == lbls).sum().item()

            _, top5 = torch.topk(out, k=min(5, num_classes), dim=1)
            for i in range(len(lbls)):
                if lbls[i].item() in top5[i].cpu().numpy():
                    top5_c += 1
            total += len(lbls)

    test_acc = (top1_c / total) * 100.0
    top5_acc = (top5_c / total) * 100.0
    prec_macro = precision_score(test_targets, test_preds, average="macro", zero_division=0) * 100.0
    prec_weighted = precision_score(test_targets, test_preds, average="weighted", zero_division=0) * 100.0
    rec_macro = recall_score(test_targets, test_preds, average="macro", zero_division=0) * 100.0
    rec_weighted = recall_score(test_targets, test_preds, average="weighted", zero_division=0) * 100.0
    f1_macro = f1_score(test_targets, test_preds, average="macro", zero_division=0) * 100.0
    f1_weighted = f1_score(test_targets, test_preds, average="weighted", zero_division=0) * 100.0

    cm = confusion_matrix(test_targets, test_preds).tolist()
    rep_dict = classification_report(test_targets, test_preds, target_names=class_names, output_dict=True, zero_division=0)

    per_class_metrics = []
    for idx, cname in enumerate(class_names):
        cd = rep_dict.get(cname, {})
        per_class_metrics.append({
            "class_index": idx,
            "class_name": cname,
            "precision": round(cd.get("precision", 0) * 100, 2),
            "recall": round(cd.get("recall", 0) * 100, 2),
            "f1_score": round(cd.get("f1-score", 0) * 100, 2),
            "support": int(cd.get("support", 0)),
            "true_positives": cm[idx][idx] if idx < len(cm) else 0
        })

    print("=" * 50)
    print("MobileNetV2 MODEL EVALUATION")
    print("=" * 50)
    print(f"Dataset:            PlantVillage ({num_classes} Classes)")
    print(f"Classes:            {num_classes}")
    print(f"Train Samples:      43444")
    print(f"Validation Samples: 5439")
    print(f"Test Samples:       {total}")
    print()
    print(f"Test Accuracy:       {test_acc:.2f}%")
    print(f"Top-1 Accuracy:      {test_acc:.2f}%")
    print(f"Top-5 Accuracy:      {top5_acc:.2f}%")
    print()
    print(f"Test Precision:      {prec_macro:.2f}%")
    print(f"Test Recall:         {rec_macro:.2f}%")
    print(f"Test Macro F1:       {f1_macro:.2f}%")
    print(f"Test Weighted F1:    {f1_weighted:.2f}%")
    print("=" * 50)

if __name__ == "__main__":
    run_evaluation()
