import os
import random
import shutil
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.cuda.empty_cache()
print("Using device:", device)

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

set_seed(42)

base_dir = "/data/czx/StreetlightsClassification/Datasets/Public"
train_dir = os.path.join(base_dir, "train")
val_dir = os.path.join(base_dir, "val")
test_dir = os.path.join(base_dir, "test")

if not (os.path.exists(train_dir) and os.path.exists(val_dir) and os.path.exists(test_dir)):
    print("Performing dataset split...")

    categories = ["covered", "dim", "off", "on"]

    for d in [train_dir, val_dir, test_dir]:
        os.makedirs(d, exist_ok=True)

    for cat in categories:
        os.makedirs(os.path.join(train_dir, cat), exist_ok=True)
        os.makedirs(os.path.join(val_dir, cat), exist_ok=True)
        os.makedirs(os.path.join(test_dir, cat), exist_ok=True)

        src_cat_dir = os.path.join(base_dir, cat)
        files = [
            f for f in os.listdir(src_cat_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp"))
        ]
        random.shuffle(files)

        n = len(files)
        n_train = int(n * 0.8)
        n_val = int(n * 0.1)

        train_files = files[:n_train]
        val_files = files[n_train:n_train + n_val]
        test_files = files[n_train + n_val:]

        for f in train_files:
            shutil.copy(os.path.join(src_cat_dir, f), os.path.join(train_dir, cat, f))
        for f in val_files:
            shutil.copy(os.path.join(src_cat_dir, f), os.path.join(val_dir, cat, f))
        for f in test_files:
            shutil.copy(os.path.join(src_cat_dir, f), os.path.join(test_dir, cat, f))

    print("Dataset split completed!")
else:
    print("train/val/test already exists. Skip dataset split.")

data_transforms = {
    "train": transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ]),
    "val": transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ]),
    "test": transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ]),
}

image_datasets = {
    "train": datasets.ImageFolder(train_dir, data_transforms["train"]),
    "val": datasets.ImageFolder(val_dir, data_transforms["val"]),
    "test": datasets.ImageFolder(test_dir, data_transforms["test"]),
}

dataloaders = {
    "train": DataLoader(image_datasets["train"], batch_size=8, shuffle=True, num_workers=2),
    "val": DataLoader(image_datasets["val"], batch_size=8, shuffle=False, num_workers=2),
    "test": DataLoader(image_datasets["test"], batch_size=8, shuffle=False, num_workers=2),
}

class_names = image_datasets["train"].classes
num_classes = len(class_names)
print("Classes:", class_names)

model = models.regnet_y_400mf(weights=models.RegNet_Y_400MF_Weights.DEFAULT)
model.fc = nn.Linear(model.fc.in_features, num_classes)
model = model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.0005)

save_path = "/data/czx/StreetlightsClassification/RegNetY400mf/best_regnet_y_400mf_public.pth"
os.makedirs(os.path.dirname(save_path), exist_ok=True)

num_epochs = 50
best_acc = -1.0

for epoch in range(num_epochs):
    print(f"\nEpoch {epoch + 1}/{num_epochs}")
    model.train()

    running_loss = 0.0
    running_corrects = 0

    for inputs, labels in tqdm(dataloaders["train"]):
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        _, preds = torch.max(outputs, 1)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        running_corrects += torch.sum(preds == labels).item()

    epoch_loss = running_loss / len(image_datasets["train"])
    epoch_acc = running_corrects / len(image_datasets["train"])
    print(f"Train Loss: {epoch_loss:.4f}  Acc: {epoch_acc:.4f}")

    model.eval()
    val_correct = 0

    with torch.no_grad():
        for inputs, labels in dataloaders["val"]:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            val_correct += torch.sum(preds == labels).item()

    val_acc = val_correct / len(image_datasets["val"])
    print(f"Val Acc: {val_acc:.4f}")

    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(model.state_dict(), save_path)
        print(f"Best Model Saved -> {save_path}")

print("\nTraining Finished!")

model.load_state_dict(torch.load(save_path, map_location=device))
model.eval()

all_preds = []
all_labels = []
correct = 0

with torch.no_grad():
    for inputs, labels in dataloaders["test"]:
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        _, preds = torch.max(outputs, 1)

        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        correct += torch.sum(preds == labels).item()

test_acc = correct / len(image_datasets["test"])
print(f"\nFinal Test Accuracy: {test_acc:.4f}")

cm = confusion_matrix(all_labels, all_preds)

plt.figure(figsize=(8, 6))
plt.imshow(cm, cmap="Blues")
plt.colorbar()
plt.xticks(np.arange(len(class_names)), class_names, rotation=45)
plt.yticks(np.arange(len(class_names)), class_names)

for i in range(len(class_names)):
    for j in range(len(class_names)):
        plt.text(j, i, cm[i, j], ha="center", va="center", color="black")

plt.title("Confusion Matrix - RegNetY-400MF")
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.tight_layout()
plt.show()