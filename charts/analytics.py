"""
Matplotlib chart generation module for College Tracker.
Generates live data visualization figures for Student and Administrator analytics with role-based completion workflow support.
Handles empty states gracefully with 'No sufficient data available for this chart.' (PRD Section 27, BR-10).
"""
import matplotlib
matplotlib.use("TkAgg")  # Ensure TkAgg backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Dict, List, Any, Optional
import config


# Apply clean minimalist chart styles
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "axes.edgecolor": config.COLORS["border_dark"],
    "axes.linewidth": 0.8,
    "grid.color": config.COLORS["border"],
    "grid.linestyle": "--",
    "grid.alpha": 0.6,
})


def create_empty_figure(title: str, message: str = "No sufficient data available for this chart.") -> Figure:
    """Create a standardized clean empty state figure."""
    fig = Figure(figsize=(5, 3.2), dpi=100, facecolor=config.COLORS["bg_card"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(config.COLORS["bg_card"])
    ax.text(
        0.5, 0.5, message,
        horizontalalignment='center',
        verticalalignment='center',
        fontsize=10,
        color=config.COLORS["text_muted"],
        fontweight="medium",
        transform=ax.transAxes
    )
    ax.set_title(title, fontsize=11, fontweight="bold", color=config.COLORS["text_dark"], pad=12)
    ax.axis("off")
    fig.tight_layout()
    return fig


def plot_task_status_distribution(metrics: Dict[str, Any], title: str = "Task Status Distribution") -> Figure:
    """
    Chart 1: Donut/Pie chart of task status distribution:
    Approved/Completed, Submitted (Under Review), Needs Resubmission, In Progress, Pending, Overdue.
    """
    completed = metrics.get("completed", 0)
    submitted = metrics.get("submitted", 0)
    needs_resubmission = metrics.get("needs_resubmission", 0)
    pending = metrics.get("pending", 0)
    in_progress = metrics.get("in_progress", 0)
    overdue = metrics.get("overdue", 0)

    total = completed + submitted + needs_resubmission + pending + in_progress
    if total == 0:
        return create_empty_figure(title)

    # Overdue tasks are deducted from pending/in_progress/resubmission to avoid visual slice duplication
    active_pending = max(0, pending - overdue)
    active_in_progress = in_progress

    labels = []
    sizes = []
    colors = []

    if completed > 0:
        labels.append(f"Approved ({completed})")
        sizes.append(completed)
        colors.append(config.COLORS["success"])

    if submitted > 0:
        labels.append(f"Submitted ({submitted})")
        sizes.append(submitted)
        colors.append(config.COLORS["submitted"])

    if needs_resubmission > 0:
        labels.append(f"Resubmit ({needs_resubmission})")
        sizes.append(needs_resubmission)
        colors.append(config.COLORS["resubmission"])

    if overdue > 0:
        labels.append(f"Overdue ({overdue})")
        sizes.append(overdue)
        colors.append(config.COLORS["danger"])

    if active_in_progress > 0:
        labels.append(f"In Progress ({active_in_progress})")
        sizes.append(active_in_progress)
        colors.append(config.COLORS["info"])

    if active_pending > 0:
        labels.append(f"Pending ({active_pending})")
        sizes.append(active_pending)
        colors.append(config.COLORS["pending"])

    if not sizes or sum(sizes) == 0:
        return create_empty_figure(title)

    fig = Figure(figsize=(5, 3.2), dpi=100, facecolor=config.COLORS["bg_card"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(config.COLORS["bg_card"])

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.0f%%",
        startangle=140,
        colors=colors,
        textprops=dict(color=config.COLORS["text_dark"], fontsize=9),
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)  # Donut chart style
    )

    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(8)
        autotext.set_weight("bold")

    ax.set_title(title, fontsize=11, fontweight="bold", color=config.COLORS["text_dark"], pad=10)
    fig.tight_layout()
    return fig


def plot_subject_task_counts(workloads: List[Dict[str, Any]], title: str = "Subject Task Workload") -> Figure:
    """
    Chart 2: Bar chart showing total number of tasks per subject.
    """
    valid_data = [w for w in workloads if w["total_tasks"] > 0]
    if not valid_data:
        return create_empty_figure(title)

    subjects = [w["subject_name"] for w in valid_data]
    counts = [w["total_tasks"] for w in valid_data]

    # Truncate subject names if too long
    display_names = [s if len(s) <= 15 else s[:13] + ".." for s in subjects]

    fig = Figure(figsize=(5, 3.2), dpi=100, facecolor=config.COLORS["bg_card"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(config.COLORS["bg_card"])

    bars = ax.bar(
        display_names,
        counts,
        color=config.COLORS["primary"],
        width=0.5,
        edgecolor=config.COLORS["primary_hover"],
        linewidth=1
    )

    # Add count labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{int(height)}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center", va="bottom",
            fontsize=9, fontweight="bold",
            color=config.COLORS["text_dark"]
        )

    ax.set_title(title, fontsize=11, fontweight="bold", color=config.COLORS["text_dark"], pad=10)
    ax.set_ylabel("Total Tasks", fontsize=9, color=config.COLORS["text_muted"])
    ax.tick_params(axis="x", labelrotation=15, labelsize=8, colors=config.COLORS["text_dark"])
    ax.tick_params(axis="y", labelsize=8, colors=config.COLORS["text_muted"])
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    # Set y limit with padding
    max_count = max(counts) if counts else 5
    ax.set_ylim(0, max_count + max(1, int(max_count * 0.25)))

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return fig


def plot_subject_completion_rates(workloads: List[Dict[str, Any]], title: str = "Subject Completion Rate (%)") -> Figure:
    """
    Chart 3: Horizontal Bar chart showing completion rate % per subject:
    (Completed/Approved Tasks / Total Tasks) * 100
    """
    valid_data = [w for w in workloads if w["total_tasks"] > 0]
    if not valid_data:
        return create_empty_figure(title)

    subjects = [w["subject_name"] for w in valid_data]
    rates = [w["completion_rate"] for w in valid_data]
    display_names = [s if len(s) <= 16 else s[:14] + ".." for s in subjects]

    fig = Figure(figsize=(5, 3.2), dpi=100, facecolor=config.COLORS["bg_card"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(config.COLORS["bg_card"])

    # Colors depending on rate: Green if >= 75%, Amber if >= 40%, Sky/Primary otherwise
    bar_colors = [
        config.COLORS["success"] if r >= 75 else (config.COLORS["warning"] if r >= 40 else config.COLORS["info"])
        for r in rates
    ]

    y_pos = range(len(display_names))
    bars = ax.barh(
        y_pos,
        rates,
        color=bar_colors,
        height=0.45,
        edgecolor="none"
    )

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(display_names, fontsize=8, color=config.COLORS["text_dark"])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Completion Rate (%)", fontsize=9, color=config.COLORS["text_muted"])
    ax.set_title(title, fontsize=11, fontweight="bold", color=config.COLORS["text_dark"], pad=10)
    ax.xaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    for bar in bars:
        width = bar.get_width()
        ax.annotate(
            f"{width:.0f}%",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            ha="left", va="center",
            fontsize=8, fontweight="bold",
            color=config.COLORS["text_dark"]
        )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


def plot_student_submission_rates(student_rates: List[Dict[str, Any]], title: str = "Student Approved Progress (%)") -> Figure:
    """
    Chart 4 (Admin): Horizontal bar chart showing verified completion rates across students.
    """
    valid_data = [s for s in student_rates if s["total_tasks"] > 0]
    if not valid_data:
        return create_empty_figure(title)

    students = [s["name"] for s in valid_data]
    rates = [s["completion_rate"] for s in valid_data]
    display_names = [s if len(s) <= 14 else s[:12] + ".." for s in students]

    fig = Figure(figsize=(5, 3.2), dpi=100, facecolor=config.COLORS["bg_card"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(config.COLORS["bg_card"])

    y_pos = range(len(display_names))
    bars = ax.barh(
        y_pos,
        rates,
        color=config.COLORS["primary"],
        height=0.45
    )

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(display_names, fontsize=8, color=config.COLORS["text_dark"])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Approval Rate (%)", fontsize=9, color=config.COLORS["text_muted"])
    ax.set_title(title, fontsize=11, fontweight="bold", color=config.COLORS["text_dark"], pad=10)
    ax.xaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    for bar in bars:
        width = bar.get_width()
        ax.annotate(
            f"{width:.0f}%",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            ha="left", va="center",
            fontsize=8, fontweight="bold",
            color=config.COLORS["text_dark"]
        )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig
