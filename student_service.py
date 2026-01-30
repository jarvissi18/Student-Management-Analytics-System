import sqlite3
from database import get_connection

# ================= ADD STUDENT =================
def add_student(roll, name, age, branch, photo=None):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO students (roll, name, age, branch, photo)
            VALUES (?, ?, ?, ?, ?)
        """, (roll, name, age, branch, photo))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


# ================= VIEW STUDENTS =================
def view_students():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT roll, name, age, branch, photo FROM students")
    rows = cur.fetchall()
    conn.close()
    return rows


# ================= GET STUDENT BY USERNAME =================
def get_student_by_username(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT roll, name, age, branch, photo
        FROM students
        WHERE username=?
    """, (username,))
    student = cur.fetchone()
    conn.close()
    return student



# ================= GET STUDENT BY ROLL =================
def get_student_by_roll(roll):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT roll, name, age, branch, photo
        FROM students
        WHERE roll=?
    """, (roll,))
    student = cur.fetchone()
    conn.close()
    return student


# ================= UPDATE STUDENT =================
def update_student(roll, name, age, branch, photo=None):
    conn = get_connection()
    cur = conn.cursor()

    if photo:
        cur.execute("""
            UPDATE students
            SET name=?, age=?, branch=?, photo=?
            WHERE roll=?
        """, (name, age, branch, photo, roll))
    else:
        cur.execute("""
            UPDATE students
            SET name=?, age=?, branch=?
            WHERE roll=?
        """, (name, age, branch, roll))

    conn.commit()
    conn.close()
    


# ================= DELETE STUDENT =================
def delete_student(roll):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE roll=?", (roll,))
    conn.commit()
    conn.close()

# ================= ATTENDENCE =================

def get_attendance_by_date(date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.roll, s.name, a.status
        FROM attendance a
        JOIN students s ON a.roll = s.roll
        WHERE a.date = ?
    """, (date,))

    rows = cur.fetchall()
    conn.close()
    return rows

# SAVE ATTENDANCE
def save_attendance_data(data, date):
    conn = get_connection()
    cur = conn.cursor()
    for roll, status in data.items():
        cur.execute("INSERT INTO attendance (roll, date, status) VALUES (?, ?, ?)", (roll, date, status))
    conn.commit()
    conn.close()

# GET BY DATE
def get_attendance_by_date(date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.roll, s.name, a.status
        FROM attendance a
        JOIN students s ON a.roll = s.roll
        WHERE a.date = ?
    """, (date,))
    rows = cur.fetchall()
    conn.close()
    return rows

# STUDENT ATTENDANCE %
def get_student_attendance(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT roll FROM students WHERE name=?", (username,))
    roll = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM attendance WHERE roll=?", (roll,))
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM attendance WHERE roll=? AND status='Present'", (roll,))
    present = cur.fetchone()[0]

    conn.close()
    percent = (present/total)*100 if total else 0
    return total, present, round(percent,2)

# LOW ATTENDANCE LIST
def get_low_attendance_students():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.name,
        ROUND((SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0)/COUNT(*),2) as percent
        FROM attendance a
        JOIN students s ON a.roll=s.roll
        GROUP BY a.roll
        HAVING percent < 75
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

import sqlite3
from database import get_connection

# Student info
def get_student_by_id(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT roll, name, age, branch FROM students WHERE roll=?", (student_id,))
    student = cur.fetchone()
    conn.close()
    return student


# Total classes count
def get_total_classes(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM attendance WHERE roll=?", (student_id,))
    total = cur.fetchone()[0]
    conn.close()
    return total


# Present days count
def get_present_days(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM attendance WHERE roll=? AND status='Present'", (student_id,))
    present = cur.fetchone()[0]
    conn.close()
    return present
