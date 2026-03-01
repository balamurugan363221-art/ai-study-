import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from pypdf import PdfReader
from dotenv import load_dotenv
from ai_helper import get_ai_response

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-key")
DB_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def init_db():
    if not DB_URL:
        print("⚠️ No DATABASE_URL found. Check your .env file or cloud settings.")
        return
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY, username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL, password TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
                    question TEXT NOT NULL, answer TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS study_progress (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
                    subject VARCHAR(255) NOT NULL, hours REAL NOT NULL,
                    date DATE DEFAULT CURRENT_DATE
                );
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
                    filename TEXT NOT NULL, content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session: return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username, email, password = request.form["username"].strip(), request.form["email"].strip(), request.form["password"]
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO users (username,email,password) VALUES (%s,%s,%s)",
                                (username, email, generate_password_hash(password)))
                    conn.commit()
            return redirect(url_for("login"))
        except psycopg2.IntegrityError:
            error = "Username or email already exists."
    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username, password = request.form["username"].strip(), request.form["password"]
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username=%s", (username,))
                user = cur.fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"], session["username"] = user["id"], user["username"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid credentials."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM chat_history WHERE user_id=%s ORDER BY timestamp DESC LIMIT 20", (user_id,))
            chats = cur.fetchall()
            cur.execute("SELECT subject, SUM(hours) as total FROM study_progress WHERE user_id=%s GROUP BY subject", (user_id,))
            progress = cur.fetchall()
            cur.execute("SELECT SUM(hours) as grand_total FROM study_progress WHERE user_id=%s", (user_id,))
            gt = cur.fetchone()
            total_hours = gt["grand_total"] if gt and gt["grand_total"] else 0
    return render_template("dashboard.html", username=session["username"], chats=chats, progress=progress, total_hours=total_hours)

@app.route("/api/upload_pdf", methods=["POST"])
@login_required
def upload_pdf():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".pdf"): return jsonify({"error": "Invalid PDF"}), 400
    text = "".join([p.extract_text() + "\n" for p in PdfReader(file).pages if p.extract_text()])
    chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
    with get_db() as conn:
        with conn.cursor() as cur:
            for chunk in chunks:
                cur.execute("INSERT INTO documents (user_id,filename,content) VALUES (%s,%s,%s)", (session["user_id"], file.filename, chunk))
            conn.commit()
    return jsonify({"message": "PDF uploaded successfully!"})

@app.route("/api/ask", methods=["POST"])
@login_required
def ask():
    data = request.get_json()
    question, language = data.get("question", "").strip(), data.get("language", "English")
    if not question: return jsonify({"error": "Question required"}), 400
    
    words = re.findall(r'\w+', question.lower())
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT content FROM documents WHERE user_id=%s", (session["user_id"],))
            docs = cur.fetchall()
    
    scored = [(sum(c["content"].lower().count(w) for w in words), c["content"]) for c in docs]
    chunks = [c for score, c in sorted(scored, reverse=True) if score > 0][:5]
    
    context = "\n\n".join(chunks)[:5000] if chunks else ""
    prompt = f"Study Material:\n{context}\n\nQuestion: {question}" if context else question
    answer = get_ai_response(prompt, language)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO chat_history (user_id,question,answer) VALUES (%s,%s,%s)", (session["user_id"], question, answer))
            conn.commit()
    return jsonify({"answer": answer})

@app.route("/api/study", methods=["POST"])
@login_required
def add_study():
    data = request.get_json()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO study_progress (user_id,subject,hours) VALUES (%s,%s,%s)", (session["user_id"], data.get("subject"), float(data.get("hours", 0))))
            conn.commit()
    return jsonify({"message": "Logged"})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)