# 🎓 Student Management & Analytics System

A full-stack web application built using **Flask** to manage students, attendance tracking, analytics, reporting, and role-based authentication with Google Login integration.

---

## 🚀 Key Features

### 👨‍🏫 Admin Panel

- Add Student with Photo Upload
- Edit Student Details (Name, Age, Branch, Email, Photo)
- Delete Students
- Manage Users (Admin & Student Roles)
- Search Students by Name or Roll
- Mark Daily Attendance
- Attendance Reports by Date
- Low Attendance Detection (<75%)
- Analytics Dashboard with Charts
- Export Student Data to **Excel**
- View Complete Student Records

---

### 🎓 Student Panel

- Google OAuth Login
- Secure Role-Based Access
- Personal Student Dashboard
- View Attendance Percentage
- View Attendance History
- View Student Profile with Photo
- Linked Student Profile using Email

---

## 🔐 Authentication & Security

- Role-Based Login (Admin / Student)
- Password Hashing (Werkzeug Security)
- Google OAuth 2.0 Login
- Session Management
- Environment Variable Support for Secrets

---

## 📊 Analytics & Reports

- Branch-wise Student Distribution
- Present vs Absent Visualization
- Attendance Percentage Calculation
- Attendance Trend Monitoring
- Excel Export Functionality

---

## 🛠 Tech Stack

| Technology | Usage |
|------------|------|
| **Python (Flask)** | Backend Framework |
| **SQLite** | Database |
| **HTML / CSS** | Frontend |
| **Chart.js** | Analytics Charts |
| **OpenPyXL** | Excel Export |
| **Werkzeug** | Password Hashing |
| **Authlib** | Google OAuth Login |

---

## ▶ How to Run Locally

```bash
git clone https://github.com/jarvissi18/Student-Management-Analytics-System
cd Student-Management-Analytics-System
pip install -r requirements.txt
python app.py
