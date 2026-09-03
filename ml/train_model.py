import os
import json
import random
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms, models


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = (
    BASE_DIR
    / "datasets"
    / "plant_village"
    / "PlantVillage"
    / "train"
)

MODEL_DIR = BASE_DIR / "ml" / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "crop_damage_model.pth"
CLASS_NAMES_PATH = MODEL_DIR / "class_names.json"

NUM_EPOCHS = 3
BATCH_SIZE = 16
LEARNING_RATE = 0.001

# Maximum images taken from each class
# 38 classes × 100 images ≈ 3800 images
MAX_IMAGES_PER_CLASS = 100

VALIDATION_SPLIT = 0.20
RANDOM_SEED = 42

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# =========================================================
# SET RANDOM SEED
# =========================================================

torch.manual_seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(RANDOM_SEED)


# =========================================================
# TRANSFORMS
# =========================================================

train_transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

validation_transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# =========================================================
# LOAD DATASET
# =========================================================

print(f"\nUsing device: {DEVICE}")
print("\nLoading PlantVillage dataset...")

if not DATASET_DIR.exists():
    print(f"\nERROR: Dataset folder not found:")
    print(DATASET_DIR)
    raise FileNotFoundError("Dataset folder not found.")


# Load once to get all samples and classes
full_dataset = datasets.ImageFolder(DATASET_DIR)

class_names = full_dataset.classes

print(f"Total images found: {len(full_dataset)}")
print(f"Number of classes: {len(class_names)}")


# =========================================================
# LIMIT IMAGES PER CLASS FOR FASTER TRAINING
# =========================================================

print(
    f"\nSelecting maximum {MAX_IMAGES_PER_CLASS} "
    f"images from each class..."
)

class_indices = {}

for index, (_, label) in enumerate(full_dataset.samples):
    if label not in class_indices:
        class_indices[label] = []

    class_indices[label].append(index)


selected_indices = []

for label, indices in class_indices.items():

    random.shuffle(indices)

    selected = indices[:MAX_IMAGES_PER_CLASS]

    selected_indices.extend(selected)


random.shuffle(selected_indices)

print(f"Images selected for training: {len(selected_indices)}")


# =========================================================
# TRAIN / VALIDATION SPLIT
# =========================================================

validation_size = int(
    len(selected_indices) * VALIDATION_SPLIT
)

training_size = len(selected_indices) - validation_size

random.shuffle(selected_indices)

train_indices = selected_indices[:training_size]
validation_indices = selected_indices[training_size:]

print(f"\nTraining images: {len(train_indices)}")
print(f"Validation images: {len(validation_indices)}")


# =========================================================
# CREATE DATASETS WITH DIFFERENT TRANSFORMS
# =========================================================

train_dataset_base = datasets.ImageFolder(
    DATASET_DIR,
    transform=train_transform
)

validation_dataset_base = datasets.ImageFolder(
    DATASET_DIR,
    transform=validation_transform
)

train_dataset = Subset(
    train_dataset_base,
    train_indices
)

validation_dataset = Subset(
    validation_dataset_base,
    validation_indices
)


# =========================================================
# DATA LOADERS
# =========================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

validation_loader = DataLoader(
    validation_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# =========================================================
# SAVE CLASS NAMES
# =========================================================

with open(CLASS_NAMES_PATH, "w") as file:
    json.dump(class_names, file, indent=4)

print("\nClass names saved successfully.")


# =========================================================
# LOAD MOBILENETV2
# =========================================================

print("\nLoading MobileNetV2...")

weights = models.MobileNet_V2_Weights.DEFAULT

model = models.mobilenet_v2(
    weights=weights
)


# Freeze pretrained feature extractor
for parameter in model.features.parameters():
    parameter.requires_grad = False


# Replace final classifier for our 38 classes
model.classifier[1] = nn.Linear(
    model.last_channel,
    len(class_names)
)

model = model.to(DEVICE)


# =========================================================
# LOSS AND OPTIMIZER
# =========================================================

criterion = nn.CrossEntropyLoss()

optimizer = optim.Adam(
    model.classifier.parameters(),
    lr=LEARNING_RATE
)


# =========================================================
# TRAINING FUNCTION
# =========================================================

print("\nStarting fast training...")
print("=" * 55)

for epoch in range(NUM_EPOCHS):

    model.train()

    running_loss = 0.0
    correct_predictions = 0
    total_predictions = 0

    print(
        f"\nEpoch [{epoch + 1}/{NUM_EPOCHS}] started..."
    )

    for batch_number, (images, labels) in enumerate(
        train_loader,
        start=1
    ):

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        running_loss += loss.item()

        _, predictions = torch.max(outputs, 1)

        correct_predictions += (
            predictions == labels
        ).sum().item()

        total_predictions += labels.size(0)


        # Show progress every 20 batches
        if batch_number % 20 == 0:

            current_accuracy = (
                100
                * correct_predictions
                / total_predictions
            )

            print(
                f"Epoch {epoch + 1} | "
                f"Batch {batch_number}/{len(train_loader)} | "
                f"Loss: {loss.item():.4f} | "
                f"Accuracy: {current_accuracy:.2f}%"
            )


    # =====================================================
    # VALIDATION
    # =====================================================

    model.eval()

    validation_correct = 0
    validation_total = 0

    with torch.no_grad():

        for images, labels in validation_loader:

            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            outputs = model(images)

            _, predictions = torch.max(outputs, 1)

            validation_correct += (
                predictions == labels
            ).sum().item()

            validation_total += labels.size(0)


    train_accuracy = (
        100
        * correct_predictions
        / total_predictions
    )

    validation_accuracy = (
        100
        * validation_correct
        / validation_total
    )

    average_loss = (
        running_loss
        / len(train_loader)
    )


    print("\n" + "-" * 55)
    print(
        f"Epoch [{epoch + 1}/{NUM_EPOCHS}] COMPLETED"
    )
    print(
        f"Average Loss: {average_loss:.4f}"
    )
    print(
        f"Training Accuracy: {train_accuracy:.2f}%"
    )
    print(
        f"Validation Accuracy: {validation_accuracy:.2f}%"
    )
    print("-" * 55)


# =========================================================
# SAVE MODEL
# =========================================================

torch.save(
    {
        "model_state_dict": model.state_dict(),
        "class_names": class_names,
        "num_classes": len(class_names),
        "image_size": 128
    },
    MODEL_PATH
)


# =========================================================
# COMPLETION MESSAGE
# =========================================================

print("\n" + "=" * 55)
print("TRAINING COMPLETED SUCCESSFULLY!")
print("=" * 55)

print(f"\nModel saved at:")
print(MODEL_PATH)

print(f"\nClasses saved at:")
print(CLASS_NAMES_PATH)

print("\nDataset used:")
print(f"38 crop/disease classes")
print(
    f"Maximum {MAX_IMAGES_PER_CLASS} "
    f"images per class"
)
print(f"Total epochs: {NUM_EPOCHS}")

print("\n" + "=" * 55)