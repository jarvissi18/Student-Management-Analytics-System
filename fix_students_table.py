import sqlite3

conn = sqlite3.connect("student.db")  # MUST match database.py
cur = conn.cursor()

# Check existing columns
cur.execute("PRAGMA table_info(students)")
columns = [col[1] for col in cur.fetchall()]

if "username" not in columns:
    cur.execute("ALTER TABLE students ADD COLUMN username TEXT UNIQUE")
    print("✅ 'username' column added to students table")
else:
    print("ℹ️ 'username' column already exists")

conn.commit()
conn.close()
