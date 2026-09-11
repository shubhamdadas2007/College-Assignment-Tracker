"""
Main entry point for College Assignment & Practical Submission Tracker (v4.0).
Initializes Tkinter application, theme styles, SQLite database, and view switching.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import config
from database import init_db
from models import User
from auth_service import AuthService
from task_service import TaskService
from subject_service import SubjectService
from student_service import StudentService
from views.login import LoginView
from views.main_window import MainWindow


class CollegeTrackerApp(tk.Tk):
    """Root Application Window & Controller."""
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title(f"{config.APP_TITLE} (v{config.APP_VERSION})")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(bg=config.COLORS["bg_main"])

        # Center window on screen
        self._center_window(1180, 760)

        # Initialize SQLite Database with Seed Data
        init_db(config.DB_FILE, seed_demo=True)

        # Initialize Services
        self.auth_service = AuthService(config.DB_FILE)
        self.task_service = TaskService(config.DB_FILE)
        self.subject_service = SubjectService(config.DB_FILE)
        self.student_service = StudentService(config.DB_FILE)

        # Active View Reference
        self.current_view: tk.Widget = None

        # Setup ttk styles
        self._setup_styles()

        # Launch into Login View
        self.show_login_view()

    def _center_window(self, width: int, height: int) -> None:
        """Center the application window on primary display."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_styles(self) -> None:
        """Configure modern ttk styles across widgets."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Frame styles
        style.configure("App.TFrame", background=config.COLORS["bg_main"])

        # Entry Style
        style.configure(
            "TEntry",
            fieldbackground=config.COLORS["bg_card"],
            foreground=config.COLORS["text_dark"],
            padding=6,
            bordercolor=config.COLORS["border"],
            lightcolor=config.COLORS["border"],
            darkcolor=config.COLORS["border"]
        )

        # Combobox Style
        style.configure(
            "TCombobox",
            fieldbackground=config.COLORS["bg_card"],
            background=config.COLORS["bg_card"],
            foreground=config.COLORS["text_dark"],
            padding=5,
            bordercolor=config.COLORS["border"]
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", config.COLORS["bg_card"])],
            selectbackground=[("readonly", config.COLORS["primary_light"])],
            selectforeground=[("readonly", config.COLORS["primary"])]
        )

        # Treeview Style
        style.configure(
            "Treeview",
            background=config.COLORS["bg_card"],
            foreground=config.COLORS["text_dark"],
            rowheight=32,
            font=config.FONTS["body"],
            fieldbackground=config.COLORS["bg_card"],
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background=config.COLORS["bg_hover"],
            foreground=config.COLORS["text_dark"],
            font=config.FONTS["small_bold"],
            padding=(6, 8),
            borderwidth=1,
            relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", config.COLORS["primary_light"])],
            foreground=[("selected", config.COLORS["primary"])]
        )

        # Scrollbar Style
        style.configure(
            "Vertical.TScrollbar",
            background=config.COLORS["bg_hover"],
            bordercolor=config.COLORS["bg_main"],
            arrowcolor=config.COLORS["text_muted"],
            troughcolor=config.COLORS["bg_main"]
        )

    def show_login_view(self) -> None:
        """Render the login screen."""
        if self.current_view:
            self.current_view.destroy()

        self.current_view = LoginView(
            parent=self,
            auth_service=self.auth_service,
            on_login_success=self.on_login_success
        )
        self.current_view.pack(fill="both", expand=True)

    def on_login_success(self, user: User) -> None:
        """Transition from Login to the main role-specific dashboard layout."""
        if self.current_view:
            self.current_view.destroy()

        self.current_view = MainWindow(
            parent=self,
            user=user,
            auth_service=self.auth_service,
            task_service=self.task_service,
            subject_service=self.subject_service,
            student_service=self.student_service,
            on_logout=self.show_login_view
        )
        self.current_view.pack(fill="both", expand=True)


def main():
    app = CollegeTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
