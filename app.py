from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import threading
import time
import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "rahasia123"

DB_NAME = "bel.db"
SOUND_FOLDER = "static/sounds"
UPLOAD_FOLDER = "uploads"

# Pastikan folder ada
os.makedirs(SOUND_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- FUNGSI DATABASE ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Tabel sekolah
        c.execute("""
            CREATE TABLE IF NOT EXISTS school (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT,
                alamat TEXT,
                kepala TEXT
            )
        """)
        # Tabel jadwal
        c.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT,
                time TEXT,
                label TEXT,
                sound TEXT,
                source TEXT DEFAULT 'default',
                is_playing INTEGER DEFAULT 0
            )
        """)
        # Isi default school kalau belum ada
        c.execute("SELECT COUNT(*) FROM school")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO school (nama, alamat, kepala) VALUES (?, ?, ?)",
                      ("SMA Negeri 1 Contoh", "Jl. Pendidikan No. 123", "Budi Santoso"))
        conn.commit()

def ensure_columns():
    """Pastikan kolom terbaru ada walaupun DB lama dipakai"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("PRAGMA table_info(schedules)")
        columns = [col[1] for col in c.fetchall()]
        if "is_playing" not in columns:
            c.execute("ALTER TABLE schedules ADD COLUMN is_playing INTEGER DEFAULT 0")
        if "source" not in columns:
            c.execute("ALTER TABLE schedules ADD COLUMN source TEXT DEFAULT 'default'")
        conn.commit()

def get_school():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM school LIMIT 1").fetchone()

def get_schedules(day=None):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        if day:
            return conn.execute("SELECT * FROM schedules WHERE day=? ORDER BY time", (day,)).fetchall()
        else:
            return conn.execute("SELECT * FROM schedules ORDER BY day, time").fetchall()

def get_schedule_by_id(id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM schedules WHERE id=?", (id,)).fetchone()

def add_schedule(day, time, label, sound, source="default"):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO schedules (day, time, label, sound, source) VALUES (?, ?, ?, ?, ?)",
                    (day, time, label, sound, source))
        conn.commit()
        return cur.lastrowid

def update_schedule(id, day, time, label, sound, source="default"):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE schedules SET day=?, time=?, label=?, sound=?, source=? WHERE id=?",
                     (day, time, label, sound, source, id))
        conn.commit()

def delete_schedule(id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM schedules WHERE id=?", (id,))
        conn.commit()

def reset_data():
    """Reset jadwal default"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM schedules")

        default_jadwal = {
            "Senin":  [("07:00", "Masuk"), ("09:00", "Istirahat"), ("12:00", "Sholat / Istirahat"), ("15:00", "Pulang")],
            "Selasa": [("07:00", "Masuk"), ("09:00", "Istirahat"), ("12:00", "Sholat / Istirahat"), ("15:00", "Pulang")],
            "Rabu":   [("07:00", "Masuk"), ("09:00", "Istirahat"), ("12:00", "Sholat / Istirahat"), ("15:00", "Pulang")],
            "Kamis":  [("07:00", "Masuk"), ("09:00", "Istirahat"), ("12:00", "Sholat / Istirahat"), ("15:00", "Pulang")],
            "Jumat":  [("07:00", "Masuk"), ("09:00", "Istirahat"), ("11:30", "Sholat Jumat"), ("14:00", "Pulang")],
            "Sabtu":  [("07:00", "Masuk"), ("09:00", "Istirahat"), ("12:00", "Sholat / Istirahat"), ("13:00", "Pulang")],
            "Minggu":[("07:00", "Masuk"), ("09:00", "Istirahat"), ("12:00", "Sholat / Istirahat"), ("15:00", "Pulang")],
        }

        for day, items in default_jadwal.items():
            for time_, label in items:
                c.execute("INSERT INTO schedules (day, time, label, sound, source) VALUES (?, ?, ?, ?, ?)",
                          (day, time_, label, "default.mp3", "default"))
        conn.commit()

# --- BEL OTOMATIS ---
def play_sound(file_path):
    os.system(f"termux-media-player play '{file_path}'")

def auto_bell():
    while True:
        now = datetime.datetime.now()
        day_map = {
            "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
            "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
        }
        day = day_map.get(now.strftime("%A"), now.strftime("%A"))
        time_now = now.strftime("%H:%M")
        schedules = get_schedules(day)
        for s in schedules:
            if s["time"] == time_now:
                path = os.path.join(UPLOAD_FOLDER if s["source"] == "upload" else SOUND_FOLDER, s["sound"])
                if os.path.exists(path):
                    play_sound(path)
                time.sleep(60)
        time.sleep(1)

threading.Thread(target=auto_bell, daemon=True).start()

# --- ROUTES ---
@app.route("/")
def index():
    # Mapping nama hari
    hari_map = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu",
    }
    today = datetime.datetime.now().strftime("%A")
    hari_ini = hari_map.get(today, today)

    # Ambil jadwal hari ini
    schedules = get_schedules(hari_ini)
    school = get_school()

    # ======= PASARAN + TANGGAL =======
    tanggal = datetime.date.today()
    timestamp = datetime.datetime.now().timestamp()
    pasaran_list = ["Legi", "Pahing", "Pon", "Wage", "Kliwon"]
    pasaran = pasaran_list[int((timestamp // 86400 + 3) % 5)]

    bulan_map = {
        "01": "Januari", "02": "Februari", "03": "Maret", "04": "April",
        "05": "Mei", "06": "Juni", "07": "Juli", "08": "Agustus",
        "09": "September", "10": "Oktober", "11": "November", "12": "Desember"
    }
    bulan = bulan_map[tanggal.strftime("%m")]

    # Format hari + pasaran + tanggal
    hari_pasaran = f"{hari_ini} {pasaran}, {tanggal.day} {bulan} {tanggal.year}"
    # ===================================

    return render_template(
        "index.html",
        schedules=schedules,
        school=school,
        hari_pasaran=hari_pasaran  # <-- ini dikirim ke template
      )
@app.route("/schedules")
def schedules_page():
    schedules = get_schedules()
    sound_files = os.listdir(SOUND_FOLDER)
    return render_template("schedules.html", schedules=schedules, sound_files=sound_files)

# --- Tambah jadwal via AJAX ---
@app.route("/add_form")
def add_form():
    sound_dir = "static/sounds"
    sound_files = os.listdir(sound_dir) if os.path.exists(sound_dir) else []
    return render_template("add_form.html", sound_files=sound_files)
@app.route("/add", methods=["POST"])
def add():
    day = request.form["day"]
    time_ = request.form["time"]
    label = request.form["label"]

    sound = request.form.get("sound")
    file = request.files.get("sound_upload")

    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        sound = filename
        source = "upload"
    else:
        source = "default"

    new_id = add_schedule(day, time_, label, sound, source)
    jadwal = get_schedule_by_id(new_id)
    return jsonify(success=True, **dict(jadwal))

# --- Edit jadwal via AJAX ---
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    jadwal = get_schedule_by_id(id)
    if not jadwal:
        return jsonify(success=False, error="Jadwal tidak ditemukan"), 404

    if request.method == "POST":
        day = request.form["day"]
        time_ = request.form["time"]
        label = request.form["label"]

        sound = request.form.get("sound")
        file = request.files.get("sound_upload")

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            sound = filename
            source = "upload"
        else:
            source = "default"

        update_schedule(id, day, time_, label, sound, source)
        updated = get_schedule_by_id(id)
        return jsonify(success=True, **dict(updated))

    sound_files = os.listdir(SOUND_FOLDER)
    return render_template("edit_form.html", s=jadwal, sound_files=sound_files)
# ==============================
# TAMBAH JADWAL (AJAX MODAL)
# ==============================
@app.route("/add-ajax", methods=["GET", "POST"])
def add_ajax():
    if request.method == "POST":
        day = request.form["day"]
        time = request.form["time"]
        label = request.form["label"]

        sound = request.form.get("sound")  # dari dropdown
        file = request.files.get("sound_upload")

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(upload_path)
            sound = filename
            source = "upload"
        else:
            source = "default"

        add_schedule(day, time, label, sound, source)

        return jsonify({
            "success": True,
            "day": day,
            "time": time,
            "label": label,
            "sound": sound
        })

    # GET → load form ke modal
    sound_files = os.listdir(SOUND_FOLDER)
    return render_template("add_form.html", sound_files=sound_files)

# --- Hapus jadwal via AJAX ---
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    delete_schedule(id)
    return jsonify(success=True)

# --- Reset via AJAX ---
@app.route("/reset", methods=["POST"])
def reset():
    reset_data()
    return jsonify(success=True)

# --- Settings sekolah ---
@app.route("/settings", methods=["GET", "POST"])
def settings():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if request.method == "POST":
            nama = request.form.get("nama")
            alamat = request.form.get("alamat")
            kepala = request.form.get("kepala")
            c.execute("UPDATE school SET nama=?, alamat=?, kepala=? WHERE id=1", (nama, alamat, kepala))
            conn.commit()
            flash("✅ Pengaturan berhasil disimpan!", "success")
            return redirect(url_for("settings"))
        school = c.execute("SELECT * FROM school WHERE id=1").fetchone()
    return render_template("settings.html", school=school)

# --- Jalankan ---
if __name__ == "__main__":
    init_db()
    ensure_columns()

    # pastikan ada default.mp3
    default_path = os.path.join(SOUND_FOLDER, "default.mp3")
    if not os.path.exists(default_path):
        with open(default_path, "wb") as f:
            f.write(b"\x49\x44\x33")  # ID3 header minimal

    # kalau kosong isi default
    with sqlite3.connect(DB_NAME) as conn:
        if conn.execute("SELECT COUNT(*) FROM schedules").fetchone()[0] == 0:
            reset_data()

    app.run(debug=True, host="0.0.0.0", port=9090)