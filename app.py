import os
import re
from decimal import Decimal, InvalidOperation
from functools import wraps

import mysql.connector
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from mysql.connector import IntegrityError
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)


# =========================================================
# APPLICATION CONFIGURATION
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "FLASK_SECRET_KEY is not configured. "
        "Set it in your terminal before starting Flask."
    )

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database="student_management_db",
    )


# =========================================================
# LOGIN PROTECTION
# =========================================================

def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.")
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view


# =========================================================
# VALIDATION HELPERS
# =========================================================

def validate_student(name, email, department, cgpa):
    name = name.strip()
    email = email.strip()
    department = department.strip()

    if not name or not email or not department or not cgpa:
        return None, "All student fields are required."

    if len(name) > 100:
        return None, "Student name must not exceed 100 characters."

    if len(email) > 100 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", email
    ):
        return None, "Please enter a valid email address."

    if len(department) > 50:
        return None, "Department must not exceed 50 characters."

    try:
        cgpa_value = Decimal(cgpa)

        if not cgpa_value.is_finite():
            raise InvalidOperation

        if not Decimal("0") <= cgpa_value <= Decimal("10"):
            return None, "CGPA must be between 0 and 10."

        cgpa_value = cgpa_value.quantize(Decimal("0.01"))

    except (InvalidOperation, ValueError):
        return None, "Please enter a valid CGPA."

    return {
        "name": name,
        "email": email,
        "department": department,
        "cgpa": cgpa_value,
    }, None


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
@login_required
def index():
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch student records with optional search and filtering.
        query = """
            SELECT id, name, email, department, cgpa
            FROM students
            WHERE 1 = 1
        """
        params = []

        if search:
            query += " AND (name LIKE %s OR email LIKE %s)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        if department:
            query += " AND department = %s"
            params.append(department)

        query += " ORDER BY id"

        cursor.execute(query, tuple(params))
        students = cursor.fetchall()

        # Get the list of departments for the filter dropdown.
        cursor.execute("""
            SELECT DISTINCT department
            FROM students
            ORDER BY department
        """)
        departments = [
            row["department"] for row in cursor.fetchall()
        ]

        # Dashboard statistics.
        cursor.execute("""
            SELECT
                COUNT(*) AS total_students,
                COUNT(DISTINCT department) AS total_departments,
                AVG(cgpa) AS average_cgpa
            FROM students
        """)
        stats = cursor.fetchone()

        return render_template(
            "index.html",
            students=students,
            departments=departments,
            stats=stats,
            search=search,
            selected_department=department,
        )

    except mysql.connector.Error:
        app.logger.exception("Error loading the dashboard")
        abort(500)

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# =========================================================
# STUDENT API
# =========================================================

@app.route("/students")
@login_required
def get_students():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, department, cgpa
            FROM students
            ORDER BY id
        """)

        students = cursor.fetchall()

        # Decimal values must be converted before JSON serialization.
        for student in students:
            if student["cgpa"] is not None:
                student["cgpa"] = float(student["cgpa"])

        return jsonify(students)

    except mysql.connector.Error:
        app.logger.exception("Error retrieving student records")
        return jsonify({"error": "Unable to retrieve students"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# =========================================================
# ADD STUDENT
# =========================================================

@app.route("/add-student", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "GET":
        return render_template("add_student.html")

    student, error = validate_student(
        request.form.get("name", ""),
        request.form.get("email", ""),
        request.form.get("department", ""),
        request.form.get("cgpa", ""),
    )

    if error:
        flash(error)
        return redirect(url_for("add_student"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO students
                (name, email, department, cgpa)
            VALUES (%s, %s, %s, %s)
        """, (
            student["name"],
            student["email"],
            student["department"],
            student["cgpa"],
        ))

        connection.commit()

        flash("Student added successfully!")
        return redirect(url_for("index"))

    except IntegrityError:
        if connection is not None and connection.is_connected():
            connection.rollback()

        flash("This email address is already registered.")

    except mysql.connector.Error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        app.logger.exception("Error adding student")
        flash("Unable to add student. Please try again.")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("add_student"))


# =========================================================
# EDIT STUDENT
# =========================================================

@app.route(
    "/edit-student/<int:student_id>",
    methods=["GET", "POST"],
)
@login_required
def edit_student(student_id):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM students WHERE id = %s",
            (student_id,),
        )
        student_record = cursor.fetchone()

        if student_record is None:
            abort(404)

        if request.method == "GET":
            return render_template(
                "edit_student.html",
                student=student_record,
            )

        student, error = validate_student(
            request.form.get("name", ""),
            request.form.get("email", ""),
            request.form.get("department", ""),
            request.form.get("cgpa", ""),
        )

        if error:
            flash(error)
            return redirect(
                url_for("edit_student", student_id=student_id)
            )

        cursor.execute("""
            UPDATE students
            SET name = %s,
                email = %s,
                department = %s,
                cgpa = %s
            WHERE id = %s
        """, (
            student["name"],
            student["email"],
            student["department"],
            student["cgpa"],
            student_id,
        ))

        connection.commit()

        flash("Student updated successfully!")
        return redirect(url_for("index"))

    except IntegrityError:
        if connection is not None and connection.is_connected():
            connection.rollback()

        flash("That email address belongs to another student.")
        return redirect(
            url_for("edit_student", student_id=student_id)
        )

    except mysql.connector.Error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        app.logger.exception("Error editing student")
        flash("Unable to update student. Please try again.")
        return redirect(url_for("index"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# =========================================================
# DELETE STUDENT
# =========================================================

@app.route(
    "/delete-student/<int:student_id>",
    methods=["POST"],
)
@login_required
def delete_student(student_id):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM students WHERE id = %s",
            (student_id,),
        )

        if cursor.rowcount == 0:
            connection.rollback()
            abort(404)

        connection.commit()

        flash("Student deleted successfully!")
        return redirect(url_for("index"))

    except mysql.connector.Error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        app.logger.exception("Error deleting student")
        flash("Unable to delete student. Please try again.")
        return redirect(url_for("index"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# =========================================================
# REGISTRATION
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not username or not email or not password or not confirm_password:
        flash("Please fill in all required fields.")
        return redirect(url_for("register"))

    if not 3 <= len(username) <= 50:
        flash("Username must contain 3 to 50 characters.")
        return redirect(url_for("register"))

    if len(email) > 100 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", email
    ):
        flash("Please enter a valid email address.")
        return redirect(url_for("register"))

    if len(password) < 8 or len(password.encode("utf-8")) > 72:
        flash("Password must be at least 8 characters and no longer than 72 UTF-8 bytes.")
        return redirect(url_for("register"))

    if password != confirm_password:
        flash("Passwords do not match.")
        return redirect(url_for("register"))

    password_hash = generate_password_hash(password)

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """, (username, email, password_hash))

        connection.commit()

        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))

    except IntegrityError:
        if connection is not None and connection.is_connected():
            connection.rollback()

        flash("That username or email is already registered.")

    except mysql.connector.Error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        app.logger.exception("Error registering user")
        flash("Registration failed because of a database error.")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("register"))


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("login.html")

    username_or_email = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username_or_email or not password:
        flash("Please enter your username/email and password.")
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, username, email, password_hash
            FROM users
            WHERE username = %s OR email = %s
            LIMIT 1
        """, (username_or_email, username_or_email))

        user = cursor.fetchone()

        if user and check_password_hash(
            user["password_hash"], password
        ):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            flash("Login successful!")
            return redirect(url_for("index"))

        flash("Invalid username/email or password.")

    except mysql.connector.Error:
        app.logger.exception("Error during login")
        flash("Unable to log in because of a database error.")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("login"))


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):
    return "The requested page or student was not found.", 404


@app.errorhandler(500)
def internal_server_error(error):
    return "An internal server error occurred. Check the Flask terminal for details.", 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)