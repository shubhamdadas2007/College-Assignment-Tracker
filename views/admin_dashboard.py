"""
Administrator Dashboard view for College Tracker.
Provides college-wide metrics, submission review alerts, and subject workload breakdown (PRD Section 10).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import config
from models import User, Task
from task_service import TaskService
from student_service import StudentService
from deadline_service import format_display_date


class AdminDashboardView(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        user: User,
        task_service: TaskService,
        student_service: StudentService,
        on_navigate: Callable[[str], None],
        on_open_task_modal: Callable[[Optional[Task], Optional[str]], None],
        on_open_student_modal: Callable[[Optional[User]], None]
    ):
        super().__init__(parent, style="App.TFrame")
        self.user = user
        self.task_service = task_service
        self.student_service = student_service
        self.on_navigate = on_navigate
        self.on_open_task_modal = on_open_task_modal
        self.on_open_student_modal = on_open_student_modal

        self._create_widgets()
        self.refresh_data()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Header Frame
        header_frame = tk.Frame(self, bg=config.COLORS["bg_main"])
        header_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 15))

        welcome_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        welcome_box.pack(side="left")

        welcome_lbl = tk.Label(
            welcome_box,
            text=f"Administrator Portal  🏛️",
            font=config.FONTS["title"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_main"]
        )
        welcome_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            welcome_box,
            text=f"Logged in as {self.user.name} ({self.user.username})  •  Teacher Verification & Academic Oversight",
            font=config.FONTS["body"],
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_main"]
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        # Quick Actions on Right
        action_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        action_box.pack(side="right")

        review_btn = tk.Button(
            action_box,
            text="📤 Review Submissions",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["info"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            command=lambda: self.on_navigate("tasks")
        )
        review_btn.pack(side="left", padx=(0, 8))

        add_stud_btn = tk.Button(
            action_box,
            text="+ Add Student",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["primary"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            command=lambda: self.on_open_student_modal(None)
        )
        add_stud_btn.pack(side="left", padx=(0, 8))

        add_task_btn = tk.Button(
            action_box,
            text="+ Create Task",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["success"],
            fg="white",
            activebackground="#15803d",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            command=lambda: self.on_open_task_modal(None, "Assignment")
        )
        add_task_btn.pack(side="left", padx=(0, 8))

        refresh_btn = tk.Button(
            action_box,
            text="🔄 Refresh",
            font=config.FONTS["small_bold"],
            bg=config.COLORS["bg_card"],
            fg=config.COLORS["text_dark"],
            activebackground=config.COLORS["bg_hover"],
            relief="flat",
            highlightbackground=config.COLORS["border"],
            highlightthickness=1,
            cursor="hand2",
            padx=8,
            pady=6,
            command=self.refresh_data
        )
        refresh_btn.pack(side="left")

        # Macro KPI Cards Grid
        self.kpi_container = tk.Frame(self, bg=config.COLORS["bg_main"])
        self.kpi_container.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 20))
        for col in range(7):
            self.kpi_container.columnconfigure(col, weight=1)

        self.kpi_cards = {}
        cards_config = [
            ("total_students", "Total Students", "👥", config.COLORS["primary"], config.COLORS["primary_light"]),
            ("total_tasks", "Total Tasks", "📚", config.COLORS["pending"], config.COLORS["pending_bg"]),
            ("submitted", "Awaiting Review", "📤", config.COLORS["submitted"], config.COLORS["submitted_bg"]),
            ("needs_resubmission", "Needs Resubmit", "⚠️", config.COLORS["resubmission"], config.COLORS["resubmission_bg"]),
            ("completed", "Approved", "✅", config.COLORS["success"], config.COLORS["success_bg"]),
            ("overdue", "Overdue Submissions", "🚨", config.COLORS["danger"], config.COLORS["danger_bg"]),
            ("due_today", "Due Today", "⏰", config.COLORS["warning"], config.COLORS["warning_bg"]),
        ]

        for idx, (key, title, icon, color, bg_color) in enumerate(cards_config):
            card = tk.Frame(
                self.kpi_container,
                bg=config.COLORS["bg_card"],
                padx=10,
                pady=10,
                highlightbackground=config.COLORS["border"],
                highlightthickness=1
            )
            card.grid(row=0, column=idx, padx=3, sticky="nsew")

            top_row = tk.Frame(card, bg=config.COLORS["bg_card"])
            top_row.pack(fill="x")

            lbl_title = tk.Label(top_row, text=title, font=config.FONTS["small_bold"], fg=config.COLORS["text_muted"], bg=config.COLORS["bg_card"])
            lbl_title.pack(side="left")

            lbl_icon = tk.Label(top_row, text=icon, font=("Segoe UI", 11), bg=config.COLORS["bg_card"])
            lbl_icon.pack(side="right")

            val_label = tk.Label(card, text="0", font=("Segoe UI", 18, "bold"), fg=color, bg=config.COLORS["bg_card"])
            val_label.pack(anchor="w", pady=(4, 0))

            self.kpi_cards[key] = val_label

        # Content Split: Overdue Students on Left, Subject Workload on Right
        content_frame = tk.Frame(self, bg=config.COLORS["bg_main"])
        content_frame.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 20))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Left Column: Students with Overdue Submissions
        overdue_card = tk.Frame(
            content_frame,
            bg=config.COLORS["bg_card"],
            padx=18,
            pady=16,
            highlightbackground=config.COLORS["border"],
            highlightthickness=1
        )
        overdue_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        overdue_card.columnconfigure(0, weight=1)
        overdue_card.rowconfigure(1, weight=1)

        ov_header = tk.Frame(overdue_card, bg=config.COLORS["bg_card"])
        ov_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        tk.Label(
            ov_header,
            text="🚨 STUDENTS WITH OVERDUE TASKS",
            font=config.FONTS["h2"],
            fg=config.COLORS["danger"],
            bg=config.COLORS["bg_card"]
        ).pack(side="left")

        manage_stud_btn = tk.Button(
            ov_header,
            text="Manage Students →",
            font=config.FONTS["small_bold"],
            fg=config.COLORS["primary"],
            bg=config.COLORS["bg_card"],
            relief="flat",
            cursor="hand2",
            command=lambda: self.on_navigate("students")
        )
        manage_stud_btn.pack(side="right")

        # Overdue Students Treeview
        ov_frame = ttk.Frame(overdue_card)
        ov_frame.grid(row=1, column=0, sticky="nsew")

        columns_ov = ("name", "username", "semester", "division", "overdue_count")
        self.ov_tree = ttk.Treeview(ov_frame, columns=columns_ov, show="headings", height=8, selectmode="browse")
        self.ov_tree.heading("name", text="Student Name")
        self.ov_tree.heading("username", text="Username")
        self.ov_tree.heading("semester", text="Semester")
        self.ov_tree.heading("division", text="Div")
        self.ov_tree.heading("overdue_count", text="Overdue Tasks")

        self.ov_tree.column("name", width=140, anchor="w")
        self.ov_tree.column("username", width=90, anchor="w")
        self.ov_tree.column("semester", width=80, anchor="center")
        self.ov_tree.column("division", width=50, anchor="center")
        self.ov_tree.column("overdue_count", width=90, anchor="center")

        ov_scroll = ttk.Scrollbar(ov_frame, orient="vertical", command=self.ov_tree.yview)
        self.ov_tree.configure(yscrollcommand=ov_scroll.set)

        self.ov_tree.pack(side="left", fill="both", expand=True)
        ov_scroll.pack(side="right", fill="y")

        self.ov_tree.tag_configure("alert", background=config.COLORS["danger_bg"], foreground=config.COLORS["danger"])
        self.ov_tree.tag_configure("evenrow", background=config.COLORS["bg_card"])
        self.ov_tree.tag_configure("oddrow", background=config.COLORS["bg_hover"])

        # Right Column: Subject Workload Overview
        workload_card = tk.Frame(
            content_frame,
            bg=config.COLORS["bg_card"],
            padx=18,
            pady=16,
            highlightbackground=config.COLORS["border"],
            highlightthickness=1
        )
        workload_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        workload_card.columnconfigure(0, weight=1)
        workload_card.rowconfigure(1, weight=1)

        wl_header = tk.Frame(workload_card, bg=config.COLORS["bg_card"])
        wl_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        tk.Label(
            wl_header,
            text="📚 SUBJECT WORKLOAD & PROGRESS",
            font=config.FONTS["h2"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"]
        ).pack(side="left")

        view_analytics_btn = tk.Button(
            wl_header,
            text="View Analytics →",
            font=config.FONTS["small_bold"],
            fg=config.COLORS["primary"],
            bg=config.COLORS["bg_card"],
            relief="flat",
            cursor="hand2",
            command=lambda: self.on_navigate("analytics")
        )
        view_analytics_btn.pack(side="right")

        # Subject Workload Treeview
        wl_frame = ttk.Frame(workload_card)
        wl_frame.grid(row=1, column=0, sticky="nsew")

        columns_wl = ("subject", "total", "completed", "submitted", "pending", "rate")
        self.wl_tree = ttk.Treeview(wl_frame, columns=columns_wl, show="headings", height=8, selectmode="browse")
        self.wl_tree.heading("subject", text="Subject Name")
        self.wl_tree.heading("total", text="Total")
        self.wl_tree.heading("completed", text="Approved")
        self.wl_tree.heading("submitted", text="Submitted")
        self.wl_tree.heading("pending", text="Pending")
        self.wl_tree.heading("rate", text="Done %")

        self.wl_tree.column("subject", width=150, anchor="w")
        self.wl_tree.column("total", width=55, anchor="center")
        self.wl_tree.column("completed", width=65, anchor="center")
        self.wl_tree.column("submitted", width=65, anchor="center")
        self.wl_tree.column("pending", width=60, anchor="center")
        self.wl_tree.column("rate", width=65, anchor="center")

        wl_scroll = ttk.Scrollbar(wl_frame, orient="vertical", command=self.wl_tree.yview)
        self.wl_tree.configure(yscrollcommand=wl_scroll.set)

        self.wl_tree.pack(side="left", fill="both", expand=True)
        wl_scroll.pack(side="right", fill="y")

        self.wl_tree.tag_configure("evenrow", background=config.COLORS["bg_card"])
        self.wl_tree.tag_configure("oddrow", background=config.COLORS["bg_hover"])

    def refresh_data(self) -> None:
        """Fetch fresh metrics from SQLite for Admin Dashboard."""
        # 1. Update KPI numbers
        metrics = self.task_service.get_dashboard_metrics()
        students = self.student_service.get_all_students()

        self.kpi_cards["total_students"].config(text=str(len(students)))
        self.kpi_cards["total_tasks"].config(text=str(metrics.get("total", 0)))
        self.kpi_cards["submitted"].config(text=str(metrics.get("submitted", 0)))
        self.kpi_cards["needs_resubmission"].config(text=str(metrics.get("needs_resubmission", 0)))
        self.kpi_cards["completed"].config(text=str(metrics.get("completed", 0)))
        self.kpi_cards["overdue"].config(text=str(metrics.get("overdue", 0)))
        self.kpi_cards["due_today"].config(text=str(metrics.get("due_today", 0)))

        # 2. Update Overdue Students
        for item in self.ov_tree.get_children():
            self.ov_tree.delete(item)

        overdue_students = self.task_service.get_overdue_students()
        if not overdue_students:
            self.ov_tree.insert("", "end", values=("No overdue submissions! ✨", "-", "-", "-", "0"))
        else:
            for idx, s in enumerate(overdue_students):
                tag = "alert" if s["overdue_count"] >= 2 else ("evenrow" if idx % 2 == 0 else "oddrow")
                self.ov_tree.insert(
                    "",
                    "end",
                    values=(
                        s["name"],
                        s["username"],
                        s["semester"] or "-",
                        s["division"] or "-",
                        f"🚨 {s['overdue_count']} overdue"
                    ),
                    tags=(tag,)
                )

        # 3. Update Subject Workload
        for item in self.wl_tree.get_children():
            self.wl_tree.delete(item)

        workloads = self.task_service.get_subject_workload()
        if not workloads:
            self.wl_tree.insert("", "end", values=("No subjects found.", "0", "0", "0", "0", "0%"))
        else:
            for idx, w in enumerate(workloads):
                tag = "evenrow" if idx % 2 == 0 else "oddrow"
                self.wl_tree.insert(
                    "",
                    "end",
                    values=(
                        w["subject_name"],
                        str(w["total_tasks"]),
                        str(w["completed_tasks"]),
                        str(w["submitted_tasks"]),
                        str(w["pending_tasks"]),
                        f"{w['completion_rate']}%"
                    ),
                    tags=(tag,)
                )
