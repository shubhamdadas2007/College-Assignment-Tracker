"""
Student account management view for College Tracker.
Provides CRUD operations and deletion safety rules for Administrators (PRD Section 20, BR-07).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import config
from models import User
from student_service import StudentService


class StudentModalDialog(tk.Toplevel):
    """Modal dialog to create or edit student accounts."""
    def __init__(
        self,
        parent: tk.Widget,
        student_service: StudentService,
        student: Optional[User] = None,
        on_saved: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.student_service = student_service
        self.student = student
        self.on_saved = on_saved

        self.title("Edit Student Account" if student else "Register New Student")
        self.geometry("500x520")
        self.minsize(460, 480)
        self.configure(bg=config.COLORS["bg_main"])
        self.transient(parent)
        self.grab_set()

        self._create_form()

    def _create_form(self) -> None:
        main_box = tk.Frame(self, bg=config.COLORS["bg_card"], padx=25, pady=20)
        main_box.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(
            main_box,
            text="Edit Student Profile" if self.student else "Register New Student Account",
            font=config.FONTS["h1"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"]
        ).pack(anchor="w", pady=(0, 15))

        # Full Name
        tk.Label(main_box, text="Full Name *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 2))
        self.name_var = tk.StringVar(value=self.student.name if self.student else "")
        self.name_entry = ttk.Entry(main_box, textvariable=self.name_var, font=config.FONTS["body"])
        self.name_entry.pack(fill="x", pady=(0, 10))

        # Username
        tk.Label(main_box, text="Username *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 2))
        self.username_var = tk.StringVar(value=self.student.username if self.student else "")
        self.username_entry = ttk.Entry(main_box, textvariable=self.username_var, font=config.FONTS["body"])
        self.username_entry.pack(fill="x", pady=(0, 10))
        if self.student:
            self.username_entry.configure(state="disabled")

        # Password
        pw_label = "New Password (leave blank to keep existing)" if self.student else "Password *"
        tk.Label(main_box, text=pw_label, font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 2))
        self.pw_var = tk.StringVar()
        self.pw_entry = ttk.Entry(main_box, textvariable=self.pw_var, show="•", font=config.FONTS["body"])
        self.pw_entry.pack(fill="x", pady=(0, 10))

        # Email
        tk.Label(main_box, text="Email Address (optional)", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 2))
        self.email_var = tk.StringVar(value=self.student.email if self.student and self.student.email else "")
        self.email_entry = ttk.Entry(main_box, textvariable=self.email_var, font=config.FONTS["body"])
        self.email_entry.pack(fill="x", pady=(0, 10))

        # Semester & Division Grid
        sem_div_frame = tk.Frame(main_box, bg=config.COLORS["bg_card"])
        sem_div_frame.pack(fill="x", pady=(0, 15))
        sem_div_frame.columnconfigure(0, weight=1)
        sem_div_frame.columnconfigure(1, weight=1)

        tk.Label(sem_div_frame, text="Semester", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=0, sticky="w")
        self.sem_var = tk.StringVar(value=self.student.semester if self.student and self.student.semester else "Semester 4")
        self.sem_entry = ttk.Entry(sem_div_frame, textvariable=self.sem_var, font=config.FONTS["body"])
        self.sem_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        tk.Label(sem_div_frame, text="Division (e.g. A, B)", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=1, sticky="w")
        self.div_var = tk.StringVar(value=self.student.division if self.student and self.student.division else "A")
        self.div_entry = ttk.Entry(sem_div_frame, textvariable=self.div_var, font=config.FONTS["body"])
        self.div_entry.grid(row=1, column=1, sticky="ew")

        # Bottom Bar
        btn_bar = tk.Frame(main_box, bg=config.COLORS["bg_card"])
        btn_bar.pack(fill="x", pady=(10, 0))

        cancel_btn = tk.Button(
            btn_bar,
            text="Cancel",
            font=config.FONTS["body"],
            bg=config.COLORS["bg_hover"],
            fg=config.COLORS["text_dark"],
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=5,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = tk.Button(
            btn_bar,
            text="Save Changes" if self.student else "Register Student",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["primary"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=5,
            command=self._handle_save
        )
        save_btn.pack(side="right")

    def _handle_save(self) -> None:
        name = self.name_var.get().strip()
        username = self.username_var.get().strip()
        password = self.pw_var.get().strip()
        email = self.email_var.get().strip()
        semester = self.sem_var.get().strip()
        division = self.div_var.get().strip()

        if not name:
            messagebox.showwarning("Validation Warning", "Student name is required.", parent=self)
            return

        if self.student:
            success, msg = self.student_service.update_student(
                student_id=self.student.id,
                name=name,
                email=email,
                semester=semester,
                division=division,
                new_password=password if password else None
            )
        else:
            if not username:
                messagebox.showwarning("Validation Warning", "Username is required.", parent=self)
                return
            if not password or len(password) < 4:
                messagebox.showwarning("Validation Warning", "Password must be at least 4 characters long.", parent=self)
                return

            success, _, msg = self.student_service.create_student(
                name=name,
                username=username,
                password=password,
                email=email,
                semester=semester,
                division=division
            )

        if success:
            if self.on_saved:
                self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)


class StudentsView(ttk.Frame):
    """Administrator Student Management View."""
    def __init__(self, parent: tk.Widget, user: User, student_service: StudentService):
        super().__init__(parent, style="App.TFrame")
        self.user = user
        self.student_service = student_service

        self._create_widgets()
        self.refresh_data()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Header Bar
        header_frame = tk.Frame(self, bg=config.COLORS["bg_main"])
        header_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 12))

        title_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="👥 STUDENT ACCOUNT MANAGEMENT",
            font=config.FONTS["title"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_main"]
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Manage enrolled students, login credentials, and academic divisions",
            font=config.FONTS["body"],
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_main"]
        ).pack(anchor="w", pady=(2, 0))

        # Header Actions
        action_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        action_box.pack(side="right")

        add_btn = tk.Button(
            action_box,
            text="+ Add New Student",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["primary"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=lambda: self._open_student_modal(None)
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

        # Search Bar
        search_frame = tk.Frame(self, bg=config.COLORS["bg_card"], padx=15, pady=10, highlightbackground=config.COLORS["border"], highlightthickness=1)
        search_frame.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 15))

        tk.Label(search_frame, text="🔍 Search Students:", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30, font=config.FONTS["body"])
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_data())

        # Students Table Card
        table_card = tk.Frame(self, bg=config.COLORS["bg_card"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        table_card.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 15))
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(0, weight=1)

        columns = ("id", "name", "username", "email", "semester", "division", "tasks_count", "created_at")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Full Name")
        self.tree.heading("username", text="Username")
        self.tree.heading("email", text="Email")
        self.tree.heading("semester", text="Semester")
        self.tree.heading("division", text="Div")
        self.tree.heading("tasks_count", text="Active Tasks")
        self.tree.heading("created_at", text="Registered On")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=180, anchor="w")
        self.tree.column("username", width=120, anchor="w")
        self.tree.column("email", width=180, anchor="w")
        self.tree.column("semester", width=100, anchor="center")
        self.tree.column("division", width=60, anchor="center")
        self.tree.column("tasks_count", width=100, anchor="center")
        self.tree.column("created_at", width=140, anchor="center")

        tree_scroll = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("evenrow", background=config.COLORS["bg_card"])
        self.tree.tag_configure("oddrow", background=config.COLORS["bg_hover"])

        self.tree.bind("<Double-1>", lambda e: self._on_edit_selected())

        # Bottom Action Bar
        bottom_bar = tk.Frame(self, bg=config.COLORS["bg_main"])
        bottom_bar.grid(row=3, column=0, sticky="ew", padx=25, pady=(0, 20))

        self.count_label = tk.Label(bottom_bar, text="Showing 0 student(s)", font=config.FONTS["small_bold"], fg=config.COLORS["text_muted"], bg=config.COLORS["bg_main"])
        self.count_label.pack(side="left")

        btn_box = tk.Frame(bottom_bar, bg=config.COLORS["bg_main"])
        btn_box.pack(side="right")

        edit_btn = tk.Button(
            btn_box,
            text="✏️ Edit Student",
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
            text="🗑️ Delete Student",
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

    def _open_student_modal(self, student: Optional[User] = None) -> None:
        StudentModalDialog(
            parent=self.winfo_toplevel(),
            student_service=self.student_service,
            student=student,
            on_saved=self.refresh_data
        )

    def _get_selected_student(self) -> Optional[User]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a student from the table first.", parent=self)
            return None
        student_id = int(selected[0])
        return self.student_service.get_student_by_id(student_id)

    def _on_edit_selected(self) -> None:
        student = self._get_selected_student()
        if student:
            self._open_student_modal(student)

    def _on_delete_selected(self) -> None:
        student = self._get_selected_student()
        if not student:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete student account:\n\n'{student.name}' ({student.username})?",
            parent=self
        )
        if confirm:
            success, msg = self.student_service.delete_student(student.id)
            if success:
                self.refresh_data()
            else:
                messagebox.showerror("Cannot Delete Student", msg, parent=self)

    def refresh_data(self) -> None:
        """Query students with search filter and populate table."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_query = self.search_var.get().strip()
        students = self.student_service.get_all_students(search_query)

        for idx, st in enumerate(students):
            task_count = self.student_service.has_associated_tasks(st.id)
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                iid=str(st.id),
                values=(
                    str(st.id),
                    st.name,
                    st.username,
                    st.email or "-",
                    st.semester or "-",
                    st.division or "-",
                    f"{task_count} tasks",
                    st.created_at[:10] if st.created_at else "-"
                ),
                tags=(tag,)
            )

        self.count_label.config(text=f"Showing {len(students)} student account(s)")
