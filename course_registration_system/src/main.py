"""
src/main.py - East West University Course Registration System
Application Entry Point, Login Screen, and Role-Based Navigation Routing.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
for p in (project_root, current_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from src.database import seed_database
    from src.models import authenticate_user
    from src.gui.admin_dashboard import AdminDashboard
    from src.gui.student_dashboard import StudentDashboard
except ImportError:
    from database import seed_database
    from models import authenticate_user
    from gui.admin_dashboard import AdminDashboard
    from gui.student_dashboard import StudentDashboard


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("East West University - Course Registration System")
        self.geometry("1020x680")
        self.minsize(950, 600)
        self.configure(bg="#f8fafc")

        # Initialize database schema and default seed data in data/ directory
        seed_database(force_reset=False)

        self.current_user = None
        self.current_frame = None

        self.show_login_screen()

    def clear_current_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()
            self.current_frame = None

    # =========================================================================
    # LOGIN SCREEN
    # =========================================================================
    def show_login_screen(self):
        self.clear_current_frame()
        self.current_user = None

        login_frame = tk.Frame(self, bg="#f8fafc")
        login_frame.pack(fill=tk.BOTH, expand=True)
        self.current_frame = login_frame

        # Centered Container Card
        card = tk.Frame(login_frame, bg="#ffffff", bd=1, relief=tk.SOLID, padx=35, pady=35)
        card.place(relx=0.5, rely=0.48, anchor=tk.CENTER)

        # Header Title & Subtitle
        header_lbl = tk.Label(
            card,
            text="EAST WEST UNIVERSITY",
            font=("Segoe UI", 18, "bold"),
            fg="#1e3a8a",
            bg="#ffffff",
        )
        header_lbl.pack(pady=(0, 2))

        subtitle_lbl = tk.Label(
            card,
            text="Course Registration System Portal",
            font=("Segoe UI", 11),
            fg="#64748b",
            bg="#ffffff",
        )
        subtitle_lbl.pack(pady=(0, 25))

        # Username Input
        tk.Label(card, text="Username:", font=("Segoe UI", 10, "bold"), fg="#334155", bg="#ffffff").pack(anchor="w", pady=(0, 3))
        username_entry = tk.Entry(card, font=("Segoe UI", 11), width=32, bd=1, relief=tk.SOLID)
        username_entry.pack(pady=(0, 15), ipady=4)
        username_entry.focus()

        # Password Input
        tk.Label(card, text="Password:", font=("Segoe UI", 10, "bold"), fg="#334155", bg="#ffffff").pack(anchor="w", pady=(0, 3))
        password_entry = tk.Entry(card, font=("Segoe UI", 11), show="•", width=32, bd=1, relief=tk.SOLID)
        password_entry.pack(pady=(0, 20), ipady=4)

        def handle_login(event=None):
            uname = username_entry.get().strip()
            passwd = password_entry.get().strip()

            if not uname or not passwd:
                messagebox.showerror("Login Error", "Please enter both username and password.")
                return

            success, msg, user = authenticate_user(uname, passwd)
            if success and user:
                self.current_user = user
                if user["role"] == "admin":
                    self.show_admin_dashboard()
                elif user["role"] == "student":
                    self.show_student_dashboard()
                else:
                    messagebox.showerror("Role Error", f"Unknown user role: {user['role']}")
            else:
                messagebox.showerror("Authentication Failed", msg)

        password_entry.bind("<Return>", handle_login)
        username_entry.bind("<Return>", handle_login)

        login_btn = tk.Button(
            card,
            text="SIGN IN TO SYSTEM",
            font=("Segoe UI", 11, "bold"),
            bg="#1e3a8a",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            width=30,
            pady=8,
            cursor="hand2",
            command=handle_login,
        )
        login_btn.pack(pady=(5, 20))

        # Helper Reference Table for Demo Accounts
        demo_frame = tk.LabelFrame(
            card,
            text=" Test Credentials Reference ",
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#ffffff",
            padx=12,
            pady=10,
        )
        demo_frame.pack(fill=tk.X)

        demo_info = [
            ("Role", "Username", "Password"),
            ("Admin Portal", "admin", "admin123"),
            ("Student (CSE)", "student1", "pass123"),
            ("Student (EEE)", "student3", "pass123"),
            ("Student (BBA)", "student5", "pass123"),
        ]

        for r_idx, row in enumerate(demo_info):
            for c_idx, val in enumerate(row):
                is_header = r_idx == 0
                lbl = tk.Label(
                    demo_frame,
                    text=val,
                    font=("Segoe UI", 8, "bold" if is_header else "normal"),
                    fg="#1e293b" if is_header else "#64748b",
                    bg="#ffffff",
                    width=15 if c_idx == 0 else 10,
                    anchor="w",
                )
                lbl.grid(row=r_idx, column=c_idx, sticky="w", pady=1)

    # =========================================================================
    # ROLE ROUTING
    # =========================================================================
    def show_admin_dashboard(self):
        self.clear_current_frame()
        dashboard = AdminDashboard(self, self.current_user, self.show_login_screen)
        dashboard.pack(fill=tk.BOTH, expand=True)
        self.current_frame = dashboard

    def show_student_dashboard(self):
        self.clear_current_frame()
        dashboard = StudentDashboard(self, self.current_user, self.show_login_screen)
        dashboard.pack(fill=tk.BOTH, expand=True)
        self.current_frame = dashboard


def main():
    app = Application()
    app.mainloop()


if __name__ == "__main__":
    main()
