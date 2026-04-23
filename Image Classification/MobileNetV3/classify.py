import os
import shutil
from PIL import Image

import torch
import torch.nn as nn
from torchvision import transforms, models


# =========================================
# 1) 路径配置
# =========================================
input_dir = "/data/czx/StreetlightsClassification/Datasets/classify"
model_path = "/data/czx/StreetlightsClassification/MobileNetV3/best_mobilenetV3_public.pth"
output_dir = "/data/czx/StreetlightsClassification/Datasets/results"

# 必须和训练时类别顺序一致
class_names = ["covered", "dim", "off", "on"]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)


# =========================================
# 2) 创建输出文件夹
# =========================================
os.makedirs(output_dir, exist_ok=True)


# =========================================
# 3) 图像预处理（必须和训练时一致）
# =========================================
transform = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])


# =========================================
# 4) 加载模型
# =========================================
model = models.mobilenet_v3_large(weights=None)
model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, len(class_names))
model.load_state_dict(torch.load(model_path, map_location=device))
model = model.to(device)
model.eval()

print("Model loaded:", model_path)


# =========================================
# 5) 判断是否为图片文件
# =========================================
def is_image_file(filename):
    valid_ext = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    return filename.lower().endswith(valid_ext)


# =========================================
# 6) 单张图片预测
# =========================================
def predict_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image_tensor)
        _, pred = torch.max(outputs, 1)

    return class_names[pred.item()]


# =========================================
# 7) 在原文件名中插入类别
#    原格式:
#    LAMP012_27.917422,120.651672_2025-12-03-23-27-31.jpg
#    新格式:
#    LAMP012_27.917422,120.651672_dim_2025-12-03-23-27-31.jpg
# =========================================
def add_class_to_filename(filename, pred_class):
    name, ext = os.path.splitext(filename)
    parts = name.split("_")

    if len(parts) >= 3:
        lamp_id = parts[0]
        location = parts[1]
        timestamp = "_".join(parts[2:])
        new_name = f"{lamp_id}_{location}_{pred_class}_{timestamp}{ext}"
    else:
        new_name = f"{name}_{pred_class}{ext}"

    return new_name


# =========================================
# 8) 遍历并处理图片
#    如果预测结果是 on -> 直接删除
#    否则 -> 重命名并移动到 output_dir
# =========================================
files = sorted(os.listdir(input_dir))

if not files:
    print(f"No files found in {input_dir}")

for filename in files:
    src_path = os.path.join(input_dir, filename)

    if not os.path.isfile(src_path):
        continue

    if not is_image_file(filename):
        print(f"Skip non-image file: {filename}")
        continue

    try:
        pred_class = predict_image(src_path)

        # 如果预测为 on，直接删除原图
        if pred_class == "on":
            os.remove(src_path)
            print(f"{filename} -> deleted (predicted: on)")
            continue

        # 否则在文件名中插入类别并移动
        new_filename = add_class_to_filename(filename, pred_class)
        dst_path = os.path.join(output_dir, new_filename)

        # 如果目标目录已经有同名文件，就跳过，避免覆盖
        if os.path.exists(dst_path):
            print(f"Skip {filename}: target already exists at {dst_path}")
            continue

        # 移动文件
        shutil.move(src_path, dst_path)
        print(f"{filename} -> {new_filename}")

    except Exception as e:
        print(f"Error processing {filename}: {e}")

print("Done.")