"""
Login view for College Assignment & Practical Submission Tracker.
Supports Username or Email login, role selection, and Firebase Auth / Local SQLite indicators.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import config
from auth_service import AuthService
from models import User


class LoginView(ttk.Frame):
    def __init__(self, parent: tk.Widget, auth_service: AuthService, on_login_success: Callable[[User], None]):
        super().__init__(parent, style="App.TFrame")
        self.auth_service = auth_service
        self.on_login_success = on_login_success

        self._create_widgets()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        center_box = tk.Frame(self, bg=config.COLORS["bg_card"], padx=45, pady=30, highlightbackground=config.COLORS["border"], highlightthickness=1)
        center_box.grid(row=0, column=0)

        # Header Icon & Title
        title_icon = tk.Label(center_box, text="🎓", font=("Segoe UI", 30), bg=config.COLORS["bg_card"])
        title_icon.pack(pady=(0, 2))

        title_lbl = tk.Label(
            center_box,
            text="COLLEGE TRACKER",
            font=("Segoe UI", 16, "bold"),
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"]
        )
        title_lbl.pack()

        subtitle_lbl = tk.Label(
            center_box,
            text="Academic & Practical Submission Manager",
            font=("Segoe UI", 9),
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_card"]
        )
        subtitle_lbl.pack(pady=(0, 10))

        # Auth Provider Badge
        auth_mode_text = "🔥 Firebase Auth Enabled" if self.auth_service.firebase_enabled else "⚡ Local SQLite Offline Auth (100+ Students)"
        auth_mode_bg = config.COLORS["warning_bg"] if self.auth_service.firebase_enabled else config.COLORS["primary_light"]
        auth_mode_fg = config.COLORS["warning"] if self.auth_service.firebase_enabled else config.COLORS["primary"]

        badge = tk.Label(
            center_box,
            text=auth_mode_text,
            font=("Segoe UI", 8, "bold"),
            bg=auth_mode_bg,
            fg=auth_mode_fg,
            padx=8,
            pady=3
        )
        badge.pack(pady=(0, 15))

        # Error / Status Banner
        self.error_var = tk.StringVar()
        self.error_label = tk.Label(
            center_box,
            textvariable=self.error_var,
            font=("Segoe UI", 9, "bold"),
            fg=config.COLORS["danger"],
            bg=config.COLORS["danger_bg"],
            padx=10,
            pady=6,
            wraplength=300
        )

        # Username / Email
        tk.Label(
            center_box,
            text="Username or Email",
            font=config.FONTS["small_bold"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"],
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.username_var = tk.StringVar(value="rahul")
        self.username_entry = ttk.Entry(center_box, textvariable=self.username_var, font=config.FONTS["body"], width=32)
        self.username_entry.pack(fill="x", pady=(0, 12))

        # Password
        tk.Label(
            center_box,
            text="Password",
            font=config.FONTS["small_bold"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"],
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.password_var = tk.StringVar(value="student123")
        self.password_entry = ttk.Entry(center_box, textvariable=self.password_var, show="•", font=config.FONTS["body"], width=32)
        self.password_entry.pack(fill="x", pady=(0, 12))

        # Role Selection
        tk.Label(
            center_box,
            text="Role",
            font=config.FONTS["small_bold"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"],
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.role_var = tk.StringVar(value="Student")
        self.role_combo = ttk.Combobox(
            center_box,
            textvariable=self.role_var,
            values=["Student", "Administrator"],
            state="readonly",
            font=config.FONTS["body"],
            width=30
        )
        self.role_combo.pack(fill="x", pady=(0, 20))

        # Login Button
        login_btn = tk.Button(
            center_box,
            text="LOGIN",
            font=("Segoe UI", 10, "bold"),
            bg=config.COLORS["primary"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
            command=self._handle_login
        )
        login_btn.pack(fill="x", pady=(0, 16))

        # Key Bindings
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

        # Demo Accounts Box
        demo_box = tk.Frame(center_box, bg=config.COLORS["bg_hover"], padx=10, pady=8, highlightbackground=config.COLORS["border"], highlightthickness=1)
        demo_box.pack(fill="x")

        tk.Label(
            demo_box,
            text="💡 Quick Demo Credentials:",
            font=("Segoe UI", 8, "bold"),
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_hover"],
            anchor="w"
        ).pack(fill="x")

        btn_row = tk.Frame(demo_box, bg=config.COLORS["bg_hover"])
        btn_row.pack(fill="x", pady=(4, 0))

        student_demo_btn = tk.Button(
            btn_row,
            text="Student (rahul)",
            font=("Segoe UI", 8),
            bg=config.COLORS["primary_light"],
            fg=config.COLORS["primary"],
            relief="flat",
            cursor="hand2",
            padx=6,
            pady=2,
            command=lambda: self._set_demo_credentials("rahul", "student123", "Student")
        )
        student_demo_btn.pack(side="left", padx=(0, 5))

        priya_demo_btn = tk.Button(
            btn_row,
            text="Student (priya)",
            font=("Segoe UI", 8),
            bg=config.COLORS["success_bg"],
            fg=config.COLORS["success"],
            relief="flat",
            cursor="hand2",
            padx=6,
            pady=2,
            command=lambda: self._set_demo_credentials("priya", "student123", "Student")
        )
        priya_demo_btn.pack(side="left", padx=(0, 5))

        admin_demo_btn = tk.Button(
            btn_row,
            text="Admin (admin)",
            font=("Segoe UI", 8),
            bg=config.COLORS["warning_bg"],
            fg=config.COLORS["warning"],
            relief="flat",
            cursor="hand2",
            padx=6,
            pady=2,
            command=lambda: self._set_demo_credentials("admin", "admin123", "Administrator")
        )
        admin_demo_btn.pack(side="left")

    def _set_demo_credentials(self, username: str, pw: str, role: str) -> None:
        self.username_var.set(username)
        self.password_var.set(pw)
        self.role_var.set(role)
        self._hide_error()

    def _show_error(self, message: str) -> None:
        self.error_var.set(message)
        self.error_label.pack(fill="x", pady=(0, 10), before=self.username_entry)

    def _hide_error(self) -> None:
        self.error_label.pack_forget()

    def _handle_login(self) -> None:
        self._hide_error()
        username = self.username_var.get()
        password = self.password_var.get()
        role = self.role_var.get()

        success, user, message = self.auth_service.authenticate(username, password, role)
        if success and user:
            self.on_login_success(user)
        else:
            self._show_error(message or "Invalid username or password.")
