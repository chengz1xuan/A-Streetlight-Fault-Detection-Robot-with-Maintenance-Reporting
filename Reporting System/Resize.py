'''
from PIL import Image
import os

# 输入与输出文件夹路径
input_folder = "/Users/chengzixuan/Desktop/WKU/Capstone Project/数据/WKU路灯_20251127"        # 原图所在文件夹
output_folder = "/Users/chengzixuan/Desktop/WKU/Capstone Project/数据/WKU路灯_20251127_resize"   # 输出文件夹

# 如果输出文件夹不存在则创建
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 遍历文件夹内所有文件
for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.jpeg')):
        img_path = os.path.join(input_folder, filename)
        img = Image.open(img_path)

        # 统一调整为 512x512 并保持比例 + 填充
        img = img.resize((512, 512), Image.LANCZOS)

        # 保存图片
        save_path = os.path.join(output_folder, filename)
        img.save(save_path)
        print(f"Saved: {save_path}")

print("All images resized to 512x512 successfully!")
'''

from PIL import Image, ExifTags
import os

def fix_orientation(img):
    try:
        exif = img._getexif()
        if exif:
            for k, v in ExifTags.TAGS.items():
                if v == 'Orientation':
                    orientation = exif.get(k)
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
    except:
        pass
    return img

input_folder = r"/Users/chengzixuan/Desktop/WKU/Capstone Project/数据/原始图片/WKU路灯_20251204"
output_folder = r"/Users/chengzixuan/Desktop/WKU/Capstone Project/数据/WKU路灯_20251204_Resize"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.jpeg')):
        img_path = os.path.join(input_folder, filename)
        img = Image.open(img_path)
        img = fix_orientation(img)
        img = img.resize((512, 512), Image.LANCZOS)
        save_path = os.path.join(output_folder, filename)
        img = img.convert("RGB")  # 去掉透明通道
        img.save(save_path)
        print("Saved:", save_path)

print("All images resized to 512x512 successfully!")
