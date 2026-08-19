# East West University - Course Registration System

A Database Systems Course Project built in **Python** using **Tkinter (GUI)** and **SQLite3 (Database)**.

---

## 📁 Project Structure

```text
course_registration_system/
│
├── src/                              # All source code
│   ├── __init__.py
│   ├── main.py                       # Application entry point
│   ├── database.py                   # Database schema & seeding
│   ├── models.py                     # CRUD & Business logic functions
│   │
│   └── gui/                          # GUI dashboard modules
│       ├── __init__.py
│       ├── admin_dashboard.py        # Administrator portal
│       └── student_dashboard.py      # Student portal
│
├── data/                             # SQLite database file
│   └── ewu_course_reg.db
│
├── tests/                            # Test suite
│   └── test_database.py
│
├── scripts/                          # Utility scripts
│   └── capture_window.ps1
│
├── docs/                             # Documentation assets
│   └── test_cap.png
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

## 🚀 How to Run

Navigate to the project root folder `course_registration_system` and execute:

```bash
python -m src.main
```

Or execute tests using:

```bash
python tests/test_database.py
```

---

## 🔐 Test Login Credentials

| Role | Username | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Full CRUD on Courses, Students, Registrations |
| **Student (CSE)** | `student1` | `pass123` | Course Catalog Registration & Dropping |
| **Student (EEE)** | `student3` | `pass123` | Course Catalog Registration & Dropping |
| **Student (BBA)** | `student5` | `pass123` | Course Catalog Registration & Dropping |

---

## 🛠️ Technology Stack & Dependencies

- **Language**: Python 3.8+
- **GUI Framework**: Tkinter & `tkinter.ttk` (Standard Library)
- **Database Engine**: SQLite3 (Standard Library)
- **Dependencies**: None (Uses Python Standard Library exclusively)
