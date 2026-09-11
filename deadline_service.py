"""
Deadline calculation and date-processing service for College Tracker.
Implements dynamic deadline state evaluation (PRD Section 24 & BR-04) supporting the role-based workflow.
"""
from datetime import datetime, date
from typing import Optional, Union, Dict, Any


def get_current_date() -> date:
    """Return the current local date."""
    return datetime.now().date()


def parse_date(date_val: Union[str, date, None]) -> Optional[date]:
    """Parse string (YYYY-MM-DD) or return date object."""
    if not date_val:
        return None
    if isinstance(date_val, date):
        return date_val
    try:
        return datetime.strptime(date_val.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def calculate_deadline_state(status: str, due_date_val: Union[str, date, None], current_date: Optional[date] = None) -> str:
    """
    Calculate dynamic deadline state for a task.
    
    Logic:
    IF status == 'Completed' -> 'Completed'
    ELSE IF status == 'Submitted' -> 'Submitted'
    ELSE IF due_date < today -> 'Overdue'
    ELSE IF due_date == today -> 'Due Today'
    ELSE -> 'Upcoming'
    """
    if status == "Completed":
        return "Completed"
    if status == "Submitted":
        return "Submitted"
    
    parsed_due = parse_date(due_date_val)
    if not parsed_due:
        return "Upcoming"
    
    today = current_date or get_current_date()
    
    if parsed_due < today:
        return "Overdue"
    elif parsed_due == today:
        return "Due Today"
    else:
        return "Upcoming"


def format_display_date(date_val: Union[str, date, None]) -> str:
    """Format YYYY-MM-DD as 'DD Mon YYYY' for human readable display."""
    d = parse_date(date_val)
    if not d:
        return "-"
    return d.strftime("%d %b %Y")


def get_days_remaining(due_date_val: Union[str, date, None], current_date: Optional[date] = None) -> Optional[int]:
    """Return integer days remaining until due date (negative if overdue)."""
    parsed_due = parse_date(due_date_val)
    if not parsed_due:
        return None
    today = current_date or get_current_date()
    return (parsed_due - today).days
