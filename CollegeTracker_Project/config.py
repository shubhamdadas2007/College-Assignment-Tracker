"""
Configuration and UI constants for College Assignment & Practical Submission Tracker.
"""
import os

# Application Info
APP_TITLE = "College Assignment & Practical Submission Tracker"
APP_VERSION = "4.0"
APP_SUBTITLE = "Desktop Academic Tracker & Submission Manager"

# Database Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "college_tracker.db")

# Firebase Authentication Configuration (Cloud Auth + Offline Fallback)
# You can provide your Firebase Web API Key and Project ID here or in the UI Settings.
FIREBASE_CONFIG = {
    "enabled": False,  # Set to True when connected to an active Firebase project
    "api_key": os.getenv("FIREBASE_API_KEY", ""),
    "project_id": os.getenv("FIREBASE_PROJECT_ID", "college-tracker-auth"),
    "auth_domain": os.getenv("FIREBASE_AUTH_DOMAIN", "college-tracker-auth.firebaseapp.com"),
    "auth_endpoint": "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
    "signup_endpoint": "https://identitytoolkit.googleapis.com/v1/accounts:signUp",
}

# Color Palette (Modern Slate & Indigo Theme)
COLORS = {
    "primary": "#4f46e5",        # Indigo 600
    "primary_hover": "#4338ca",  # Indigo 700
    "primary_light": "#e0e7ff",  # Indigo 100
    "secondary": "#64748b",      # Slate 500
    "secondary_hover": "#475569",# Slate 600
    "bg_dark": "#0f172a",        # Slate 900 (Sidebar dark)
    "bg_dark_hover": "#1e293b",  # Slate 800
    "bg_dark_active": "#334155", # Slate 700
    "bg_main": "#f8fafc",        # Slate 50 (App background)
    "bg_card": "#ffffff",        # White (Cards & Panels)
    "bg_hover": "#f1f5f9",       # Slate 100
    "text_dark": "#0f172a",      # Slate 900
    "text_muted": "#64748b",     # Slate 500
    "text_light": "#f8fafc",     # Slate 50
    "border": "#e2e8f0",         # Slate 200
    "border_dark": "#cbd5e1",    # Slate 300
    
    # Semantic Status & Priority Colors
    "success": "#16a34a",        # Green 600 (Completed)
    "success_bg": "#dcfce7",     # Green 100
    "warning": "#d97706",        # Amber 600 (Due Today / Medium)
    "warning_bg": "#fef3c7",     # Amber 100
    "danger": "#dc2626",         # Red 600 (Overdue / High)
    "danger_bg": "#fee2e2",      # Red 100
    "info": "#0284c7",           # Sky 600 (Upcoming / In Progress)
    "info_bg": "#e0f2fe",        # Sky 100
    "pending": "#9333ea",        # Purple 600 (Pending)
    "pending_bg": "#f3e8ff",     # Purple 100
}

# Typography
FONTS = {
    "title": ("Segoe UI", 18, "bold"),
    "h1": ("Segoe UI", 15, "bold"),
    "h2": ("Segoe UI", 13, "bold"),
    "h3": ("Segoe UI", 11, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9),
    "small_bold": ("Segoe UI", 9, "bold"),
    "mono": ("Consolas", 10),
}

# Task Types
TASK_TYPES = [
    "Assignment",
    "Practical",
    "Journal",
    "Project",
    "Presentation",
    "Other",
]

# Task Statuses (Stored in DB)
TASK_STATUSES = [
    "Pending",
    "In Progress",
    "Completed",
]

# Task Priorities
TASK_PRIORITIES = [
    "Low",
    "Medium",
    "High",
]

# Submission Modes
SUBMISSION_MODES = [
    "Online (LMS / Portal)",
    "Hardcopy / Handwritten",
    "Lab Demonstration",
    "Presentation / Viva",
    "Email Submission",
    "Other",
]

# User Roles
ROLES = {
    "STUDENT": "Student",
    "ADMIN": "Administrator",
}
