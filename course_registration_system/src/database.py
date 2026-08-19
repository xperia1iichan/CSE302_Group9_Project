"""
src/database.py - East West University Course Registration System
Database Connection, 3NF Relational Schema Creation, and Data Seeding.

--- DESIGN DECISIONS & 3NF NORMALIZATION RATIONALE ---

1. Department Table (Department):
   - PK: dept_code (e.g., 'CSE', 'EEE', 'BBA'). Natural key for academic departments.
   - Design Rationale: Normalizes department metadata. Prevents repeating department names in Student & Course.
   - 3NF Status: In 3NF because dept_code functionally determines dept_name with no transitive dependencies.

2. Student Table (Student):
   - PK: student_id (e.g., '2023-1-60-001'). Institutional identifier.
   - FK: dept_code references Department(dept_code) with ON UPDATE CASCADE / ON DELETE RESTRICT.
   - Design Rationale: Decouples student identity from course enrollments. 'credits_enrolled' tracks total active credit load.
   - 3NF Status: In 3NF. All non-key attributes depend solely on student_id.

3. Course Table (Course):
   - PK: course_id (INTEGER PRIMARY KEY AUTOINCREMENT). Internal unique surrogate key.
   - Attributes: course_code (UNIQUE), course_name, credits, dept_code (FK), faculty_name, time_slot, max_seats.
   - FK: dept_code references Department(dept_code).
   - Design Rationale: Normalizes course catalog. Defines structural properties like seat capacity and schedule.
   - 3NF Status: In 3NF. Non-key attributes depend fully on course_id/course_code.

4. Registration Table (Registration):
   - PK: registration_id (INTEGER PRIMARY KEY AUTOINCREMENT).
   - FKs: student_id references Student(student_id), course_id references Course(course_id).
   - Unique Constraint: UNIQUE(student_id, course_id) prevents duplicate course registration for the same student.
   - Attributes: registration_date (timestamp), status ('ENROLLED' or 'DROPPED').
   - Design Rationale: Resolves Many-to-Many relationship between Student and Course.
   - 3NF Status: In 3NF. Stores only relationship-specific facts.

5. User Table (User):
   - PK: user_id (INTEGER PRIMARY KEY AUTOINCREMENT).
   - Attributes: username (UNIQUE), password, role ('admin' or 'student'), linked_id (FK to Student.student_id).
   - Design Rationale: Decouples authentication & RBAC from domain entities.
   - 3NF Status: In 3NF.
"""

import sqlite3
import os

# Point DB_PATH directly to course_registration_system/data/ewu_course_reg.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "ewu_course_reg.db")


def get_connection():
    """
    Establishes a connection to the SQLite database in the data/ folder.
    CRITICAL: Enables Foreign Key enforcement for SQLite.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def create_schema():
    """
    Creates all tables for the 3NF schema if they do not already exist.
    Applies integrity constraints (PK, FK, UNIQUE, CHECK).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Department Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Department (
            dept_code TEXT PRIMARY KEY,
            dept_name TEXT NOT NULL
        );
    """)

    # 2. Student Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Student (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            dept_code TEXT NOT NULL,
            credits_enrolled INTEGER DEFAULT 0 CHECK (credits_enrolled >= 0),
            FOREIGN KEY (dept_code) REFERENCES Department(dept_code)
                ON UPDATE CASCADE ON DELETE RESTRICT
        );
    """)

    # 3. Course Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Course (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL UNIQUE,
            course_name TEXT NOT NULL,
            credits INTEGER NOT NULL CHECK (credits > 0),
            dept_code TEXT NOT NULL,
            faculty_name TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            max_seats INTEGER NOT NULL CHECK (max_seats > 0),
            FOREIGN KEY (dept_code) REFERENCES Department(dept_code)
                ON UPDATE CASCADE ON DELETE RESTRICT
        );
    """)

    # 4. Registration Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Registration (
            registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL CHECK (status IN ('ENROLLED', 'DROPPED')),
            FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES Course(course_id) ON DELETE CASCADE,
            CONSTRAINT unique_student_course UNIQUE (student_id, course_id)
        );
    """)

    # 5. User Authentication Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS User (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'student')),
            linked_id TEXT,
            FOREIGN KEY (linked_id) REFERENCES Student(student_id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()


def seed_database(force_reset=False):
    """
    Populates the database with initial seed data:
    - 3 Departments (CSE, EEE, BBA)
    - 6 Students (2 per dept)
    - 10 Courses
    - 12 Registrations
    - User login accounts (1 Admin + 6 Students)
    """
    if force_reset and os.path.exists(DB_PATH):
        conn = get_connection()
        conn.execute("PRAGMA foreign_keys = OFF;")
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS Registration")
        cursor.execute("DROP TABLE IF EXISTS User")
        cursor.execute("DROP TABLE IF EXISTS Course")
        cursor.execute("DROP TABLE IF EXISTS Student")
        cursor.execute("DROP TABLE IF EXISTS Department")
        conn.commit()
        conn.close()

    create_schema()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Department")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Seed Departments (3)
    departments = [
        ("CSE", "Computer Science & Engineering"),
        ("EEE", "Electrical & Electronic Engineering"),
        ("BBA", "Business Administration"),
    ]
    cursor.executemany("INSERT INTO Department (dept_code, dept_name) VALUES (?, ?)", departments)

    # Seed Students (6)
    students = [
        ("2023-1-60-001", "Aritra Rahman", "aritra@ewu.edu.bd", "pass123", "CSE", 0),
        ("2023-1-60-002", "Nusrat Jahan", "nusrat@ewu.edu.bd", "pass123", "CSE", 0),
        ("2023-1-10-001", "Tanvir Ahmed", "tanvir@ewu.edu.bd", "pass123", "EEE", 0),
        ("2023-1-10-002", "Farhana Karim", "farhana@ewu.edu.bd", "pass123", "EEE", 0),
        ("2023-1-30-001", "Saimon Hossain", "saimon@ewu.edu.bd", "pass123", "BBA", 0),
        ("2023-1-30-002", "Mehnaz Chowdhury", "mehnaz@ewu.edu.bd", "pass123", "BBA", 0),
    ]
    cursor.executemany(
        "INSERT INTO Student (student_id, name, email, password, dept_code, credits_enrolled) VALUES (?, ?, ?, ?, ?, ?)",
        students,
    )

    # Seed Courses (10)
    courses = [
        ("CSE101", "Structured Programming", 3, "CSE", "Dr. Ahmed Hasan", "MW 08:30-10:00", 5),
        ("CSE102", "Data Structures", 3, "CSE", "Prof. Nusrat Zahan", "TR 10:10-11:40", 4),
        ("CSE201", "Database Systems", 3, "CSE", "Dr. Mohammad Ali", "MW 11:50-13:20", 5),
        ("CSE301", "Software Engineering", 3, "CSE", "Engr. Rashid Khan", "TR 13:30-15:00", 3),
        ("EEE101", "Electrical Circuits I", 3, "EEE", "Dr. Shahidul Islam", "MW 10:10-11:40", 4),
        ("EEE201", "Electronics & Devices", 3, "EEE", "Dr. Mahmuda Parveen", "TR 08:30-10:00", 4),
        ("BBA101", "Principles of Management", 3, "BBA", "Dr. Kamrul Ahsan", "MW 13:30-15:00", 5),
        ("BBA102", "Financial Accounting", 3, "BBA", "Prof. Selina Begum", "TR 11:50-13:20", 5),
        ("BBA201", "Marketing Management", 3, "BBA", "Dr. Tariqul Islam", "MW 15:10-16:40", 4),
        ("BBA301", "Corporate Finance", 3, "BBA", "Dr. Rehana Akter", "TR 15:10-16:40", 4),
    ]
    cursor.executemany(
        """INSERT INTO Course (course_code, course_name, credits, dept_code, faculty_name, time_slot, max_seats)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        courses,
    )

    # Seed Users (1 Admin + 6 Students)
    users = [
        ("admin", "admin123", "admin", None),
        ("student1", "pass123", "student", "2023-1-60-001"),
        ("student2", "pass123", "student", "2023-1-60-002"),
        ("student3", "pass123", "student", "2023-1-10-001"),
        ("student4", "pass123", "student", "2023-1-10-002"),
        ("student5", "pass123", "student", "2023-1-30-001"),
        ("student6", "pass123", "student", "2023-1-30-002"),
    ]
    cursor.executemany(
        "INSERT INTO User (username, password, role, linked_id) VALUES (?, ?, ?, ?)",
        users,
    )

    cursor.execute("SELECT course_code, course_id FROM Course")
    course_map = {row["course_code"]: row["course_id"] for row in cursor.fetchall()}

    # Seed Registrations (12)
    registration_pairs = [
        ("2023-1-60-001", "CSE101"),
        ("2023-1-60-001", "CSE102"),
        ("2023-1-60-001", "CSE201"),
        ("2023-1-60-002", "CSE101"),
        ("2023-1-60-002", "CSE102"),
        ("2023-1-60-002", "BBA101"),
        ("2023-1-10-001", "EEE101"),
        ("2023-1-10-001", "EEE201"),
        ("2023-1-10-002", "EEE101"),
        ("2023-1-10-002", "BBA101"),
        ("2023-1-30-001", "BBA101"),
        ("2023-1-30-002", "BBA102"),
    ]

    for std_id, c_code in registration_pairs:
        c_id = course_map[c_code]
        cursor.execute(
            "INSERT INTO Registration (student_id, course_id, status) VALUES (?, ?, 'ENROLLED')",
            (std_id, c_id),
        )

    # Recalculate student credits_enrolled
    cursor.execute("""
        UPDATE Student
        SET credits_enrolled = (
            SELECT COALESCE(SUM(c.credits), 0)
            FROM Registration r
            JOIN Course c ON r.course_id = c.course_id
            WHERE r.student_id = Student.student_id AND r.status = 'ENROLLED'
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    seed_database(force_reset=True)
    print(f"Database schema created and seed data inserted at: {DB_PATH}")
