from database import get_connection

# Mark attendance
def mark_attendance(roll, date, status):
    conn = get_connection()
    cur = conn.cursor()

    # Duplicate entry avoid
    cur.execute("SELECT * FROM attendance WHERE roll=? AND date=?", (roll, date))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO attendance (roll, date, status)
            VALUES (?, ?, ?)
        """, (roll, date, status))

    conn.commit()
    conn.close()


# Admin date-wise view
def get_attendance_by_date(date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT students.roll, students.name, attendance.status
        FROM attendance
        JOIN students ON attendance.roll = students.roll
        WHERE attendance.date = ?
    """, (date,))

    data = cur.fetchall()
    conn.close()
    return data


# Student personal attendance
def get_student_attendance(roll):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT date, status FROM attendance
        WHERE roll = ?
        ORDER BY date DESC
    """, (roll,))

    data = cur.fetchall()
    conn.close()
    return data


# Attendance percentage
def get_attendance_percentage(roll):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM attendance WHERE roll=?", (roll,))
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM attendance WHERE roll=? AND status='Present'", (roll,))
    present = cur.fetchone()[0]

    conn.close()

    if total == 0:
        return 0
    return round((present / total) * 100, 2)
