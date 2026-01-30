# ================= IMPORTS =================
from student_service import get_student_by_id, get_total_classes, get_present_days

from attendance_service import mark_attendance, get_attendance_by_date, get_student_attendance, get_attendance_percentage
import datetime
from student_service import save_attendance_data, get_attendance_by_date, get_student_attendance, get_low_attendance_students
from flask import Flask, render_template, request, redirect, session, url_for, jsonify, send_file, Response
import os, io, random, datetime, logging
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib import colors

import openpyxl

from database import create_tables, get_connection
from auth_service import create_user, reset_password, get_all_users, delete_user
from student_service import add_student, view_students, get_student_by_username, get_student_by_roll, update_student, delete_student

from dotenv import load_dotenv
load_dotenv()

# ================= APP SETUP =================

app = Flask(__name__)
app.secret_key = "student_management_secret"

UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logging.basicConfig(filename='app.log', level=logging.INFO)


from authlib.integrations.flask_client import OAuth
oauth = OAuth(app)

app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID")
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET")



google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)



# DB tables
create_tables()


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT username, password, role FROM users WHERE username=? AND role=?",
            (username, role)
        )
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["username"] = user[0]   
            session["role"] = user[2]


            logging.info(f"User {username} logged in as {role}")
            return redirect(url_for("dashboard" if role == "ADMIN" else "student_dashboard"))

        logging.warning(f"Failed login attempt for {username}")
        return render_template("login.html", show_error=True)

    return render_template("login.html")


# ================= STUDENT DASHBOARD =================
@app.route("/student/dashboard")
def student_dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    student_id = session["username"]

    student = get_student_by_id(student_id)
    total_days = get_total_classes(student_id)
    present_days = get_present_days(student_id)

    attendance_percent = round((present_days / total_days) * 100, 2) if total_days > 0 else 0

    return render_template(
        "student_dashboard.html",
        student=student,
        total_days=total_days,
        present_days=present_days,
        attendance_percent=attendance_percent
    )


# ================= STUDENT PROFILE =================
@app.route("/student/profile")
def student_profile():
    if session.get("role") != "STUDENT":
        return redirect(url_for("login"))

    student = get_student_by_username(session["username"])
    return render_template("student_profile.html", student=student)


# ================= ADMIN DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("student_dashboard"))

    conn = get_connection()
    cur = conn.cursor()

    # Total students
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        role=session["role"],
        total_students=total_students
    )

# ================= REPORT PAGE =================

@app.route("/reports")
def reports_page():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # Branch-wise data
    cur.execute("SELECT branch, COUNT(*) FROM students GROUP BY branch")
    branch_data = cur.fetchall()

    conn.close()

    labels = [row[0] for row in branch_data]
    values = [row[1] for row in branch_data]

    return render_template("reports.html", labels=labels, values=values)


# ================= Analytics Page =================

@app.route("/analytics")
def analytics_page():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT branch, COUNT(*) FROM students GROUP BY branch")
    branch_data = cur.fetchall()

    conn.close()

    labels = [row[0] for row in branch_data]
    values = [row[1] for row in branch_data]

    return render_template("analytics.html", labels=labels, values=values)

# ================= API Students =================

@app.route("/api/students")
def api_students():
    if session.get("role") != "ADMIN":
        return jsonify({"error": "Unauthorized"}), 403

    students = view_students()

    data = [
        {
            "roll": s[0],
            "name": s[1],
            "age": s[2],
            "branch": s[3],
            "photo": s[4]   # ✅ added
        }
        for s in students
    ]
    return jsonify(data)


# ================= Download Report =================

# Page number function
def add_page_number(canvas, doc):
    page_num_text = f"Page {doc.page}"
    canvas.drawRightString(200 * mm, 15 * mm, page_num_text)

@app.route("/download-report")
def download_report():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    students = view_students()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # ===== HEADER =====
    elements.append(Paragraph("Student Management & Analytics System", styles["Title"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Official Student Report", styles["Heading2"]))
    elements.append(Spacer(1, 12))

    # ===== REPORT INFO =====
    today = datetime.date.today().strftime("%d %B %Y")
    elements.append(Paragraph(f"Report Date: {today}", styles["Normal"]))
    elements.append(Paragraph(f"Total Students: {len(students)}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # ===== TABLE =====
    data = [["Roll", "Name", "Age", "Branch"]]
    for s in students:
        data.append([s[0], s[1], s[2], s[3]])

    table = Table(data, colWidths=[1*inch, 1.5*inch, 1*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 40))

    # ===== SIGNATURE AREA =====
    elements.append(Paragraph("__________________________", styles["Normal"]))
    elements.append(Paragraph("Authorized Signature", styles["Italic"]))

    # Build PDF with page numbers
    doc.build(elements, onLaterPages=add_page_number, onFirstPage=add_page_number)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name="student_report.pdf",
                     mimetype="application/pdf")
    
    
    # ================= Attendance System  =================

    # ================= ATTENDANCE TABLE CREATE =================
def create_attendance_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll INTEGER,
            date TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

create_attendance_table()


# ================= ATTENDANCE PAGE (ADMIN) =================
from datetime import date

@app.route("/attendance", methods=["GET", "POST"])
def attendance_page():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    today = datetime.date.today().isoformat()

    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (today,))
    if cur.fetchone()[0] > 0:
        conn.close()
        return render_template("already_marked.html")

    if request.method == "POST":
        students = view_students()

        for s in students:
            roll = s[0]
            status = request.form.get(f"status_{roll}")

            if status:
                cur.execute("INSERT OR REPLACE INTO attendance (roll, date, status) VALUES (?, ?, ?)", (roll, today, status))

        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    students = view_students()
    conn.close()
    return render_template("attendance.html", students=students)



# ================= SAVE ATTENDANCE =================
@app.route("/save-attendance", methods=["POST"])
def save_attendance():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    date = datetime.date.today().isoformat()

    students = view_students()

    conn = get_connection()
    cur = conn.cursor()

    for s in students:
        roll = s[0]
        status = request.form.get(f"status_{roll}")

        if status:
            cur.execute("""
                INSERT OR REPLACE INTO attendance (roll, date, status)
                VALUES (?, ?, ?)
            """, (roll, date, status))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# ================= MY ATTENDANCE =================
@app.route("/my-attendance")
def my_attendance():
    if session.get("role") != "STUDENT":
        return redirect(url_for("login"))

    username = session.get("username")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT roll FROM students WHERE username=?", (username,))
    student = cur.fetchone()

    if not student:
        conn.close()
        return "Student profile not linked. Contact admin."

    roll = student[0]
    cur.execute("SELECT date, status FROM attendance WHERE roll=?", (roll,))
    records = cur.fetchall()
    conn.close()

    total_days = len(records)
    present_days = sum(1 for r in records if r[1] == "Present")
    percent = round((present_days / total_days) * 100, 2) if total_days > 0 else 0

    return render_template("my_attendance.html", records=records, total=total_days, present=present_days, percent=percent)

# ================= Low ATTENDANCE =================

@app.route("/low-attendance")
def low_attendance():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.name,
        (SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0/COUNT(a.id)) as percent
        FROM attendance a
        JOIN students s ON s.roll=a.roll
        GROUP BY s.roll
        HAVING percent < 75
    """)

    students = cur.fetchall()
    conn.close()

    return render_template("low_attendance.html", students=students)


# ================= REPORT ATTENDANCE =================

@app.route("/attendance-report")
def attendance_report():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    date_selected = request.args.get("date")

    if not date_selected:
        return render_template("attendance_report.html", records=None)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.roll, s.name, a.status
        FROM attendance a
        JOIN students s ON a.roll = s.roll
        WHERE a.date = ?
    """, (date_selected,))

    records = cur.fetchall()
    conn.close()

    return render_template("attendance_report.html", records=records, date=date_selected)

# =================  ATTENDANCE ANALYTICS =================

@app.route("/attendance-analytics")
def attendance_analytics():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    conn = get_connection()
    cur = conn.cursor()

    # Present vs Absent
    cur.execute("""
        SELECT status, COUNT(*)
        FROM attendance
        GROUP BY status
    """)
    data = cur.fetchall()

    present = 0
    absent = 0
    for row in data:
        if row[0] == "Present":
            present = row[1]
        elif row[0] == "Absent":
            absent = row[1]

    # Branch-wise attendance
    cur.execute("""
        SELECT s.branch, COUNT(a.status)
        FROM attendance a
        JOIN students s ON s.roll = a.roll
        WHERE a.status='Present'
        GROUP BY s.branch
    """)
    branch_data = cur.fetchall()

    conn.close()

    labels = [b[0] for b in branch_data]
    values = [b[1] for b in branch_data]

    return render_template(
        "attendance_analytics.html",
        present=present,
        absent=absent,
        labels=labels,
        values=values
    )


# ================= EXPORT ATTENDANCE EXCEL =================

import pandas as pd

@app.route("/download-attendance-excel/<date>")
def download_attendance_excel(date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.roll, s.name, a.status
        FROM attendance a
        JOIN students s ON a.roll = s.roll
        WHERE a.date = ?
    """, (date,))
    records = cur.fetchall()
    conn.close()

    if not records:
        return "No data"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Roll", "Name", "Status"])

    for r in records:
        ws.append(r)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return Response(output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=attendance.xlsx"})


# ================= DOWNLOAD ATTENDANCE PDF =================

from fpdf import FPDF
from flask import request, send_file
import io

@app.route("/download-attendance-pdf/<date>")
def download_attendance_pdf(date):
    records = get_attendance_by_date(date)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # ================= HEADER =================
    title_style = ParagraphStyle(
        'title',
        fontSize=22,
        alignment=1,
        textColor=colors.HexColor("#0A3D91"),
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'subtitle',
        fontSize=12,
        textColor=colors.gray,
        alignment=1
    )

    elements.append(Paragraph("Student Management & Analytics System", title_style))
    elements.append(Paragraph("Official Attendance Report", subtitle_style))
    elements.append(Spacer(1, 12))

    # ================= DATE BADGE =================
    elements.append(Paragraph(f"<b>Date:</b> {date}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # ================= TABLE DATA =================
    data = [["Roll", "Name", "Status"]]

    for r in records:
        status_color = colors.green if r[2] == "Present" else colors.red
        data.append([
            str(r[0]),
            r[1],
            Paragraph(f'<font color="{status_color}"><b>{r[2]}</b></font>', styles["Normal"])
        ])

    table = Table(data, colWidths=[1*inch, 2*inch, 1.5*inch])

    table.setStyle(TableStyle([
        # Header Style
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A3D91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),

        # Body
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ROWHEIGHT", (0, 0), (-1, -1), 18),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 30))

    # ================= FOOTER =================
    footer_style = ParagraphStyle('footer', alignment=1, fontSize=9, textColor=colors.gray)
    elements.append(Paragraph("Generated by Student Management & Analytics System", footer_style))

    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"attendance_report_{date}.pdf",
                     mimetype="application/pdf")

# ================= EXPORT EXCEL =================
@app.route("/export/excel")
def export_excel():
    if "username" not in session:
        return redirect(url_for("login"))


    students = view_students()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students"

    # Header
    ws.append(["Roll", "Name", "Age", "Branch"])

    # Data
    for s in students:
        ws.append(s)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=students.xlsx"}
    )
    


# ================= GOOGLE LOGIN =================


@app.route('/google-login')
def google_login():
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/google-auth')
def google_auth():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')

    session["username"] = user_info["email"]
    session["role"] = "STUDENT"

    return redirect(url_for("student_dashboard"))



# ================= VIEW STUDENTS =================

@app.route("/students")
def students_page():
    if "username" not in session:
        return redirect(url_for("login"))

    students = view_students()
    return render_template("view_students.html", students=students, role=session["role"])


# ================= SEARCH STUDENTS =================
@app.route("/students/search")
def search_students_page():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    query = request.args.get("q")
    students = []
    searched = False

    if query:
        searched = True
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT roll, name, age, branch, photo
            FROM students
            WHERE name LIKE ? OR roll LIKE ?
            """,
            (f"%{query}%", f"%{query}%")
        )
        students = cur.fetchall()
        conn.close()

    return render_template("search_students.html", students=students, searched=searched, role=session["role"])


# ================= ADD STUDENT =================
@app.route("/students/add", methods=["GET", "POST"])
def add_student_page():
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    error = None

    if request.method == "POST":
        roll = request.form.get("roll")
        name = request.form.get("name")
        age = request.form.get("age")
        branch = request.form.get("branch")

        photo_file = request.files.get("photo")
        filename = None

        if photo_file and photo_file.filename != "":
            filename = secure_filename(photo_file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo_file.save(save_path)

        if not add_student(roll, name, age, branch, photo=filename):
            error = "Roll number already exists!"
        else:
            return redirect(url_for("students_page"))

    return render_template("add_student.html", error=error)

# ================= USER MANAGEMENT =================
@app.route("/users")
def manage_users():
    if session.get("role") != "ADMIN":
        return redirect(url_for("dashboard"))

    users = get_all_users()
    return render_template("view_users.html", users=users, current=session["username"])


@app.route("/users/add", methods=["GET", "POST"])
def add_user_page():
    if session.get("role") != "ADMIN":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")
        answer = request.form.get("answer")

        if not all([username, password, role, answer]):
            return render_template("add_user.html", error="All fields are required")

        if len(password) < 6:
            return render_template("add_user.html", error="Password must be at least 6 characters")

        if not create_user(username, password, role, answer):
            return render_template("add_user.html", error="Username already exists")

        return redirect(url_for("manage_users"))

    return render_template("add_user.html")


@app.route("/users/delete/<username>")
def delete_user_page(username):
    if session.get("role") != "ADMIN":
        return redirect(url_for("dashboard"))

    if username != session["username"]:
        delete_user(username)

    return redirect(url_for("manage_users"))


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    logging.info(f"User {session.get('user')} logged out")
    session.clear()
    return redirect(url_for("login"))


# ================= FORGOT PASSWORD =================
@app.route("/forgot", methods=["GET", "POST"])
def forgot_password_page():
    if request.method == "POST":
        if reset_password(
            request.form["username"],
            request.form["role"],
            request.form.get("answer"),
            request.form["new_password"]
        ):
            return redirect(url_for("login"))

        return render_template("forgot_password.html", error=True)

    return render_template("forgot_password.html")

# ================= Edit Student Page =================

@app.route("/students/edit/<int:roll>")
def edit_student_page(roll):
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    student = get_student_by_roll(roll)
    return render_template("edit_student.html", student=student)

# ================= UPDATE STUDENT =================

@app.route("/students/update/<int:roll>", methods=["POST"])
def update_student_route(roll):
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    photo_file = request.files.get("photo")
    filename = None

    if photo_file and photo_file.filename != "":
        filename = secure_filename(photo_file.filename)
        photo_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    update_student(
        roll,
        request.form["name"],
        request.form["age"],
        request.form["branch"],
        photo=filename
    )
    return redirect(url_for("students_page"))


# ================= DELETE STUDENT =================

@app.route("/students/delete/<int:roll>")
def delete_student_route(roll):
    if session.get("role") != "ADMIN":
        return redirect(url_for("login"))

    delete_student(roll)
    return redirect(url_for("students_page"))



if __name__ == "__main__":
    app.run(debug=True)
