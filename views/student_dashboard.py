"""
Student Dashboard view for College Tracker.
Displays personal metrics, role-based KPI cards, and upcoming deadline list (PRD Section 9).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import config
from models import User, Task
from task_service import TaskService
from deadline_service import format_display_date, get_days_remaining


class StudentDashboardView(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        user: User,
        task_service: TaskService,
        on_navigate: Callable[[str], None],
        on_open_task_modal: Callable[[Optional[Task], Optional[str]], None]
    ):
        super().__init__(parent, style="App.TFrame")
        self.user = user
        self.task_service = task_service
        self.on_navigate = on_navigate
        self.on_open_task_modal = on_open_task_modal

        self._create_widgets()
        self.refresh_data()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Top Welcome & Action Header
        header_frame = tk.Frame(self, bg=config.COLORS["bg_main"])
        header_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 15))

        welcome_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        welcome_box.pack(side="left")

        welcome_lbl = tk.Label(
            welcome_box,
            text=f"Welcome back, {self.user.name}! 👋",
            font=config.FONTS["title"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_main"]
        )
        welcome_lbl.pack(anchor="w")

        meta_text = f"Student Dashboard  •  {self.user.semester or 'Semester 4'}  •  Division {self.user.division or 'A'}"
        sub_lbl = tk.Label(
            welcome_box,
            text=meta_text,
            font=config.FONTS["body"],
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_main"]
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        # Action Buttons on Right
        action_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        action_box.pack(side="right")

        add_task_btn = tk.Button(
            action_box,
            text="+ Add New Task",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["primary"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=lambda: self.on_open_task_modal(None, "Assignment")
        )
        add_task_btn.pack(side="left", padx=(0, 10))

        add_prac_btn = tk.Button(
            action_box,
            text="+ Add Practical",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["info"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=lambda: self.on_open_task_modal(None, "Practical")
        )
        add_prac_btn.pack(side="left", padx=(0, 10))

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

        # KPI Summary Cards Grid
        self.kpi_container = tk.Frame(self, bg=config.COLORS["bg_main"])
        self.kpi_container.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 20))
        for col in range(7):
            self.kpi_container.columnconfigure(col, weight=1)

        self.kpi_cards = {}
        cards_config = [
            ("total", "Total Tasks", "📚", config.COLORS["primary"], config.COLORS["primary_light"]),
            ("pending", "Pending", "⏳", config.COLORS["pending"], config.COLORS["pending_bg"]),
            ("in_progress", "In Progress", "⚙️", config.COLORS["info"], config.COLORS["info_bg"]),
            ("submitted", "Submitted", "📤", config.COLORS["submitted"], config.COLORS["submitted_bg"]),
            ("needs_resubmission", "Resubmit Needed", "⚠️", config.COLORS["resubmission"], config.COLORS["resubmission_bg"]),
            ("completed", "Approved", "✅", config.COLORS["success"], config.COLORS["success_bg"]),
            ("overdue", "Overdue", "🚨", config.COLORS["danger"], config.COLORS["danger_bg"]),
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

        # Content Section (Upcoming Deadlines & Quick Navigation)
        content_frame = tk.Frame(self, bg=config.COLORS["bg_main"])
        content_frame.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 20))
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Left Column: Upcoming Deadlines Card
        deadlines_card = tk.Frame(
            content_frame,
            bg=config.COLORS["bg_card"],
            padx=18,
            pady=16,
            highlightbackground=config.COLORS["border"],
            highlightthickness=1
        )
        deadlines_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        deadlines_card.columnconfigure(0, weight=1)
        deadlines_card.rowconfigure(1, weight=1)

        dl_header = tk.Frame(deadlines_card, bg=config.COLORS["bg_card"])
        dl_header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        tk.Label(
            dl_header,
            text="⏰ ACTIVE ACADEMIC DEADLINES",
            font=config.FONTS["h2"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"]
        ).pack(side="left")

        view_all_btn = tk.Button(
            dl_header,
            text="View All Tasks →",
            font=config.FONTS["small_bold"],
            fg=config.COLORS["primary"],
            bg=config.COLORS["bg_card"],
            activeforeground=config.COLORS["primary_hover"],
            relief="flat",
            cursor="hand2",
            command=lambda: self.on_navigate("tasks")
        )
        view_all_btn.pack(side="right")

        # Upcoming Deadlines Table / List
        self.deadlines_scroll = ttk.Frame(deadlines_card)
        self.deadlines_scroll.grid(row=1, column=0, sticky="nsew")

        # Create Treeview for deadlines
        columns = ("title", "subject", "type", "due_date", "priority", "status", "actions")
        self.dl_tree = ttk.Treeview(self.deadlines_scroll, columns=columns, show="headings", height=8, selectmode="browse")
        
        self.dl_tree.heading("title", text="Task Title")
        self.dl_tree.heading("subject", text="Subject")
        self.dl_tree.heading("type", text="Type")
        self.dl_tree.heading("due_date", text="Due Date / Urgency")
        self.dl_tree.heading("priority", text="Priority")
        self.dl_tree.heading("status", text="Workflow Status")
        self.dl_tree.heading("actions", text="Action")

        self.dl_tree.column("title", width=180, anchor="w")
        self.dl_tree.column("subject", width=130, anchor="w")
        self.dl_tree.column("type", width=85, anchor="center")
        self.dl_tree.column("due_date", width=130, anchor="center")
        self.dl_tree.column("priority", width=80, anchor="center")
        self.dl_tree.column("status", width=140, anchor="center")
        self.dl_tree.column("actions", width=110, anchor="center")

        tree_scroll = ttk.Scrollbar(self.deadlines_scroll, orient="vertical", command=self.dl_tree.yview)
        self.dl_tree.configure(yscrollcommand=tree_scroll.set)

        self.dl_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # Treeview tag styling
        self.dl_tree.tag_configure("high", foreground=config.COLORS["danger"])
        self.dl_tree.tag_configure("overdue", background=config.COLORS["danger_bg"])
        self.dl_tree.tag_configure("due_today", background=config.COLORS["warning_bg"])
        self.dl_tree.tag_configure("submitted", background=config.COLORS["submitted_bg"])
        self.dl_tree.tag_configure("resubmission", background=config.COLORS["resubmission_bg"])
        self.dl_tree.tag_configure("evenrow", background=config.COLORS["bg_card"])
        self.dl_tree.tag_configure("oddrow", background=config.COLORS["bg_hover"])

        self.dl_tree.bind("<Double-1>", self._on_double_click_task)

        # Right Column: Quick Links & Summary Card
        quick_card = tk.Frame(
            content_frame,
            bg=config.COLORS["bg_card"],
            padx=18,
            pady=16,
            highlightbackground=config.COLORS["border"],
            highlightthickness=1
        )
        quick_card.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            quick_card,
            text="🚀 QUICK SHORTCUTS",
            font=config.FONTS["h2"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"]
        ).pack(anchor="w", pady=(0, 15))

        shortcuts = [
            ("🔬 Filter Practicals", "practicals", config.COLORS["info_bg"], config.COLORS["info"]),
            ("📊 View My Analytics", "analytics", config.COLORS["primary_light"], config.COLORS["primary"]),
            ("📖 Browse Subjects", "subjects", config.COLORS["warning_bg"], config.COLORS["warning"]),
            ("⚙️ Account Settings", "settings", config.COLORS["bg_hover"], config.COLORS["text_dark"]),
        ]

        for text, route, bg_c, fg_c in shortcuts:
            btn = tk.Button(
                quick_card,
                text=text,
                font=config.FONTS["body_bold"],
                bg=bg_c,
                fg=fg_c,
                activebackground=config.COLORS["border"],
                relief="flat",
                cursor="hand2",
                anchor="w",
                padx=12,
                pady=10,
                command=lambda r=route: self.on_navigate(r)
            )
            btn.pack(fill="x", pady=(0, 8))

        # Academic Workflow Tip Box
        tip_box = tk.Frame(quick_card, bg=config.COLORS["bg_hover"], padx=10, pady=10)
        tip_box.pack(fill="x", pady=(15, 0), side="bottom")

        tk.Label(
            tip_box,
            text="💡 Verification Workflow:",
            font=config.FONTS["small_bold"],
            fg=config.COLORS["primary"],
            bg=config.COLORS["bg_hover"]
        ).pack(anchor="w")

        tk.Label(
            tip_box,
            text="Submit your assignments and practicals for verification. Once approved by your teacher/admin, tasks are marked Completed.",
            font=config.FONTS["small"],
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_hover"],
            wraplength=180,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

    def refresh_data(self) -> None:
        """Fetch fresh metrics from SQLite and reload widgets."""
        metrics = self.task_service.get_dashboard_metrics(student_id=self.user.id)
        for key, label in self.kpi_cards.items():
            label.config(text=str(metrics.get(key, 0)))

        # Refresh Upcoming Deadlines Table
        for item in self.dl_tree.get_children():
            self.dl_tree.delete(item)

        upcoming_tasks = self.task_service.get_upcoming_deadlines(student_id=self.user.id, limit=8)

        if not upcoming_tasks:
            self.dl_tree.insert("", "end", values=("No active tasks found! 🎉", "-", "-", "-", "-", "-", "-"))
            return

        for idx, task in enumerate(upcoming_tasks):
            tag_list = ["evenrow" if idx % 2 == 0 else "oddrow"]

            if task.status == "Submitted":
                tag_list.append("submitted")
                state_badge = f"📤 {format_display_date(task.due_date)}"
                status_icon = "📤 Awaiting Review"
            elif task.status == "Needs Resubmission":
                tag_list.append("resubmission")
                status_icon = "⚠️ Resubmit Needed"
                if task.deadline_state == "Overdue":
                    state_badge = f"🚨 {format_display_date(task.due_date)} (Overdue)"
                    tag_list.append("overdue")
                elif task.deadline_state == "Due Today":
                    state_badge = f"⏰ {format_display_date(task.due_date)} (Today)"
                    tag_list.append("due_today")
                else:
                    days = get_days_remaining(task.due_date)
                    days_str = f"in {days}d" if days is not None and days >= 0 else ""
                    state_badge = f"{format_display_date(task.due_date)} ({days_str})"
            else:
                if task.deadline_state == "Overdue":
                    tag_list.append("overdue")
                    state_badge = f"🚨 {format_display_date(task.due_date)} (Overdue)"
                elif task.deadline_state == "Due Today":
                    tag_list.append("due_today")
                    state_badge = f"⏰ {format_display_date(task.due_date)} (Today)"
                else:
                    days = get_days_remaining(task.due_date)
                    days_str = f"in {days}d" if days is not None and days >= 0 else ""
                    state_badge = f"{format_display_date(task.due_date)} ({days_str})"

                status_icon = "⚙️ In Progress" if task.status == "In Progress" else "⏳ Pending"

            priority_icon = "🔴 High" if task.priority == "High" else ("🟡 Medium" if task.priority == "Medium" else "🟢 Low")

            self.dl_tree.insert(
                "",
                "end",
                iid=str(task.id),
                values=(
                    task.title,
                    task.subject_name or "-",
                    task.task_type,
                    state_badge,
                    priority_icon,
                    status_icon,
                    "Double click to view"
                ),
                tags=tuple(tag_list)
            )

    def _on_double_click_task(self, event) -> None:
        selected_items = self.dl_tree.selection()
        if not selected_items:
            return
        task_id_str = selected_items[0]
        try:
            task_id = int(task_id_str)
            task = self.task_service.get_task_by_id(task_id)
            if task:
                self.on_open_task_modal(task, None)
        except ValueError:
            pass
