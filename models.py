"""
Data models and domain entities for College Assignment & Practical Submission Tracker.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    name: str
    username: str
    password_hash: str
    role: str  # 'Student' or 'Administrator'
    email: Optional[str] = None
    semester: Optional[str] = None
    division: Optional[str] = None
    created_at: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        return self.role == "Administrator"

    @property
    def is_student(self) -> bool:
        return self.role == "Student"


@dataclass
class Subject:
    id: Optional[int]
    name: str
    semester: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Task:
    id: Optional[int]
    student_id: int
    subject_id: int
    title: str
    task_type: str  # Assignment, Practical, Journal, Project, Presentation, Other
    due_date: str   # YYYY-MM-DD
    priority: str   # Low, Medium, High
    status: str     # Pending, In Progress, Completed
    description: Optional[str] = None
    assigned_date: Optional[str] = None  # YYYY-MM-DD
    submission_mode: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Joined fields for presentation
    student_name: Optional[str] = None
    student_username: Optional[str] = None
    subject_name: Optional[str] = None
    deadline_state: Optional[str] = None  # Dynamically calculated: Overdue, Due Today, Upcoming, Completed
