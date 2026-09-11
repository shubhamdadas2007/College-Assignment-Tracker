"""
Settings and user profile view for College Tracker.
Allows students and administrators to manage profile details, change password, and configure Firebase Auth.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import config
from models import User
from auth_service import AuthService


class SettingsView(ttk.Frame):
    """User account settings, system information, and Firebase cloud auth config."""
    def __init__(self, parent: tk.Widget, user: User, auth_service: AuthService):
        super().__init__(parent, style="App.TFrame")
        self.user = user
        self.auth_service = auth_service

        self._create_widgets()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Header Bar
        header_frame = tk.Frame(self, bg=config.COLORS["bg_main"])
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=25, pady=(20, 15))

        tk.Label(
            header_frame,
            text="⚙️ ACCOUNT SETTINGS & SYSTEM CONFIGURATION",
            font=config.FONTS["title"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_main"]
        ).pack(anchor="w")

        tk.Label(
            header_frame,
            text="Manage profile details, credentials, and configure Firebase Cloud Authentication",
            font=config.FONTS["body"],
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_main"]
        ).pack(anchor="w", pady=(2, 0))

        # Left Column: Profile Information Card
        profile_card = tk.Frame(
            self,
            bg=config.COLORS["bg_card"],
            padx=25,
            pady=20,
            highlightbackground=config.COLORS["border"],
            highlightthickness=1
        )
        profile_card.grid(row=1, column=0, sticky="nsew", padx=(25, 12), pady=(0, 20))

        tk.Label(
            profile_card,
            text="👤 User Profile",
            font=config.FONTS["h2"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"]
        ).pack(anchor="w", pady=(0, 15))

        # Full Name
        tk.Label(profile_card, text="Full Name *", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(4, 2))
        self.name_var = tk.StringVar(value=self.user.name)
        self.name_entry = ttk.Entry(profile_card, textvariable=self.name_var, font=config.FONTS["body"])
        self.name_entry.pack(fill="x", pady=(0, 10))

        # Username (Disabled)
        tk.Label(profile_card, text="Username (Immutable)", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_muted"]).pack(anchor="w", pady=(4, 2))
        self.username_entry = ttk.Entry(profile_card, font=config.FONTS["body"])
        self.username_entry.insert(0, self.user.username)
        self.username_entry.configure(state="disabled")
        self.username_entry.pack(fill="x", pady=(0, 10))

        # Role (Disabled)
        tk.Label(profile_card, text="Account Role", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_muted"]).pack(anchor="w", pady=(4, 2))
        self.role_entry = ttk.Entry(profile_card, font=config.FONTS["body"])
        self.role_entry.insert(0, self.user.role)
        self.role_entry.configure(state="disabled")
        self.role_entry.pack(fill="x", pady=(0, 10))

        # Email
        tk.Label(profile_card, text="Email Address", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(4, 2))
        self.email_var = tk.StringVar(value=self.user.email or "")
        self.email_entry = ttk.Entry(profile_card, textvariable=self.email_var, font=config.FONTS["body"])
        self.email_entry.pack(fill="x", pady=(0, 10))

        if self.user.is_student:
            # Semester & Division
            sem_div_frame = tk.Frame(profile_card, bg=config.COLORS["bg_card"])
            sem_div_frame.pack(fill="x", pady=(0, 10))
            sem_div_frame.columnconfigure(0, weight=1)
            sem_div_frame.columnconfigure(1, weight=1)

            tk.Label(sem_div_frame, text="Semester", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=0, sticky="w")
            self.sem_var = tk.StringVar(value=self.user.semester or "Semester 4")
            self.sem_entry = ttk.Entry(sem_div_frame, textvariable=self.sem_var, font=config.FONTS["body"])
            self.sem_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

            tk.Label(sem_div_frame, text="Division", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).grid(row=0, column=1, sticky="w")
            self.div_var = tk.StringVar(value=self.user.division or "A")
            self.div_entry = ttk.Entry(sem_div_frame, textvariable=self.div_var, font=config.FONTS["body"])
            self.div_entry.grid(row=1, column=1, sticky="ew")

        # Save Profile Button
        save_profile_btn = tk.Button(
            profile_card,
            text="Save Profile Changes",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["primary"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self._handle_update_profile
        )
        save_profile_btn.pack(anchor="w", pady=(10, 0))

        # Right Column: Security (Change Password) & Firebase Config / System Info
        right_col = tk.Frame(self, bg=config.COLORS["bg_main"])
        right_col.grid(row=1, column=1, sticky="nsew", padx=(12, 25), pady=(0, 20))
        right_col.columnconfigure(0, weight=1)

        # Change Password Card
        pw_card = tk.Frame(
            right_col,
            bg=config.COLORS["bg_card"],
            padx=25,
            pady=16,
            highlightbackground=config.COLORS["border"],
            highlightthickness=1
        )
        pw_card.pack(fill="x", pady=(0, 15))

        tk.Label(
            pw_card,
            text="🔒 Change Password",
            font=config.FONTS["h2"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_card"]
        ).pack(anchor="w", pady=(0, 10))

        # Old Password
        tk.Label(pw_card, text="Current Password", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(2, 1))
        self.old_pw_var = tk.StringVar()
        self.old_pw_entry = ttk.Entry(pw_card, textvariable=self.old_pw_var, show="•", font=config.FONTS["body"])
        self.old_pw_entry.pack(fill="x", pady=(0, 8))

        # New Password
        tk.Label(pw_card, text="New Password (min. 4 chars)", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(2, 1))
        self.new_pw_var = tk.StringVar()
        self.new_pw_entry = ttk.Entry(pw_card, textvariable=self.new_pw_var, show="•", font=config.FONTS["body"])
        self.new_pw_entry.pack(fill="x", pady=(0, 8))

        # Confirm New Password
        tk.Label(pw_card, text="Confirm New Password", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(2, 1))
        self.confirm_pw_var = tk.StringVar()
        self.confirm_pw_entry = ttk.Entry(pw_card, textvariable=self.confirm_pw_var, show="•", font=config.FONTS["body"])
        self.confirm_pw_entry.pack(fill="x", pady=(0, 12))

        update_pw_btn = tk.Button(
            pw_card,
            text="Update Password",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["info"],
            fg="white",
            activebackground=config.COLORS["primary_hover"],
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=5,
            command=self._handle_change_password
        )
        update_pw_btn.pack(anchor="w")

        # Admin: Firebase Authentication Card
        if self.user.is_admin:
            fb_card = tk.Frame(
                right_col,
                bg=config.COLORS["bg_card"],
                padx=20,
                pady=16,
                highlightbackground=config.COLORS["border"],
                highlightthickness=1
            )
            fb_card.pack(fill="x", pady=(0, 15))

            tk.Label(
                fb_card,
                text="🔥 Firebase Cloud Authentication",
                font=config.FONTS["h2"],
                fg=config.COLORS["warning"],
                bg=config.COLORS["bg_card"]
            ).pack(anchor="w", pady=(0, 6))

            tk.Label(
                fb_card,
                text="Integrate Google Firebase Auth REST API for cloud token verification:",
                font=config.FONTS["small"],
                fg=config.COLORS["text_muted"],
                bg=config.COLORS["bg_card"],
                wraplength=350,
                justify="left"
            ).pack(anchor="w", pady=(0, 8))

            self.fb_enable_var = tk.BooleanVar(value=self.auth_service.firebase_enabled)
            fb_check = tk.Checkbutton(
                fb_card,
                text="Enable Firebase Cloud Authentication",
                variable=self.fb_enable_var,
                font=config.FONTS["small_bold"],
                bg=config.COLORS["bg_card"],
                fg=config.COLORS["text_dark"],
                activebackground=config.COLORS["bg_card"]
            )
            fb_check.pack(anchor="w", pady=(0, 6))

            tk.Label(fb_card, text="Firebase Web API Key", font=config.FONTS["small_bold"], bg=config.COLORS["bg_card"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(2, 1))
            self.fb_key_var = tk.StringVar(value=self.auth_service.firebase_api_key)
            self.fb_key_entry = ttk.Entry(fb_card, textvariable=self.fb_key_var, font=config.FONTS["body"])
            self.fb_key_entry.pack(fill="x", pady=(0, 10))

            save_fb_btn = tk.Button(
                fb_card,
                text="Save Firebase Config",
                font=config.FONTS["small_bold"],
                bg=config.COLORS["warning"],
                fg="white",
                activebackground="#b45309",
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=4,
                command=self._handle_save_firebase
            )
            save_fb_btn.pack(anchor="w")

        # System Info Card
        sys_card = tk.Frame(
            right_col,
            bg=config.COLORS["bg_card"],
            padx=20,
            pady=14,
            highlightbackground=config.COLORS["border"],
            highlightthickness=1
        )
        sys_card.pack(fill="x")

        tk.Label(
            sys_card,
            text="ℹ️ System Information",
            font=config.FONTS["small_bold"],
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_card"]
        ).pack(anchor="w", pady=(0, 6))

        sys_details = [
            ("Application", f"{config.APP_TITLE} (v{config.APP_VERSION})"),
            ("Operating Mode", "Offline-first with Firebase Cloud Auth Support"),
            ("Seeded Students", "100 Active Enrolled Students"),
            ("Database Path", config.DB_FILE),
        ]

        for label, val in sys_details:
            row = tk.Frame(sys_card, bg=config.COLORS["bg_card"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"{label}:", font=config.FONTS["small_bold"], fg=config.COLORS["text_dark"], bg=config.COLORS["bg_card"]).pack(side="left")
            tk.Label(row, text=f" {val}", font=config.FONTS["small"], fg=config.COLORS["text_muted"], bg=config.COLORS["bg_card"]).pack(side="left")

    def _handle_save_firebase(self) -> None:
        enabled = self.fb_enable_var.get()
        key = self.fb_key_var.get().strip()
        self.auth_service.set_firebase_config(enabled=enabled, api_key=key)
        messagebox.showinfo("Firebase Configuration", "Firebase authentication settings updated successfully.", parent=self)

    def _handle_update_profile(self) -> None:
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        sem = self.sem_var.get().strip() if hasattr(self, "sem_var") else None
        div = self.div_var.get().strip() if hasattr(self, "div_var") else None

        if not name:
            messagebox.showwarning("Validation Warning", "Name cannot be empty.", parent=self)
            return

        success, msg = self.auth_service.update_profile(
            user_id=self.user.id,
            name=name,
            email=email,
            semester=sem,
            division=div
        )
        if success:
            messagebox.showinfo("Success", msg, parent=self)
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _handle_change_password(self) -> None:
        old_pw = self.old_pw_var.get().strip()
        new_pw = self.new_pw_var.get().strip()
        confirm_pw = self.confirm_pw_var.get().strip()

        if not old_pw:
            messagebox.showwarning("Validation Warning", "Please enter your current password.", parent=self)
            return

        if not new_pw or len(new_pw) < 4:
            messagebox.showwarning("Validation Warning", "New password must be at least 4 characters long.", parent=self)
            return

        if new_pw != confirm_pw:
            messagebox.showwarning("Validation Warning", "New password and confirmation do not match.", parent=self)
            return

        success, msg = self.auth_service.change_password(self.user.id, old_pw, new_pw)
        if success:
            messagebox.showinfo("Success", msg, parent=self)
            self.old_pw_var.set("")
            self.new_pw_var.set("")
            self.confirm_pw_var.set("")
        else:
            messagebox.showerror("Password Change Failed", msg, parent=self)
