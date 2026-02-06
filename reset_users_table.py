import sqlite3
from werkzeug.security import generate_password_hash

# Connect to same DB used in project
conn = sqlite3.connect("student.db")
cur = conn.cursor()

# Drop only users table
cur.execute("DROP TABLE IF EXISTS users")

# Recreate users table
cur.execute("""
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    answer TEXT NOT NULL
)
""")

# Recreate default admin account
hashed = generate_password_hash("admin123")
cur.execute(
    "INSERT INTO users (username, password, role, answer) VALUES (?, ?, ?, ?)",
    ("admin", hashed, "ADMIN", "admin")
)

conn.commit()
conn.close()

print("Users table reset successfully with default admin")