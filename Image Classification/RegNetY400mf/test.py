import os
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader


# =========================================
# 1) 配置路径
# =========================================
base_dir = "/data/czx/StreetlightsClassification/Datasets/Public"
test_dir = os.path.join(base_dir, "test")
model_path = "/data/czx/StreetlightsClassification/RegNetY400mf/best_regnet_y_400mf_public.pth"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)


# =========================================
# 2) DataLoader（必须与训练时一致）
# =========================================
test_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

test_dataset = datasets.ImageFolder(test_dir, transform=test_transform)
test_loader = DataLoader(test_dataset, batch_size=4, shuffle=False, num_workers=2)

class_names = test_dataset.classes
print("Classes:", class_names)


# =========================================
# 3) 加载模型
# =========================================
num_classes = 4

model = models.regnet_y_400mf(weights=None)
in_features = model.fc.in_features
model.fc = nn.Linear(in_features, num_classes)

model.load_state_dict(torch.load(model_path, map_location=device))
model = model.to(device)
model.eval()

print("\nModel loaded:", model_path)


# =========================================
# 4) 测试 + 获取预测
# =========================================
all_preds = []
all_labels = []
correct = 0

with torch.no_grad():
    for inputs, labels in test_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        _, preds = torch.max(outputs, 1)

        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

        correct += torch.sum(preds == labels).item()

all_preds = np.array(all_preds)
all_labels = np.array(all_labels)

# =========================================
# 5) Accuracy（按论文公式）
# =========================================
N = len(test_dataset)
accuracy = correct / N
print(f"\nFinal Test Accuracy: {accuracy:.4f}")


# =========================================
# 6) 混淆矩阵
# =========================================
cm = confusion_matrix(all_labels, all_preds)
print("\nConfusion Matrix:")
print(cm)


# =========================================
# 7) 按论文公式计算每一类 Precision / Recall / F1-score
# =========================================
num_classes = len(class_names)

per_class_precision = []
per_class_recall = []
per_class_f1 = []

print("\nPer-class Metrics:")
print("-" * 70)
print(f"{'Class':<12}{'TP':<8}{'FP':<8}{'FN':<8}{'Precision':<12}{'Recall':<12}{'F1-score':<12}")
print("-" * 70)

for i in range(num_classes):
    TP = cm[i, i]
    FP = cm[:, i].sum() - TP
    FN = cm[i, :].sum() - TP

    # Precision_i = TP_i / (TP_i + FP_i)
    precision_i = TP / (TP + FP) if (TP + FP) > 0 else 0.0

    # Recall_i = TP_i / (TP_i + FN_i)
    recall_i = TP / (TP + FN) if (TP + FN) > 0 else 0.0

    # F1_i = 2 * P_i * R_i / (P_i + R_i)
    f1_i = (2 * precision_i * recall_i / (precision_i + recall_i)
            if (precision_i + recall_i) > 0 else 0.0)

    per_class_precision.append(precision_i)
    per_class_recall.append(recall_i)
    per_class_f1.append(f1_i)

    print(f"{class_names[i]:<12}{TP:<8}{FP:<8}{FN:<8}{precision_i:<12.4f}{recall_i:<12.4f}{f1_i:<12.4f}")


# =========================================
# 8) Macro Average（如果论文表格需要单个总指标）
# =========================================
macro_precision = np.mean(per_class_precision)
macro_recall = np.mean(per_class_recall)
macro_f1 = np.mean(per_class_f1)

print("-" * 70)
print(f"{'Macro Avg':<36}{macro_precision:<12.4f}{macro_recall:<12.4f}{macro_f1:<12.4f}")


# =========================================
# 9) 可视化混淆矩阵
# =========================================
plt.figure(figsize=(8, 6))
plt.imshow(cm, cmap="Reds")
plt.colorbar()

plt.xticks(np.arange(len(class_names)), class_names, rotation=45)
plt.yticks(np.arange(len(class_names)), class_names)

for i in range(len(class_names)):
    for j in range(len(class_names)):
        plt.text(j, i, cm[i, j], ha='center', va='center', color='black')

plt.title("Confusion Matrix")
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.tight_layout()
plt.show()