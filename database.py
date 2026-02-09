import sqlite3
from werkzeug.security import generate_password_hash


# ================= CONNECTION =================

def get_connection():
    conn = sqlite3.connect("student.db", timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


# ================= CREATE TABLES =================

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # ================= USERS TABLE =================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        answer TEXT NOT NULL
    )
    """)

    # ================= STUDENTS TABLE =================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        roll INTEGER PRIMARY KEY,
        photo TEXT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        branch TEXT NOT NULL,
        email TEXT,
        username TEXT UNIQUE
    )
    """)

    # ================= ATTENDANCE TABLE =================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll INTEGER,
        name TEXT,
        status TEXT,
        date TEXT,
        UNIQUE(roll, date)
    )
    """)

    cursor.execute("PRAGMA table_info(students)")
    cols = [c["name"] for c in cursor.fetchall()]

    if "email" not in cols:
        cursor.execute("ALTER TABLE students ADD COLUMN email TEXT")

    if "username" not in cols:
        cursor.execute("ALTER TABLE students ADD COLUMN username TEXT")

    if "photo" not in cols:
        cursor.execute("ALTER TABLE students ADD COLUMN photo TEXT")

    # ================= DEFAULT ADMIN =================
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        hashed = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?)",
            ("admin", hashed, "ADMIN", "admin")
        )

    conn.commit()
    conn.close()


# ================= ADD STUDENT =================

def add_student(roll, name, age, branch, email=None, photo=None):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO students (roll, name, age, branch, email, photo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (roll, name, age, branch, email, photo))

        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


# ================= GET ALL STUDENTS =================

def get_all_students():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT roll, name, age, branch, email, photo FROM students")
    students = cur.fetchall()
    conn.close()
    return students


# ================= GET STUDENT BY ROLL =================

def get_student_by_roll(roll):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT roll, name, age, branch, email, photo FROM students WHERE roll=?", (roll,))
    student = cur.fetchone()
    conn.close()
    return student


# ================= UPDATE STUDENT =================

def update_student(roll, name, age, branch, email, photo=None):
    conn = get_connection()
    cur = conn.cursor()

    if photo:
        cur.execute("""
            UPDATE students
            SET name = ?, age = ?, branch = ?, email = ?, photo = ?
            WHERE roll = ?
        """, (name, age, branch, email, photo, roll))
    else:
        cur.execute("""
            UPDATE students
            SET name = ?, age = ?, branch = ?, email = ?
            WHERE roll = ?
        """, (name, age, branch, email, roll))

    conn.commit()
    conn.close()


# ================= DELETE STUDENT =================

def delete_student(roll):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE roll=?", (roll,))
    conn.commit()
    conn.close()


# ================= GET STUDENT BY EMAIL (GOOGLE LOGIN) =================

def get_student_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT roll, name, age, branch, email, photo FROM students WHERE email=?", (email,))
    student = cur.fetchone()
    conn.close()
    return student
