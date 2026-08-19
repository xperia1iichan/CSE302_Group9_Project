"""
tests/test_database.py - Verification test suite for course_registration_system.
"""

import sys
import os

# Add course_registration_system parent folder to sys.path
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src import database, models


def run_tests():
    print("--- 1. Testing Database Seeding & Schema Creation ---")
    database.seed_database(force_reset=True)
    print("Database seeded successfully.")

    success, msg, stats = models.get_dashboard_counts()
    assert success, f"get_dashboard_counts failed: {msg}"
    print(f"Stats check: {stats}")
    assert stats["total_departments"] == 3, f"Expected 3 depts, got {stats['total_departments']}"
    assert stats["total_students"] == 6, f"Expected 6 students, got {stats['total_students']}"
    assert stats["total_courses"] == 10, f"Expected 10 courses, got {stats['total_courses']}"
    assert stats["active_registrations"] == 12, f"Expected 12 registrations, got {stats['active_registrations']}"

    print("\n--- 2. Testing Authentication ---")
    success, msg, admin_user = models.authenticate_user("admin", "admin123")
    assert success and admin_user["role"] == "admin", "Admin login failed!"
    print("Admin login successful:", admin_user)

    success, msg, student_user = models.authenticate_user("student1", "pass123")
    assert success and student_user["role"] == "student", "Student login failed!"
    print("Student login successful:", student_user)

    print("\n--- 3. Testing Department CRUD ---")
    s, m, dept_data = models.create_department("CE", "Civil Engineering")
    assert s, f"Create department failed: {m}"

    s, m, dept_obj = models.get_department_by_id("CE")
    assert s and dept_obj["dept_name"] == "Civil Engineering", "Get department by ID failed!"

    s, m, updated_dept = models.update_department("CE", "Civil & Environmental Engineering")
    assert s and updated_dept["dept_name"] == "Civil & Environmental Engineering", "Update department failed!"

    s, m, _ = models.delete_department("CE")
    assert s, "Delete department failed!"

    print("\n--- 4. Testing Student CRUD ---")
    s, m, std_data = models.create_student("2023-1-60-999", "Test Student", "teststd@ewu.edu.bd", "pass123", "CSE")
    assert s, f"Create student failed: {m}"

    s, m, std_obj = models.get_student_by_id("2023-1-60-999")
    assert s and std_obj["name"] == "Test Student", "Get student by ID failed!"

    s, m, updated_std = models.update_student("2023-1-60-999", "Test Student Updated", "teststd@ewu.edu.bd", "pass123", "CSE")
    assert s and updated_std["name"] == "Test Student Updated", "Update student failed!"

    s, m, _ = models.delete_student("2023-1-60-999")
    assert s, "Delete student failed!"

    print("\n--- 5. Testing Course CRUD & get_available_courses ---")
    s, m, courses = models.get_available_courses()
    assert s and len(courses) == 10, f"get_available_courses failed: {m}"
    assert "seats_remaining" in courses[0], "seats_remaining key missing!"

    s, m, new_c = models.create_course("CSE499", "Senior Project", 3, "CSE", "Dr. Test", "MW 10:00-11:30", 2)
    assert s, f"Create course failed: {m}"
    c_id = new_c["course_id"]

    s, m, c_obj = models.get_course_by_id(c_id)
    assert s and c_obj["course_code"] == "CSE499", "Get course by ID failed!"

    s, m, _ = models.delete_course(c_id)
    assert s, "Delete course failed!"

    print("\n--- 6. Testing register_student logic (Duplicate & Capacity Checks) ---")
    # Student1 (2023-1-60-001) is already enrolled in CSE101 (course_id 1)
    s_dup, msg_dup, _ = models.register_student("2023-1-60-001", 1)
    print("Duplicate Registration Result:", s_dup, "| Message:", msg_dup)
    assert not s_dup, "Duplicate registration should have been blocked!"

    # Testing Capacity limit check on CSE301 (course_id 4, max_seats = 3)
    s, m, cse301 = models.get_course_by_id(4)
    for std_id in ["2023-1-60-001", "2023-1-60-002", "2023-1-10-001"]:
        models.register_student(std_id, 4)

    s_cap, msg_cap, _ = models.register_student("2023-1-10-002", 4)
    print("Capacity Limit Result:", s_cap, "| Message:", msg_cap)
    assert not s_cap, "Over-capacity registration should have failed!"

    print("\n--- 7. Testing get_student_courses & drop_registration ---")
    s, m, std_courses = models.get_student_courses("2023-1-60-001")
    assert s, f"get_student_courses failed: {m}"

    s, m, all_regs = models.get_all_registrations()
    reg_id_to_drop = None
    for r in all_regs:
        if r["student_id"] == "2023-1-60-001" and r["course_id"] == 1 and r["status"] == "ENROLLED":
            reg_id_to_drop = r["registration_id"]
            break

    assert reg_id_to_drop is not None, "Registration record to drop not found!"

    s_drop, msg_drop, dropped_data = models.drop_registration(reg_id_to_drop)
    print("Drop Registration Result:", s_drop, "| Message:", msg_drop)
    assert s_drop and dropped_data["status"] == "DROPPED", "drop_registration failed!"

    s, m, std1_after = models.get_student_by_id("2023-1-60-001")
    print("Student 1 Credits after drop:", std1_after["credits_enrolled"])

    print("\n--- ALL TESTS PASSED SUCCESSFULLY! ---")


if __name__ == "__main__":
    run_tests()
