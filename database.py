import sqlite3
from werkzeug.security import generate_password_hash

def get_connection():
    conn = sqlite3.connect("student.db", timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn



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

    

    
        # ===== AUTO FIX OLD DATABASE (ADD MISSING COLUMNS) =====
    cursor.execute("PRAGMA table_info(students)")
    columns = [col[1] for col in cursor.fetchall()]

    if "username" not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN username TEXT")

    if "photo" not in columns:
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
