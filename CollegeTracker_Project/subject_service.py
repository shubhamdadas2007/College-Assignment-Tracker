"""
Subject management service for College Tracker.
Provides CRUD operations and enforces referential integrity rules (PRD Section 19, BR-06).
"""
import sqlite3
from typing import List, Optional, Tuple
from database import get_connection
from models import Subject


class SubjectService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_all_subjects(self) -> List[Subject]:
        """Retrieve all subjects ordered by name."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, semester, created_at FROM subjects ORDER BY name ASC;")
            rows = cursor.fetchall()
            return [
                Subject(
                    id=row["id"],
                    name=row["name"],
                    semester=row["semester"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]
        finally:
            conn.close()

    def get_subject_by_id(self, subject_id: int) -> Optional[Subject]:
        """Retrieve a specific subject by its ID."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, semester, created_at FROM subjects WHERE id = ?;", (subject_id,))
            row = cursor.fetchone()
            if row:
                return Subject(
                    id=row["id"],
                    name=row["name"],
                    semester=row["semester"],
                    created_at=row["created_at"]
                )
            return None
        finally:
            conn.close()

    def create_subject(self, name: str, semester: Optional[str] = None) -> Tuple[bool, Optional[int], str]:
        """Create a new academic subject."""
        clean_name = name.strip() if name else ""
        if not clean_name:
            return False, None, "Subject name is required."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO subjects (name, semester) VALUES (?, ?);",
                (clean_name, semester.strip() if semester else None)
            )
            conn.commit()
            return True, cursor.lastrowid, "Subject created successfully."
        except sqlite3.Error as e:
            return False, None, f"Database error: {str(e)}"
        finally:
            conn.close()

    def update_subject(self, subject_id: int, name: str, semester: Optional[str] = None) -> Tuple[bool, str]:
        """Update an existing subject."""
        clean_name = name.strip() if name else ""
        if not clean_name:
            return False, "Subject name is required."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE subjects SET name = ?, semester = ? WHERE id = ?;",
                (clean_name, semester.strip() if semester else None, subject_id)
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Subject not found."
            return True, "Subject updated successfully."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    def has_associated_tasks(self, subject_id: int) -> int:
        """Return the count of tasks referencing this subject."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE subject_id = ?;", (subject_id,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def delete_subject(self, subject_id: int) -> Tuple[bool, str]:
        """
        Delete a subject safely.
        Enforces Business Rule BR-06: A subject with associated tasks cannot be deleted.
        """
        task_count = self.has_associated_tasks(subject_id)
        if task_count > 0:
            return False, (
                f"Cannot delete subject: There are {task_count} academic task(s) currently linked to this subject. "
                "Please reassign or remove the linked tasks first."
            )

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM subjects WHERE id = ?;", (subject_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Subject not found."
            return True, "Subject deleted successfully."
        except sqlite3.IntegrityError:
            return False, "Cannot delete subject: Foreign key constraint violation."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()
