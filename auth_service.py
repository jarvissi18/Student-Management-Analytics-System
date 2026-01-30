import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection


# ================= LOGIN USER =================
def login_user(username, password):
    conn = get_connection()
    conn.execute("PRAGMA busy_timeout = 5000")
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT password, role FROM users WHERE username=?",
            (username,)
        )
        row = cur.fetchone()

        if row and check_password_hash(row[0], password):
            return row[1]  # ADMIN / STUDENT

        return None

    finally:
        conn.close()


# ================= CREATE USER =================
def create_user(username, password, role, answer):
    conn = get_connection()
    conn.execute("PRAGMA busy_timeout = 5000")
    cur = conn.cursor()

    try:
        hashed = generate_password_hash(password)

        cur.execute(
            "INSERT INTO users (username, password, role, answer) VALUES (?,?,?,?)",
            (username, hashed, role.upper(), answer)
        )
        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


# ================= RESET PASSWORD =================
def reset_password(username, role, answer, new_password):
    conn = get_connection()
    conn.execute("PRAGMA busy_timeout = 5000")
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT 1 FROM users WHERE username=? AND role=? AND answer=?",
            (username, role.upper(), answer)
        )

        if not cur.fetchone():
            return False

        hashed = generate_password_hash(new_password)

        cur.execute(
            "UPDATE users SET password=? WHERE username=?",
            (hashed, username)
        )
        conn.commit()
        return True

    finally:
        conn.close()


# ================= GET ALL USERS =================
def get_all_users():
    conn = get_connection()
    conn.execute("PRAGMA busy_timeout = 5000")
    cur = conn.cursor()

    try:
        cur.execute("SELECT username, role FROM users")
        return cur.fetchall()

    finally:
        conn.close()


# ================= DELETE USER =================
def delete_user(username):
    conn = get_connection()
    conn.execute("PRAGMA busy_timeout = 5000")
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
        return True

    except sqlite3.Error:
        return False

    finally:
        conn.close()
