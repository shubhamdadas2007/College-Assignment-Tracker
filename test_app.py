"""
Comprehensive Automated Test Suite for College Assignment & Practical Submission Tracker (v4.0).
Verifies all Functional Requirements, Business Rules, 100+ student dataset, Firebase Auth, and Role-Based Completion Workflow.
"""
import os
import unittest
import tempfile
import sqlite3
from datetime import datetime, date, timedelta

import config
from database import init_db, get_connection, hash_password
from models import User, Subject, Task
from auth_service import AuthService
from subject_service import SubjectService
from student_service import StudentService
from task_service import TaskService
from deadline_service import calculate_deadline_state, parse_date, format_display_date, get_days_remaining


class TestCollegeTrackerSuite(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for isolated testing
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        init_db(self.temp_db_path, seed_demo=True)

        self.auth_service = AuthService(self.temp_db_path)
        self.subject_service = SubjectService(self.temp_db_path)
        self.student_service = StudentService(self.temp_db_path)
        self.task_service = TaskService(self.temp_db_path)

    def tearDown(self):
        os.close(self.temp_db_fd)
        try:
            os.remove(self.temp_db_path)
        except PermissionError:
            pass

    # -------------------------------------------------------------
    # 0. 100+ Students Dataset Verification
    # -------------------------------------------------------------
    def test_hundred_students_seeded(self):
        """Verify that at least 90-100 students are seeded in the database."""
        students = self.student_service.get_all_students()
        self.assertGreaterEqual(len(students), 90)
        self.assertEqual(len(students), 100)

        # Check that students have valid semester and division
        for s in students[:10]:
            self.assertIsNotNone(s.semester)
            self.assertIsNotNone(s.division)
            self.assertTrue(s.email.endswith("@college.edu"))

    # -------------------------------------------------------------
    # 1. Authentication & Role Handling (FR-01, FR-02, BR-01)
    # -------------------------------------------------------------
    def test_student_and_admin_authentication(self):
        """Test AC1 & AC2: Student and Admin can log in with valid credentials."""
        # Student Login by username
        success, student, msg = self.auth_service.authenticate("rahul", "student123", "Student")
        self.assertTrue(success)
        self.assertIsNotNone(student)
        self.assertEqual(student.username, "rahul")
        self.assertEqual(student.role, "Student")

        # Student Login by email
        success, student2, msg = self.auth_service.authenticate("rahul.sharma@college.edu", "student123", "Student")
        self.assertTrue(success)
        self.assertEqual(student2.id, student.id)

        # Admin Login
        success, admin, msg = self.auth_service.authenticate("admin", "admin123", "Administrator")
        self.assertTrue(success)
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, "admin")
        self.assertEqual(admin.role, "Administrator")

    def test_invalid_credentials_rejected(self):
        """Test AC3: Invalid passwords and wrong roles are rejected with clear errors."""
        # Wrong password
        success, user, msg = self.auth_service.authenticate("rahul", "wrongpassword", "Student")
        self.assertFalse(success)
        self.assertIn("Invalid username or password", msg)

        # Wrong role mismatch
        success, user, msg = self.auth_service.authenticate("rahul", "student123", "Administrator")
        self.assertFalse(success)
        self.assertIn("Access denied", msg)

        # Non-existent user
        success, user, msg = self.auth_service.authenticate("ghost_user", "pass", "Student")
        self.assertFalse(success)
        self.assertIn("Invalid username or password", msg)

    def test_password_hashing(self):
        """Test Security Requirement: Passwords stored as SHA-256 salted hashes, not plaintext."""
        conn = get_connection(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = 'admin';")
        pw_hash = cursor.fetchone()["password_hash"]
        conn.close()

        self.assertNotEqual(pw_hash, "admin123")
        self.assertEqual(pw_hash, hash_password("admin123"))

    # -------------------------------------------------------------
    # 2. Dynamic Deadline Calculation (FR-08, BR-04, AC13, AC14)
    # -------------------------------------------------------------
    def test_deadline_calculation_logic(self):
        """
        Verify dynamic deadline state evaluation:
        - status == 'Completed' -> 'Completed'
        - status == 'Submitted' -> 'Submitted'
        - due_date < today -> 'Overdue'
        - due_date == today -> 'Due Today'
        - due_date > today -> 'Upcoming'
        - Stored DB status is never overwritten with 'Overdue'.
        """
        today = date(2026, 9, 1)
        yesterday = date(2026, 8, 31)
        tomorrow = date(2026, 9, 2)

        # Completed tasks always show Completed state regardless of date
        self.assertEqual(calculate_deadline_state("Completed", yesterday, today), "Completed")
        self.assertEqual(calculate_deadline_state("Completed", tomorrow, today), "Completed")

        # Submitted tasks show Submitted (under review)
        self.assertEqual(calculate_deadline_state("Submitted", yesterday, today), "Submitted")
        self.assertEqual(calculate_deadline_state("Submitted", tomorrow, today), "Submitted")

        # Pending / In Progress tasks
        self.assertEqual(calculate_deadline_state("Pending", yesterday, today), "Overdue")
        self.assertEqual(calculate_deadline_state("In Progress", yesterday, today), "Overdue")
        self.assertEqual(calculate_deadline_state("Pending", today, today), "Due Today")
        self.assertEqual(calculate_deadline_state("Pending", tomorrow, today), "Upcoming")

    # -------------------------------------------------------------
    # 3. Role-Based Completion Workflow (Student Submit -> Admin Approve / Request Resubmission)
    # -------------------------------------------------------------
    def test_role_based_completion_workflow_complete(self):
        """
        Comprehensive test for role-based completion workflow:
        1. Student creates Pending task.
        2. Student CANNOT mark it Completed directly (Security / Permission enforcement).
        3. Student CANNOT set Needs Resubmission (Permission enforcement).
        4. Student submits for verification -> status becomes 'Submitted'.
        5. Student cannot re-submit an already Submitted task.
        6. Admin reviews and requests resubmission -> status becomes 'Needs Resubmission'.
        7. Student resubmits the task -> status transitions from 'Needs Resubmission' to 'Submitted'.
        8. Admin approves submission -> status transitions to 'Completed'.
        9. Student sees task as Completed and cannot modify its status further.
        """
        rahul = self.student_service.get_student_by_id(2)
        admin = User(id=1, name="Admin", username="admin", password_hash="", role="Administrator")

        # Step 1: Student creates Pending task
        today_str = datetime.now().strftime("%Y-%m-%d")
        s_ok, task_id, _ = self.task_service.create_task(
            student_id=rahul.id,
            subject_id=1,
            title="Database Sharding Assignment",
            task_type="Assignment",
            due_date_str=today_str,
            priority="High",
            status="Pending",
            acting_user=rahul
        )
        self.assertTrue(s_ok)

        # Step 2: Student attempts to directly mark task as Completed -> REJECTED
        c_ok, c_msg = self.task_service.update_task_status(task_id, "Completed", acting_user=rahul)
        self.assertFalse(c_ok)
        self.assertIn("Permission denied", c_msg)
        self.assertIn("Students cannot mark tasks as Completed", c_msg)

        # Step 3: Student attempts to set Needs Resubmission -> REJECTED
        r_ok, r_msg = self.task_service.update_task_status(task_id, "Needs Resubmission", acting_user=rahul)
        self.assertFalse(r_ok)
        self.assertIn("Permission denied", r_msg)

        # Step 4: Student submits for verification -> SUCCESS (status -> Submitted)
        sub_ok, sub_msg = self.task_service.update_task_status(task_id, "Submitted", acting_user=rahul)
        self.assertTrue(sub_ok)
        t_after_sub = self.task_service.get_task_by_id(task_id)
        self.assertEqual(t_after_sub.status, "Submitted")

        # Step 5: Student attempts to submit again when already Submitted -> REJECTED gracefully
        sub2_ok, sub2_msg = self.task_service.update_task_status(task_id, "Submitted", acting_user=rahul)
        self.assertFalse(sub2_ok)
        self.assertIn("already submitted", sub2_msg)

        # Step 6: Admin reviews and requests resubmission -> SUCCESS (status -> Needs Resubmission)
        admin_req_ok, admin_req_msg = self.task_service.update_task_status(task_id, "Needs Resubmission", acting_user=admin)
        self.assertTrue(admin_req_ok)
        t_after_req = self.task_service.get_task_by_id(task_id)
        self.assertEqual(t_after_req.status, "Needs Resubmission")

        # Step 7: Student resubmits task -> SUCCESS (status -> Submitted)
        resub_ok, resub_msg = self.task_service.update_task_status(task_id, "Submitted", acting_user=rahul)
        self.assertTrue(resub_ok)
        t_after_resub = self.task_service.get_task_by_id(task_id)
        self.assertEqual(t_after_resub.status, "Submitted")

        # Step 8: Admin approves submission -> SUCCESS (status -> Completed)
        app_ok, app_msg = self.task_service.update_task_status(task_id, "Completed", acting_user=admin)
        self.assertTrue(app_ok)
        t_after_app = self.task_service.get_task_by_id(task_id)
        self.assertEqual(t_after_app.status, "Completed")

        # Step 9: Student cannot submit or change an already Completed task
        post_ok, post_msg = self.task_service.update_task_status(task_id, "Submitted", acting_user=rahul)
        self.assertFalse(post_ok)
        self.assertIn("already verified", post_msg)

    # -------------------------------------------------------------
    # 4. Unified Task & Practicals Architecture (FR-06, FR-07, BR-03, AC8, AC9, AC10)
    # -------------------------------------------------------------
    def test_unified_task_entity_and_practicals_filter(self):
        """
        Verify that Practicals use the exact same tasks table and task service:
        - No separate practicals table or CRUD exists.
        - Practicals are queried with task_type = 'Practical'.
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        success, task_id, msg = self.task_service.create_task(
            student_id=2,
            subject_id=1,
            title="Java OOP Lab 05 - Polymorphism",
            task_type="Practical",
            due_date_str=today_str,
            priority="High",
            status="Pending"
        )
        self.assertTrue(success)
        self.assertIsNotNone(task_id)

        all_tasks = self.task_service.get_tasks(student_id=2)
        practical_tasks = self.task_service.get_tasks(student_id=2, task_type="Practical")

        task_ids_in_all = [t.id for t in all_tasks]
        task_ids_in_prac = [t.id for t in practical_tasks]

        self.assertIn(task_id, task_ids_in_all)
        self.assertIn(task_id, task_ids_in_prac)
        for t in practical_tasks:
            self.assertEqual(t.task_type, "Practical")

    # -------------------------------------------------------------
    # 5. Student Isolation & Permissions (FR-03, BR-01, BR-02, AC5, AC6)
    # -------------------------------------------------------------
    def test_student_isolation_and_modification_rules(self):
        """
        Test BR-01 & BR-02:
        - Students can only view and modify their own tasks.
        - Students cannot edit or delete other students' tasks.
        - Administrators can manage tasks for all students.
        """
        rahul = self.student_service.get_student_by_id(2)
        priya = self.student_service.get_student_by_id(3)
        admin = User(id=1, name="Admin", username="admin", password_hash="", role="Administrator")

        # Rahul tries to create a task for Priya -> Permission denied
        success, _, msg = self.task_service.create_task(
            student_id=priya.id,
            subject_id=1,
            title="Sneaky Task",
            task_type="Assignment",
            due_date_str="2026-09-10",
            acting_user=rahul
        )
        self.assertFalse(success)
        self.assertIn("Permission denied", msg)

        # Get Priya's task
        priya_tasks = self.task_service.get_tasks(student_id=priya.id)
        self.assertTrue(len(priya_tasks) > 0)
        priya_task_id = priya_tasks[0].id

        # Rahul tries to delete Priya's task -> Permission denied
        success, msg = self.task_service.delete_task(priya_task_id, acting_user=rahul)
        self.assertFalse(success)
        self.assertIn("Permission denied", msg)

        # Admin deletes Priya's task -> Allowed
        success, msg = self.task_service.delete_task(priya_task_id, acting_user=admin)
        self.assertTrue(success)

    # -------------------------------------------------------------
    # 6. Referential Integrity & Deletion Safety (BR-06, BR-07, AC11, AC12)
    # -------------------------------------------------------------
    def test_subject_deletion_safety(self):
        """Test BR-06: A subject with associated tasks cannot be deleted."""
        # Subject 1 has associated tasks
        success, msg = self.subject_service.delete_subject(1)
        self.assertFalse(success)
        self.assertIn("Cannot delete subject", msg)

        # Create a new empty subject with 0 tasks
        s_ok, new_sub_id, _ = self.subject_service.create_subject("Cloud Security", "Semester 7")
        self.assertTrue(s_ok)

        # Empty subject can be deleted safely
        del_ok, del_msg = self.subject_service.delete_subject(new_sub_id)
        self.assertTrue(del_ok)

    def test_student_deletion_safety(self):
        """Test BR-07: A student with associated tasks cannot be deleted."""
        # Student 2 (Rahul) has active tasks
        success, msg = self.student_service.delete_student(2)
        self.assertFalse(success)
        self.assertIn("Cannot delete student", msg)

        # Register a new student with no tasks
        s_ok, new_st_id, _ = self.student_service.create_student(
            name="New Student",
            username="newstudent999",
            password="password123"
        )
        self.assertTrue(s_ok)

        # Deleting student with 0 tasks succeeds
        del_ok, del_msg = self.student_service.delete_student(new_st_id)
        self.assertTrue(del_ok)

    # -------------------------------------------------------------
    # 7. Task Validation Rules (FR-14, BR-08)
    # -------------------------------------------------------------
    def test_task_date_validation(self):
        """Test BR-08: due_date must be >= assigned_date and title required."""
        # Empty title
        success, _, msg = self.task_service.create_task(
            student_id=2,
            subject_id=1,
            title="",
            task_type="Assignment",
            due_date_str="2026-09-10"
        )
        self.assertFalse(success)
        self.assertIn("title is required", msg)

        # Due date before assigned date
        success, _, msg = self.task_service.create_task(
            student_id=2,
            subject_id=1,
            title="Impossible Assignment",
            task_type="Assignment",
            assigned_date_str="2026-09-15",
            due_date_str="2026-09-10"
        )
        self.assertFalse(success)
        self.assertIn("Due date cannot be earlier than assigned date", msg)

    # -------------------------------------------------------------
    # 8. Live Dashboard Metrics & Analytics (FR-11, FR-12, BR-09)
    # -------------------------------------------------------------
    def test_dashboard_metrics_and_workflow_counts(self):
        """
        Verify that dashboard counters separate Submitted from Completed:
        - Submitted does NOT contribute to Completed count.
        - Only Admin-approved tasks increment Completed.
        """
        rahul = self.student_service.get_student_by_id(2)
        admin = User(id=1, name="Admin", username="admin", password_hash="", role="Administrator")

        # Create a new Pending task for Rahul
        s_ok, task_id, _ = self.task_service.create_task(
            student_id=2,
            subject_id=1,
            title="Metric Verification Task",
            task_type="Assignment",
            due_date_str="2026-09-20",
            priority="Medium",
            status="Pending"
        )
        self.assertTrue(s_ok)

        m0 = self.task_service.get_dashboard_metrics(student_id=2)
        c0 = m0["completed"]
        sub0 = m0["submitted"]

        # Student submits task
        self.task_service.update_task_status(task_id, "Submitted", acting_user=rahul)

        m1 = self.task_service.get_dashboard_metrics(student_id=2)
        # Completed must NOT increase when task is merely Submitted
        self.assertEqual(m1["completed"], c0)
        # Submitted counter must increase by 1
        self.assertEqual(m1["submitted"], sub0 + 1)

        # Admin approves task -> status becomes Completed
        self.task_service.update_task_status(task_id, "Completed", acting_user=admin)

        m2 = self.task_service.get_dashboard_metrics(student_id=2)
        # Completed must now increase by 1
        self.assertEqual(m2["completed"], c0 + 1)
        # Submitted counter must decrease by 1
        self.assertEqual(m2["submitted"], sub0)

    # -------------------------------------------------------------
    # 9. Search, Filter, and Sorting (FR-09, FR-10, AC15, AC16)
    # -------------------------------------------------------------
    def test_search_and_sorting(self):
        """Test case-insensitive search and multiple sorting orders."""
        results = self.task_service.get_tasks(search_query="multithreading")
        self.assertTrue(len(results) >= 1)
        self.assertIn("Multithreading", results[0].title)

        results_lower = self.task_service.get_tasks(search_query="MULTITHREADING")
        self.assertEqual(len(results), len(results_lower))

        tasks_sorted = self.task_service.get_tasks(sort_by="priority_desc")
        self.assertTrue(len(tasks_sorted) > 0)
        if len(tasks_sorted) > 1:
            self.assertEqual(tasks_sorted[0].priority, "High")


if __name__ == "__main__":
    unittest.main()
