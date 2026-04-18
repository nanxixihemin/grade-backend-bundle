
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from pathlib import Path

app = Flask(__name__, static_folder="static", static_url_path="")
DB_PATH = Path("grades.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def score_to_gpa(score):
    if score is None:
        return None
    score = float(score)
    if score >= 90: return 4.0
    if score >= 85: return 3.7
    if score >= 80: return 3.2
    if score >= 75: return 2.7
    if score >= 70: return 2.2
    if score >= 65: return 1.7
    if score >= 60: return 1.2
    return 0.0

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            semester TEXT NOT NULL,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            credit REAL NOT NULL,
            score REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT,
            time TEXT,
            result TEXT,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/api/grades")
def get_grades():
    conn = get_conn()
    rows = conn.execute("SELECT id, score FROM courses ORDER BY id").fetchall()
    conn.close()
    return jsonify({str(r["id"]): r["score"] for r in rows})

@app.post("/api/grades")
def set_grade():
    data = request.get_json(force=True)
    course_id = data.get("course_id")
    score = data.get("score")
    if course_id is None:
        return jsonify({"error": "course_id required"}), 400
    if score in ("", None):
        score = None
    else:
        try:
            score = float(score)
        except Exception:
            return jsonify({"error": "invalid score"}), 400

    conn = get_conn()
    conn.execute("UPDATE courses SET score = ? WHERE id = ?", (score, int(course_id)))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.get("/api/stats")
def get_stats():
    conn = get_conn()
    rows = conn.execute("SELECT credit, score FROM courses").fetchall()
    conn.close()
    rows = [dict(r) for r in rows]
    done = [r for r in rows if r["score"] is not None]
    all_courses = len(rows)
    done_courses = len(done)
    all_credits = sum(r["credit"] for r in rows)
    done_credits = sum(r["credit"] for r in done)
    avg_score = (sum(r["score"] for r in done) / done_courses) if done_courses else None
    avg_gpa = (
        sum(score_to_gpa(r["score"]) * r["credit"] for r in done) / done_credits
        if done_credits else None
    )
    return jsonify({
        "done_courses": done_courses,
        "all_courses": all_courses,
        "done_credits": done_credits,
        "all_credits": all_credits,
        "avg_score": avg_score,
        "avg_gpa": avg_gpa,
    })

@app.get("/api/records")
def get_records():
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, name, category, status, time, result, note
        FROM records
        ORDER BY rowid DESC
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.post("/api/records")
def replace_records():
    data = request.get_json(force=True)
    if not isinstance(data, list):
        return jsonify({"error": "list required"}), 400

    conn = get_conn()
    conn.execute("DELETE FROM records")
    for item in data:
        conn.execute("""
            INSERT INTO records (id, name, category, status, time, result, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(item.get("id")),
            item.get("name", ""),
            item.get("category", ""),
            item.get("status", ""),
            item.get("time", ""),
            item.get("result", ""),
            item.get("note", ""),
        ))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
