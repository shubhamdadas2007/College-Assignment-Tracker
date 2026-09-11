"""
Web Application entrypoint for College Assignment & Practical Submission Tracker (v4.0).
Provides a live, interactive web GUI powered by Streamlit and SQLite.
Deployable with 1 click to Streamlit Cloud for a public web URL.
"""
import streamlit as st
import os
import pandas as pd
from datetime import datetime, date
import config
from database import init_db
from models import User, Task
from auth_service import AuthService
from task_service import TaskService
from subject_service import SubjectService
from student_service import StudentService
from deadline_service import format_display_date, get_days_remaining
from charts.analytics import (
    plot_task_status_distribution,
    plot_subject_task_counts,
    plot_subject_completion_rates,
    plot_student_submission_rates
)

# Page configuration
st.set_page_config(
    page_title="College Submission Tracker v4.0",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db(config.DB_FILE, seed_demo=True)

# Initialize services
auth_service = AuthService(config.DB_FILE)
task_service = TaskService(config.DB_FILE)
subject_service = SubjectService(config.DB_FILE)
student_service = StudentService(config.DB_FILE)

# Session State for Authentication
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# Custom CSS styling for modern UI
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-submitted {
        background-color: #e0f2fe;
        color: #0284c7;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 4px;
    }
    .badge-resubmit {
        background-color: #ffedd5;
        color: #ea580c;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 4px;
    }
    .badge-completed {
        background-color: #dcfce7;
        color: #16a34a;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 4px;
    }
    .badge-pending {
        background-color: #f3e8ff;
        color: #9333ea;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# LOGIN SCREEN
# =====================================================================
if not st.session_state.logged_in_user:
    st.title("🎓 College Assignment & Practical Submission Tracker")
    st.caption("v4.0 • Academic Submission & Role-Based Verification System")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔑 Sign In")
        role = st.selectbox("Role", ["Student", "Administrator"])
        username = st.text_input("Username or Email", placeholder="e.g. rahul or admin")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        if st.button("Log In", type="primary", use_container_width=True):
            ok, user, msg = auth_service.authenticate(username, password, role)
            if ok:
                st.session_state.logged_in_user = user
                st.rerun()
            else:
                st.error(msg)

    with col2:
        st.subheader("⚡ Quick Demo Access")
        st.write("Click any button below to instantly explore the live portal:")
        
        if st.button("🧑‍🎓 Login as Student (Rahul)", use_container_width=True):
            ok, user, _ = auth_service.authenticate("rahul", "student123", "Student")
            if ok:
                st.session_state.logged_in_user = user
                st.rerun()

        if st.button("👩‍🎓 Login as Student (Priya)", use_container_width=True):
            ok, user, _ = auth_service.authenticate("priya", "student123", "Student")
            if ok:
                st.session_state.logged_in_user = user
                st.rerun()

        if st.button("🏛️ Login as Administrator / Teacher", type="primary", use_container_width=True):
            ok, user, _ = auth_service.authenticate("admin", "admin123", "Administrator")
            if ok:
                st.session_state.logged_in_user = user
                st.rerun()

    st.stop()


# =====================================================================
# AUTHENTICATED PORTAL
# =====================================================================
user: User = st.session_state.logged_in_user

# Sidebar
st.sidebar.title("🎓 College Tracker")
st.sidebar.markdown(f"**Logged in as:** {user.name}")
st.sidebar.caption(f"Role: **{user.role}**" + (f" • {user.semester}" if user.semester else ""))

if user.is_student:
    nav_options = ["🏠 My Dashboard", "📚 My Tasks", "🔬 Practicals & Labs", "📊 Academic Analytics"]
else:
    nav_options = ["🏛️ Admin Dashboard", "📤 Submissions & Tasks", "🔬 Practicals Overview", "📊 College Analytics", "👥 Manage Students", "📖 Manage Subjects"]

selected_page = st.sidebar.radio("Navigation", nav_options)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in_user = None
    st.rerun()


# =====================================================================
# STUDENT DASHBOARD
# =====================================================================
if selected_page == "🏠 My Dashboard":
    st.title(f"Welcome back, {user.name}! 👋")
    st.caption(f"Student Portal • {user.semester or 'Semester 4'} • Division {user.division or 'A'}")

    metrics = task_service.get_dashboard_metrics(student_id=user.id)
    
    # KPI Row
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("📚 Total Tasks", metrics["total"])
    c2.metric("⏳ Pending", metrics["pending"])
    c3.metric("⚙️ In Progress", metrics["in_progress"])
    c4.metric("📤 Submitted", metrics["submitted"])
    c5.metric("⚠️ Needs Resubmit", metrics["needs_resubmission"])
    c6.metric("✅ Approved", metrics["completed"])
    c7.metric("🚨 Overdue", metrics["overdue"])

    st.divider()

    # Active deadlines
    st.subheader("⏰ Active Academic Deadlines")
    tasks = task_service.get_tasks(student_id=user.id, sort_by="due_date_asc")
    active_tasks = [t for t in tasks if t.status != "Completed"]

    if not active_tasks:
        st.success("🎉 All tasks have been verified and completed!")
    else:
        for t in active_tasks[:6]:
            with st.container():
                cols = st.columns([3, 2, 2, 2, 2])
                cols[0].markdown(f"**{t.title}** ({t.task_type})")
                cols[1].write(f"📖 {t.subject_name}")
                
                # Status Badge
                if t.status == "Submitted":
                    cols[2].markdown('<span class="badge-submitted">📤 Awaiting Review</span>', unsafe_allow_html=True)
                elif t.status == "Needs Resubmission":
                    cols[2].markdown('<span class="badge-resubmit">⚠️ Needs Resubmit</span>', unsafe_allow_html=True)
                elif t.status == "In Progress":
                    cols[2].write("⚙️ In Progress")
                else:
                    cols[2].write("⏳ Pending")

                cols[3].write(f"📅 Due: {format_display_date(t.due_date)}")

                # Student Submission Action
                if t.status in ("Pending", "In Progress", "Needs Resubmission"):
                    if cols[4].button("📤 Submit", key=f"dash_sub_{t.id}"):
                        ok, msg = task_service.update_task_status(t.id, "Submitted", acting_user=user)
                        if ok:
                            st.toast("Submitted for teacher verification! 📤")
                            st.rerun()
                else:
                    cols[4].write("Under Review")
                st.divider()


# =====================================================================
# ADMIN DASHBOARD
# =====================================================================
elif selected_page == "🏛️ Admin Dashboard":
    st.title("🏛️ Administrator & Teacher Portal")
    st.caption("Institution-Level Oversight & Academic Verification")

    metrics = task_service.get_dashboard_metrics()
    students = student_service.get_all_students()

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("👥 Students", len(students))
    c2.metric("📚 Total Tasks", metrics["total"])
    c3.metric("📤 Awaiting Review", metrics["submitted"])
    c4.metric("⚠️ Needs Resubmit", metrics["needs_resubmission"])
    c5.metric("✅ Approved", metrics["completed"])
    c6.metric("🚨 Overdue", metrics["overdue"])
    c7.metric("⏰ Due Today", metrics["due_today"])

    st.divider()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("🚨 Students with Overdue Tasks")
        overdue_students = task_service.get_overdue_students()
        if not overdue_students:
            st.success("No overdue submissions! ✨")
        else:
            df_ov = pd.DataFrame(overdue_students)[["name", "username", "semester", "division", "overdue_count"]]
            df_ov.columns = ["Name", "Username", "Semester", "Div", "Overdue Tasks"]
            st.dataframe(df_ov, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("📚 Subject Workload & Progress")
        workloads = task_service.get_subject_workload()
        if workloads:
            df_wl = pd.DataFrame(workloads)[["subject_name", "total_tasks", "completed_tasks", "submitted_tasks", "completion_rate"]]
            df_wl.columns = ["Subject", "Total", "Approved", "Submitted", "Done %"]
            st.dataframe(df_wl, use_container_width=True, hide_index=True)


# =====================================================================
# TASKS & PRACTICALS VIEW
# =====================================================================
elif selected_page in ("📚 My Tasks", "🔬 Practicals & Labs", "📤 Submissions & Tasks", "🔬 Practicals Overview"):
    is_practicals = "Practicals" in selected_page
    st.title("🔬 Practicals & Lab Submissions" if is_practicals else "📚 Academic Tasks & Submissions")
    
    # Filter Toolbar
    fc1, fc2, fc3, fc4 = st.columns(4)
    search_q = fc1.text_input("🔍 Search", placeholder="Title, student, subject...")
    
    subjects = subject_service.get_all_subjects()
    sub_map = {s.name: s.id for s in subjects}
    selected_sub = fc2.selectbox("Subject", ["All Subjects"] + list(sub_map.keys()))
    
    status_filter = fc3.selectbox("Status", ["All Statuses"] + config.TASK_STATUSES)
    priority_filter = fc4.selectbox("Priority", ["All Priorities"] + config.TASK_PRIORITIES)

    # Add Task Expander
    with st.expander("➕ Add New " + ("Practical" if is_practicals else "Task")):
        with st.form("add_task_form"):
            t_title = st.text_input("Task Title *")
            t_type = "Practical" if is_practicals else st.selectbox("Type", config.TASK_TYPES)
            t_sub = st.selectbox("Subject", list(sub_map.keys()))
            
            if user.is_admin:
                all_st = student_service.get_all_students()
                st_map = {f"{s.name} ({s.username})": s.id for s in all_st}
                t_student = st.selectbox("Assign to Student", list(st_map.keys()))
                assigned_st_id = st_map[t_student]
            else:
                assigned_st_id = user.id

            t_due = st.date_input("Due Date", min_value=datetime.today())
            t_prio = st.selectbox("Priority", config.TASK_PRIORITIES, index=1)
            t_mode = st.selectbox("Submission Mode", config.SUBMISSION_MODES)
            t_desc = st.text_area("Description")

            if st.form_submit_button("Create Task", type="primary"):
                if not t_title.strip():
                    st.error("Title is required.")
                else:
                    ok, tid, msg = task_service.create_task(
                        student_id=assigned_st_id,
                        subject_id=sub_map[t_sub],
                        title=t_title,
                        task_type=t_type,
                        due_date_str=t_due.strftime("%Y-%m-%d"),
                        priority=t_prio,
                        status="Pending",
                        description=t_desc,
                        submission_mode=t_mode,
                        acting_user=user
                    )
                    if ok:
                        st.success("Task created successfully!")
                        st.rerun()
                    else:
                        st.error(msg)

    # Query tasks
    student_id = user.id if user.is_student else None
    task_type = "Practical" if is_practicals else None
    sub_id = sub_map.get(selected_sub)
    status_val = None if status_filter == "All Statuses" else status_filter
    prio_val = None if priority_filter == "All Priorities" else priority_filter

    tasks = task_service.get_tasks(
        student_id=student_id,
        task_type=task_type,
        status=status_val,
        subject_id=sub_id,
        priority=prio_val,
        search_query=search_q,
        sort_by="due_date_asc"
    )

    st.write(f"Showing **{len(tasks)}** task(s):")

    for t in tasks:
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 3])
            c1.markdown(f"**{t.title}** ({t.task_type})")
            if user.is_admin:
                c1.caption(f"Student: {t.student_name} ({t.student_username})")

            c2.write(f"📖 {t.subject_name}")
            
            # Status Badge
            if t.status == "Completed":
                c3.markdown('<span class="badge-completed">✅ Approved</span>', unsafe_allow_html=True)
            elif t.status == "Submitted":
                c3.markdown('<span class="badge-submitted">📤 Submitted</span>', unsafe_allow_html=True)
            elif t.status == "Needs Resubmission":
                c3.markdown('<span class="badge-resubmit">⚠️ Needs Resubmit</span>', unsafe_allow_html=True)
            elif t.status == "In Progress":
                c3.write("⚙️ In Progress")
            else:
                c3.markdown('<span class="badge-pending">⏳ Pending</span>', unsafe_allow_html=True)

            c4.write(f"📅 {format_display_date(t.due_date)}")

            # Actions based on role
            if user.is_student:
                if t.status in ("Pending", "In Progress", "Needs Resubmission"):
                    if c5.button("📤 Submit for Verification", key=f"sub_btn_{t.id}"):
                        ok, msg = task_service.update_task_status(t.id, "Submitted", acting_user=user)
                        if ok:
                            st.toast("Submitted for teacher review! 📤")
                            st.rerun()
                elif t.status == "Submitted":
                    c5.caption("⏳ Awaiting Teacher Review")
                else:
                    c5.caption("✅ Approved by Teacher")
            else:
                # Admin actions
                btn_cols = c5.columns(2)
                if t.status != "Completed":
                    if btn_cols[0].button("✓ Approve", key=f"app_btn_{t.id}", type="primary"):
                        ok, msg = task_service.update_task_status(t.id, "Completed", acting_user=user)
                        if ok:
                            st.toast("Task approved and completed! ✅")
                            st.rerun()
                if t.status == "Submitted":
                    if btn_cols[1].button("↻ Reject", key=f"rej_btn_{t.id}"):
                        ok, msg = task_service.update_task_status(t.id, "Needs Resubmission", acting_user=user)
                        if ok:
                            st.toast("Resubmission requested ↻")
                            st.rerun()

            st.divider()


# =====================================================================
# ANALYTICS VIEW
# =====================================================================
elif selected_page in ("📊 Academic Analytics", "📊 College Analytics"):
    st.title("📊 Visual Academic Analytics")
    st.caption("Live statistical insights and submission distribution")

    student_id = user.id if user.is_student else None
    metrics = task_service.get_dashboard_metrics(student_id=student_id)
    workloads = task_service.get_subject_workload(student_id=student_id)

    col1, col2 = st.columns(2)
    with col1:
        fig1 = plot_task_status_distribution(metrics, "Task Status Breakdown")
        st.pyplot(fig1)

    with col2:
        fig2 = plot_subject_task_counts(workloads, "Tasks per Subject")
        st.pyplot(fig2)

    col3, col4 = st.columns(2)
    with col3:
        fig3 = plot_subject_completion_rates(workloads, "Subject Approval Rate (%)")
        st.pyplot(fig3)

    with col4:
        if user.is_admin:
            rates = task_service.get_student_submission_rates()
            fig4 = plot_student_submission_rates(rates, "Student Progress (%)")
            st.pyplot(fig4)
        else:
            st.subheader("🎯 Academic Summary")
            total = metrics.get("total", 0)
            completed = metrics.get("completed", 0)
            submitted = metrics.get("submitted", 0)
            rate = round((completed / total * 100), 1) if total > 0 else 0.0
            st.metric("Overall Approval Rate", f"{rate}%")
            st.info(f"You have **{completed}** approved completions and **{submitted}** tasks under review out of **{total}** total tasks.")


# =====================================================================
# MANAGE STUDENTS & SUBJECTS (ADMIN)
# =====================================================================
elif selected_page == "👥 Manage Students":
    st.title("👥 Student Directory (100 Active Students)")
    all_students = student_service.get_all_students()
    df_st = pd.DataFrame(all_students)[["id", "name", "username", "email", "semester", "division"]]
    df_st.columns = ["ID", "Name", "Username", "Email", "Semester", "Division"]
    st.dataframe(df_st, use_container_width=True, hide_index=True)

elif selected_page == "📖 Manage Subjects":
    st.title("📖 Academic Curriculum Subjects")
    all_subjects = subject_service.get_all_subjects()
    df_sub = pd.DataFrame(all_subjects)[["id", "name", "semester"]]
    df_sub.columns = ["ID", "Subject Name", "Semester"]
    st.dataframe(df_sub, use_container_width=True, hide_index=True)
