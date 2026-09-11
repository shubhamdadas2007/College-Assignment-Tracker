"""
Main Window container layout for College Tracker.
Provides role-based sidebar navigation and view orchestration (PRD Section 6, 8, 36).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict
import config
from models import User, Task
from auth_service import AuthService
from task_service import TaskService
from subject_service import SubjectService
from student_service import StudentService
from views.student_dashboard import StudentDashboardView
from views.admin_dashboard import AdminDashboardView
from views.tasks import TasksView, TaskModalDialog
from views.subjects import SubjectsView
from views.students import StudentsView, StudentModalDialog
from views.analytics import AnalyticsView
from views.settings import SettingsView


class MainWindow(ttk.Frame):
    """Main application frame with role-tailored sidebar and active content container."""
    def __init__(
        self,
        parent: tk.Widget,
        user: User,
        auth_service: AuthService,
        task_service: TaskService,
        subject_service: SubjectService,
        student_service: StudentService,
        on_logout: Callable[[], None]
    ):
        super().__init__(parent, style="App.TFrame")
        self.user = user
        self.auth_service = auth_service
        self.task_service = task_service
        self.subject_service = subject_service
        self.student_service = student_service
        self.on_logout = on_logout

        self.current_route = "dashboard"
        self.nav_buttons: Dict[str, tk.Button] = {}
        self.current_view_widget: Optional[tk.Widget] = None

        self._create_layout()
        self.navigate_to("dashboard")

    def _create_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # 1. Left Sidebar Frame (Dark Slate)
        self.sidebar = tk.Frame(self, bg=config.COLORS["bg_dark"], width=230)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)

        # App Brand Header in Sidebar
        brand_frame = tk.Frame(self.sidebar, bg=config.COLORS["bg_dark"], padx=18, pady=20)
        brand_frame.pack(fill="x")

        tk.Label(
            brand_frame,
            text="🎓 COLLEGE TRACKER",
            font=("Segoe UI", 12, "bold"),
            fg=config.COLORS["text_light"],
            bg=config.COLORS["bg_dark"]
        ).pack(anchor="w")

        role_badge_text = f"● {self.user.role.upper()} PORTAL"
        role_color = config.COLORS["primary_light"] if self.user.is_student else config.COLORS["warning"]
        tk.Label(
            brand_frame,
            text=role_badge_text,
            font=("Segoe UI", 8, "bold"),
            fg=role_color,
            bg=config.COLORS["bg_dark"]
        ).pack(anchor="w", pady=(4, 0))

        # Divider line
        tk.Frame(self.sidebar, bg=config.COLORS["bg_dark_active"], height=1).pack(fill="x", padx=15, pady=(5, 15))

        # Navigation Items based on Role (PRD Section 6)
        nav_items_frame = tk.Frame(self.sidebar, bg=config.COLORS["bg_dark"])
        nav_items_frame.pack(fill="both", expand=True, padx=10)

        if self.user.is_student:
            routes = [
                ("dashboard", "📊  Dashboard"),
                ("tasks", "📚  Tasks"),
                ("practicals", "🔬  Practicals"),
                ("subjects", "📖  Subjects"),
                ("analytics", "📈  Analytics"),
                ("settings", "⚙️  Settings"),
            ]
        else:
            routes = [
                ("dashboard", "🏛️  Dashboard"),
                ("students", "👥  Students"),
                ("tasks", "📚  Tasks"),
                ("subjects", "📖  Subjects"),
                ("analytics", "📈  Analytics"),
                ("settings", "⚙️  Settings"),
            ]

        for route_id, label in routes:
            btn = tk.Button(
                nav_items_frame,
                text=label,
                font=config.FONTS["body_bold"],
                bg=config.COLORS["bg_dark"],
                fg=config.COLORS["text_muted"],
                activebackground=config.COLORS["bg_dark_hover"],
                activeforeground=config.COLORS["text_light"],
                relief="flat",
                cursor="hand2",
                anchor="w",
                padx=16,
                pady=10,
                command=lambda r=route_id: self.navigate_to(r)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[route_id] = btn

        # User Info & Logout at Sidebar Bottom
        tk.Frame(self.sidebar, bg=config.COLORS["bg_dark_active"], height=1).pack(fill="x", padx=15, pady=(15, 10))

        user_bottom = tk.Frame(self.sidebar, bg=config.COLORS["bg_dark"], padx=15, pady=12)
        user_bottom.pack(fill="x", side="bottom")

        tk.Label(
            user_bottom,
            text=self.user.name,
            font=config.FONTS["small_bold"],
            fg=config.COLORS["text_light"],
            bg=config.COLORS["bg_dark"],
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            user_bottom,
            text=f"@{self.user.username}",
            font=config.FONTS["small"],
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_dark"],
            anchor="w"
        ).pack(fill="x", pady=(1, 8))

        logout_btn = tk.Button(
            user_bottom,
            text="🚪  Logout",
            font=config.FONTS["small_bold"],
            bg=config.COLORS["danger_bg"],
            fg=config.COLORS["danger"],
            activebackground=config.COLORS["danger"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            command=self._handle_logout
        )
        logout_btn.pack(fill="x")

        # 2. Right Content Area Frame
        self.content_area = tk.Frame(self, bg=config.COLORS["bg_main"])
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.columnconfigure(0, weight=1)
        self.content_area.rowconfigure(0, weight=1)

    def navigate_to(self, route_id: str) -> None:
        """Switch active view and highlight sidebar button."""
        self.current_route = route_id

        # Update button highlights
        for r_id, btn in self.nav_buttons.items():
            if r_id == route_id:
                btn.configure(
                    bg=config.COLORS["bg_dark_active"],
                    fg=config.COLORS["text_light"]
                )
            else:
                btn.configure(
                    bg=config.COLORS["bg_dark"],
                    fg=config.COLORS["text_muted"]
                )

        # Destroy existing view widget
        if self.current_view_widget:
            self.current_view_widget.destroy()
            self.current_view_widget = None

        # Build new view
        if route_id == "dashboard":
            if self.user.is_student:
                self.current_view_widget = StudentDashboardView(
                    parent=self.content_area,
                    user=self.user,
                    task_service=self.task_service,
                    on_navigate=self.navigate_to,
                    on_open_task_modal=self._open_task_modal
                )
            else:
                self.current_view_widget = AdminDashboardView(
                    parent=self.content_area,
                    user=self.user,
                    task_service=self.task_service,
                    student_service=self.student_service,
                    on_navigate=self.navigate_to,
                    on_open_task_modal=self._open_task_modal,
                    on_open_student_modal=self._open_student_modal
                )
        elif route_id == "tasks":
            self.current_view_widget = TasksView(
                parent=self.content_area,
                user=self.user,
                task_service=self.task_service,
                subject_service=self.subject_service,
                student_service=self.student_service,
                is_practicals_view=False
            )
        elif route_id == "practicals":
            # Unified Task view filtered by task_type = 'Practical' (PRD Section 7 & 18)
            self.current_view_widget = TasksView(
                parent=self.content_area,
                user=self.user,
                task_service=self.task_service,
                subject_service=self.subject_service,
                student_service=self.student_service,
                is_practicals_view=True
            )
        elif route_id == "subjects":
            self.current_view_widget = SubjectsView(
                parent=self.content_area,
                user=self.user,
                subject_service=self.subject_service
            )
        elif route_id == "students":
            self.current_view_widget = StudentsView(
                parent=self.content_area,
                user=self.user,
                student_service=self.student_service
            )
        elif route_id == "analytics":
            self.current_view_widget = AnalyticsView(
                parent=self.content_area,
                user=self.user,
                task_service=self.task_service
            )
        elif route_id == "settings":
            self.current_view_widget = SettingsView(
                parent=self.content_area,
                user=self.user,
                auth_service=self.auth_service
            )

        if self.current_view_widget:
            self.current_view_widget.grid(row=0, column=0, sticky="nsew")

    def _open_task_modal(self, task: Optional[Task] = None, preset_type: Optional[str] = None) -> None:
        TaskModalDialog(
            parent=self.winfo_toplevel(),
            task_service=self.task_service,
            subject_service=self.subject_service,
            student_service=self.student_service,
            current_user=self.user,
            task=task,
            preset_type=preset_type,
            on_saved=self._refresh_current_view
        )

    def _open_student_modal(self, student: Optional[User] = None) -> None:
        StudentModalDialog(
            parent=self.winfo_toplevel(),
            student_service=self.student_service,
            student=student,
            on_saved=self._refresh_current_view
        )

    def _refresh_current_view(self) -> None:
        if self.current_view_widget and hasattr(self.current_view_widget, "refresh_data"):
            self.current_view_widget.refresh_data()

    def _handle_logout(self) -> None:
        confirm = messagebox.askyesno("Logout", "Are you sure you want to log out?", parent=self)
        if confirm:
            self.auth_service.logout()
            self.on_logout()
