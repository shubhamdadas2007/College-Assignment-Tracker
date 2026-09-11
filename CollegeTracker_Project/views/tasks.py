"""
Unified Task & Practicals management view for College Tracker.
Implements reusable CRUD, multi-filtering, search, sorting, and task modal dialog.
Fully complies with PRD Section 7, 18, and BR-03 (Zero-duplicate Practicals entity).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from typing import Callable, Optional, List, Dict, Any
import config
from models import User, Task, Subject
from task_service import TaskService
from subject_service import SubjectService
from student_service import StudentService
from deadline_service import format_display_date, get_days_remaining, parse_date


class TaskModalDialog(tk.Toplevel):
    """Modal dialog for creating and editing academic tasks & practicals."""
    def __init__(
        self,
        parent: tk.Widget,
        task_service: TaskService,
        subject_service: SubjectService,
        student_service: StudentService,
        current_user: User,
        task: Optional[Task] = None,
        preset_type: Optional[str] = None,
        on_saved: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.task_service = task_service
        self.subject_service = subject_service
        self.student_service = student_service
        self.current_user = current_user
        self.task = task
        self.preset_type = preset_type
        self.on_saved = on_saved

        self.title("Edit Task" if task else ("New Practical" if preset_type == "Practical" else "New Academic Task"))
        self.geometry("640x720")
        self.minsize(580, 600)
        self.configure(bg=config.COLORS["bg_main"])
        self.transient(parent)
        self.grab_set()

        self._load_dependencies()
        self._create_form()
        self._populate_fields()

    def _load_dependencies(self) -> None:
        self.subjects = self.subject_service.get_all_subjects()
        self.subject_map = {s.name: s.id for s in self.subjects}

        if self.current_user.is_admin:
            self.students = self.student_service.get_all_students()
            self.student_map = {f"{st.name} ({st.username})": st.id for st in self.students}
        else:
            self.students = []
            self.student_map = {self.current_user.name: self.current_user.id}

    def _create_form(self) -> None:
        main_frame = tk.Frame(self, bg=config.COLORS["bg_card"], padx=25, pady=20)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        modal_title = "Edit Task" if self.task else ("Create New Practical" if self.preset_type == "Practical" else "Create Academic Task")
        tk.Label(
            main_frame,
            text=modal_title,
            font=config.FONTS["h1"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"]
        ).pack(anchor="w", pady=(0, 15))

        # Error Banner (Hidden by default)
        self.error_var = tk.StringVar()
        self.error_label = tk.Label(
            main_frame,
            textvariable=self.error_var,
            font=config.FONTS["small_bold"],
            fg=config.COLORS["danger"],
            bg=config.COLORS["danger_bg"],
            padx=10,
            pady=6,
            wraplength=520
        )

        # Form Scrollable Canvas Container
        form_frame = tk.Frame(main_frame, bg=config.COLORS["bg_card"])
        form_frame.pack(fill="both", expand=True)

        # Row 1: Title (Full width)
        tk.Label(form_frame, text="Task Title *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(4, 2))
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(form_frame, textvariable=self.title_var, font=config.FONTS["body"])
        self.title_entry.pack(fill="x", pady=(0, 10))

        # Row 2: Grid for Student & Subject
        grid_row1 = tk.Frame(form_frame, bg=config.COLORS["bg_card"])
        grid_row1.pack(fill="x", pady=(0, 10))
        grid_row1.columnconfigure(0, weight=1)
        grid_row1.columnconfigure(1, weight=1)

        # Student Field
        tk.Label(grid_row1, text="Assigned Student *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=0, sticky="w")
        self.student_var = tk.StringVar()
        if self.current_user.is_admin:
            student_names = list(self.student_map.keys())
            self.student_combo = ttk.Combobox(grid_row1, textvariable=self.student_var, values=student_names, state="readonly", font=config.FONTS["body"])
            self.student_combo.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        else:
            self.student_var.set(f"{self.current_user.name} ({self.current_user.username})")
            lbl = tk.Label(grid_row1, text=f"{self.current_user.name}", font=config.FONTS["body_bold"], bg=config.COLORS["bg_hover"], fg=config.COLORS["text_dark"], padx=8, pady=5, anchor="w")
            lbl.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        # Subject Field
        tk.Label(grid_row1, text="Subject *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=1, sticky="w")
        self.subject_var = tk.StringVar()
        subject_names = list(self.subject_map.keys())
        self.subject_combo = ttk.Combobox(grid_row1, textvariable=self.subject_var, values=subject_names, state="readonly", font=config.FONTS["body"])
        self.subject_combo.grid(row=1, column=1, sticky="ew")

        # Row 3: Grid for Task Type & Priority & Status
        grid_row2 = tk.Frame(form_frame, bg=config.COLORS["bg_card"])
        grid_row2.pack(fill="x", pady=(0, 10))
        grid_row2.columnconfigure(0, weight=1)
        grid_row2.columnconfigure(1, weight=1)
        grid_row2.columnconfigure(2, weight=1)

        # Task Type
        tk.Label(grid_row2, text="Task Type *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=0, sticky="w")
        self.type_var = tk.StringVar(value=self.preset_type or "Assignment")
        self.type_combo = ttk.Combobox(grid_row2, textvariable=self.type_var, values=config.TASK_TYPES, state="readonly", font=config.FONTS["body"])
        self.type_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        # Priority
        tk.Label(grid_row2, text="Priority *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=1, sticky="w")
        self.priority_var = tk.StringVar(value="Medium")
        self.priority_combo = ttk.Combobox(grid_row2, textvariable=self.priority_var, values=config.TASK_PRIORITIES, state="readonly", font=config.FONTS["body"])
        self.priority_combo.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        # Status
        tk.Label(grid_row2, text="Status *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=2, sticky="w")
        self.status_var = tk.StringVar(value="Pending")
        self.status_combo = ttk.Combobox(grid_row2, textvariable=self.status_var, values=config.TASK_STATUSES, state="readonly", font=config.FONTS["body"])
        self.status_combo.grid(row=1, column=2, sticky="ew")

        # Row 4: Grid for Dates (Assigned Date & Due Date) & Submission Mode
        grid_row3 = tk.Frame(form_frame, bg=config.COLORS["bg_card"])
        grid_row3.pack(fill="x", pady=(0, 10))
        grid_row3.columnconfigure(0, weight=1)
        grid_row3.columnconfigure(1, weight=1)
        grid_row3.columnconfigure(2, weight=1)

        # Assigned Date
        tk.Label(grid_row3, text="Assigned Date (YYYY-MM-DD)", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=0, sticky="w")
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.assigned_date_var = tk.StringVar(value=today_str)
        self.assigned_date_entry = ttk.Entry(grid_row3, textvariable=self.assigned_date_var, font=config.FONTS["body"])
        self.assigned_date_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        # Due Date
        tk.Label(grid_row3, text="Due Date (YYYY-MM-DD) *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=1, sticky="w")
        self.due_date_var = tk.StringVar(value=today_str)
        self.due_date_entry = ttk.Entry(grid_row3, textvariable=self.due_date_var, font=config.FONTS["body"])
        self.due_date_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        # Submission Mode
        tk.Label(grid_row3, text="Submission Mode", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=2, sticky="w")
        self.submission_mode_var = tk.StringVar(value=config.SUBMISSION_MODES[0])
        self.sub_mode_combo = ttk.Combobox(grid_row3, textvariable=self.submission_mode_var, values=config.SUBMISSION_MODES, state="readonly", font=config.FONTS["body"])
        self.sub_mode_combo.grid(row=1, column=2, sticky="ew")

        # Row 5: Description (Multiline)
        tk.Label(form_frame, text="Description", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(4, 2))
        self.desc_text = tk.Text(form_frame, height=3, font=config.FONTS["body"], bg=config.COLORS["bg_hover"], highlightbackground=config.COLORS["border"], highlightthickness=1, relief="flat")
        self.desc_text.pack(fill="x", pady=(0, 10))

        # Row 6: Notes (Multiline)
        tk.Label(form_frame, text="Notes / Remarks", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(4, 2))
        self.notes_text = tk.Text(form_frame, height=2, font=config.FONTS["body"], bg=config.COLORS["bg_hover"], highlightbackground=config.COLORS["border"], highlightthickness=1, relief="flat")
        self.notes_text.pack(fill="x", pady=(0, 15))

        # Bottom Button Bar
        btn_bar = tk.Frame(main_frame, bg=config.COLORS["bg_card"])
        btn_bar.pack(fill="x", pady=(10, 0))

        cancel_btn = tk.Button(
            btn_bar,
            text="Cancel",
            font=config.FONTS["body"],
            bg=config.COLORS["bg_hover"],
            fg=config.COLORS["text_dark"],
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = tk.Button(
            btn_bar,
            text="Save Task" if self.task else "Create Task",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["primary"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=6,
            command=self._handle_save
        )
        save_btn.pack(side="right")

    def _populate_fields(self) -> None:
        if not self.task:
            if self.subjects:
                self.subject_var.set(self.subjects[0].name)
            if self.current_user.is_admin and self.students:
                first_st = self.students[0]
                self.student_var.set(f"{first_st.name} ({first_st.username})")
            return

        # Populate with existing task
        self.title_var.set(self.task.title)
        self.type_var.set(self.task.task_type)
        self.priority_var.set(self.task.priority)
        self.status_var.set(self.task.status)
        self.assigned_date_var.set(self.task.assigned_date or "")
        self.due_date_var.set(self.task.due_date)
        self.submission_mode_var.set(self.task.submission_mode or config.SUBMISSION_MODES[0])

        if self.task.subject_name:
            self.subject_var.set(self.task.subject_name)
        else:
            sub = self.subject_service.get_subject_by_id(self.task.subject_id)
            if sub:
                self.subject_var.set(sub.name)

        if self.current_user.is_admin:
            st = self.student_service.get_student_by_id(self.task.student_id)
            if st:
                self.student_var.set(f"{st.name} ({st.username})")

        if self.task.description:
            self.desc_text.insert("1.0", self.task.description)
        if self.task.notes:
            self.notes_text.insert("1.0", self.task.notes)

    def _show_error(self, message: str) -> None:
        self.error_var.set(message)
        self.error_label.pack(fill="x", pady=(0, 10), before=self.title_entry.master.winfo_children()[0])

    def _handle_save(self) -> None:
        title = self.title_var.get().strip()
        task_type = self.type_var.get()
        priority = self.priority_var.get()
        status = self.status_var.get()
        assigned_date = self.assigned_date_var.get().strip()
        due_date = self.due_date_var.get().strip()
        submission_mode = self.submission_mode_var.get()
        description = self.desc_text.get("1.0", "end-1c").strip()
        notes = self.notes_text.get("1.0", "end-1c").strip()

        # Resolve Student ID
        if self.current_user.is_admin:
            st_key = self.student_var.get()
            student_id = self.student_map.get(st_key)
            if not student_id:
                self._show_error("Please select a valid student.")
                return
        else:
            student_id = self.current_user.id

        # Resolve Subject ID
        subj_name = self.subject_var.get()
        subject_id = self.subject_map.get(subj_name)
        if not subject_id:
            self._show_error("Please select a valid subject.")
            return

        if self.task:
            # Update
            success, msg = self.task_service.update_task(
                task_id=self.task.id,
                student_id=student_id,
                subject_id=subject_id,
                title=title,
                task_type=task_type,
                due_date_str=due_date,
                priority=priority,
                status=status,
                description=description,
                assigned_date_str=assigned_date,
                submission_mode=submission_mode,
                notes=notes,
                acting_user=self.current_user
            )
        else:
            # Create
            success, _, msg = self.task_service.create_task(
                student_id=student_id,
                subject_id=subject_id,
                title=title,
                task_type=task_type,
                due_date_str=due_date,
                priority=priority,
                status=status,
                description=description,
                assigned_date_str=assigned_date,
                submission_mode=submission_mode,
                notes=notes,
                acting_user=self.current_user
            )

        if success:
            if self.on_saved:
                self.on_saved()
            self.destroy()
        else:
            self._show_error(msg)


class TasksView(ttk.Frame):
    """
    Unified academic tasks and practicals list view.
    When is_practicals_view=True, sets task_type to 'Practical' and reuses all CRUD logic.
    """
    def __init__(
        self,
        parent: tk.Widget,
        user: User,
        task_service: TaskService,
        subject_service: SubjectService,
        student_service: StudentService,
        is_practicals_view: bool = False
    ):
        super().__init__(parent, style="App.TFrame")
        self.user = user
        self.task_service = task_service
        self.subject_service = subject_service
        self.student_service = student_service
        self.is_practicals_view = is_practicals_view

        self._create_widgets()
        self.refresh_data()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Header Bar
        header_frame = tk.Frame(self, bg=config.COLORS["bg_main"])
        header_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))

        title_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        title_box.pack(side="left")

        page_title = "🔬 PRACTICALS & LAB SUBMISSIONS" if self.is_practicals_view else "📚 ACADEMIC TASKS & ASSIGNMENTS"
        tk.Label(
            title_box,
            text=page_title,
            font=config.FONTS["title"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_main"]
        ).pack(anchor="w")

        sub_text = (
            "Filtered view of practical and laboratory tasks (task_type = 'Practical')"
            if self.is_practicals_view else
            "Manage and track all college assignments, journals, projects, and presentations"
        )
        tk.Label(
            title_box,
            text=sub_text,
            font=config.FONTS["body"],
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_main"]
        ).pack(anchor="w", pady=(2, 0))

        # Top Right Actions
        action_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        action_box.pack(side="right")

        btn_label = "+ Add Practical" if self.is_practicals_view else "+ Add New Task"
        add_btn = tk.Button(
            action_box,
            text=btn_label,
            font=config.FONTS["body_bold"],
            bg=config.COLORS["primary"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=lambda: self._open_task_modal(None)
        )
        add_btn.pack(side="left", padx=(0, 8))

        refresh_btn = tk.Button(
            action_box,
            text="🔄 Refresh",
            font=config.FONTS["small_bold"],
            bg=config.COLORS["bg_card"],
            fg=config.COLORS["text_dark"],
            relief="flat",
            highlightbackground=config.COLORS["border"],
            highlightthickness=1,
            cursor="hand2",
            padx=8,
            pady=6,
            command=self.refresh_data
        )
        refresh_btn.pack(side="left")

        # Filter & Search Toolbar
        toolbar = tk.Frame(self, bg=config.COLORS["bg_card"], padx=16, pady=12, highlightbackground=config.COLORS["border"], highlightthickness=1)
        toolbar.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 15))

        # Search box
        tk.Label(toolbar, text="🔍 Search:", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=18, font=config.FONTS["body"])
        self.search_entry.pack(side="left", padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_data())

        # Subject Filter
        tk.Label(toolbar, text="Subject:", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 4))
        self.subject_filter_var = tk.StringVar(value="All Subjects")
        self.subject_combo = ttk.Combobox(toolbar, textvariable=self.subject_filter_var, state="readonly", width=16, font=config.FONTS["small"])
        self.subject_combo.pack(side="left", padx=(0, 15))
        self.subject_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Task Type Filter (Only visible if not in practicals view)
        if not self.is_practicals_view:
            tk.Label(toolbar, text="Type:", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 4))
            self.type_filter_var = tk.StringVar(value="All Types")
            type_options = ["All Types"] + config.TASK_TYPES
            self.type_combo = ttk.Combobox(toolbar, textvariable=self.type_filter_var, values=type_options, state="readonly", width=12, font=config.FONTS["small"])
            self.type_combo.pack(side="left", padx=(0, 15))
            self.type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Status Filter
        tk.Label(toolbar, text="Status:", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 4))
        self.status_filter_var = tk.StringVar(value="All Statuses")
        status_options = ["All Statuses"] + config.TASK_STATUSES
        self.status_combo = ttk.Combobox(toolbar, textvariable=self.status_filter_var, values=status_options, state="readonly", width=12, font=config.FONTS["small"])
        self.status_combo.pack(side="left", padx=(0, 15))
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Priority Filter
        tk.Label(toolbar, text="Priority:", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 4))
        self.priority_filter_var = tk.StringVar(value="All Priorities")
        priority_options = ["All Priorities"] + config.TASK_PRIORITIES
        self.priority_combo = ttk.Combobox(toolbar, textvariable=self.priority_filter_var, values=priority_options, state="readonly", width=11, font=config.FONTS["small"])
        self.priority_combo.pack(side="left", padx=(0, 15))
        self.priority_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Deadline State Filter
        tk.Label(toolbar, text="Urgency:", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 4))
        self.deadline_filter_var = tk.StringVar(value="All Deadlines")
        deadline_options = ["All Deadlines", "Overdue", "Due Today", "Upcoming", "Completed"]
        self.deadline_combo = ttk.Combobox(toolbar, textvariable=self.deadline_filter_var, values=deadline_options, state="readonly", width=12, font=config.FONTS["small"])
        self.deadline_combo.pack(side="left", padx=(0, 15))
        self.deadline_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Sort Dropdown
        tk.Label(toolbar, text="Sort by:", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 4))
        self.sort_var = tk.StringVar(value="Due Date (Earliest)")
        sort_options = [
            "Due Date (Earliest)",
            "Due Date (Latest)",
            "Priority (High to Low)",
            "Priority (Low to High)",
            "Status",
            "Subject",
            "Title"
        ]
        if self.user.is_admin:
            sort_options.append("Student Name")

        self.sort_combo = ttk.Combobox(toolbar, textvariable=self.sort_var, values=sort_options, state="readonly", width=16, font=config.FONTS["small"])
        self.sort_combo.pack(side="left")
        self.sort_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Tasks Table Container
        table_card = tk.Frame(self, bg=config.COLORS["bg_card"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        table_card.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 15))
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(0, weight=1)

        # Columns definition
        base_cols = ["id", "title", "subject", "type", "due_date", "priority", "status", "mode"]
        if self.user.is_admin:
            base_cols.insert(2, "student")

        self.tree = ttk.Treeview(table_card, columns=base_cols, show="headings", selectmode="browse")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Task Title")
        self.tree.heading("subject", text="Subject")
        self.tree.heading("type", text="Type")
        self.tree.heading("due_date", text="Due Date & Urgency")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("status", text="Status")
        self.tree.heading("mode", text="Submission Mode")

        if self.user.is_admin:
            self.tree.heading("student", text="Student")
            self.tree.column("student", width=120, anchor="w")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("title", width=220, anchor="w")
        self.tree.column("subject", width=140, anchor="w")
        self.tree.column("type", width=90, anchor="center")
        self.tree.column("due_date", width=140, anchor="center")
        self.tree.column("priority", width=90, anchor="center")
        self.tree.column("status", width=95, anchor="center")
        self.tree.column("mode", width=130, anchor="w")

        tree_scroll_y = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")

        # Tree tags for styling
        self.tree.tag_configure("evenrow", background=config.COLORS["bg_card"])
        self.tree.tag_configure("oddrow", background=config.COLORS["bg_hover"])
        self.tree.tag_configure("overdue", background=config.COLORS["danger_bg"])
        self.tree.tag_configure("due_today", background=config.COLORS["warning_bg"])
        self.tree.tag_configure("completed", foreground=config.COLORS["success"])

        # Double click to edit
        self.tree.bind("<Double-1>", lambda e: self._on_edit_selected())

        # Bottom Control Bar
        control_bar = tk.Frame(self, bg=config.COLORS["bg_main"])
        control_bar.grid(row=3, column=0, sticky="ew", padx=25, pady=(0, 20))

        self.count_label = tk.Label(control_bar, text="Showing 0 tasks", font=config.FONTS["small_bold"], fg=config.COLORS["text_muted"], bg=config.COLORS["bg_main"])
        self.count_label.pack(side="left")

        # Action Buttons
        btn_box = tk.Frame(control_bar, bg=config.COLORS["bg_main"])
        btn_box.pack(side="right")

        complete_btn = tk.Button(
            btn_box,
            text="✓ Mark Completed",
            font=config.FONTS["small_bold"],
            bg=config.COLORS["success"],
            fg="white",
            activebackground="#15803d",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=5,
            command=self._mark_selected_completed
        )
        complete_btn.pack(side="left", padx=(0, 8))

        edit_btn = tk.Button(
            btn_box,
            text="✏️ Edit",
            font=config.FONTS["small_bold"],
            bg=config.COLORS["bg_card"],
            fg=config.COLORS["text_dark"],
            relief="flat",
            highlightbackground=config.COLORS["border"],
            highlightthickness=1,
            cursor="hand2",
            padx=10,
            pady=5,
            command=self._on_edit_selected
        )
        edit_btn.pack(side="left", padx=(0, 8))

        delete_btn = tk.Button(
            btn_box,
            text="🗑️ Delete",
            font=config.FONTS["small_bold"],
            bg=config.COLORS["danger_bg"],
            fg=config.COLORS["danger"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=5,
            command=self._on_delete_selected
        )
        delete_btn.pack(side="left")

    def _open_task_modal(self, task: Optional[Task] = None) -> None:
        preset_type = "Practical" if self.is_practicals_view else None
        TaskModalDialog(
            parent=self.winfo_toplevel(),
            task_service=self.task_service,
            subject_service=self.subject_service,
            student_service=self.student_service,
            current_user=self.user,
            task=task,
            preset_type=preset_type,
            on_saved=self.refresh_data
        )

    def _get_selected_task(self) -> Optional[Task]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a task from the table first.", parent=self)
            return None
        task_id_str = selected[0]
        try:
            return self.task_service.get_task_by_id(int(task_id_str))
        except ValueError:
            return None

    def _on_edit_selected(self) -> None:
        task = self._get_selected_task()
        if task:
            self._open_task_modal(task)

    def _mark_selected_completed(self) -> None:
        task = self._get_selected_task()
        if not task:
            return
        if task.status == "Completed":
            messagebox.showinfo("Already Completed", "This task is already marked as Completed.", parent=self)
            return

        success, msg = self.task_service.update_task_status(task.id, "Completed", acting_user=self.user)
        if success:
            self.refresh_data()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _on_delete_selected(self) -> None:
        task = self._get_selected_task()
        if not task:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the task:\n\n'{task.title}'?",
            parent=self
        )
        if confirm:
            success, msg = self.task_service.delete_task(task.id, acting_user=self.user)
            if success:
                self.refresh_data()
            else:
                messagebox.showerror("Delete Error", msg, parent=self)

    def refresh_data(self) -> None:
        """Query tasks according to current filters and populate treeview."""
        # 1. Update subject filter options
        subjects = self.subject_service.get_all_subjects()
        subject_dict = {s.name: s.id for s in subjects}
        sub_options = ["All Subjects"] + [s.name for s in subjects]
        self.subject_combo["values"] = sub_options

        # 2. Extract filter criteria
        search_query = self.search_var.get().strip()

        # Subject ID
        selected_sub_name = self.subject_filter_var.get()
        subject_id = subject_dict.get(selected_sub_name)

        # Task Type
        if self.is_practicals_view:
            task_type = "Practical"
        else:
            task_type = self.type_filter_var.get()
            if task_type == "All Types":
                task_type = None

        # Status
        status = self.status_filter_var.get()
        if status == "All Statuses":
            status = None

        # Priority
        priority = self.priority_filter_var.get()
        if priority == "All Priorities":
            priority = None

        # Deadline State
        deadline_state = self.deadline_filter_var.get()
        if deadline_state == "All Deadlines":
            deadline_state = None

        # Sort SQL map
        sort_map = {
            "Due Date (Earliest)": "due_date_asc",
            "Due Date (Latest)": "due_date_desc",
            "Priority (High to Low)": "priority_desc",
            "Priority (Low to High)": "priority_asc",
            "Status": "status_asc",
            "Subject": "subject_asc",
            "Title": "title_asc",
            "Student Name": "student_asc",
        }
        sort_by = sort_map.get(self.sort_var.get(), "due_date_asc")

        # Student scoping: If student, restrict to own id
        student_id = self.user.id if self.user.is_student else None

        tasks = self.task_service.get_tasks(
            student_id=student_id,
            task_type=task_type,
            status=status,
            subject_id=subject_id,
            priority=priority,
            deadline_state=deadline_state,
            search_query=search_query,
            sort_by=sort_by
        )

        # Populate tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, t in enumerate(tasks):
            tag_list = ["evenrow" if idx % 2 == 0 else "oddrow"]
            if t.deadline_state == "Overdue":
                tag_list.append("overdue")
                state_badge = f"🚨 {format_display_date(t.due_date)} (Overdue)"
            elif t.deadline_state == "Due Today":
                tag_list.append("due_today")
                state_badge = f"⏰ {format_display_date(t.due_date)} (Today)"
            elif t.deadline_state == "Completed":
                tag_list.append("completed")
                state_badge = f"✅ {format_display_date(t.due_date)}"
            else:
                days = get_days_remaining(t.due_date)
                days_str = f"in {days}d" if days is not None and days >= 0 else ""
                state_badge = f"{format_display_date(t.due_date)} ({days_str})"

            priority_badge = "🔴 High" if t.priority == "High" else ("🟡 Medium" if t.priority == "Medium" else "🟢 Low")
            status_badge = "⏳ Pending" if t.status == "Pending" else ("⚙️ In Progress" if t.status == "In Progress" else "✅ Completed")

            values = [
                str(t.id),
                t.title,
                t.subject_name or "-",
                t.task_type,
                state_badge,
                priority_badge,
                status_badge,
                t.submission_mode or "-"
            ]
            if self.user.is_admin:
                values.insert(2, t.student_name or t.student_username or "-")

            self.tree.insert("", "end", iid=str(t.id), values=values, tags=tag_list)

        self.count_label.config(text=f"Showing {len(tasks)} academic task(s)")
