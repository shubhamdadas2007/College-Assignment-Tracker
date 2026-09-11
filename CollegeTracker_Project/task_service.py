"""
Task service for College Tracker.
Handles unified CRUD operations for all academic work (Assignments, Practicals, Journals, Projects, etc.)
Enforces student isolation, validation, filtering, search, sorting, and dashboard metrics.
"""
import sqlite3
from datetime import datetime, date
from typing import List, Optional, Tuple, Dict, Any
from database import get_connection
from models import Task, User
from deadline_service import calculate_deadline_state, parse_date, get_current_date
import config


class TaskService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _row_to_task(self, row: sqlite3.Row, current_date: Optional[date] = None) -> Task:
        """Convert a SQLite row into a Task model with dynamic deadline state."""
        status = row["status"]
        due_date = row["due_date"]
        deadline_state = calculate_deadline_state(status, due_date, current_date)

        return Task(
            id=row["id"],
            student_id=row["student_id"],
            subject_id=row["subject_id"],
            title=row["title"],
            task_type=row["task_type"],
            description=row["description"],
            assigned_date=row["assigned_date"],
            due_date=row["due_date"],
            priority=row["priority"],
            status=row["status"],
            submission_mode=row["submission_mode"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            student_name=row["student_name"] if "student_name" in row.keys() else None,
            student_username=row["student_username"] if "student_username" in row.keys() else None,
            subject_name=row["subject_name"] if "subject_name" in row.keys() else None,
            deadline_state=deadline_state
        )

    def validate_task_data(
        self,
        student_id: int,
        subject_id: int,
        title: str,
        task_type: str,
        due_date_str: str,
        priority: str,
        status: str,
        assigned_date_str: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Validate task data constraints and business rules."""
        if not title or not title.strip():
            return False, "Task title is required."

        if not student_id or student_id <= 0:
            return False, "A valid student must be selected."

        if not subject_id or subject_id <= 0:
            return False, "A valid subject must be selected."

        if task_type not in config.TASK_TYPES:
            return False, f"Invalid task type. Choose from: {', '.join(config.TASK_TYPES)}"

        if priority not in config.TASK_PRIORITIES:
            return False, f"Invalid priority. Choose from: {', '.join(config.TASK_PRIORITIES)}"

        if status not in config.TASK_STATUSES:
            return False, f"Invalid status. Choose from: {', '.join(config.TASK_STATUSES)}"

        parsed_due = parse_date(due_date_str)
        if not parsed_due:
            return False, "Invalid due date format. Expected YYYY-MM-DD."

        if assigned_date_str and assigned_date_str.strip():
            parsed_assigned = parse_date(assigned_date_str)
            if not parsed_assigned:
                return False, "Invalid assigned date format. Expected YYYY-MM-DD."
            if parsed_due < parsed_assigned:
                return False, "Due date cannot be earlier than assigned date."

        return True, "Valid"

    def create_task(
        self,
        student_id: int,
        subject_id: int,
        title: str,
        task_type: str,
        due_date_str: str,
        priority: str = "Medium",
        status: str = "Pending",
        description: Optional[str] = None,
        assigned_date_str: Optional[str] = None,
        submission_mode: Optional[str] = None,
        notes: Optional[str] = None,
        acting_user: Optional[User] = None
    ) -> Tuple[bool, Optional[int], str]:
        """
        Create a new academic task.
        Enforces permissions: Students can only create tasks for themselves.
        """
        if acting_user and acting_user.is_student and acting_user.id != student_id:
            return False, None, "Permission denied: Students can only create tasks for themselves."

        is_valid, err_msg = self.validate_task_data(
            student_id=student_id,
            subject_id=subject_id,
            title=title,
            task_type=task_type,
            due_date_str=due_date_str,
            priority=priority,
            status=status,
            assigned_date_str=assigned_date_str
        )
        if not is_valid:
            return False, None, err_msg

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO tasks (
                    student_id, subject_id, title, task_type, description, 
                    assigned_date, due_date, priority, status, submission_mode, notes,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """, (
                student_id,
                subject_id,
                title.strip(),
                task_type,
                description.strip() if description else None,
                assigned_date_str.strip() if assigned_date_str else None,
                due_date_str.strip(),
                priority,
                status,
                submission_mode.strip() if submission_mode else None,
                notes.strip() if notes else None
            ))
            conn.commit()
            return True, cursor.lastrowid, "Task created successfully."
        except sqlite3.IntegrityError as e:
            return False, None, f"Foreign key error: Selected student or subject does not exist. ({str(e)})"
        except sqlite3.Error as e:
            return False, None, f"Database error: {str(e)}"
        finally:
            conn.close()

    def update_task(
        self,
        task_id: int,
        student_id: int,
        subject_id: int,
        title: str,
        task_type: str,
        due_date_str: str,
        priority: str,
        status: str,
        description: Optional[str] = None,
        assigned_date_str: Optional[str] = None,
        submission_mode: Optional[str] = None,
        notes: Optional[str] = None,
        acting_user: Optional[User] = None
    ) -> Tuple[bool, str]:
        """
        Update an existing task.
        Enforces permissions: Students can only edit their own tasks.
        """
        existing = self.get_task_by_id(task_id)
        if not existing:
            return False, "Task not found."

        if acting_user and acting_user.is_student:
            if existing.student_id != acting_user.id or student_id != acting_user.id:
                return False, "Permission denied: Students can only modify their own tasks."

        is_valid, err_msg = self.validate_task_data(
            student_id=student_id,
            subject_id=subject_id,
            title=title,
            task_type=task_type,
            due_date_str=due_date_str,
            priority=priority,
            status=status,
            assigned_date_str=assigned_date_str
        )
        if not is_valid:
            return False, err_msg

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE tasks
                SET student_id = ?, subject_id = ?, title = ?, task_type = ?,
                    description = ?, assigned_date = ?, due_date = ?, priority = ?,
                    status = ?, submission_mode = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """, (
                student_id,
                subject_id,
                title.strip(),
                task_type,
                description.strip() if description else None,
                assigned_date_str.strip() if assigned_date_str else None,
                due_date_str.strip(),
                priority,
                status,
                submission_mode.strip() if submission_mode else None,
                notes.strip() if notes else None,
                task_id
            ))
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Task not found."
            return True, "Task updated successfully."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    def update_task_status(self, task_id: int, new_status: str, acting_user: Optional[User] = None) -> Tuple[bool, str]:
        """Quickly update the status of a task."""
        if new_status not in config.TASK_STATUSES:
            return False, f"Invalid status: {new_status}"

        existing = self.get_task_by_id(task_id)
        if not existing:
            return False, "Task not found."

        if acting_user and acting_user.is_student and existing.student_id != acting_user.id:
            return False, "Permission denied: You can only update your own tasks."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE tasks
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """, (new_status, task_id))
            conn.commit()
            return True, f"Status updated to '{new_status}'."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    def delete_task(self, task_id: int, acting_user: Optional[User] = None) -> Tuple[bool, str]:
        """
        Delete a task.
        Enforces permissions: Students can only delete their own tasks.
        """
        existing = self.get_task_by_id(task_id)
        if not existing:
            return False, "Task not found."

        if acting_user and acting_user.is_student and existing.student_id != acting_user.id:
            return False, "Permission denied: Students can only delete their own tasks."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
            conn.commit()
            return True, "Task deleted successfully."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Retrieve a single task with joined student and subject names."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    t.id, t.student_id, t.subject_id, t.title, t.task_type,
                    t.description, t.assigned_date, t.due_date, t.priority,
                    t.status, t.submission_mode, t.notes, t.created_at, t.updated_at,
                    u.name AS student_name, u.username AS student_username,
                    s.name AS subject_name
                FROM tasks t
                JOIN users u ON t.student_id = u.id
                JOIN subjects s ON t.subject_id = s.id
                WHERE t.id = ?;
            """, (task_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_task(row)
            return None
        finally:
            conn.close()

    def get_tasks(
        self,
        student_id: Optional[int] = None,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        subject_id: Optional[int] = None,
        priority: Optional[str] = None,
        deadline_state: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "due_date_asc",
        current_date: Optional[date] = None
    ) -> List[Task]:
        """
        Query tasks with comprehensive filters, search, and sorting.
        Used for both general Tasks view and Practicals view (where task_type='Practical').
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            query = """
                SELECT 
                    t.id, t.student_id, t.subject_id, t.title, t.task_type,
                    t.description, t.assigned_date, t.due_date, t.priority,
                    t.status, t.submission_mode, t.notes, t.created_at, t.updated_at,
                    u.name AS student_name, u.username AS student_username,
                    s.name AS subject_name
                FROM tasks t
                JOIN users u ON t.student_id = u.id
                JOIN subjects s ON t.subject_id = s.id
                WHERE 1=1
            """
            params: List[Any] = []

            if student_id:
                query += " AND t.student_id = ?"
                params.append(student_id)

            if task_type and task_type != "All":
                query += " AND t.task_type = ?"
                params.append(task_type)

            if status and status != "All":
                query += " AND t.status = ?"
                params.append(status)

            if subject_id and subject_id > 0:
                query += " AND t.subject_id = ?"
                params.append(subject_id)

            if priority and priority != "All":
                query += " AND t.priority = ?"
                params.append(priority)

            if search_query and search_query.strip():
                term = f"%{search_query.strip()}%"
                query += " AND (t.title LIKE ? OR s.name LIKE ? OR u.name LIKE ?)"
                params.extend([term, term, term])

            # Sorting clause
            order_clauses = {
                "due_date_asc": "t.due_date ASC, t.id ASC",
                "due_date_desc": "t.due_date DESC, t.id ASC",
                "priority_desc": "CASE t.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END, t.due_date ASC",
                "priority_asc": "CASE t.priority WHEN 'Low' THEN 1 WHEN 'Medium' THEN 2 WHEN 'High' THEN 3 ELSE 4 END, t.due_date ASC",
                "status_asc": "t.status ASC, t.due_date ASC",
                "subject_asc": "s.name ASC, t.due_date ASC",
                "title_asc": "t.title ASC",
                "student_asc": "u.name ASC, t.due_date ASC",
            }
            sort_sql = order_clauses.get(sort_by, "t.due_date ASC")
            query += f" ORDER BY {sort_sql};"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            tasks = [self._row_to_task(r, current_date) for r in rows]

            # Filter dynamically calculated deadline state in memory if requested
            if deadline_state and deadline_state != "All":
                tasks = [t for t in tasks if t.deadline_state == deadline_state]

            return tasks
        finally:
            conn.close()

    def get_dashboard_metrics(self, student_id: Optional[int] = None, current_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Calculate live statistics directly from SQLite for Dashboards (PRD Section 9 & 10).
        Returns counts for: Total, Pending, In Progress, Completed, Overdue, Due Today.
        """
        today = current_date or get_current_date()
        today_str = today.strftime("%Y-%m-%d")

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            where_student = "WHERE student_id = ?" if student_id else ""
            params = [student_id] if student_id else []

            # 1. Total tasks
            cursor.execute(f"SELECT COUNT(*) FROM tasks {where_student};", params)
            total = cursor.fetchone()[0]

            # 2. Completed
            cursor.execute(
                f"SELECT COUNT(*) FROM tasks {where_student} {'AND' if where_student else 'WHERE'} status = 'Completed';",
                params
            )
            completed = cursor.fetchone()[0]

            # 3. Pending
            cursor.execute(
                f"SELECT COUNT(*) FROM tasks {where_student} {'AND' if where_student else 'WHERE'} status = 'Pending';",
                params
            )
            pending = cursor.fetchone()[0]

            # 4. In Progress
            cursor.execute(
                f"SELECT COUNT(*) FROM tasks {where_student} {'AND' if where_student else 'WHERE'} status = 'In Progress';",
                params
            )
            in_progress = cursor.fetchone()[0]

            # 5. Overdue (status != Completed AND due_date < today)
            cursor.execute(
                f"SELECT COUNT(*) FROM tasks {where_student} {'AND' if where_student else 'WHERE'} status != 'Completed' AND due_date < ?;",
                params + [today_str]
            )
            overdue = cursor.fetchone()[0]

            # 6. Due Today (status != Completed AND due_date == today)
            cursor.execute(
                f"SELECT COUNT(*) FROM tasks {where_student} {'AND' if where_student else 'WHERE'} status != 'Completed' AND due_date = ?;",
                params + [today_str]
            )
            due_today = cursor.fetchone()[0]

            return {
                "total": total,
                "pending": pending,
                "in_progress": in_progress,
                "completed": completed,
                "overdue": overdue,
                "due_today": due_today,
            }
        finally:
            conn.close()

    def get_upcoming_deadlines(self, student_id: Optional[int] = None, limit: int = 5, current_date: Optional[date] = None) -> List[Task]:
        """
        Get nearest upcoming deadlines (status != Completed, ordered by due_date ASC).
        """
        today = current_date or get_current_date()
        tasks = self.get_tasks(
            student_id=student_id,
            status=None,
            sort_by="due_date_asc",
            current_date=today
        )
        # Filter out completed tasks and get nearest active tasks
        active_tasks = [t for t in tasks if t.status != "Completed"]
        return active_tasks[:limit]

    def get_overdue_students(self, current_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        For Admin Dashboard: Return list of students who have one or more overdue tasks.
        """
        today = current_date or get_current_date()
        today_str = today.strftime("%Y-%m-%d")

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    u.id AS student_id,
                    u.name AS student_name,
                    u.username AS student_username,
                    u.semester,
                    u.division,
                    COUNT(t.id) AS overdue_count
                FROM users u
                JOIN tasks t ON u.id = t.student_id
                WHERE u.role = 'Student' AND t.status != 'Completed' AND t.due_date < ?
                GROUP BY u.id, u.name, u.username, u.semester, u.division
                ORDER BY overdue_count DESC, u.name ASC;
            """, (today_str,))
            rows = cursor.fetchall()
            return [
                {
                    "student_id": r["student_id"],
                    "name": r["student_name"],
                    "username": r["student_username"],
                    "semester": r["semester"],
                    "division": r["division"],
                    "overdue_count": r["overdue_count"]
                }
                for r in rows
            ]
        finally:
            conn.close()

    def get_subject_workload(self, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Calculate task counts and completion rates per subject for analytics and dashboards.
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            where_clause = "WHERE t.student_id = ?" if student_id else ""
            params = [student_id] if student_id else []

            query = f"""
                SELECT 
                    s.id AS subject_id,
                    s.name AS subject_name,
                    COUNT(t.id) AS total_tasks,
                    SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks,
                    SUM(CASE WHEN t.status = 'Pending' THEN 1 ELSE 0 END) AS pending_tasks,
                    SUM(CASE WHEN t.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_tasks
                FROM subjects s
                LEFT JOIN tasks t ON s.id = t.subject_id {'AND t.student_id = ?' if student_id else ''}
                GROUP BY s.id, s.name
                ORDER BY s.name ASC;
            """
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            result = []
            for r in rows:
                total = r["total_tasks"] or 0
                completed = r["completed_tasks"] or 0
                rate = round((completed / total * 100), 1) if total > 0 else 0.0
                result.append({
                    "subject_id": r["subject_id"],
                    "subject_name": r["subject_name"],
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "pending_tasks": r["pending_tasks"] or 0,
                    "in_progress_tasks": r["in_progress_tasks"] or 0,
                    "completion_rate": rate
                })
            return result
        finally:
            conn.close()

    def get_student_submission_rates(self) -> List[Dict[str, Any]]:
        """
        For Admin Analytics: Get completion rates across all students.
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    u.id AS student_id,
                    u.name AS student_name,
                    u.username AS student_username,
                    COUNT(t.id) AS total_tasks,
                    SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks
                FROM users u
                LEFT JOIN tasks t ON u.id = t.student_id
                WHERE u.role = 'Student'
                GROUP BY u.id, u.name, u.username
                ORDER BY u.name ASC;
            """)
            rows = cursor.fetchall()
            result = []
            for r in rows:
                total = r["total_tasks"] or 0
                completed = r["completed_tasks"] or 0
                rate = round((completed / total * 100), 1) if total > 0 else 0.0
                result.append({
                    "student_id": r["student_id"],
                    "name": r["student_name"],
                    "username": r["student_username"],
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "completion_rate": rate
                })
            return result
        finally:
            conn.close()
