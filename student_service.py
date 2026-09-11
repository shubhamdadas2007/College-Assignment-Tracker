"""
Student management service for College Tracker.
Provides CRUD operations for student accounts (PRD Section 20, BR-07).
"""
import sqlite3
from typing import List, Optional, Tuple
from database import get_connection, hash_password
from models import User


class StudentService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_all_students(self, search_query: Optional[str] = None) -> List[User]:
        """Retrieve all student accounts, optionally filtered by search query."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            if search_query and search_query.strip():
                term = f"%{search_query.strip()}%"
                cursor.execute("""
                    SELECT id, name, username, password_hash, role, email, semester, division, created_at 
                    FROM users 
                    WHERE role = 'Student' AND (name LIKE ? OR username LIKE ? OR email LIKE ? OR semester LIKE ?)
                    ORDER BY name ASC;
                """, (term, term, term, term))
            else:
                cursor.execute("""
                    SELECT id, name, username, password_hash, role, email, semester, division, created_at 
                    FROM users 
                    WHERE role = 'Student'
                    ORDER BY name ASC;
                """)
            rows = cursor.fetchall()
            return [
                User(
                    id=row["id"],
                    name=row["name"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=row["role"],
                    email=row["email"],
                    semester=row["semester"],
                    division=row["division"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]
        finally:
            conn.close()

    def get_student_by_id(self, student_id: int) -> Optional[User]:
        """Retrieve a student by user ID."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, name, username, password_hash, role, email, semester, division, created_at 
                FROM users 
                WHERE id = ? AND role = 'Student';
            """, (student_id,))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row["id"],
                    name=row["name"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=row["role"],
                    email=row["email"],
                    semester=row["semester"],
                    division=row["division"],
                    created_at=row["created_at"]
                )
            return None
        finally:
            conn.close()

    def create_student(
        self,
        name: str,
        username: str,
        password: str,
        email: Optional[str] = None,
        semester: Optional[str] = None,
        division: Optional[str] = None
    ) -> Tuple[bool, Optional[int], str]:
        """
        Create a new student account.
        Validates required fields and username uniqueness.
        """
        clean_name = name.strip() if name else ""
        clean_user = username.strip().lower() if username else ""
        clean_pw = password.strip() if password else ""

        if not clean_name:
            return False, None, "Student name is required."
        if not clean_user:
            return False, None, "Username is required."
        if not clean_pw or len(clean_pw) < 4:
            return False, None, "Password must be at least 4 characters long."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            # Check for duplicate username
            cursor.execute("SELECT id FROM users WHERE username = ?;", (clean_user,))
            if cursor.fetchone():
                return False, None, f"Username '{clean_user}' is already taken."

            pw_hash = hash_password(clean_pw)
            cursor.execute("""
                INSERT INTO users (name, username, password_hash, role, email, semester, division)
                VALUES (?, ?, ?, 'Student', ?, ?, ?);
            """, (
                clean_name,
                clean_user,
                pw_hash,
                email.strip() if email else None,
                semester.strip() if semester else None,
                division.strip() if division else None
            ))
            conn.commit()
            return True, cursor.lastrowid, "Student account created successfully."
        except sqlite3.IntegrityError:
            return False, None, f"Username '{clean_user}' already exists."
        except sqlite3.Error as e:
            return False, None, f"Database error: {str(e)}"
        finally:
            conn.close()

    def update_student(
        self,
        student_id: int,
        name: str,
        email: Optional[str] = None,
        semester: Optional[str] = None,
        division: Optional[str] = None,
        new_password: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Update student account details and optionally change password."""
        clean_name = name.strip() if name else ""
        if not clean_name:
            return False, "Student name is required."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            if new_password and new_password.strip():
                clean_pw = new_password.strip()
                if len(clean_pw) < 4:
                    return False, "New password must be at least 4 characters long."
                pw_hash = hash_password(clean_pw)
                cursor.execute("""
                    UPDATE users
                    SET name = ?, email = ?, semester = ?, division = ?, password_hash = ?
                    WHERE id = ? AND role = 'Student';
                """, (
                    clean_name,
                    email.strip() if email else None,
                    semester.strip() if semester else None,
                    division.strip() if division else None,
                    pw_hash,
                    student_id
                ))
            else:
                cursor.execute("""
                    UPDATE users
                    SET name = ?, email = ?, semester = ?, division = ?
                    WHERE id = ? AND role = 'Student';
                """, (
                    clean_name,
                    email.strip() if email else None,
                    semester.strip() if semester else None,
                    division.strip() if division else None,
                    student_id
                ))
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Student not found."
            return True, "Student details updated successfully."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    def has_associated_tasks(self, student_id: int) -> int:
        """Return the count of academic tasks linked to this student."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE student_id = ?;", (student_id,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def delete_student(self, student_id: int) -> Tuple[bool, str]:
        """
        Delete a student account safely.
        Enforces Business Rule BR-07: A student with associated tasks cannot be deleted.
        """
        task_count = self.has_associated_tasks(student_id)
        if task_count > 0:
            return False, (
                f"Cannot delete student: This student has {task_count} associated academic task(s). "
                "Please delete or reassign their tasks before removing this account."
            )

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id = ? AND role = 'Student';", (student_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Student not found."
            return True, "Student account deleted successfully."
        except sqlite3.IntegrityError:
            return False, "Cannot delete student: Foreign key constraint violation."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()
