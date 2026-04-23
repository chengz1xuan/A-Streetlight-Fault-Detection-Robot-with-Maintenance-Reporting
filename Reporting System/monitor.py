'''

import os
import time
import shutil
import pymysql
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ==========================
# 1) 数据库连接
# ==========================
db = pymysql.connect(
    host="localhost",
    user="root",
    password="Czx20040119",
    database="streetlight_db",
    charset="utf8mb4"
)
cursor = db.cursor()

# ==========================
# 2) 加载维修人员
# ==========================
def load_workers():
    cursor.execute("SELECT worker_id FROM workers ORDER BY worker_id")
    result = cursor.fetchall()
    return [row[0] for row in result]

workers = load_workers()
worker_index = 0


def get_next_worker():
    global worker_index
    worker = workers[worker_index]
    worker_index = (worker_index + 1) % len(workers)
    return worker


# ==========================
# 3) 需要监听的目录
# ==========================
WATCH_FOLDER = r"/Users/chengzixuan/WKU/Capstone Project/Data"
STATIC_FOLDER = "/Users/chengzixuan/VSCode/Capstone/static/images"

print("监听目录：", WATCH_FOLDER)
print("目录存在：", os.path.exists(WATCH_FOLDER))
print("目录内容：", os.listdir(WATCH_FOLDER))


# ==========================
# 4) 解析文件名：4段式
# ==========================
def parse_filename(filename):
    base = os.path.splitext(filename)[0]
    parts = base.split("_")
    if len(parts) < 4:
        print("文件名格式错误：", filename)
        return None

    lamp_id = parts[0]
    gps = parts[1]
    status = parts[2]

    # 时间字段可能包含重复编号（例如 _1）
    time_raw = parts[3]

    # 分解时间：YYYY-MM-DD-HH-MM-SS
    t = time_raw.split("-")
    if len(t) != 6:
        print("时间格式错误：", time_raw)
        return None

    # 拼成 MySQL 可接受格式
    detection_time = f"{t[0]}-{t[1]}-{t[2]} {t[3]}:{t[4]}:{t[5]}"

    return lamp_id, gps, status, detection_time



# ==========================
# 5) 数据库插入
# ==========================
def insert_to_db(original_path):
    filename = os.path.basename(original_path)

    parsed = parse_filename(filename)
    if not parsed:
        return

    lamp_id, gps, status, detection_time = parsed
    worker = get_next_worker()

    # 防重复覆盖：生成唯一文件名
    dst_path = os.path.join(STATIC_FOLDER, filename)
    base, ext = os.path.splitext(filename)
    count = 1
    while os.path.exists(dst_path):
        new_filename = f"{base}_{count}{ext}"
        dst_path = os.path.join(STATIC_FOLDER, new_filename)
        count += 1
    final_filename = os.path.basename(dst_path)

    shutil.copy(original_path, dst_path)

    web_path = f"/static/images/{final_filename}"

    # --- 防止重复插入 ---
    cursor.execute("SELECT 1 FROM streetlight_records WHERE file_path=%s", (web_path,))
    if cursor.fetchone():
        print(f"[跳过] {filename} 已存在数据库")
        return


    sql = """
    INSERT INTO streetlight_records
    (lamp_id, gps, status, file_path, repair_worker, created_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (lamp_id, gps, status, web_path, worker, detection_time))
    db.commit()

    print(f"[已写入] {final_filename} → 工人: {worker} → 时间: {detection_time}")


# ==========================
# 6) 事件监听（macOS 兼容）
# ==========================
class Handler(FileSystemEventHandler):

    processed_files = set()   # 避免重复处理同一个文件

    def on_any_event(self, event):
        if event.is_directory:
            return

        file_path = event.src_path

        # macOS Finder 会触发多个 modified → 忽略它们
        if event.event_type == "modified":
            return

        # 只处理 created 和 moved
        if event.event_type in ("created", "moved"):
            filename = os.path.basename(file_path)

            # 如果处理过同一个文件，则跳过
            if filename in self.processed_files:
                print(f"重复事件忽略：{filename}")
                return

            self.processed_files.add(filename)

            print(f"处理事件：{event.event_type} → {file_path}")
            insert_to_db(file_path)




# ==========================
# 7) 首次扫描
# ==========================

def scan_existing():
    print("扫描既有文件...")
    for fname in os.listdir(WATCH_FOLDER):
        full_path = os.path.join(WATCH_FOLDER, fname)
        if os.path.isfile(full_path):
            insert_to_db(full_path)


# ==========================
# 8) 主程序
# ==========================
if __name__ == "__main__":
    scan_existing()

    print("开始监听新文件...")
    observer = Observer()
    observer.schedule(Handler(), WATCH_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

'''

import os
import time
import shutil
import pymysql
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ==========================
# 1) 数据库连接
# ==========================
db = pymysql.connect(
    host="localhost",
    user="root",
    password="Czx20040119",
    database="streetlight_db",
    charset="utf8mb4"
)
cursor = db.cursor()

# ==========================
# 2) 加载维修人员
# ==========================
def load_workers():
    cursor.execute("SELECT worker_id FROM workers ORDER BY worker_id")
    result = cursor.fetchall()
    return [row[0] for row in result]

workers = load_workers()
worker_index = 0

def get_next_worker():
    global worker_index
    if not workers:
        return None
    worker = workers[worker_index]
    worker_index = (worker_index + 1) % len(workers)
    return worker


# ==========================
# 3) 需要监听的目录
# ==========================
WATCH_FOLDER = r"/Users/chengzixuan/WKU/Capstone Project/Data"
STATIC_FOLDER = "/Users/chengzixuan/VSCode/Capstone/static/images"

print("监听目录：", WATCH_FOLDER)
print("目录存在：", os.path.exists(WATCH_FOLDER))
print("目录内容：", os.listdir(WATCH_FOLDER))


# ==========================
# 4) 解析文件名：4段式
# ==========================
def parse_filename(filename):
    base = os.path.splitext(filename)[0]
    parts = base.split("_")
    if len(parts) < 4:
        print("文件名格式错误：", filename)
        return None

    lamp_id = parts[0]
    gps = parts[1]
    status = parts[2]
    time_raw = parts[3]

    t = time_raw.split("-")
    if len(t) != 6:
        print("时间格式错误：", time_raw)
        return None

    detection_time = f"{t[0]}-{t[1]}-{t[2]} {t[3]}:{t[4]}:{t[5]}"
    return lamp_id, gps, status, detection_time


# ==========================
# 5) 数据库插入
# ==========================
def insert_to_db(original_path):
    filename = os.path.basename(original_path)

    parsed = parse_filename(filename)
    if not parsed:
        return

    lamp_id, gps, status, detection_time = parsed

    # 先查重：按 lamp_id + created_at 判断是否已存在
    cursor.execute("""
        SELECT 1 FROM streetlight_records
        WHERE lamp_id=%s AND created_at=%s
    """, (lamp_id, detection_time))

    if cursor.fetchone():
        print(f"[跳过] {filename} 已存在数据库")
        return

    worker = get_next_worker()

    # 再复制文件
    dst_path = os.path.join(STATIC_FOLDER, filename)
    base, ext = os.path.splitext(filename)
    count = 1
    while os.path.exists(dst_path):
        new_filename = f"{base}_{count}{ext}"
        dst_path = os.path.join(STATIC_FOLDER, new_filename)
        count += 1

    final_filename = os.path.basename(dst_path)
    shutil.copy2(original_path, dst_path)

    web_path = f"/static/images/{final_filename}"

    sql = """
    INSERT INTO streetlight_records
    (lamp_id, gps, status, file_path, repair_worker, created_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (lamp_id, gps, status, web_path, worker, detection_time))
    db.commit()

    print(f"[已写入] {final_filename} → 工人: {worker} → 时间: {detection_time}")


# ==========================
# 6) 事件监听
# ==========================
class Handler(FileSystemEventHandler):
    processed_files = set()

    def on_any_event(self, event):
        if event.is_directory:
            return

        if event.event_type == "modified":
            return

        file_path = event.src_path

        if event.event_type in ("created", "moved"):
            filename = os.path.basename(file_path)

            if filename in self.processed_files:
                print(f"重复事件忽略：{filename}")
                return

            # 可选：只处理图片文件
            if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp")):
                print(f"非图片文件忽略：{filename}")
                return

            self.processed_files.add(filename)

            print(f"处理事件：{event.event_type} → {file_path}")
            time.sleep(0.5)   # 防止文件还没写完
            insert_to_db(file_path)


# ==========================
# 7) 主程序
# ==========================
if __name__ == "__main__":
    print("开始监听新文件...")
    observer = Observer()
    observer.schedule(Handler(), WATCH_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()