"""
Database connection, schema initialization, automated migration, and 100+ student seed data for College Tracker.
"""
import sqlite3
import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional, List
import config


def hash_password(password: str, salt: str = "college_tracker_salt") -> str:
    """Hash password using SHA-256 with a salt."""
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Establish a connection to SQLite database with foreign key support enabled.
    Returns a connection configured with Row factory.
    """
    path = db_path or config.DB_FILE
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None, seed_demo: bool = True) -> None:
    """
    Initialize SQLite tables if they do not exist, run automatic column and constraint migrations,
    and seed 100+ student accounts if needed.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Student', 'Administrator')),
            email TEXT,
            semester TEXT,
            division TEXT,
            firebase_uid TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Create subjects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            semester TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Create tasks table (Unified entity with role-based workflow statuses)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            task_type TEXT NOT NULL CHECK(task_type IN ('Assignment', 'Practical', 'Journal', 'Project', 'Presentation', 'Other')),
            description TEXT,
            assigned_date DATE,
            due_date DATE NOT NULL,
            priority TEXT NOT NULL CHECK(priority IN ('Low', 'Medium', 'High')),
            status TEXT NOT NULL CHECK(status IN ('Pending', 'In Progress', 'Submitted', 'Needs Resubmission', 'Completed')),
            submission_mode TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE RESTRICT,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE RESTRICT
        );
    """)

    conn.commit()

    # 4. Automated Schema Migration: Ensure firebase_uid column exists in existing DBs
    cursor.execute("PRAGMA table_info(users);")
    user_columns = [row[1] for row in cursor.fetchall()]
    if "firebase_uid" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN firebase_uid TEXT;")
        conn.commit()

    # 5. Automated Schema Migration: Check if tasks CHECK constraint supports 'Submitted'
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks';")
    tasks_sql_row = cursor.fetchone()
    if tasks_sql_row and tasks_sql_row[0] and "Submitted" not in tasks_sql_row[0]:
        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("ALTER TABLE tasks RENAME TO tasks_old;")
        cursor.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                task_type TEXT NOT NULL CHECK(task_type IN ('Assignment', 'Practical', 'Journal', 'Project', 'Presentation', 'Other')),
                description TEXT,
                assigned_date DATE,
                due_date DATE NOT NULL,
                priority TEXT NOT NULL CHECK(priority IN ('Low', 'Medium', 'High')),
                status TEXT NOT NULL CHECK(status IN ('Pending', 'In Progress', 'Submitted', 'Needs Resubmission', 'Completed')),
                submission_mode TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE RESTRICT,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE RESTRICT
            );
        """)
        cursor.execute("""
            INSERT INTO tasks (
                id, student_id, subject_id, title, task_type, description,
                assigned_date, due_date, priority, status, submission_mode, notes,
                created_at, updated_at
            )
            SELECT 
                id, student_id, subject_id, title, task_type, description,
                assigned_date, due_date, priority, status, submission_mode, notes,
                created_at, updated_at
            FROM tasks_old;
        """)
        cursor.execute("DROP TABLE tasks_old;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

    if seed_demo:
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Student';")
        student_count = cursor.fetchone()[0]
        if student_count < 90:
            seed_initial_data(conn)

    conn.close()


def seed_initial_data(conn: sqlite3.Connection) -> None:
    """
    Seed 100+ student accounts, academic subjects, and sample tasks across all semesters.
    """
    cursor = conn.cursor()
    today = datetime.now().date()
    yesterday = today - timedelta(days=2)
    tomorrow = today + timedelta(days=2)
    next_week = today + timedelta(days=7)

    # Clean existing data safely
    cursor.execute("DELETE FROM tasks;")
    cursor.execute("DELETE FROM subjects;")
    cursor.execute("DELETE FROM users;")
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('tasks', 'subjects', 'users');")
    except sqlite3.OperationalError:
        pass

    # 1. Admin Account (ID = 1)
    admin_pw = hash_password("admin123")
    cursor.execute("""
        INSERT INTO users (id, name, username, password_hash, role, email, semester, division)
        VALUES (1, 'College Administrator', 'admin', ?, 'Administrator', 'admin@college.edu', NULL, NULL);
    """, (admin_pw,))

    # 2. Seed Subjects with explicit IDs
    subjects_data = [
        (1, "Java Programming", "Semester 4"),
        (2, "Engineering Mathematics IV", "Semester 4"),
        (3, "Database Management Systems", "Semester 4"),
        (4, "Digital Electronics", "Semester 4"),
        (5, "Software Engineering", "Semester 4"),
        (6, "Data Structures & Algorithms", "Semester 3"),
        (7, "Computer Networks", "Semester 5"),
        (8, "Operating Systems", "Semester 5"),
        (9, "Artificial Intelligence", "Semester 6"),
        (10, "Cloud Computing & DevOps", "Semester 6"),
    ]
    cursor.executemany("INSERT INTO subjects (id, name, semester) VALUES (?, ?, ?);", subjects_data)

    # 3. 100 Student Names
    first_names = [
        "Rahul", "Priya", "Aman", "Sneha", "Rohan", "Ananya", "Aarav", "Pooja",
        "Vikram", "Neha", "Aditya", "Tanvi", "Devansh", "Riya", "Siddharth", "Kavya",
        "Harsh", "Meera", "Karan", "Divya", "Arjun", "Ishita", "Varun", "Shruti",
        "Nikhil", "Akanksha", "Sameer", "Simran", "Gaurav", "Swati", "Manish", "Aditi",
        "Pranav", "Bhavna", "Kunal", "Deepika", "Abhishek", "Rashmi", "Rajat", "Sakshi",
        "Suresh", "Mansi", "Yash", "Monika", "Deepak", "Nandini", "Vivek", "Pallavi",
        "Tarun", "Kritika", "Alok", "Garima", "Mohit", "Jyoti", "Naveen", "Megha",
        "Ankit", "Archana", "Sanjay", "Komal", "Mayank", "Shweta", "Ajay", "Shalini",
        "Sachin", "Preeti", "Sunil", "Payal", "Pankaj", "Anjali", "Rakesh", "Suman",
        "Dinesh", "Ritu", "Ashish", "Chhavi", "Vijay", "Anita", "Hemant", "Namrata",
        "Rajesh", "Poonam", "Lalit", "Shikha", "Bharat", "Aarti", "Mukesh", "Barkha",
        "Chetan", "Bhavya", "Dev", "Gunjan", "Girish", "Heena", "Jatin", "Isha",
        "Kapil", "Juhi", "Lokesh", "Kanika"
    ]

    last_names = [
        "Sharma", "Patel", "Verma", "Joshi", "Gupta", "Singh", "Mehta", "Iyer",
        "Nair", "Rao", "Deshmukh", "Kulkarni", "Shah", "Sen", "Bhat", "Nambiar",
        "Patil", "Menon", "Kapoor", "Pillai", "Choudhury", "Reddy", "Mishra", "Banerjee",
        "Agarwal", "Saxena", "Bose", "Ghosh", "Pandey", "Trivedi", "Shukla", "Chatterjee",
        "Bhardwaj", "Bhattacharya", "Chauhan", "Dubey", "Goswami", "Jadhav", "Kashyap", "Lal"
    ]

    semesters = ["Semester 1", "Semester 2", "Semester 3", "Semester 4", "Semester 5", "Semester 6", "Semester 7", "Semester 8"]
    divisions = ["A", "B", "C", "D"]

    student_pw = hash_password("student123")
    students_to_insert = []
    
    # Pre-add Rahul as Student #2 for primary demo
    students_to_insert.append((
        2, "Rahul Sharma", "rahul", student_pw, "Student", "rahul.sharma@college.edu", "Semester 4", "A"
    ))
    # Priya Patel as Student #3
    students_to_insert.append((
        3, "Priya Patel", "priya", student_pw, "Student", "priya.patel@college.edu", "Semester 4", "A"
    ))
    # Aman Verma as Student #4
    students_to_insert.append((
        4, "Aman Verma", "aman", student_pw, "Student", "aman.verma@college.edu", "Semester 4", "B"
    ))

    used_usernames = {"admin", "rahul", "priya", "aman"}

    # Generate the remaining 97 students to reach 100 total
    for i in range(5, 102):
        fn = first_names[(i - 5) % len(first_names)]
        ln = last_names[(i * 3) % len(last_names)]
        full_name = f"{fn} {ln}"
        
        base_username = f"{fn.lower()}.{ln.lower()}"
        username = base_username
        counter = 1
        while username in used_usernames:
            username = f"{base_username}{counter}"
            counter += 1
        used_usernames.add(username)

        email = f"{username}@college.edu"
        sem = semesters[(i) % len(semesters)]
        div = divisions[(i) % len(divisions)]

        students_to_insert.append((
            i, full_name, username, student_pw, "Student", email, sem, div
        ))

    cursor.executemany("""
        INSERT INTO users (id, name, username, password_hash, role, email, semester, division)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, students_to_insert)

    # 4. Seed Rich Tasks across students showcasing the role-based workflow
    # Rahul's tasks (Primary Demo)
    cursor.execute("""
        INSERT INTO tasks (student_id, subject_id, title, task_type, description, assigned_date, due_date, priority, status, submission_mode, notes)
        VALUES 
        (2, 1, 'Java Multithreading Assignment', 'Assignment', 'Implement thread synchronization with producer-consumer problem.', ?, ?, 'High', 'Pending', 'Online (LMS / Portal)', 'Refer unit 3 lecture slides.'),
        (2, 1, 'Java OOP Lab 04 - Inheritance', 'Practical', 'Implement class hierarchy and method overriding for Banking System.', ?, ?, 'High', 'Submitted', 'Lab Demonstration', 'Submitted on portal. Awaiting teacher sign-off.'),
        (2, 2, 'Laplace Transforms Journal', 'Journal', 'Solve exercise problems 4.1 to 4.5 in standard journal format.', ?, ?, 'Medium', 'Needs Resubmission', 'Hardcopy / Handwritten', 'Teacher requested rewriting Problem 4.3 with detailed steps.'),
        (2, 3, 'SQL Query Optimization Project', 'Project', 'Build normalized schema and optimize query execution plans.', ?, ?, 'High', 'In Progress', 'Presentation / Viva', 'Team project milestone 1.'),
        (2, 4, 'Flip-Flop Circuit Simulation', 'Practical', 'Simulate JK and D Flip-Flops in Logisim / Proteus.', ?, ?, 'Low', 'Completed', 'Lab Demonstration', 'Approved and graded by lab supervisor.'),
        (2, 5, 'Agile Scrum Case Study', 'Presentation', 'Prepare 10-minute presentation on Sprint Planning in FinTech.', ?, ?, 'Medium', 'Pending', 'Presentation / Viva', 'Slide deck in PDF format.');
    """, (
        yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d"),
        today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"),
        yesterday.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d"),
        yesterday.strftime("%Y-%m-%d"), next_week.strftime("%Y-%m-%d"),
        (yesterday - timedelta(days=5)).strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d"),
        today.strftime("%Y-%m-%d"), next_week.strftime("%Y-%m-%d"),
    ))

    # Tasks distribution across other students
    task_templates = [
        ("Assignment", "Unit 1 Problem Set", 1, "Medium", "Hardcopy / Handwritten"),
        ("Practical", "Lab Experiment 01 - Basics", 1, "High", "Lab Demonstration"),
        ("Journal", "Unit 2 Analysis Journal", 2, "Low", "Hardcopy / Handwritten"),
        ("Practical", "Database Schema Normalization Lab", 3, "High", "Lab Demonstration"),
        ("Assignment", "ER Diagram Case Study", 3, "Medium", "Online (LMS / Portal)"),
        ("Project", "Mini Project Phase 1 Submission", 5, "High", "Presentation / Viva"),
        ("Practical", "Sequential Logic Circuit Lab", 4, "Medium", "Lab Demonstration"),
        ("Assignment", "Sorting Algorithms Complexity Analysis", 6, "High", "Online (LMS / Portal)"),
        ("Practical", "Socket Programming Client-Server", 7, "High", "Lab Demonstration"),
        ("Presentation", "Cloud Microservices Architecture", 10, "Medium", "Presentation / Viva"),
    ]

    random.seed(42)
    generated_tasks = []

    for st_id in range(3, 102):
        num_tasks = 2 + (st_id % 3)
        for t_idx in range(num_tasks):
            tmpl = task_templates[(st_id * 2 + t_idx) % len(task_templates)]
            task_type, base_title, subject_id, priority, sub_mode = tmpl

            title = f"{base_title} (Batch {st_id % 4 + 1})"
            state_seed = (st_id + t_idx) % 6
            if state_seed == 0:
                status = "Pending"
                a_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
                d_date = (today - timedelta(days=random.randint(1, 3))).strftime("%Y-%m-%d")
            elif state_seed == 1:
                status = "Submitted"
                a_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")
                d_date = today.strftime("%Y-%m-%d")
            elif state_seed == 2:
                status = "Completed"
                a_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
                d_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")
            elif state_seed == 3:
                status = "In Progress"
                a_date = today.strftime("%Y-%m-%d")
                d_date = (today + timedelta(days=random.randint(2, 6))).strftime("%Y-%m-%d")
            elif state_seed == 4:
                status = "Needs Resubmission"
                a_date = (today - timedelta(days=4)).strftime("%Y-%m-%d")
                d_date = (today + timedelta(days=2)).strftime("%Y-%m-%d")
            else:
                status = "Pending"
                a_date = today.strftime("%Y-%m-%d")
                d_date = (today + timedelta(days=random.randint(4, 10))).strftime("%Y-%m-%d")

            generated_tasks.append((
                st_id, subject_id, title, task_type,
                f"Course submission requirements for {title}.",
                a_date, d_date, priority, status, sub_mode,
                "Auto-assigned academic task."
            ))

    cursor.executemany("""
        INSERT INTO tasks (
            student_id, subject_id, title, task_type, description,
            assigned_date, due_date, priority, status, submission_mode, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, generated_tasks)

    conn.commit()
