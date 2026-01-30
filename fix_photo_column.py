import sqlite3

conn = sqlite3.connect("student.db")
cur = conn.cursor()

cur.execute("PRAGMA table_info(students)")
columns = [col[1] for col in cur.fetchall()]

if "photo" not in columns:
    cur.execute("ALTER TABLE students ADD COLUMN photo TEXT")
    print("✅ photo column added")
else:
    print("ℹ photo column already exists")

conn.commit()
conn.close()
