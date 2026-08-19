"""
src/gui/student_dashboard.py - Student Portal GUI (Limited Access)
East West University Course Registration System
"""

import tkinter as tk
from tkinter import ttk, messagebox

try:
    from .. import models
except ImportError:
    import models


class StudentDashboard(tk.Frame):
    def __init__(self, parent, user_data, logout_callback):
        super().__init__(parent, bg="#f8fafc")
        self.parent = parent
        self.user_data = user_data
        self.student_id = user_data.get("linked_id")
        self.logout_callback = logout_callback

        success, msg, self.student_profile = models.get_student_by_id(self.student_id)

        self.setup_ui()
        self.refresh_all_data()

    def setup_ui(self):
        # Header Bar
        header_frame = tk.Frame(self, bg="#1e3a8a", height=60, padx=20, pady=10)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_label = tk.Label(
            header_frame,
            text="EAST WEST UNIVERSITY  |  STUDENT PORTAL",
            font=("Segoe UI", 14, "bold"),
            fg="#ffffff",
            bg="#1e3a8a",
        )
        title_label.pack(side=tk.LEFT)

        logout_btn = tk.Button(
            header_frame,
            text="Logout",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg="#ef4444",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            bd=0,
            padx=15,
            pady=4,
            cursor="hand2",
            command=self.logout_callback,
        )
        logout_btn.pack(side=tk.RIGHT)

        # Profile Header Card
        self.profile_card = tk.Frame(self, bg="#ffffff", bd=1, relief=tk.SOLID, padx=20, pady=15)
        self.profile_card.pack(fill=tk.X, padx=15, pady=(15, 5))

        self.lbl_std_name = tk.Label(self.profile_card, text="", font=("Segoe UI", 14, "bold"), fg="#0f172a", bg="#ffffff")
        self.lbl_std_name.pack(anchor="w")

        details_frame = tk.Frame(self.profile_card, bg="#ffffff")
        details_frame.pack(fill=tk.X, pady=(5, 0))

        self.lbl_std_id = tk.Label(details_frame, text="", font=("Segoe UI", 10, "bold"), fg="#475569", bg="#ffffff")
        self.lbl_std_id.pack(side=tk.LEFT, padx=(0, 20))

        self.lbl_std_dept = tk.Label(details_frame, text="", font=("Segoe UI", 10), fg="#475569", bg="#ffffff")
        self.lbl_std_dept.pack(side=tk.LEFT, padx=(0, 20))

        self.lbl_std_credits = tk.Label(details_frame, text="", font=("Segoe UI", 11, "bold"), fg="#2563eb", bg="#ffffff")
        self.lbl_std_credits.pack(side=tk.RIGHT)

        # Main Notebook Tabs
        style = ttk.Style()
        style.theme_use("clam")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.tab_available = tk.Frame(self.notebook, bg="#ffffff", padx=20, pady=20)
        self.tab_my_courses = tk.Frame(self.notebook, bg="#ffffff", padx=20, pady=20)

        self.notebook.add(self.tab_available, text=" Available Courses ")
        self.notebook.add(self.tab_my_courses, text=" My Courses ")

        self.setup_available_tab()
        self.setup_my_courses_tab()

    def update_profile_header(self):
        success, msg, self.student_profile = models.get_student_by_id(self.student_id)
        if success and self.student_profile:
            self.lbl_std_name.config(text=f"Welcome, {self.student_profile['name']}")
            self.lbl_std_id.config(text=f"ID: {self.student_profile['student_id']}")
            self.lbl_std_dept.config(text=f"Dept: {self.student_profile['dept_code']} ({self.student_profile['dept_name']})")
            self.lbl_std_credits.config(text=f"⚡ Credits Enrolled: {self.student_profile['credits_enrolled']} Credits")

    # =========================================================================
    # TAB 1: AVAILABLE COURSES TAB
    # =========================================================================
    def setup_available_tab(self):
        ctrl_frame = tk.Frame(self.tab_available, bg="#ffffff")
        ctrl_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(ctrl_frame, text="Select course below to enroll:", font=("Segoe UI", 11, "bold"), fg="#334155", bg="#ffffff").pack(side=tk.LEFT)

        btn_register = tk.Button(
            ctrl_frame,
            text="✨ Enroll / Register Course",
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2",
            command=self.register_selected_course,
        )
        btn_register.pack(side=tk.RIGHT)

        columns = ("course_id", "course_code", "course_name", "credits", "dept_code", "faculty_name", "time_slot", "seats_remaining")
        self.avail_tree = ttk.Treeview(self.tab_available, columns=columns, show="headings", height=13)

        headings = {
            "course_id": ("ID", 40),
            "course_code": ("Code", 80),
            "course_name": ("Course Title", 220),
            "credits": ("Credits", 60),
            "dept_code": ("Dept", 60),
            "faculty_name": ("Faculty Member", 150),
            "time_slot": ("Schedule", 120),
            "seats_remaining": ("Seats Remaining", 120),
        }

        for col, (head, width) in headings.items():
            self.avail_tree.heading(col, text=head)
            self.avail_tree.column(col, width=width, anchor="center" if col in ("course_id", "credits", "dept_code", "seats_remaining") else "w")

        scrollbar = ttk.Scrollbar(self.tab_available, orient=tk.VERTICAL, command=self.avail_tree.yview)
        self.avail_tree.configure(yscroll=scrollbar.set)

        self.avail_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_available_courses_table(self):
        for item in self.avail_tree.get_children():
            self.avail_tree.delete(item)

        success, msg, courses = models.get_available_courses()
        if success:
            for c in courses:
                rem = c["seats_remaining"]
                rem_str = f"{rem} seats free" if rem > 0 else "FULL (0 free)"
                self.avail_tree.insert(
                    "",
                    tk.END,
                    values=(
                        c["course_id"],
                        c["course_code"],
                        c["course_name"],
                        c["credits"],
                        c["dept_code"],
                        c["faculty_name"],
                        c["time_slot"],
                        rem_str,
                    ),
                )

    def register_selected_course(self):
        selected = self.avail_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a course from the table to enroll.")
            return

        item = self.avail_tree.item(selected[0])
        course_id = item["values"][0]

        success, msg, data = models.register_student(self.student_id, course_id)
        if success:
            messagebox.showinfo("Registration Successful", msg)
            self.refresh_all_data()
        else:
            messagebox.showerror("Registration Rejection", msg)

    # =========================================================================
    # TAB 2: MY COURSES TAB
    # =========================================================================
    def setup_my_courses_tab(self):
        ctrl_frame = tk.Frame(self.tab_my_courses, bg="#ffffff")
        ctrl_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(ctrl_frame, text="Your Registered Courses", font=("Segoe UI", 11, "bold"), fg="#1e293b", bg="#ffffff").pack(side=tk.LEFT)

        btn_drop = tk.Button(
            ctrl_frame,
            text="❌ Drop Course",
            font=("Segoe UI", 10, "bold"),
            bg="#ef4444",
            fg="#ffffff",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2",
            command=self.drop_selected_course,
        )
        btn_drop.pack(side=tk.RIGHT)

        columns = ("reg_id", "course_code", "course_name", "credits", "faculty_name", "time_slot", "status", "reg_date")
        self.my_tree = ttk.Treeview(self.tab_my_courses, columns=columns, show="headings", height=13)

        headings = {
            "reg_id": ("Reg ID", 60),
            "course_code": ("Code", 80),
            "course_name": ("Course Title", 220),
            "credits": ("Credits", 60),
            "faculty_name": ("Faculty Member", 150),
            "time_slot": ("Schedule", 120),
            "status": ("Status", 90),
            "reg_date": ("Registered Date", 140),
        }

        for col, (head, width) in headings.items():
            self.my_tree.heading(col, text=head)
            self.my_tree.column(col, width=width, anchor="center" if col in ("reg_id", "credits", "status") else "w")

        scrollbar = ttk.Scrollbar(self.tab_my_courses, orient=tk.VERTICAL, command=self.my_tree.yview)
        self.my_tree.configure(yscroll=scrollbar.set)

        self.my_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_my_courses_table(self):
        for item in self.my_tree.get_children():
            self.my_tree.delete(item)

        success, msg, regs = models.get_student_courses(self.student_id)
        if success:
            for r in regs:
                self.my_tree.insert(
                    "",
                    tk.END,
                    values=(
                        r["registration_id"],
                        r["course_code"],
                        r["course_name"],
                        r["credits"],
                        r["faculty_name"],
                        r["time_slot"],
                        r["status"],
                        r["registration_date"],
                    ),
                )

    def drop_selected_course(self):
        selected = self.my_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a course to drop.")
            return

        item = self.my_tree.item(selected[0])
        reg_id = item["values"][0]
        course_code = item["values"][1]
        status = item["values"][6]

        if status != "ENROLLED":
            messagebox.showwarning("Invalid Operation", "This course is already dropped.")
            return

        if messagebox.askyesno("Confirm Drop", f"Are you sure you want to drop course {course_code}?\nCredits will be deducted from your load."):
            success, msg, data = models.drop_registration(reg_id)
            if success:
                messagebox.showinfo("Success", msg)
                self.refresh_all_data()
            else:
                messagebox.showerror("Error", msg)

    # =========================================================================
    # REFRESH CONTROLS
    # =========================================================================
    def refresh_all_data(self):
        self.update_profile_header()
        self.load_available_courses_table()
        self.load_my_courses_table()
