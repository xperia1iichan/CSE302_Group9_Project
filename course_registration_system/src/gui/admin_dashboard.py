"""
src/gui/admin_dashboard.py - Administrator Portal GUI (Full CRUD Access)
East West University Course Registration System
"""

import tkinter as tk
from tkinter import ttk, messagebox

try:
    from src.database import get_connection
    from src import models, database
except ImportError:
    try:
        from .. import models, database
    except ImportError:
        import models, database


class AdminDashboard(tk.Frame):
    def __init__(self, parent, user_data, logout_callback):
        super().__init__(parent, bg="#f8fafc")
        self.parent = parent
        self.user_data = user_data
        self.logout_callback = logout_callback

        self.setup_ui()
        self.refresh_all_data()

    def setup_ui(self):
        # Header Bar
        header_frame = tk.Frame(self, bg="#0f172a", height=60, padx=20, pady=10)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_label = tk.Label(
            header_frame,
            text="EAST WEST UNIVERSITY  |  ADMINISTRATOR PORTAL",
            font=("Segoe UI", 14, "bold"),
            fg="#ffffff",
            bg="#0f172a",
        )
        title_label.pack(side=tk.LEFT)

        user_info_label = tk.Label(
            header_frame,
            text=f"Logged in as: {self.user_data['username']} (Admin)",
            font=("Segoe UI", 10),
            fg="#94a3b8",
            bg="#0f172a",
        )
        user_info_label.pack(side=tk.LEFT, padx=20)

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

        # Top Row Summary Cards
        cards_container = tk.Frame(self, bg="#f8fafc", padx=15, pady=10)
        cards_container.pack(fill=tk.X, side=tk.TOP)

        self.card_students = self.create_summary_card(cards_container, "Total Students", "0", "#2563eb")
        self.card_courses = self.create_summary_card(cards_container, "Total Courses", "0", "#10b981")
        self.card_registrations = self.create_summary_card(cards_container, "Active Registrations", "0", "#8b5cf6")

        self.card_students.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8)
        self.card_courses.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8)
        self.card_registrations.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8)

        # Notebook Container
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#f8fafc", borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 11, "bold"),
            padding=[15, 8],
            background="#e2e8f0",
            foreground="#334155",
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#0f172a")],
            foreground=[("selected", "#ffffff")],
        )

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Tabs
        self.tab_courses = tk.Frame(self.notebook, bg="#ffffff", padx=15, pady=15)
        self.tab_students = tk.Frame(self.notebook, bg="#ffffff", padx=15, pady=15)
        self.tab_registrations = tk.Frame(self.notebook, bg="#ffffff", padx=15, pady=15)

        self.notebook.add(self.tab_courses, text=" Course Catalog (CRUD) ")
        self.notebook.add(self.tab_students, text=" Student Roster (CRUD) ")
        self.notebook.add(self.tab_registrations, text=" Registrations Management ")

        self.setup_courses_tab()
        self.setup_students_tab()
        self.setup_registrations_tab()

    def create_summary_card(self, parent, title, value, accent_color):
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief=tk.SOLID, padx=15, pady=12)
        title_lbl = tk.Label(card, text=title, font=("Segoe UI", 10, "bold"), fg="#64748b", bg="#ffffff")
        title_lbl.pack(anchor="w")
        val_lbl = tk.Label(card, text=value, font=("Segoe UI", 20, "bold"), fg=accent_color, bg="#ffffff")
        val_lbl.pack(anchor="w", pady=(2, 0))
        card.val_lbl = val_lbl
        return card

    # =========================================================================
    # TAB 1: COURSES MANAGEMENT (Full CRUD)
    # =========================================================================
    def setup_courses_tab(self):
        ctrl_frame = tk.Frame(self.tab_courses, bg="#ffffff")
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(ctrl_frame, text="Dept Filter:", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#334155").pack(side=tk.LEFT, padx=(0, 5))
        self.course_dept_var = tk.StringVar(value="ALL")
        self.course_dept_cb = ttk.Combobox(ctrl_frame, textvariable=self.course_dept_var, state="readonly", width=10)
        self.course_dept_cb.pack(side=tk.LEFT, padx=(0, 15))
        self.course_dept_cb.bind("<<ComboboxSelected>>", lambda e: self.load_courses_table())

        tk.Label(ctrl_frame, text="Search:", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#334155").pack(side=tk.LEFT, padx=(0, 5))
        self.course_search_entry = tk.Entry(ctrl_frame, font=("Segoe UI", 10), width=18, bd=1, relief=tk.SOLID)
        self.course_search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.course_search_entry.bind("<KeyRelease>", lambda e: self.load_courses_table())

        btn_del = tk.Button(ctrl_frame, text="🗑️ Delete Course", font=("Segoe UI", 9, "bold"), bg="#ef4444", fg="#ffffff", bd=0, padx=10, pady=5, cursor="hand2", command=self.delete_selected_course)
        btn_del.pack(side=tk.RIGHT, padx=4)

        btn_edit = tk.Button(ctrl_frame, text="✏️ Edit Course", font=("Segoe UI", 9, "bold"), bg="#f59e0b", fg="#ffffff", bd=0, padx=10, pady=5, cursor="hand2", command=self.open_edit_course_modal)
        btn_edit.pack(side=tk.RIGHT, padx=4)

        btn_add = tk.Button(ctrl_frame, text="➕ Add Course", font=("Segoe UI", 9, "bold"), bg="#10b981", fg="#ffffff", bd=0, padx=10, pady=5, cursor="hand2", command=self.open_add_course_modal)
        btn_add.pack(side=tk.RIGHT, padx=4)

        columns = ("course_id", "course_code", "course_name", "credits", "dept_code", "faculty_name", "time_slot", "capacity", "available")
        self.course_tree = ttk.Treeview(self.tab_courses, columns=columns, show="headings", height=11)

        headings = {
            "course_id": ("ID", 40),
            "course_code": ("Code", 80),
            "course_name": ("Course Title", 220),
            "credits": ("Credits", 60),
            "dept_code": ("Dept", 60),
            "faculty_name": ("Faculty Member", 150),
            "time_slot": ("Schedule", 120),
            "capacity": ("Enrolled / Max", 110),
            "available": ("Available Seats", 110),
        }

        for col, (head, width) in headings.items():
            self.course_tree.heading(col, text=head)
            self.course_tree.column(col, width=width, anchor="center" if col in ("course_id", "credits", "dept_code", "capacity", "available") else "w")

        scrollbar = ttk.Scrollbar(self.tab_courses, orient=tk.VERTICAL, command=self.course_tree.yview)
        self.course_tree.configure(yscroll=scrollbar.set)
        self.course_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_courses_table(self):
        for item in self.course_tree.get_children():
            self.course_tree.delete(item)

        dept_val = self.course_dept_var.get()
        search_val = self.course_search_entry.get().strip()

        success, msg, courses = models.get_all_courses(dept_filter=dept_val, search_query=search_val)
        if success:
            for c in courses:
                cap_str = f"{c['enrolled_count']} / {c['max_seats']}"
                avail = c['available_seats']
                self.course_tree.insert(
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
                        cap_str,
                        f"{avail} seats free" if avail > 0 else "FULL",
                    ),
                )

    def open_add_course_modal(self):
        self.open_course_modal(title="Add New Course", is_edit=False)

    def open_edit_course_modal(self):
        selected = self.course_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a course from the table to edit.")
            return
        item = self.course_tree.item(selected[0])
        course_id = item["values"][0]
        success, msg, course_data = models.get_course_by_id(course_id)
        if success and course_data:
            self.open_course_modal(title="Edit Course", is_edit=True, course_data=course_data)

    def open_course_modal(self, title, is_edit=False, course_data=None):
        modal = tk.Toplevel(self)
        modal.title(title)
        modal.geometry("450x520")
        modal.resizable(False, False)
        modal.configure(bg="#ffffff")
        modal.grab_set()

        tk.Label(modal, text=title, font=("Segoe UI", 14, "bold"), fg="#1e293b", bg="#ffffff").pack(pady=15)
        form_frame = tk.Frame(modal, bg="#ffffff", padx=30)
        form_frame.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("Course Code:", "code"),
            ("Course Name:", "name"),
            ("Credits:", "credits"),
            ("Department Code:", "dept"),
            ("Faculty Name:", "faculty"),
            ("Time Slot:", "timeslot"),
            ("Max Capacity (Seats):", "seats"),
        ]

        entries = {}
        s, m, depts_list = models.get_all_departments()
        departments = [d["dept_code"] for d in depts_list] if s else ["CSE"]

        for i, (label_text, key) in enumerate(fields):
            tk.Label(form_frame, text=label_text, font=("Segoe UI", 10, "bold"), fg="#475569", bg="#ffffff").grid(row=i, column=0, sticky="w", pady=6)
            if key == "dept":
                var = tk.StringVar(value=course_data["dept_code"] if is_edit else (departments[0] if departments else "CSE"))
                cb = ttk.Combobox(form_frame, textvariable=var, values=departments, state="readonly", width=25)
                cb.grid(row=i, column=1, sticky="w", pady=6)
                entries[key] = var
            else:
                entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=27, bd=1, relief=tk.SOLID)
                entry.grid(row=i, column=1, sticky="w", pady=6)
                if is_edit and course_data:
                    val_map = {
                        "code": course_data["course_code"],
                        "name": course_data["course_name"],
                        "credits": str(course_data["credits"]),
                        "faculty": course_data["faculty_name"],
                        "timeslot": course_data["time_slot"],
                        "seats": str(course_data["max_seats"]),
                    }
                    entry.insert(0, val_map[key])
                entries[key] = entry

        def save_course():
            code = entries["code"].get().strip()
            name = entries["name"].get().strip()
            credits_str = entries["credits"].get().strip()
            dept = entries["dept"].get()
            faculty = entries["faculty"].get().strip()
            timeslot = entries["timeslot"].get().strip()
            seats_str = entries["seats"].get().strip()

            if not (code and name and credits_str and dept and faculty and timeslot and seats_str):
                messagebox.showerror("Validation Error", "All fields are required!", parent=modal)
                return

            try:
                credits_val = int(credits_str)
                seats_val = int(seats_str)
                if credits_val <= 0 or seats_val <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Validation Error", "Credits and Max Seats must be positive integers!", parent=modal)
                return

            if is_edit:
                success, msg, data = models.update_course(course_data["course_id"], code, name, credits_val, dept, faculty, timeslot, seats_val)
            else:
                success, msg, data = models.create_course(code, name, credits_val, dept, faculty, timeslot, seats_val)

            if success:
                messagebox.showinfo("Success", msg, parent=modal)
                modal.destroy()
                self.refresh_all_data()
            else:
                messagebox.showerror("Error", msg, parent=modal)

        save_btn = tk.Button(
            modal,
            text="Save Course",
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=save_course,
        )
        save_btn.pack(pady=20)

    def delete_selected_course(self):
        selected = self.course_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a course to delete.")
            return

        item = self.course_tree.item(selected[0])
        course_id = item["values"][0]
        course_code = item["values"][1]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete course '{course_code}'?\nThis will remove all associated registrations!"):
            success, msg, data = models.delete_course(course_id)
            if success:
                messagebox.showinfo("Success", msg)
                self.refresh_all_data()
            else:
                messagebox.showerror("Error", msg)

    # =========================================================================
    # TAB 2: STUDENTS MANAGEMENT (Full CRUD)
    # =========================================================================
    def setup_students_tab(self):
        ctrl_frame = tk.Frame(self.tab_students, bg="#ffffff")
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(ctrl_frame, text="Dept Filter:", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#334155").pack(side=tk.LEFT, padx=(0, 5))
        self.std_dept_var = tk.StringVar(value="ALL")
        self.std_dept_cb = ttk.Combobox(ctrl_frame, textvariable=self.std_dept_var, state="readonly", width=12)
        self.std_dept_cb.pack(side=tk.LEFT, padx=(0, 15))
        self.std_dept_cb.bind("<<ComboboxSelected>>", lambda e: self.load_students_table())

        btn_del = tk.Button(ctrl_frame, text="🗑️ Delete Student", font=("Segoe UI", 9, "bold"), bg="#ef4444", fg="#ffffff", bd=0, padx=10, pady=5, cursor="hand2", command=self.delete_selected_student)
        btn_del.pack(side=tk.RIGHT, padx=4)

        btn_edit = tk.Button(ctrl_frame, text="✏️ Edit Student", font=("Segoe UI", 9, "bold"), bg="#f59e0b", fg="#ffffff", bd=0, padx=10, pady=5, cursor="hand2", command=self.open_edit_student_modal)
        btn_edit.pack(side=tk.RIGHT, padx=4)

        btn_add = tk.Button(ctrl_frame, text="➕ Add Student", font=("Segoe UI", 9, "bold"), bg="#10b981", fg="#ffffff", bd=0, padx=10, pady=5, cursor="hand2", command=self.open_add_student_modal)
        btn_add.pack(side=tk.RIGHT, padx=4)

        columns = ("student_id", "name", "email", "dept_code", "dept_name", "credits_enrolled")
        self.std_tree = ttk.Treeview(self.tab_students, columns=columns, show="headings", height=11)

        headings = {
            "student_id": ("Student ID", 110),
            "name": ("Full Name", 200),
            "email": ("Institutional Email", 220),
            "dept_code": ("Dept", 70),
            "dept_name": ("Department Name", 220),
            "credits_enrolled": ("Credits Enrolled", 110),
        }

        for col, (head, width) in headings.items():
            self.std_tree.heading(col, text=head)
            self.std_tree.column(col, width=width, anchor="center" if col in ("student_id", "dept_code", "credits_enrolled") else "w")

        scrollbar = ttk.Scrollbar(self.tab_students, orient=tk.VERTICAL, command=self.std_tree.yview)
        self.std_tree.configure(yscroll=scrollbar.set)
        self.std_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_students_table(self):
        for item in self.std_tree.get_children():
            self.std_tree.delete(item)

        dept_val = self.std_dept_var.get()
        success, msg, students = models.get_all_students(dept_filter=dept_val)
        if success:
            for s in students:
                self.std_tree.insert(
                    "",
                    tk.END,
                    values=(
                        s["student_id"],
                        s["name"],
                        s["email"],
                        s["dept_code"],
                        s["dept_name"],
                        f"{s['credits_enrolled']} Credits",
                    ),
                )

    def open_add_student_modal(self):
        self.open_student_modal(title="Add New Student", is_edit=False)

    def open_edit_student_modal(self):
        selected = self.std_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a student to edit.")
            return
        item = self.std_tree.item(selected[0])
        student_id = item["values"][0]
        success, msg, std_data = models.get_student_by_id(student_id)
        if success and std_data:
            self.open_student_modal(title="Edit Student", is_edit=True, std_data=std_data)

    def open_student_modal(self, title, is_edit=False, std_data=None):
        modal = tk.Toplevel(self)
        modal.title(title)
        modal.geometry("420x420")
        modal.resizable(False, False)
        modal.configure(bg="#ffffff")
        modal.grab_set()

        tk.Label(modal, text=title, font=("Segoe UI", 14, "bold"), fg="#1e293b", bg="#ffffff").pack(pady=15)
        form_frame = tk.Frame(modal, bg="#ffffff", padx=25)
        form_frame.pack(fill=tk.BOTH, expand=True)

        s, m, depts_list = models.get_all_departments()
        departments = [d["dept_code"] for d in depts_list] if s else ["CSE"]

        fields = [
            ("Student ID:", "id"),
            ("Full Name:", "name"),
            ("Email:", "email"),
            ("Password:", "pass"),
            ("Department:", "dept"),
        ]
        entries = {}

        for i, (lbl_txt, key) in enumerate(fields):
            tk.Label(form_frame, text=lbl_txt, font=("Segoe UI", 10, "bold"), fg="#475569", bg="#ffffff").grid(row=i, column=0, sticky="w", pady=6)
            if key == "dept":
                var = tk.StringVar(value=std_data["dept_code"] if is_edit else (departments[0] if departments else "CSE"))
                cb = ttk.Combobox(form_frame, textvariable=var, values=departments, state="readonly", width=23)
                cb.grid(row=i, column=1, sticky="w", pady=6)
                entries[key] = var
            else:
                entry = tk.Entry(form_frame, font=("Segoe UI", 10), width=25, bd=1, relief=tk.SOLID)
                entry.grid(row=i, column=1, sticky="w", pady=6)
                if is_edit and std_data:
                    val_map = {
                        "id": std_data["student_id"],
                        "name": std_data["name"],
                        "email": std_data["email"],
                        "pass": std_data["password"],
                    }
                    entry.insert(0, val_map[key])
                    if key == "id":
                        entry.config(state="disabled")
                entries[key] = entry

        def save_student():
            std_id = std_data["student_id"] if is_edit else entries["id"].get().strip()
            name = entries["name"].get().strip()
            email = entries["email"].get().strip()
            passwd = entries["pass"].get().strip()
            dept = entries["dept"].get()

            if not (std_id and name and email and passwd and dept):
                messagebox.showerror("Validation Error", "All fields are required!", parent=modal)
                return

            if is_edit:
                success, msg, data = models.update_student(std_id, name, email, passwd, dept)
            else:
                success, msg, data = models.create_student(std_id, name, email, passwd, dept)

            if success:
                messagebox.showinfo("Success", msg, parent=modal)
                modal.destroy()
                self.refresh_all_data()
            else:
                messagebox.showerror("Error", msg, parent=modal)

        save_btn = tk.Button(
            modal,
            text="Save Student",
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=save_student,
        )
        save_btn.pack(pady=20)

    def delete_selected_student(self):
        selected = self.std_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a student to delete.")
            return

        item = self.std_tree.item(selected[0])
        student_id = item["values"][0]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete student '{student_id}'?\nThis will remove all associated registrations!"):
            success, msg, data = models.delete_student(student_id)
            if success:
                messagebox.showinfo("Success", msg)
                self.refresh_all_data()
            else:
                messagebox.showerror("Error", msg)

    # =========================================================================
    # TAB 3: REGISTRATIONS MANAGEMENT (Force Drop)
    # =========================================================================
    def setup_registrations_tab(self):
        ctrl_frame = tk.Frame(self.tab_registrations, bg="#ffffff")
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(ctrl_frame, text="Status Filter:", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#334155").pack(side=tk.LEFT, padx=(0, 5))
        self.reg_status_var = tk.StringVar(value="ALL")
        self.reg_status_cb = ttk.Combobox(ctrl_frame, textvariable=self.reg_status_var, values=["ALL", "ENROLLED", "DROPPED"], state="readonly", width=12)
        self.reg_status_cb.pack(side=tk.LEFT)
        self.reg_status_cb.bind("<<ComboboxSelected>>", lambda e: self.load_registrations_table())

        btn_force_drop = tk.Button(
            ctrl_frame,
            text="🚨 Force Drop Selected Registration",
            font=("Segoe UI", 9, "bold"),
            bg="#ef4444",
            fg="#ffffff",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.force_drop_registration,
        )
        btn_force_drop.pack(side=tk.RIGHT)

        columns = ("reg_id", "student_id", "student_name", "course_code", "course_name", "status", "date")
        self.reg_tree = ttk.Treeview(self.tab_registrations, columns=columns, show="headings", height=11)

        headings = {
            "reg_id": ("Reg ID", 60),
            "student_id": ("Student ID", 110),
            "student_name": ("Student Name", 180),
            "course_code": ("Course", 80),
            "course_name": ("Course Title", 220),
            "status": ("Status", 90),
            "date": ("Registration Timestamp", 150),
        }

        for col, (head, width) in headings.items():
            self.reg_tree.heading(col, text=head)
            self.reg_tree.column(col, width=width, anchor="center" if col in ("reg_id", "student_id", "course_code", "status") else "w")

        scrollbar = ttk.Scrollbar(self.tab_registrations, orient=tk.VERTICAL, command=self.reg_tree.yview)
        self.reg_tree.configure(yscroll=scrollbar.set)
        self.reg_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_registrations_table(self):
        for item in self.reg_tree.get_children():
            self.reg_tree.delete(item)

        status_val = self.reg_status_var.get()
        success, msg, regs = models.get_all_registrations(status_filter=status_val)

        if success:
            for r in regs:
                self.reg_tree.insert(
                    "",
                    tk.END,
                    values=(
                        r["registration_id"],
                        r["student_id"],
                        r["student_name"],
                        r["course_code"],
                        r["course_name"],
                        r["status"],
                        r["registration_date"],
                    ),
                )

    def force_drop_registration(self):
        selected = self.reg_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a registration from the table to drop.")
            return

        item = self.reg_tree.item(selected[0])
        reg_id = item["values"][0]
        std_id = item["values"][1]
        c_code = item["values"][3]
        status = item["values"][5]

        if status == "DROPPED":
            messagebox.showwarning("Invalid Operation", "This registration is already dropped.")
            return

        if messagebox.askyesno("Confirm Force Drop", f"Are you sure you want to force drop registration #{reg_id}?\nStudent: {std_id} | Course: {c_code}"):
            success, msg, data = models.drop_registration(reg_id)
            if success:
                messagebox.showinfo("Success", f"Force Drop Success: {msg}")
                self.refresh_all_data()
            else:
                messagebox.showerror("Error", msg)

    # =========================================================================
    # REFRESH CONTROLS
    # =========================================================================
    def refresh_all_data(self):
        success, msg, stats = models.get_dashboard_counts()
        if success:
            self.card_students.val_lbl.config(text=str(stats["total_students"]))
            self.card_courses.val_lbl.config(text=str(stats["total_courses"]))
            self.card_registrations.val_lbl.config(text=str(stats["active_registrations"]))

        s, m, depts_list = models.get_all_departments()
        depts = ["ALL"] + [d["dept_code"] for d in depts_list] if s else ["ALL"]
        self.course_dept_cb["values"] = depts
        self.std_dept_cb["values"] = depts

        self.load_courses_table()
        self.load_students_table()
        self.load_registrations_table()
