import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("ALTER TABLE users ADD COLUMN answer TEXT")

conn.commit()
conn.close()

print("answer column added successfully")
