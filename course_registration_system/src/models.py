"""
src/models.py - East West University Course Registration System
Data Access Layer with complete CRUD operations and Business-Logic functions.
ALL functions return a 3-tuple: (success: bool, message: str, data: Any)
ALL SQL queries use parameterized queries exclusively (?) to prevent SQL injection.
"""

import sqlite3
import re

try:
    from src.database import get_connection
except ImportError:
    try:
        from .database import get_connection
    except ImportError:
        from database import get_connection


def is_valid_email(email):
    """Validates basic email address format using regex."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email.strip()) is not None


def _recalculate_student_credits(cursor, student_id):
    """Recalculates student's credits_enrolled safely."""
    cursor.execute("""
        UPDATE Student
        SET credits_enrolled = (
            SELECT COALESCE(SUM(c.credits), 0)
            FROM Registration r
            JOIN Course c ON r.course_id = c.course_id
            WHERE r.student_id = ? AND r.status = 'ENROLLED'
        )
        WHERE student_id = ?
    """, (student_id, student_id))


# -----------------------------------------------------------------------------
# User Authentication
# -----------------------------------------------------------------------------

def authenticate_user(username, password):
    """
    Validates credentials against User table.
    Returns (success, message, user_dict_or_None).
    """
    try:
        uname = username.strip()
        passwd = password.strip()
        if not uname or not passwd:
            return False, "Username and password cannot be empty.", None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.username, u.role, u.linked_id, s.name as student_name, s.dept_code
            FROM User u
            LEFT JOIN Student s ON u.linked_id = s.student_id
            WHERE u.username = ? AND u.password = ?
        """, (uname, passwd))
        row = cursor.fetchone()
        conn.close()

        if row:
            return True, "Authentication successful.", dict(row)
        else:
            return False, "Invalid username or password.", None
    except Exception as e:
        return False, f"Authentication error: {str(e)}", None


# -----------------------------------------------------------------------------
# 1. DEPARTMENT CRUD
# -----------------------------------------------------------------------------

def create_department(dept_code, dept_name):
    """Create a new Department record."""
    try:
        dept_code = dept_code.strip().upper()
        dept_name = dept_name.strip()
        if not dept_code or not dept_name:
            return False, "Department code and name cannot be empty.", None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Department (dept_code, dept_name) VALUES (?, ?)",
            (dept_code, dept_name)
        )
        conn.commit()
        conn.close()
        return True, "Department created successfully.", {"dept_code": dept_code, "dept_name": dept_name}
    except sqlite3.IntegrityError:
        return False, f"Department code '{dept_code}' already exists.", None
    except Exception as e:
        return False, f"Error creating department: {str(e)}", None


def get_all_departments():
    """Read all Departments."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Department ORDER BY dept_code ASC")
        rows = cursor.fetchall()
        conn.close()
        return True, "Departments fetched successfully.", [dict(r) for r in rows]
    except Exception as e:
        return False, f"Error fetching departments: {str(e)}", []


def get_department_by_id(dept_code):
    """Read Department by PK (dept_code)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Department WHERE dept_code = ?", (dept_code.strip().upper(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return True, "Department found.", dict(row)
        return False, f"Department '{dept_code}' not found.", None
    except Exception as e:
        return False, f"Error fetching department: {str(e)}", None


def update_department(dept_code, dept_name):
    """Update Department record."""
    try:
        dept_code = dept_code.strip().upper()
        dept_name = dept_name.strip()
        if not dept_name:
            return False, "Department name cannot be empty.", None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Department SET dept_name = ? WHERE dept_code = ?", (dept_name, dept_code))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if updated:
            return True, "Department updated successfully.", {"dept_code": dept_code, "dept_name": dept_name}
        return False, f"Department '{dept_code}' not found.", None
    except Exception as e:
        return False, f"Error updating department: {str(e)}", None


def delete_department(dept_code):
    """Delete Department record."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Department WHERE dept_code = ?", (dept_code.strip().upper(),))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if deleted:
            return True, f"Department '{dept_code}' deleted successfully.", None
        return False, f"Department '{dept_code}' not found.", None
    except sqlite3.IntegrityError:
        return False, f"Cannot delete department '{dept_code}': Students or courses depend on it.", None
    except Exception as e:
        return False, f"Error deleting department: {str(e)}", None


# -----------------------------------------------------------------------------
# 2. STUDENT CRUD
# -----------------------------------------------------------------------------

def create_student(student_id, name, email, password, dept_code):
    """Create a new Student record."""
    try:
        student_id = student_id.strip()
        name = name.strip()
        email = email.strip()
        password = password.strip()
        dept_code = dept_code.strip().upper()

        if not all([student_id, name, email, password, dept_code]):
            return False, "All student fields are required.", None

        if not is_valid_email(email):
            return False, f"Invalid email format: '{email}'. Please enter a valid email address.", None

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT dept_code FROM Department WHERE dept_code = ?", (dept_code,))
        if not cursor.fetchone():
            conn.close()
            return False, f"Department '{dept_code}' does not exist.", None

        cursor.execute("""
            INSERT INTO Student (student_id, name, email, password, dept_code, credits_enrolled)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (student_id, name, email, password, dept_code))

        username = student_id.lower().replace("-", "")
        cursor.execute("""
            INSERT INTO User (username, password, role, linked_id)
            VALUES (?, ?, 'student', ?)
        """, (username, password, student_id))

        conn.commit()
        conn.close()
        return True, "Student account created successfully.", {
            "student_id": student_id, "name": name, "email": email, "dept_code": dept_code, "credits_enrolled": 0
        }
    except sqlite3.IntegrityError as ie:
        err_msg = str(ie)
        if "student_id" in err_msg or "PRIMARY KEY" in err_msg:
            return False, f"Student ID '{student_id}' already exists.", None
        if "email" in err_msg or "UNIQUE constraint failed: Student.email" in err_msg:
            return False, f"Email '{email}' is already registered to another student.", None
        return False, f"Database integrity error: {err_msg}", None
    except Exception as e:
        return False, f"Error creating student: {str(e)}", None


def get_all_students(dept_filter=None):
    """Read all Students with optional department filter."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT s.*, d.dept_name
            FROM Student s
            JOIN Department d ON s.dept_code = d.dept_code
            WHERE 1=1
        """
        params = []
        if dept_filter and dept_filter != "ALL":
            query += " AND s.dept_code = ?"
            params.append(dept_filter.strip())

        query += " ORDER BY s.dept_code, s.student_id ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return True, "Students fetched successfully.", [dict(r) for r in rows]
    except Exception as e:
        return False, f"Error fetching students: {str(e)}", []


def get_student_by_id(student_id):
    """Read Student by PK (student_id)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, d.dept_name
            FROM Student s
            JOIN Department d ON s.dept_code = d.dept_code
            WHERE s.student_id = ?
        """, (student_id.strip(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return True, "Student found.", dict(row)
        return False, f"Student ID '{student_id}' not found.", None
    except Exception as e:
        return False, f"Error fetching student: {str(e)}", None


def update_student(student_id, name, email, password, dept_code):
    """Update Student record."""
    try:
        student_id = student_id.strip()
        name = name.strip()
        email = email.strip()
        password = password.strip()
        dept_code = dept_code.strip().upper()

        if not all([student_id, name, email, password, dept_code]):
            return False, "All student fields are required.", None

        if not is_valid_email(email):
            return False, f"Invalid email format: '{email}'. Please enter a valid email address.", None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Student
            SET name = ?, email = ?, password = ?, dept_code = ?
            WHERE student_id = ?
        """, (name, email, password, dept_code, student_id))
        updated = cursor.rowcount > 0

        cursor.execute("""
            UPDATE User
            SET password = ?
            WHERE linked_id = ?
        """, (password, student_id))

        conn.commit()
        conn.close()

        if updated:
            return True, "Student updated successfully.", get_student_by_id(student_id)[2]
        return False, f"Student '{student_id}' not found.", None
    except sqlite3.IntegrityError as ie:
        if "UNIQUE constraint failed: Student.email" in str(ie):
            return False, f"Email '{email}' is already in use by another student.", None
        return False, f"Integrity error: {str(ie)}", None
    except Exception as e:
        return False, f"Error updating student: {str(e)}", None


def delete_student(student_id):
    """Delete Student record."""
    try:
        student_id = student_id.strip()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Student WHERE student_id = ?", (student_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if deleted:
            return True, f"Student '{student_id}' deleted successfully.", None
        return False, f"Student '{student_id}' not found.", None
    except Exception as e:
        return False, f"Error deleting student: {str(e)}", None


# -----------------------------------------------------------------------------
# 3. COURSE CRUD
# -----------------------------------------------------------------------------

def create_course(course_code, course_name, credits, dept_code, faculty_name, time_slot, max_seats):
    """Create a new Course record."""
    try:
        course_code = course_code.strip().upper()
        course_name = course_name.strip()
        dept_code = dept_code.strip().upper()
        faculty_name = faculty_name.strip()
        time_slot = time_slot.strip()

        if not (course_code and course_name and dept_code and faculty_name and time_slot):
            return False, "All course fields are required.", None

        try:
            credits_val = int(credits)
            max_seats_val = int(max_seats)
        except ValueError:
            return False, "Credits and Max Seats must be valid integer numbers.", None

        if credits_val <= 0 or max_seats_val <= 0:
            return False, "Credits and Max Seats must be positive numbers (> 0).", None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Course (course_code, course_name, credits, dept_code, faculty_name, time_slot, max_seats)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (course_code, course_name, credits_val, dept_code, faculty_name, time_slot, max_seats_val))
        course_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return True, "Course created successfully.", {
            "course_id": course_id, "course_code": course_code, "course_name": course_name,
            "credits": credits_val, "dept_code": dept_code, "faculty_name": faculty_name,
            "time_slot": time_slot, "max_seats": max_seats_val
        }
    except sqlite3.IntegrityError:
        return False, f"Course code '{course_code}' already exists in the catalog.", None
    except Exception as e:
        return False, f"Error creating course: {str(e)}", None


def get_all_courses(dept_filter=None, search_query=None):
    """Read all Courses with optional filters."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT c.*,
                   COUNT(CASE WHEN r.status = 'ENROLLED' THEN 1 END) as enrolled_count,
                   (c.max_seats - COUNT(CASE WHEN r.status = 'ENROLLED' THEN 1 END)) as available_seats
            FROM Course c
            LEFT JOIN Registration r ON c.course_id = r.course_id
            WHERE 1=1
        """
        params = []
        if dept_filter and dept_filter != "ALL":
            query += " AND c.dept_code = ?"
            params.append(dept_filter.strip())

        if search_query:
            query += " AND (c.course_code LIKE ? OR c.course_name LIKE ? OR c.faculty_name LIKE ?)"
            q = f"%{search_query.strip()}%"
            params.extend([q, q, q])

        query += " GROUP BY c.course_id ORDER BY c.dept_code, c.course_code ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return True, "Courses fetched successfully.", [dict(r) for r in rows]
    except Exception as e:
        return False, f"Error fetching courses: {str(e)}", []


def get_course_by_id(course_id):
    """Read Course by PK (course_id)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*,
                   COUNT(CASE WHEN r.status = 'ENROLLED' THEN 1 END) as enrolled_count,
                   (c.max_seats - COUNT(CASE WHEN r.status = 'ENROLLED' THEN 1 END)) as available_seats
            FROM Course c
            LEFT JOIN Registration r ON c.course_id = r.course_id
            WHERE c.course_id = ?
            GROUP BY c.course_id
        """, (int(course_id),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return True, "Course found.", dict(row)
        return False, f"Course ID {course_id} not found.", None
    except Exception as e:
        return False, f"Error fetching course: {str(e)}", None


def update_course(course_id, course_code, course_name, credits, dept_code, faculty_name, time_slot, max_seats):
    """Update Course record."""
    try:
        c_id = int(course_id)
        course_code = course_code.strip().upper()
        course_name = course_name.strip()
        dept_code = dept_code.strip().upper()
        faculty_name = faculty_name.strip()
        time_slot = time_slot.strip()

        if not (course_code and course_name and dept_code and faculty_name and time_slot):
            return False, "All course fields are required.", None

        try:
            credits_val = int(credits)
            max_seats_val = int(max_seats)
        except ValueError:
            return False, "Credits and Max Seats must be valid numbers.", None

        if credits_val <= 0 or max_seats_val <= 0:
            return False, "Credits and Max Seats must be positive numbers (> 0).", None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Course
            SET course_code = ?, course_name = ?, credits = ?, dept_code = ?,
                faculty_name = ?, time_slot = ?, max_seats = ?
            WHERE course_id = ?
        """, (
            course_code, course_name, credits_val,
            dept_code, faculty_name, time_slot,
            max_seats_val, c_id
        ))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if updated:
            return True, "Course updated successfully.", get_course_by_id(c_id)[2]
        return False, f"Course ID {course_id} not found.", None
    except sqlite3.IntegrityError:
        return False, f"Course code '{course_code}' is already used by another course.", None
    except Exception as e:
        return False, f"Error updating course: {str(e)}", None


def delete_course(course_id):
    """Delete Course record."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Course WHERE course_id = ?", (int(course_id),))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if deleted:
            return True, f"Course ID {course_id} deleted successfully.", None
        return False, f"Course ID {course_id} not found.", None
    except Exception as e:
        return False, f"Error deleting course: {str(e)}", None


# -----------------------------------------------------------------------------
# 4. REGISTRATION CRUD
# -----------------------------------------------------------------------------

def create_registration(student_id, course_id, status="ENROLLED"):
    """Create raw Registration record."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Registration (student_id, course_id, status)
            VALUES (?, ?, ?)
        """, (student_id.strip(), int(course_id), status))
        reg_id = cursor.lastrowid
        _recalculate_student_credits(cursor, student_id.strip())
        conn.commit()
        conn.close()
        return True, "Registration created.", {"registration_id": reg_id, "student_id": student_id, "course_id": course_id, "status": status}
    except Exception as e:
        return False, f"Error creating registration: {str(e)}", None


def get_all_registrations(status_filter=None):
    """Read all Registrations."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT r.registration_id, r.registration_date, r.status,
                   s.student_id, s.name as student_name, s.dept_code as student_dept,
                   c.course_id, c.course_code, c.course_name, c.credits, c.faculty_name
            FROM Registration r
            JOIN Student s ON r.student_id = s.student_id
            JOIN Course c ON r.course_id = c.course_id
            WHERE 1=1
        """
        params = []
        if status_filter and status_filter != "ALL":
            query += " AND r.status = ?"
            params.append(status_filter)

        query += " ORDER BY r.registration_date DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return True, "Registrations fetched successfully.", [dict(r) for r in rows]
    except Exception as e:
        return False, f"Error fetching registrations: {str(e)}", []


def get_registration_by_id(registration_id):
    """Read Registration by PK."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, s.name as student_name, c.course_code, c.course_name
            FROM Registration r
            JOIN Student s ON r.student_id = s.student_id
            JOIN Course c ON r.course_id = c.course_id
            WHERE r.registration_id = ?
        """, (int(registration_id),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return True, "Registration record found.", dict(row)
        return False, f"Registration ID {registration_id} not found.", None
    except Exception as e:
        return False, f"Error fetching registration: {str(e)}", None


def update_registration_status(registration_id, status):
    """Update Registration status ('ENROLLED' or 'DROPPED')."""
    try:
        reg_id = int(registration_id)
        if status not in ("ENROLLED", "DROPPED"):
            return False, "Status must be 'ENROLLED' or 'DROPPED'.", None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_id FROM Registration WHERE registration_id = ?", (reg_id,))
        reg = cursor.fetchone()
        if not reg:
            conn.close()
            return False, f"Registration ID {registration_id} not found.", None

        std_id = reg["student_id"]
        cursor.execute("UPDATE Registration SET status = ? WHERE registration_id = ?", (status, reg_id))
        _recalculate_student_credits(cursor, std_id)
        conn.commit()
        conn.close()
        return True, f"Registration status updated to '{status}'.", get_registration_by_id(reg_id)[2]
    except Exception as e:
        return False, f"Error updating registration status: {str(e)}", None


def delete_registration(registration_id):
    """Delete Registration record permanently."""
    try:
        reg_id = int(registration_id)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_id FROM Registration WHERE registration_id = ?", (reg_id,))
        reg = cursor.fetchone()
        if not reg:
            conn.close()
            return False, f"Registration ID {registration_id} not found.", None

        std_id = reg["student_id"]
        cursor.execute("DELETE FROM Registration WHERE registration_id = ?", (reg_id,))
        _recalculate_student_credits(cursor, std_id)
        conn.commit()
        conn.close()
        return True, f"Registration ID {registration_id} deleted successfully.", None
    except Exception as e:
        return False, f"Error deleting registration: {str(e)}", None


# -----------------------------------------------------------------------------
# BUSINESS-LOGIC FUNCTIONS
# -----------------------------------------------------------------------------

def register_student(student_id, course_id):
    """
    Registers a student for a course with full capacity and duplicate checking.
    - Rejects if course is full.
    - Rejects if student is already enrolled.
    Returns: (success: bool, message: str, data: dict|None)
    """
    try:
        std_id = str(student_id).strip()
        c_id = int(course_id)
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.*,
                   COUNT(CASE WHEN r.status = 'ENROLLED' THEN 1 END) as enrolled_count
            FROM Course c
            LEFT JOIN Registration r ON c.course_id = r.course_id
            WHERE c.course_id = ?
            GROUP BY c.course_id
        """, (c_id,))
        course = cursor.fetchone()

        if not course:
            conn.close()
            return False, "Course not found.", None

        course_dict = dict(course)

        if course_dict["enrolled_count"] >= course_dict["max_seats"]:
            conn.close()
            return False, f"Registration Rejection: Course '{course_dict['course_code']}' is FULL ({course_dict['enrolled_count']}/{course_dict['max_seats']} seats occupied).", None

        cursor.execute("""
            SELECT registration_id, status FROM Registration
            WHERE student_id = ? AND course_id = ?
        """, (std_id, c_id))
        reg_record = cursor.fetchone()

        if reg_record:
            if reg_record["status"] == "ENROLLED":
                conn.close()
                return False, f"Registration Rejection: You are already registered for course '{course_dict['course_code']}'.", None
            else:
                reg_id = reg_record["registration_id"]
                cursor.execute("""
                    UPDATE Registration
                    SET status = 'ENROLLED', registration_date = CURRENT_TIMESTAMP
                    WHERE registration_id = ?
                """, (reg_id,))
        else:
            cursor.execute("""
                INSERT INTO Registration (student_id, course_id, status)
                VALUES (?, ?, 'ENROLLED')
            """, (std_id, c_id))
            reg_id = cursor.lastrowid

        _recalculate_student_credits(cursor, std_id)
        conn.commit()

        cursor.execute("SELECT * FROM Registration WHERE registration_id = ?", (reg_id,))
        reg_data = dict(cursor.fetchone())
        conn.close()

        return True, f"Successfully registered for {course_dict['course_code']} - {course_dict['course_name']}!", reg_data

    except Exception as e:
        return False, f"Registration error: {str(e)}", None


def drop_registration(registration_id):
    """
    Drops a registration record by updating status to 'DROPPED'.
    Returns: (success: bool, message: str, data: dict|None)
    """
    try:
        reg_id = int(registration_id)
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Registration WHERE registration_id = ?", (reg_id,))
        reg = cursor.fetchone()
        if not reg:
            conn.close()
            return False, f"Registration ID {registration_id} not found.", None

        std_id = reg["student_id"]
        cursor.execute("""
            UPDATE Registration
            SET status = 'DROPPED'
            WHERE registration_id = ?
        """, (reg_id,))

        _recalculate_student_credits(cursor, std_id)
        conn.commit()

        cursor.execute("SELECT * FROM Registration WHERE registration_id = ?", (reg_id,))
        updated_reg = dict(cursor.fetchone())
        conn.close()

        return True, "Registration dropped successfully.", updated_reg
    except Exception as e:
        return False, f"Error dropping registration: {str(e)}", None


def get_available_courses():
    """
    Returns all courses with calculated seats_remaining.
    Returns: (success: bool, message: str, data: list[dict])
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*,
                   COUNT(CASE WHEN r.status = 'ENROLLED' THEN 1 END) as enrolled_count,
                   (c.max_seats - COUNT(CASE WHEN r.status = 'ENROLLED' THEN 1 END)) as seats_remaining
            FROM Course c
            LEFT JOIN Registration r ON c.course_id = r.course_id
            GROUP BY c.course_id
            ORDER BY c.dept_code, c.course_code ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return True, "Available courses fetched.", [dict(r) for r in rows]
    except Exception as e:
        return False, f"Error fetching available courses: {str(e)}", []


def get_student_courses(student_id):
    """
    Returns all courses a student is registered in.
    Returns: (success: bool, message: str, data: list[dict])
    """
    try:
        std_id = str(student_id).strip()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.registration_id, r.registration_date, r.status,
                   c.course_id, c.course_code, c.course_name, c.credits,
                   c.dept_code, c.faculty_name, c.time_slot
            FROM Registration r
            JOIN Course c ON r.course_id = c.course_id
            WHERE r.student_id = ?
            ORDER BY r.status ASC, c.course_code ASC
        """, (std_id,))
        rows = cursor.fetchall()
        conn.close()
        return True, f"Courses for student {std_id} fetched.", [dict(r) for r in rows]
    except Exception as e:
        return False, f"Error fetching student courses: {str(e)}", []


def get_dashboard_counts():
    """
    Returns total counts of students, courses, registrations, departments, and total seats capacity.
    Returns: (success: bool, message: str, data: dict)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Student")
        total_students = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Course")
        total_courses = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Registration WHERE status = 'ENROLLED'")
        active_registrations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Department")
        total_departments = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(max_seats), 0) FROM Course")
        total_seats_capacity = cursor.fetchone()[0]

        conn.close()

        counts = {
            "total_students": total_students,
            "total_courses": total_courses,
            "active_registrations": active_registrations,
            "total_departments": total_departments,
            "total_seats_capacity": total_seats_capacity,
        }
        return True, "Dashboard counts calculated.", counts
    except Exception as e:
        return False, f"Error calculating dashboard counts: {str(e)}", {}


# Aliases for compatibility
register_course = register_student

def drop_course(student_id, course_id):
    """Drop course by student_id and course_id combination."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT registration_id FROM Registration
            WHERE student_id = ? AND course_id = ? AND status = 'ENROLLED'
        """, (str(student_id).strip(), int(course_id)))
        reg = cursor.fetchone()
        conn.close()
        if reg:
            return drop_registration(reg["registration_id"])
        return False, "Course registration not found or already dropped.", None
    except Exception as e:
        return False, f"Error dropping course: {str(e)}", None

get_student_registrations = get_student_courses
get_system_overview_stats = get_dashboard_counts
