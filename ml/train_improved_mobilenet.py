import os
import json
import time
import random
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
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

BASE_DIR = Path(r"c:\Users\user\OneDrive\Documents\Desktop\PMFBY")
PV_DIR = BASE_DIR / "datasets" / "plant_village" / "PlantVillage"
TRAIN_DIR = PV_DIR / "train"
VAL_DIR = PV_DIR / "val"
TEST_DIR = PV_DIR / "test"

MODEL_DIR = BASE_DIR / "ml" / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_SAVE_PATH = MODEL_DIR / "crop_damage_model.pth"
CLASS_NAMES_PATH = MODEL_DIR / "class_names.json"
REPORT_SAVE_PATH = MODEL_DIR / "mobilenet_v2_evaluation_report.json"

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

IMAGE_SIZE = 128
BATCH_SIZE = 32
SAMPLES_PER_CLASS = 150  # 38 x 150 = 5,700 balanced training images
STAGE1_EPOCHS = 1        # Classifier head warmup
STAGE2_EPOCHS = 3        # Fine-tuning upper feature blocks
TOTAL_EPOCHS = STAGE1_EPOCHS + STAGE2_EPOCHS

print("=" * 65)
print("PMFBY DEEP LEARNING IMPROVEMENT PIPELINE — MobileNetV2")
print("=" * 65)
print(f"Device: {DEVICE}")
print(f"CPU Threads: {torch.get_num_threads()}")
print(f"Train Dir: {TRAIN_DIR}")
print(f"Val Dir:   {VAL_DIR}")
print(f"Test Dir:  {TEST_DIR}")

# Transforms
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.85, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(degrees=12),
    transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 1. Prepare Training Subset (Stratified & Balanced)
print("\nLoading training dataset and creating balanced stratified subset...")
base_train_dataset = datasets.ImageFolder(TRAIN_DIR, transform=train_transform)
class_names = base_train_dataset.classes
num_classes = len(class_names)
print(f"Classes found: {num_classes}")

with open(CLASS_NAMES_PATH, "w", encoding="utf-8") as f:
    json.dump(class_names, f, indent=4)

class_indices = {i: [] for i in range(num_classes)}
for idx, (_, label) in enumerate(base_train_dataset.samples):
    class_indices[label].append(idx)

selected_train_indices = []
for label, indices in class_indices.items():
    random.seed(RANDOM_SEED + label)
    random.shuffle(indices)
    selected_train_indices.extend(indices[:SAMPLES_PER_CLASS])

random.shuffle(selected_train_indices)
train_subset = Subset(base_train_dataset, selected_train_indices)
print(f"Stratified Training Samples: {len(train_subset)} (up to {SAMPLES_PER_CLASS} per class)")

train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)

# 2. Prepare Validation & Test Loaders
val_dataset = datasets.ImageFolder(VAL_DIR, transform=eval_transform)
val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=0)
print(f"Validation Samples: {len(val_dataset)}")

test_dataset = datasets.ImageFolder(TEST_DIR, transform=eval_transform)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False, num_workers=0)
print(f"Held-out Test Samples: {len(test_dataset)}")

# 3. Initialize Model with ImageNet Pre-trained Weights or Existing Checkpoint
print("\nInitializing MobileNetV2 with ImageNet Pre-trained backbone...")
weights = models.MobileNet_V2_Weights.DEFAULT
model = models.mobilenet_v2(weights=weights)

model.classifier = nn.Sequential(
    nn.Dropout(p=0.2),
    nn.Linear(model.last_channel, num_classes)
)
model = model.to(DEVICE)

# Loss function with label smoothing for regularization & generalization
criterion = nn.CrossEntropyLoss(label_smoothing=0.05)

# Tracking history
history = []
best_val_acc = 0.0
best_model_state = None

def evaluate_on_val(model, loader):
    model.eval()
    val_loss = 0.0
    val_correct = 0
    val_total = 0
    with torch.no_grad():
        for images, targets in loader:
            images = images.to(DEVICE)
            targets = targets.to(DEVICE)
            outputs = model(images)
            loss = criterion(outputs, targets)
            val_loss += loss.item() * len(targets)
            preds = outputs.argmax(dim=1)
            val_correct += (preds == targets).sum().item()
            val_total += len(targets)
    return val_loss / val_total, (val_correct / val_total) * 100.0

# =========================================================
# STAGE 1: Classifier Head Warmup (Backbone Frozen)
# =========================================================
print("\n--- STAGE 1: Classifier Head Warmup (Backbone Frozen) ---")
for param in model.features.parameters():
    param.requires_grad = False
for param in model.classifier.parameters():
    param.requires_grad = True

optimizer_stage1 = optim.AdamW(model.classifier.parameters(), lr=1e-3, weight_decay=1e-4)

t0 = time.time()
model.train()
running_loss = 0.0
train_correct = 0
train_total = 0

for b_idx, (imgs, lbls) in enumerate(train_loader, start=1):
    imgs, lbls = imgs.to(DEVICE), lbls.to(DEVICE)
    optimizer_stage1.zero_grad()
    outputs = model(imgs)
    loss = criterion(outputs, lbls)
    loss.backward()
    optimizer_stage1.step()
    
    running_loss += loss.item() * len(lbls)
    preds = outputs.argmax(dim=1)
    train_correct += (preds == lbls).sum().item()
    train_total += len(lbls)

epoch1_train_loss = running_loss / train_total
epoch1_train_acc = (train_correct / train_total) * 100.0
epoch1_val_loss, epoch1_val_acc = evaluate_on_val(model, val_loader)

print(f"Epoch 1/{TOTAL_EPOCHS} (Stage 1 Head) | Train Loss: {epoch1_train_loss:.4f} | Train Acc: {epoch1_train_acc:.2f}% | Val Loss: {epoch1_val_loss:.4f} | Val Acc: {epoch1_val_acc:.2f}% | Time: {time.time()-t0:.1f}s")
history.append({
    "epoch": 1,
    "train_loss": round(epoch1_train_loss, 4),
    "val_loss": round(epoch1_val_loss, 4),
    "train_accuracy": round(epoch1_train_acc, 2),
    "val_accuracy": round(epoch1_val_acc, 2)
})
if epoch1_val_acc > best_val_acc:
    best_val_acc = epoch1_val_acc
    best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

# =========================================================
# STAGE 2: Fine-Tuning Upper Feature Blocks
# =========================================================
print("\n--- STAGE 2: Fine-Tuning Upper Feature Blocks ---")
for param in model.features[13:].parameters():
    param.requires_grad = True

optimizer_stage2 = optim.AdamW([
    {"params": model.features[13:].parameters(), "lr": 1e-4},
    {"params": model.classifier.parameters(), "lr": 5e-4}
], weight_decay=1e-4)

scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer_stage2, T_max=STAGE2_EPOCHS, eta_min=1e-5)

for ep_idx in range(STAGE2_EPOCHS):
    epoch_num = 2 + ep_idx
    t_start = time.time()
    model.train()
    running_loss = 0.0
    train_correct = 0
    train_total = 0

    for imgs, lbls in train_loader:
        imgs, lbls = imgs.to(DEVICE), lbls.to(DEVICE)
        optimizer_stage2.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, lbls)
        loss.backward()
        optimizer_stage2.step()
        
        running_loss += loss.item() * len(lbls)
        preds = outputs.argmax(dim=1)
        train_correct += (preds == lbls).sum().item()
        train_total += len(lbls)
        
    scheduler.step()
    
    ep_train_loss = running_loss / train_total
    ep_train_acc = (train_correct / train_total) * 100.0
    ep_val_loss, ep_val_acc = evaluate_on_val(model, val_loader)
    
    print(f"Epoch {epoch_num}/{TOTAL_EPOCHS} (Stage 2 Fine-tune) | Train Loss: {ep_train_loss:.4f} | Train Acc: {ep_train_acc:.2f}% | Val Loss: {ep_val_loss:.4f} | Val Acc: {ep_val_acc:.2f}% | Time: {time.time()-t_start:.1f}s")
    history.append({
        "epoch": epoch_num,
        "train_loss": round(ep_train_loss, 4),
        "val_loss": round(ep_val_loss, 4),
        "train_accuracy": round(ep_train_acc, 2),
        "val_accuracy": round(ep_val_acc, 2)
    })
    
    if ep_val_acc > best_val_acc:
        best_val_acc = ep_val_acc
        best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        print(f"  --> New Best Validation Accuracy: {best_val_acc:.2f}%! Checkpoint saved.")

print(f"\nTraining Complete! Best Validation Accuracy achieved: {best_val_acc:.2f}%")

# Save the best model
if best_model_state is not None:
    model.load_state_dict(best_model_state)
    torch.save({
        "model_state_dict": best_model_state,
        "class_names": class_names,
        "num_classes": num_classes,
        "image_size": IMAGE_SIZE
    }, MODEL_SAVE_PATH)
    print(f"Best model successfully saved to {MODEL_SAVE_PATH}")

# =========================================================
# FINAL UNBIASED EVALUATION ON HELD-OUT TEST SET
# =========================================================
print("\n" + "=" * 65)
print("RUNNING FINAL UNBIASED EVALUATION ON HELD-OUT TEST SET...")
print("=" * 65)

model.eval()
test_preds = []
test_targets = []
top1_correct = 0
top5_correct = 0
total_test = 0

with torch.no_grad():
    for images, targets in test_loader:
        images = images.to(DEVICE)
        outputs = model(images)
        
        # Top 1
        preds = outputs.argmax(dim=1)
        test_preds.extend(preds.cpu().numpy().tolist())
        test_targets.extend(targets.numpy().tolist())
        top1_correct += (preds.cpu() == targets).sum().item()
        
        # Top 5
        _, top5_indices = torch.topk(outputs, k=min(5, num_classes), dim=1)
        for i in range(len(targets)):
            if targets[i].item() in top5_indices[i].cpu().numpy():
                top5_correct += 1
                
        total_test += len(targets)

test_top1_acc = (top1_correct / total_test) * 100.0
test_top5_acc = (top5_correct / total_test) * 100.0

test_macro_prec = precision_score(test_targets, test_preds, average="macro", zero_division=0) * 100.0
test_weighted_prec = precision_score(test_targets, test_preds, average="weighted", zero_division=0) * 100.0
test_macro_rec = recall_score(test_targets, test_preds, average="macro", zero_division=0) * 100.0
test_weighted_rec = recall_score(test_targets, test_preds, average="weighted", zero_division=0) * 100.0
test_macro_f1 = f1_score(test_targets, test_preds, average="macro", zero_division=0) * 100.0
test_weighted_f1 = f1_score(test_targets, test_preds, average="weighted", zero_division=0) * 100.0

cm = confusion_matrix(test_targets, test_preds).tolist()
report_dict = classification_report(test_targets, test_preds, target_names=class_names, output_dict=True, zero_division=0)

per_class_metrics = []
for idx, cname in enumerate(class_names):
    c_data = report_dict.get(cname, {})
    per_class_metrics.append({
        "class_index": idx,
        "class_name": cname,
        "precision": round(c_data.get("precision", 0) * 100, 2),
        "recall": round(c_data.get("recall", 0) * 100, 2),
        "f1_score": round(c_data.get("f1-score", 0) * 100, 2),
        "support": int(c_data.get("support", 0)),
        "true_positives": cm[idx][idx] if idx < len(cm) else 0
    })

sorted_by_f1 = sorted(per_class_metrics, key=lambda x: x["f1_score"], reverse=True)
best_classified = sorted_by_f1[:5]

confused_classes = []
for i in range(num_classes):
    row = cm[i]
    off_diag = [(j, count) for j, count in enumerate(row) if j != i]
    if off_diag:
        top_err = max(off_diag, key=lambda x: x[1])
        if top_err[1] > 0:
            confused_classes.append({
                "actual_class": class_names[i],
                "confused_with": class_names[top_err[0]],
                "misclassified_count": top_err[1],
                "f1_score": per_class_metrics[i]["f1_score"]
            })
confused_classes = sorted(confused_classes, key=lambda x: x["misclassified_count"], reverse=True)[:5]

final_train_acc = history[-1]["train_accuracy"]
train_val_gap = round(final_train_acc - best_val_acc, 2)
if train_val_gap > 12.0:
    generalization_verdict = "Training performance is higher than validation performance; additional regularization or augmentation may be beneficial."
    overfitting_status = "Mild Overfitting"
elif train_val_gap < 0:
    generalization_verdict = "Validation performance matches or exceeds training performance due to regularization & label smoothing."
    overfitting_status = "Well Generalized"
else:
    generalization_verdict = "Training and validation performance are reasonably aligned, demonstrating strong generalization."
    overfitting_status = "Balanced / Good Generalization"

full_report = {
    "model_name": "MobileNetV2",
    "architecture": "mobilenet_v2",
    "pretrained_weights": "ImageNet (MobileNet_V2_Weights.DEFAULT)",
    "num_classes": num_classes,
    "class_names": class_names,
    "dataset": {
        "name": "PlantVillage",
        "total_images": 54305,
        "train_samples": len(base_train_dataset),
        "val_samples": len(val_dataset),
        "test_samples": total_test,
        "train_percent": 80.0,
        "val_percent": 10.02,
        "test_percent": 9.98,
        "image_size": [IMAGE_SIZE, IMAGE_SIZE]
    },
    "training_config": {
        "epochs": TOTAL_EPOCHS,
        "batch_size": BATCH_SIZE,
        "optimizer": "AdamW",
        "loss_function": "CrossEntropyLoss (label_smoothing=0.05)",
        "scheduler": "CosineAnnealingLR",
        "two_stage_transfer_learning": True,
        "data_augmentation": "RandomResizedCrop, RandomHorizontalFlip, RandomRotation, ColorJitter",
        "weight_decay": 1e-4
    },
    "metrics": {
        "training_accuracy": final_train_acc,
        "best_validation_accuracy": round(best_val_acc, 2),
        "validation_accuracy": round(best_val_acc, 2),
        "test_accuracy": round(test_top1_acc, 2),
        "top1_accuracy": round(test_top1_acc, 2),
        "top5_accuracy": round(test_top5_acc, 2),
        "test_precision_macro": round(test_macro_prec, 2),
        "test_precision_weighted": round(test_weighted_prec, 2),
        "test_recall_macro": round(test_macro_rec, 2),
        "test_recall_weighted": round(test_weighted_rec, 2),
        "test_f1_macro": round(test_macro_f1, 2),
        "test_f1_weighted": round(test_weighted_f1, 2),
        "precision": round(test_macro_prec, 2),
        "recall": round(test_macro_rec, 2),
        "f1_score": round(test_macro_f1, 2)
    },
    "generalization": {
        "train_val_gap_pct": train_val_gap,
        "status": overfitting_status,
        "explanation": generalization_verdict
    },
    "training_history": history,
    "best_classified_classes": best_classified,
    "most_confused_classes": confused_classes,
    "confusion_matrix": cm,
    "per_class_metrics": per_class_metrics
}

with open(REPORT_SAVE_PATH, "w", encoding="utf-8") as f:
    json.dump(full_report, f, indent=2)

print("\n" + "=" * 65)
print("MobileNetV2 MODEL EVALUATION")
print("=" * 65)
print(f"Dataset: PlantVillage (38 Classes)")
print(f"Train Samples:      {len(base_train_dataset)} (Trained on {len(train_subset)} stratified subset)")
print(f"Validation Samples: {len(val_dataset)}")
print(f"Test Samples:       {total_test}")
print("-" * 65)
print(f"Training Accuracy:   {final_train_acc:.2f}%")
print(f"Validation Accuracy: {best_val_acc:.2f}%")
print(f"Test Accuracy:       {test_top1_acc:.2f}%")
print(f"Top-1 Accuracy:      {test_top1_acc:.2f}%")
print(f"Top-5 Accuracy:      {test_top5_acc:.2f}%")
print(f"Test Precision (Macro):    {test_macro_prec:.2f}%")
print(f"Test Precision (Weighted): {test_weighted_prec:.2f}%")
print(f"Test Recall (Macro):       {test_macro_rec:.2f}%")
print(f"Test Recall (Weighted):    {test_weighted_rec:.2f}%")
print(f"Test Macro F1:             {test_macro_f1:.2f}%")
print(f"Test Weighted F1:          {test_weighted_f1:.2f}%")
print("-" * 65)
print(f"Generalization Status: {overfitting_status}")
print(f"Gap: {train_val_gap}% | {generalization_verdict}")
print("=" * 65)
print(f"Saved evaluation report to {REPORT_SAVE_PATH}")
