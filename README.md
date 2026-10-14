# 🎓 Student Management System

A full-stack web application developed using **Python, Flask, MySQL, HTML, and CSS** to manage student records efficiently.

The application provides a web-based interface for managing student information, searching records, filtering departments, and viewing academic statistics. It also includes user registration and login functionality.

---

## 📌 Project Overview

The Student Management System simplifies student record management through a web-based dashboard connected to a MySQL database.

Users can register, log in, and manage student records through a clean, responsive interface.

## ✨ Features

### 🔐 User Authentication
- User registration
- Login using username or email
- Password hashing
- Session-based authentication
- Logout functionality
- Login-required route protection

### 👨‍🎓 Student Management
- Add new student records
- View student information
- Edit existing student details
- Delete student records
- Prevent duplicate student email addresses

### 📊 Dashboard
- Display total number of students
- Display departments represented
- Calculate average CGPA
- Search students by name or email
- Filter students by department
- View student records in a structured table

### 🎨 User Interface
- Responsive dashboard layout
- Styled forms and buttons
- Student statistics cards
- Search and filtering controls
- Login and registration pages

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| MySQL | Relational database |
| MySQL Connector/Python | Database connectivity |
| HTML5 | Webpage structure |
| CSS3 | Styling and responsive layout |
| Git | Version control |
| GitHub | Source code hosting |

---

## 📂 Project Structure

```text
student-management-system/
│
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── static/
│   └── style.css
│
└── templates/
    ├── index.html
    ├── add_student.html
    ├── edit_student.html
    ├── login.html
    └── register.html
```

---

## ⚙️ Installation and Setup

### Prerequisites

Install the following software:

- Python
- MySQL Server
- MySQL Workbench
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Kishorekandavel004/Student-management-system.git
```

Navigate to the project directory:

```bash
cd Student-management-system
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the MySQL database

Open MySQL Workbench and execute:

```sql
CREATE DATABASE student_management_db;

USE student_management_db;

CREATE TABLE students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(50) NOT NULL,
    cgpa DECIMAL(3,2)
);

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

If these tables already exist, do not create them again.

### 5. Configure environment variables

The application reads database credentials and its Flask secret key from environment variables.

Set the variables in Windows PowerShell:

```powershell
$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_PASSWORD = "YOUR_MYSQL_PASSWORD"
$env:FLASK_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
```

Replace `YOUR_MYSQL_PASSWORD` with your local MySQL password.

**Never commit your actual password or Flask secret key to GitHub.**

The Flask secret key above is temporary for the current terminal session. Generate a new secret when starting a new development session.

### 6. Run the application

```bash
python app.py
```

Open the following address in your browser:

```text
http://127.0.0.1:5000
```

Register an account, log in, and begin managing student records.

---

## 🔒 Security Considerations

- Passwords are stored as hashes rather than plain-text values.
- Database queries use parameterized SQL statements.
- Database credentials are configured through environment variables.
- Dashboard and student-management routes require authentication.

**Before public deployment:** Add CSRF protection to forms, configure production session security, disable Flask debug mode, and use a dedicated database account with limited permissions.

This project is intended for educational and local-development use until the additional production security measures are implemented.

---

## 🎯 Future Enhancements

- Export student records to Excel or CSV
- Import student records from CSV
- Pagination for large student lists
- Student profile pages
- Password reset functionality
- Role-based access control
- Automated testing
- Cloud deployment

---

## 👨‍💻 Author

**Kishore Kandavel**

GitHub: [Kishorekandavel004](https://github.com/Kishorekandavel004)

---

## 📄 License

No license has been specified yet. Add an appropriate license if you intend to permit others to reuse, modify, or distribute this project.
