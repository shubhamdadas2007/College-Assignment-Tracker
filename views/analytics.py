"""
Analytics view for College Tracker embedding live Matplotlib charts in Tkinter (PRD Section 25, 26, 27).
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import config
from models import User
from task_service import TaskService
from charts.analytics import (
    plot_task_status_distribution,
    plot_subject_task_counts,
    plot_subject_completion_rates,
    plot_student_submission_rates
)


class AnalyticsView(ttk.Frame):
    """Embeds Matplotlib charts dynamically based on Student or Admin role."""
    def __init__(self, parent: tk.Widget, user: User, task_service: TaskService):
        super().__init__(parent, style="App.TFrame")
        self.user = user
        self.task_service = task_service
        self.canvas_widgets = []

        self._create_widgets()
        self.refresh_data()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Header Bar
        header_frame = tk.Frame(self, bg=config.COLORS["bg_main"])
        header_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))

        title_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        title_box.pack(side="left")

        page_title = "📊 PERSONAL ACADEMIC ANALYTICS" if self.user.is_student else "📈 COLLEGE-WIDE ACADEMIC ANALYTICS"
        tk.Label(
            title_box,
            text=page_title,
            font=config.FONTS["title"],
            fg=config.COLORS["text_dark"],
            bg=config.COLORS["bg_main"]
        ).pack(anchor="w")

        sub_text = (
            "Visual insights on your task completion rates, verification distribution, and subject workloads"
            if self.user.is_student else
            "Institutional overview of student completion rates, verification backlog, and subject workload"
        )
        tk.Label(
            title_box,
            text=sub_text,
            font=config.FONTS["body"],
            fg=config.COLORS["text_muted"],
            bg=config.COLORS["bg_main"]
        ).pack(anchor="w", pady=(2, 0))

        # Refresh Action on Right
        action_box = tk.Frame(header_frame, bg=config.COLORS["bg_main"])
        action_box.pack(side="right")

        refresh_btn = tk.Button(
            action_box,
            text="🔄 Refresh Charts",
            font=config.FONTS["small_bold"],
            bg=config.COLORS["bg_card"],
            fg=config.COLORS["text_dark"],
            relief="flat",
            highlightbackground=config.COLORS["border"],
            highlightthickness=1,
            cursor="hand2",
            padx=10,
            pady=6,
            command=self.refresh_data
        )
        refresh_btn.pack(side="left")

        # Scrollable container for charts grid
        self.scroll_canvas = tk.Canvas(self, bg=config.COLORS["bg_main"], highlightthickness=0)
        self.scroll_bar = ttk.Scrollbar(self, orient="vertical", command=self.scroll_canvas.yview)
        
        self.chart_container = tk.Frame(self.scroll_canvas, bg=config.COLORS["bg_main"])
        self.chart_container.bind(
            "<Configure>",
            lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        )

        self.canvas_window = self.scroll_canvas.create_window((0, 0), window=self.chart_container, anchor="nw")
        self.scroll_canvas.configure(yscrollcommand=self.scroll_bar.set)

        self.scroll_canvas.grid(row=1, column=0, sticky="nsew", padx=25, pady=(0, 20))
        self.scroll_bar.grid(row=1, column=1, sticky="ns", pady=(0, 20))

        # Resize event to stretch canvas window
        self.bind("<Configure>", self._on_window_resize)

    def _on_window_resize(self, event) -> None:
        canvas_width = event.width - 60
        self.scroll_canvas.itemconfig(self.canvas_window, width=max(canvas_width, 700))

    def _clear_charts(self) -> None:
        for cw in self.canvas_widgets:
            try:
                cw.get_tk_widget().destroy()
            except Exception:
                pass
        self.canvas_widgets.clear()

        for child in self.chart_container.winfo_children():
            child.destroy()

    def refresh_data(self) -> None:
        """Fetch fresh SQLite data and render Matplotlib charts."""
        self._clear_charts()

        # Grid configuration
        self.chart_container.columnconfigure(0, weight=1)
        self.chart_container.columnconfigure(1, weight=1)

        student_id = self.user.id if self.user.is_student else None
        metrics = self.task_service.get_dashboard_metrics(student_id=student_id)
        workloads = self.task_service.get_subject_workload(student_id=student_id)

        # 1. Chart 1: Task Status Distribution (Donut Chart)
        fig_status = plot_task_status_distribution(
            metrics=metrics,
            title="Personal Task Status Distribution" if self.user.is_student else "Overall Task Status Distribution"
        )
        self._embed_figure(fig_status, row=0, col=0)

        # 2. Chart 2: Subject Task Workload
        fig_workload = plot_subject_task_counts(
            workloads=workloads,
            title="Tasks per Subject" if self.user.is_student else "College Subject Task Counts"
        )
        self._embed_figure(fig_workload, row=0, col=1)

        # 3. Chart 3: Subject Completion Rate (%)
        fig_completion = plot_subject_completion_rates(
            workloads=workloads,
            title="Subject Approved Completion Rate (%)"
        )
        self._embed_figure(fig_completion, row=1, col=0)

        # 4. Chart 4 (Admin): Student Approved Progress (%)
        if self.user.is_admin:
            student_rates = self.task_service.get_student_submission_rates()
            fig_student = plot_student_submission_rates(
                student_rates=student_rates,
                title="Student Approved Progress (%)"
            )
            self._embed_figure(fig_student, row=1, col=1)
        else:
            # For Student: Show an Informational Card in the 4th slot
            info_card = tk.Frame(
                self.chart_container,
                bg=config.COLORS["bg_card"],
                padx=20,
                pady=20,
                highlightbackground=config.COLORS["border"],
                highlightthickness=1
            )
            info_card.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)

            tk.Label(
                info_card,
                text="🎯 Verification & Progress Summary",
                font=config.FONTS["h2"],
                fg=config.COLORS["text_dark"],
                bg=config.COLORS["bg_card"]
            ).pack(anchor="w", pady=(0, 10))

            total = metrics.get("total", 0)
            completed = metrics.get("completed", 0)
            submitted = metrics.get("submitted", 0)
            needs_resub = metrics.get("needs_resubmission", 0)
            overall_rate = round((completed / total * 100), 1) if total > 0 else 0.0

            tk.Label(
                info_card,
                text=f"Approved Completion: {overall_rate}%",
                font=("Segoe UI", 16, "bold"),
                fg=config.COLORS["primary"],
                bg=config.COLORS["bg_card"]
            ).pack(anchor="w", pady=(5, 10))

            summary_msg = (
                f"• Approved by Teacher: {completed} / {total}\n"
                f"• Awaiting Verification: {submitted}\n"
                f"• Needs Resubmission: {needs_resub}\n\n"
                "Remember to submit your practicals and assignments on time so teachers can review and sign off!"
            )
            tk.Label(
                info_card,
                text=summary_msg,
                font=config.FONTS["body"],
                fg=config.COLORS["text_muted"],
                bg=config.COLORS["bg_card"],
                wraplength=300,
                justify="left"
            ).pack(anchor="w")

    def _embed_figure(self, figure, row: int, col: int) -> None:
        """Embed a Matplotlib Figure inside a rounded card in the grid."""
        card_frame = tk.Frame(
            self.chart_container,
            bg=config.COLORS["bg_card"],
            padx=10,
            pady=10,
            highlightbackground=config.COLORS["border"],
            highlightthickness=1
        )
        card_frame.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

        canvas = FigureCanvasTkAgg(figure, master=card_frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)

        self.canvas_widgets.append(canvas)
