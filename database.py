import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="student_management_db"
    )

    print("Connected to MySQL!")

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")

    records = cursor.fetchall()

    print("\nSTUDENT RECORDS")
    print("-" * 60)

    for student in records:
        print(student)

    print("-" * 60)
    print("Total students:", len(records))

except mysql.connector.Error as error:
    print("Database error:", error)

finally:
    if "cursor" in locals():
        cursor.close()

    if "conn" in locals() and conn.is_connected():
        conn.close()