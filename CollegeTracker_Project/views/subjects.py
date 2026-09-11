"""
Subject management view for College Tracker.
Provides CRUD operations for Administrators and catalog viewing for Students (PRD Section 19, BR-06).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import config
from models import User, Subject
from subject_service import SubjectService


class SubjectModalDialog(tk.Toplevel):
    """Modal dialog to add or edit academic subjects."""
    def __init__(
        self,
        parent: tk.Widget,
        subject_service: SubjectService,
        subject: Optional[Subject] = None,
        on_saved: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.subject_service = subject_service
        self.subject = subject
        self.on_saved = on_saved

        self.title("Edit Subject" if subject else "Add New Subject")
        self.geometry("450x280")
        self.resizable(False, False)
        self.configure(bg=config.COLORS["bg_main"])
        self.transient(parent)
        self.grab_set()

        self._create_form()

    def _create_form(self) -> None:
        main_box = tk.Frame(self, bg=config.COLORS["bg_card"], padx=25, pady=20)
        main_box.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(
            main_box,
            text="Edit Subject" if self.subject else "Create Academic Subject",
            font=config.FONTS["h2"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"]
        ).pack(anchor="w", pady=(0, 15))

        # Subject Name
        tk.Label(main_box, text="Subject Name *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 2))
        self.name_var = tk.StringVar(value=self.subject.name if self.subject else "")
        self.name_entry = ttk.Entry(main_box, textvariable=self.name_var, font=config.FONTS["body"])
        self.name_entry.pack(fill="x", pady=(0, 12))

        # Semester
        tk.Label(main_box, text="Semester (e.g. Semester 4)", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 2))
        self.sem_var = tk.StringVar(value=self.subject.semester if self.subject and self.subject.semester else "Semester 4")
        self.sem_entry = ttk.Entry(main_box, textvariable=self.sem_var, font=config.FONTS["body"])
        self.sem_entry.pack(fill="x", pady=(0, 20))

        # Button Bar
        btn_bar = tk.Frame(main_box, bg=config.COLORS["bg_card"])
        btn_bar.pack(fill="x")

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
            text="Save Subject" if self.subject else "Create Subject",
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
        semester = self.sem_var.get().strip()

        if not name:
            messagebox.showwarning("Validation Warning", "Subject name is required.", parent=self)
            return

        if self.subject:
            success, msg = self.subject_service.update_subject(self.subject.id, name, semester)
        else:
            success, _, msg = self.subject_service.create_subject(name, semester)

        if success:
            if self.on_saved:
                self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)


class SubjectsView(ttk.Frame):
    """Subject catalog & management view."""
    def __init__(self, parent: tk.Widget, user: User, subject_service: SubjectService):
        super().__init__(parent, style="App.TFrame")
        self.user = user
        self.subject_service = subject_service

        self._create_widgets()
        self.refresh_data()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Header Bar
        header_frame = tk.Frame(self, bg=config.COLORS["bg_main"])
        header_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 15))

        title_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="📖 COLLEGE SUBJECTS & COURSES",
            font=config.FONTS["title"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_main"]
        ).pack(anchor="w")

        sub_text = (
            "Manage academic curriculum and course offerings"
            if self.user.is_admin else
            "View enrolled semester subjects and course codes"
        )
        tk.Label(
            title_box,
            text=sub_text,
            font=config.FONTS["body"],
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_main"]
        ).pack(anchor="w", pady=(2, 0))

        # Admin Actions on Top Right
        action_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        action_box.pack(side="right")

        if self.user.is_admin:
            add_btn = tk.Button(
                action_box,
                text="+ Add New Subject",
                font=config.FONTS["body_bold"],
                bg=config.COLORS["primary"],
                fg="white",
                activebackground=config.COLORS["primary_hover"],
                relief="flat",
                cursor="hand2",
                padx=12,
                pady=6,
                command=lambda: self._open_subject_modal(None)
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

        # Subjects Table Card
        table_card = tk.Frame(self, bg=config.COLORS["bg_card"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        table_card.grid(row=1, column=0, sticky="nsew", padx=25, pady=(0, 15))
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(0, weight=1)

        columns = ("id", "name", "semester", "linked_tasks", "created_at")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="Subject ID")
        self.tree.heading("name", text="Subject Name")
        self.tree.heading("semester", text="Semester")
        self.tree.heading("linked_tasks", text="Active Tasks")
        self.tree.heading("created_at", text="Created On")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("semester", width=140, anchor="center")
        self.tree.column("linked_tasks", width=120, anchor="center")
        self.tree.column("created_at", width=160, anchor="center")

        tree_scroll = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("evenrow", background=config.COLORS["bg_card"])
        self.tree.tag_configure("oddrow", background=config.COLORS["bg_hover"])

        # Double click to edit for admin
        if self.user.is_admin:
            self.tree.bind("<Double-1>", lambda e: self._on_edit_selected())

        # Bottom Bar (Admin Edit / Delete buttons)
        bottom_bar = tk.Frame(self, bg=config.COLORS["bg_main"])
        bottom_bar.grid(row=2, column=0, sticky="ew", padx=25, pady=(0, 20))

        self.count_label = tk.Label(bottom_bar, text="Showing 0 subject(s)", font=config.FONTS["small_bold"], fg=config.COLORS["text_muted"], bg=config.COLORS["bg_main"])
        self.count_label.pack(side="left")

        if self.user.is_admin:
            btn_box = tk.Frame(bottom_bar, bg=config.COLORS["bg_main"])
            btn_box.pack(side="right")

            edit_btn = tk.Button(
                btn_box,
                text="✏️ Edit Subject",
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
                text="🗑️ Delete Subject",
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

    def _open_subject_modal(self, subject: Optional[Subject] = None) -> None:
        SubjectModalDialog(
            parent=self.winfo_toplevel(),
            subject_service=self.subject_service,
            subject=subject,
            on_saved=self.refresh_data
        )

    def _get_selected_subject(self) -> Optional[Subject]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a subject from the table first.", parent=self)
            return None
        sub_id = int(selected[0])
        return self.subject_service.get_subject_by_id(sub_id)

    def _on_edit_selected(self) -> None:
        if not self.user.is_admin:
            return
        subject = self._get_selected_subject()
        if subject:
            self._open_subject_modal(subject)

    def _on_delete_selected(self) -> None:
        if not self.user.is_admin:
            return
        subject = self._get_selected_subject()
        if not subject:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the subject '{subject.name}'?",
            parent=self
        )
        if confirm:
            success, msg = self.subject_service.delete_subject(subject.id)
            if success:
                self.refresh_data()
            else:
                messagebox.showerror("Cannot Delete Subject", msg, parent=self)

    def refresh_data(self) -> None:
        """Fetch all subjects and populate table."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        subjects = self.subject_service.get_all_subjects()
        for idx, sub in enumerate(subjects):
            task_count = self.subject_service.has_associated_tasks(sub.id)
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                iid=str(sub.id),
                values=(
                    str(sub.id),
                    sub.name,
                    sub.semester or "-",
                    f"{task_count} tasks",
                    sub.created_at[:10] if sub.created_at else "-"
                ),
                tags=(tag,)
            )

        self.count_label.config(text=f"Showing {len(subjects)} registered subject(s)")
