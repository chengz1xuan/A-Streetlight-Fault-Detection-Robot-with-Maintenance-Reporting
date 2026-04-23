from flask import Flask, render_template, request, redirect
import pymysql

app = Flask(__name__)

def get_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Czx20040119",
        database="streetlight_db",
        charset="utf8mb4"
    )


# ============================
# 管理页面（SHOW ALL TASKS）
# ============================
@app.route("/")
def index():
    db = get_db()
    cursor = db.cursor()

    # 获取所有任务（含工人姓名）
    cursor.execute("""
        SELECT 
            s.id,           -- r[0]
            s.lamp_id,      -- r[1]
            s.gps,          -- r[2]
            s.status,       -- r[3]
            s.file_path,    -- r[4]
            s.created_at,   -- r[5]
            w.worker_name,  -- r[6]
            s.repair_status,-- r[7]
            s.repair_worker -- r[8]
        FROM streetlight_records s
        LEFT JOIN workers w
        ON s.repair_worker = w.worker_id
        ORDER BY s.created_at DESC
    """)

    rows = cursor.fetchall()

    # 获取所有维修人员
    cursor.execute("SELECT worker_id, worker_name FROM workers")
    workers = cursor.fetchall()

    db.close()
    return render_template("table.html", rows=rows, workers=workers)


# ============================
# 维修人员任务页面 (按 worker_id)
# ============================
@app.route("/worker/<int:worker_id>")
def worker_page(worker_id):
    db = get_db()
    cursor = db.cursor()

    # 获取工人名
    cursor.execute("SELECT worker_name FROM workers WHERE worker_id=%s", (worker_id,))
    worker_name = cursor.fetchone()[0]

    # 获取该工人任务
    cursor.execute("""
        SELECT id, lamp_id, gps, status, file_path, created_at, repair_status
        FROM streetlight_records
        WHERE repair_worker=%s
        ORDER BY id DESC
    """, (worker_id,))
    rows = cursor.fetchall()

    db.close()

    return render_template("worker.html", worker=worker_name, rows=rows)



# ============================
# 更新任务状态（POST）
# ============================
@app.route("/update_status", methods=["POST"])
def update_status():
    task_id = request.form["task_id"]
    new_status = request.form["status"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE streetlight_records
        SET repair_status=%s
        WHERE id=%s
    """, (new_status, task_id))

    db.commit()
    db.close()

    return redirect(request.referrer)

# ============================
# 更新 repair_worker
# ============================
@app.route("/update_worker", methods=["POST"])
def update_worker():
    task_id = request.form["task_id"]
    new_worker = request.form["worker_id"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE streetlight_records
        SET repair_worker=%s
        WHERE id=%s
    """, (new_worker, task_id))

    db.commit()
    db.close()

    return redirect(request.referrer)


if __name__ == "__main__":
    app.run(debug=True)
