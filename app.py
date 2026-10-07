"""
ACEest Fitness & Gym Management System - Flask Web Application & REST API
Modular service layer providing core gym management, membership tracking,
workout logging, progress analytics, and AI routine generation endpoints.
"""

import os
import sqlite3
import random
from datetime import datetime, timezone, date
from flask import Flask, request, jsonify

DB_NAME = os.environ.get("ACEEST_DB", "aceest_fitness.db")

PROGRAM_TEMPLATES = {
    "Fat Loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
    "Muscle Gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
    "Beginner": ["Full Body 3x/week", "Light Strength + Mobility"]
}


def get_db_connection(db_path=None):
    """Establish connection to SQLite database with Row mapping."""
    target_db = db_path if db_path else DB_NAME
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None):
    """Initialize database tables and seed baseline admin user."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    # Users (for role-based login)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )
    """)

    # Clients
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        age INTEGER,
        height REAL,
        weight REAL,
        program TEXT,
        calories INTEGER,
        target_weight REAL,
        target_adherence INTEGER,
        membership_status TEXT,
        membership_end TEXT
    )
    """)

    # Progress
    cur.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        week TEXT,
        adherence INTEGER
    )
    """)

    # Workouts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        date TEXT,
        workout_type TEXT,
        duration_min INTEGER,
        notes TEXT
    )
    """)

    # Exercises
    cur.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_id INTEGER,
        name TEXT,
        sets INTEGER,
        reps INTEGER,
        weight REAL
    )
    """)

    # Metrics
    cur.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        date TEXT,
        weight REAL,
        waist REAL,
        bodyfat REAL
    )
    """)

    # Add default admin if not exists
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES ('admin', 'admin', 'Admin')")

    conn.commit()
    conn.close()


def create_app(test_config=None):
    """Application factory for ACEest Fitness & Gym Flask App."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "aceest-secret-key-2026"),
        DATABASE=os.environ.get("ACEEST_DB", DB_NAME)
    )

    if test_config:
        app.config.update(test_config)

    # Initialize tables on startup
    with app.app_context():
        init_db(app.config["DATABASE"])

    def db():
        return get_db_connection(app.config["DATABASE"])

    # ------------------ Web / Health Endpoints ------------------

    @app.route("/")
    def index():
        return jsonify({
            "service": "ACEest Fitness & Gym Web Application",
            "version": "1.0.0",
            "status": "operational",
            "endpoints": [
                "/health",
                "/api/auth/login",
                "/api/clients",
                "/api/clients/<name>",
                "/api/clients/<name>/generate-program",
                "/api/clients/<name>/membership",
                "/api/workouts",
                "/api/exercises",
                "/api/metrics",
                "/api/progress"
            ]
        }), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "UP",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200

    # ------------------ Auth Endpoints ------------------

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT username, role FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            return jsonify({
                "status": "success",
                "username": user["username"],
                "role": user["role"]
            }), 200
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    # ------------------ Client Endpoints ------------------

    @app.route("/api/clients", methods=["GET"])
    def get_clients():
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clients ORDER BY name")
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return jsonify(rows), 200

    @app.route("/api/clients", methods=["POST"])
    def add_client():
        data = request.get_json(silent=True) or {}
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "Client name is required"}), 400

        age = data.get("age")
        height = data.get("height")
        weight = data.get("weight")
        program = data.get("program")
        calories = data.get("calories")
        target_weight = data.get("target_weight")
        target_adherence = data.get("target_adherence")
        membership_status = data.get("membership_status", "Active")
        membership_end = data.get("membership_end")

        conn = db()
        cur = conn.cursor()
        try:
            cur.execute("""
            INSERT INTO clients (
                name, age, height, weight, program, calories,
                target_weight, target_adherence, membership_status, membership_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, age, height, weight, program, calories,
                  target_weight, target_adherence, membership_status, membership_end))
            conn.commit()
            new_id = cur.lastrowid
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"error": f"Client '{name}' already exists"}), 409

        conn.close()
        return jsonify({
            "message": f"Client {name} saved successfully",
            "id": new_id
        }), 201

    @app.route("/api/clients/<string:name>", methods=["GET"])
    def get_client_by_name(name):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clients WHERE name=?", (name,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify({"error": f"Client '{name}' not found"}), 404
        return jsonify(dict(row)), 200

    @app.route("/api/clients/<string:name>/generate-program", methods=["POST"])
    def generate_program_for_client(name):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clients WHERE name=?", (name,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": f"Client '{name}' not found"}), 404

        category = random.choice(list(PROGRAM_TEMPLATES.keys()))
        program_detail = random.choice(PROGRAM_TEMPLATES[category])
        cur.execute("UPDATE clients SET program=? WHERE name=?", (program_detail, name))
        conn.commit()
        conn.close()
        return jsonify({
            "status": "success",
            "client": name,
            "category": category,
            "program": program_detail
        }), 200

    @app.route("/api/clients/<string:name>/membership", methods=["GET"])
    def check_client_membership(name):
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT membership_status, membership_end FROM clients WHERE name=?", (name,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify({"error": f"Client '{name}' not found"}), 404
        return jsonify({
            "client": name,
            "membership_status": row["membership_status"],
            "membership_end": row["membership_end"]
        }), 200

    # ------------------ Workout Endpoints ------------------

    @app.route("/api/workouts", methods=["GET"])
    def get_workouts():
        client_name = request.args.get("client_name")
        conn = db()
        cur = conn.cursor()
        if client_name:
            cur.execute("SELECT * FROM workouts WHERE client_name=? ORDER BY date DESC", (client_name,))
        else:
            cur.execute("SELECT * FROM workouts ORDER BY date DESC")
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return jsonify(rows), 200

    @app.route("/api/workouts", methods=["POST"])
    def add_workout():
        data = request.get_json(silent=True) or {}
        client_name = data.get("client_name", "").strip()
        if not client_name:
            return jsonify({"error": "client_name is required"}), 400

        workout_date = data.get("date", date.today().isoformat())
        workout_type = data.get("workout_type", "Strength")
        duration_min = data.get("duration_min", 60)
        notes = data.get("notes", "")

        conn = db()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
        VALUES (?, ?, ?, ?, ?)
        """, (client_name, workout_date, workout_type, duration_min, notes))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({
            "message": "Workout recorded",
            "id": new_id
        }), 201

    # ------------------ Exercise Endpoints ------------------

    @app.route("/api/exercises", methods=["GET"])
    def get_exercises():
        workout_id = request.args.get("workout_id")
        conn = db()
        cur = conn.cursor()
        if workout_id:
            cur.execute("SELECT * FROM exercises WHERE workout_id=?", (workout_id,))
        else:
            cur.execute("SELECT * FROM exercises")
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return jsonify(rows), 200

    @app.route("/api/exercises", methods=["POST"])
    def add_exercise():
        data = request.get_json(silent=True) or {}
        workout_id = data.get("workout_id")
        name = data.get("name", "").strip()
        sets = data.get("sets", 3)
        reps = data.get("reps", 10)
        weight = data.get("weight", 0.0)

        if not workout_id or not name:
            return jsonify({"error": "workout_id and exercise name are required"}), 400

        conn = db()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO exercises (workout_id, name, sets, reps, weight)
        VALUES (?, ?, ?, ?, ?)
        """, (workout_id, name, sets, reps, weight))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({
            "message": "Exercise recorded",
            "id": new_id
        }), 201

    # ------------------ Progress Endpoints ------------------

    @app.route("/api/progress", methods=["GET"])
    def get_progress():
        client_name = request.args.get("client_name")
        conn = db()
        cur = conn.cursor()
        if client_name:
            cur.execute("SELECT * FROM progress WHERE client_name=? ORDER BY id", (client_name,))
        else:
            cur.execute("SELECT * FROM progress ORDER BY id")
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return jsonify(rows), 200

    @app.route("/api/progress", methods=["POST"])
    def add_progress():
        data = request.get_json(silent=True) or {}
        client_name = data.get("client_name", "").strip()
        week = data.get("week", "").strip()
        adherence = data.get("adherence", 0)

        if not client_name or not week:
            return jsonify({"error": "client_name and week are required"}), 400

        conn = db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
            (client_name, week, adherence)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({
            "message": "Progress recorded",
            "id": new_id
        }), 201

    # ------------------ Metrics Endpoints ------------------

    @app.route("/api/metrics", methods=["GET"])
    def get_metrics():
        client_name = request.args.get("client_name")
        conn = db()
        cur = conn.cursor()
        if client_name:
            cur.execute("SELECT * FROM metrics WHERE client_name=? ORDER BY date DESC", (client_name,))
        else:
            cur.execute("SELECT * FROM metrics ORDER BY date DESC")
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return jsonify(rows), 200

    @app.route("/api/metrics", methods=["POST"])
    def add_metrics():
        data = request.get_json(silent=True) or {}
        client_name = data.get("client_name", "").strip()
        if not client_name:
            return jsonify({"error": "client_name is required"}), 400

        metric_date = data.get("date", date.today().isoformat())
        weight = data.get("weight", 0.0)
        waist = data.get("waist", 0.0)
        bodyfat = data.get("bodyfat", 0.0)

        conn = db()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO metrics (client_name, date, weight, waist, bodyfat)
        VALUES (?, ?, ?, ?, ?)
        """, (client_name, metric_date, weight, waist, bodyfat))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({
            "message": "Metrics recorded",
            "id": new_id
        }), 201

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
