
import os
from datetime import date, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)

app = Flask(__name__)

app.secret_key = os.environ.get(
    "TASKFLOW_SECRET_KEY",
    "change-this-secret-key-for-local-demo"
)

# ----------------------------------
# PRIVATE ADMIN CONFIGURATION
# ----------------------------------

ADMIN_EMAIL = os.environ.get("TASKFLOW_ADMIN_EMAIL", "admin@123")
ADMIN_PASSWORD = os.environ.get("TASKFLOW_ADMIN_PASSWORD", "1234")

# ----------------------------------
# EMPTY DATA
# ----------------------------------

users = []
tasks = []


# ----------------------------------
# HELPER FUNCTIONS
# ----------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id") and session.get("role") != "admin":
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def user_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "user":
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def is_overdue(task):
    return (
        bool(task.get("due_date"))
        and task["status"] != "Completed"
        and task["due_date"] < date.today().isoformat()
    )


def task_stats(task_list):
    return {
        "total": len(task_list),
        "completed": sum(t["status"] == "Completed" for t in task_list),
        "pending": sum(t["status"] == "Pending" for t in task_list),
        "in_progress": sum(t["status"] == "In Progress" for t in task_list),
        "overdue": sum(is_overdue(t) for t in task_list)
    }


def get_user_tasks():
    current_user_id = session.get("user_id")

    return [
        task for task in tasks
        if task.get("user_id") == current_user_id
    ]


def get_user_by_id(user_id):
    return next((u for u in users if u["id"] == user_id), None)


def get_task_by_id(task_id):
    return next((t for t in tasks if t["id"] == task_id), None)


def next_id(items):
    return max([item["id"] for item in items], default=0) + 1


# Set task status and record its completion date.
def set_task_status(task, new_status):

    old_status = task.get("status")

    task["status"] = new_status

    if new_status == "Completed" and old_status != "Completed":
        task["completed_at"] = date.today().isoformat()

    elif new_status != "Completed":
        task["completed_at"] = None


# Prepare last 7 days of productivity data.
def get_productivity_data():

    today = date.today()

    graph_dates = [
        today - timedelta(days=i)
        for i in range(6, -1, -1)
    ]

    labels = [day.strftime("%d %b") for day in graph_dates]

    datasets = []

    colors = [
        "#6956e8",
        "#16a085",
        "#f39c12",
        "#e056a0",
        "#3498db",
        "#e74c3c",
        "#8e44ad"
    ]

    for index, user in enumerate(users):

        daily_counts = []

        for graph_day in graph_dates:

            count = sum(
                1 for task in tasks
                if task.get("user_id") == user["id"]
                and task.get("status") == "Completed"
                and task.get("completed_at") == graph_day.isoformat()
            )

            daily_counts.append(count)

        datasets.append({
            "label": user["name"],
            "data": daily_counts,
            "borderColor": colors[index % len(colors)],
            "backgroundColor": colors[index % len(colors)],
            "tension": 0.35,
            "fill": False
        })

    return labels, datasets


@app.context_processor
def inject_overdue_count():

    if session.get("role") == "admin":
        count = sum(is_overdue(t) for t in tasks)

    elif session.get("role") == "user":
        count = sum(is_overdue(t) for t in get_user_tasks())

    else:
        count = 0

    return {"overdue_count": count}


# ----------------------------------
# HOME / DASHBOARD
# ----------------------------------

@app.route("/")
@login_required
def dashboard():

    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    user_tasks = get_user_tasks()

    return render_template(
        "dashboard.html",
        tasks=user_tasks,
        stats=task_stats(user_tasks),
        is_overdue=is_overdue
    )


# ----------------------------------
# USER TASK MANAGEMENT
# ----------------------------------

@app.route("/tasks")
@user_required
def task_list():

    user_tasks = get_user_tasks()

    return render_template(
        "tasks.html",
        tasks=user_tasks,
        is_overdue=is_overdue
    )


# ADD USER TASK

@app.route("/add-task", methods=["POST"])
@user_required
def add_task():

    title = request.form.get("title", "").strip()

    if not title:
        flash("Please enter a task title.")
        return redirect(url_for("task_list"))

    priority = request.form.get("priority", "Medium")

    if priority not in ["Low", "Medium", "High"]:
        priority = "Medium"

    tasks.append({
        "id": next_id(tasks),
        "title": title,
        "description": request.form.get("description", "").strip(),
        "priority": priority,
        "status": "Pending",
        "due_date": request.form.get("due_date", ""),
        "completed_at": None,
        "user": session.get("name"),
        "user_id": session.get("user_id")
    })

    flash("Task added successfully.")
    return redirect(url_for("task_list"))


# EDIT USER TASK

@app.route("/edit-task/<int:task_id>", methods=["POST"])
@user_required
def edit_task(task_id):

    task = get_task_by_id(task_id)

    if not task or task.get("user_id") != session.get("user_id"):
        flash("Task not found or access denied.")
        return redirect(url_for("task_list"))

    title = request.form.get("title", "").strip()

    if not title:
        flash("Task title cannot be empty.")
        return redirect(url_for("task_list"))

    priority = request.form.get("priority", "Medium")

    if priority not in ["Low", "Medium", "High"]:
        priority = "Medium"

    task["title"] = title
    task["description"] = request.form.get("description", "").strip()
    task["priority"] = priority
    task["due_date"] = request.form.get("due_date", "")

    flash("Task updated successfully.")
    return redirect(url_for("task_list"))


# COMPLETE / UNDO USER TASK

@app.route("/complete/<int:task_id>", methods=["POST"])
@user_required
def complete_task(task_id):

    task = get_task_by_id(task_id)

    if task and task.get("user_id") == session.get("user_id"):

        new_status = (
            "Pending" if task["status"] == "Completed"
            else "Completed"
        )

        set_task_status(task, new_status)

        flash("Task status updated.")

    return redirect(url_for("task_list"))


# DELETE USER TASK

@app.route("/delete/<int:task_id>", methods=["POST"])
@user_required
def delete_task(task_id):

    global tasks

    tasks = [
        task for task in tasks
        if not (
            task["id"] == task_id
            and task.get("user_id") == session.get("user_id")
        )
    ]

    flash("Task deleted.")
    return redirect(url_for("task_list"))


# ----------------------------------
# ADMIN DASHBOARD
# ----------------------------------

@app.route("/admin")
@admin_required
def admin_dashboard():

    stats = task_stats(tasks)
    total = max(stats["total"], 1)

    chart = [
        {
            "label": "Completed",
            "value": stats["completed"],
            "percent": round(stats["completed"] / total * 100),
            "class_name": "bar-completed"
        },
        {
            "label": "Pending",
            "value": stats["pending"],
            "percent": round(stats["pending"] / total * 100),
            "class_name": "bar-pending"
        },
        {
            "label": "In progress",
            "value": stats["in_progress"],
            "percent": round(stats["in_progress"] / total * 100),
            "class_name": "bar-progress"
        },
        {
            "label": "Overdue",
            "value": stats["overdue"],
            "percent": round(stats["overdue"] / total * 100),
            "class_name": "bar-overdue"
        }
    ]

    user_progress = []

    for user in users:

        user_task_list = [
            task for task in tasks
            if task.get("user_id") == user["id"]
        ]

        user_stats = task_stats(user_task_list)

        user_progress.append({
            "id": user["id"],
            "name": user["name"],
            "total": user_stats["total"],
            "completed": user_stats["completed"],
            "pending": user_stats["pending"]
        })

    productivity_labels, productivity_datasets = get_productivity_data()

    return render_template(
        "admin_dashboard.html",
        tasks=tasks,
        stats=stats,
        chart=chart,
        users=users,
        user_progress=user_progress,
        productivity_labels=productivity_labels,
        productivity_datasets=productivity_datasets,
        is_overdue=is_overdue
    )


# ----------------------------------
# ADMIN: USER MANAGEMENT
# ----------------------------------

@app.route("/admin/users")
@admin_required
def admin_users():

    return render_template(
        "admin_users.html",
        users=users,
        tasks=tasks
    )


# PROMOTE / DEMOTE USER

@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@admin_required
def change_user_role(user_id):

    user = get_user_by_id(user_id)

    if not user:
        flash("User not found.")
        return redirect(url_for("admin_users"))

    new_role = request.form.get("role", "").lower()

    if new_role not in ["user", "admin"]:
        flash("Invalid role.")
        return redirect(url_for("admin_users"))

    if user["id"] == session.get("user_id"):
        flash("You cannot change your own role.")
        return redirect(url_for("admin_users"))

    user["role"] = new_role

    flash(
        f"{user['name']} is now an "
        f"{'Admin' if new_role == 'admin' else 'User'}."
    )

    return redirect(url_for("admin_users"))


# ACTIVATE / DEACTIVATE USER

@app.route("/admin/users/<int:user_id>/status", methods=["POST"])
@admin_required
def change_user_status(user_id):

    user = get_user_by_id(user_id)

    if not user:
        flash("User not found.")
        return redirect(url_for("admin_users"))

    if user["id"] == session.get("user_id"):
        flash("You cannot deactivate your own account.")
        return redirect(url_for("admin_users"))

    new_status = request.form.get("status", "").capitalize()

    if new_status not in ["Active", "Inactive"]:
        flash("Invalid account status.")
        return redirect(url_for("admin_users"))

    user["status"] = new_status

    flash(f"{user['name']}'s account is now {new_status}.")
    return redirect(url_for("admin_users"))


# DELETE USER

@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):

    global users, tasks

    user = get_user_by_id(user_id)

    if not user:
        flash("User not found.")
        return redirect(url_for("admin_users"))

    if user["id"] == session.get("user_id"):
        flash("You cannot delete your own account.")
        return redirect(url_for("admin_users"))

    users = [u for u in users if u["id"] != user_id]
    tasks = [t for t in tasks if t.get("user_id") != user_id]

    flash("User and their tasks have been deleted.")
    return redirect(url_for("admin_users"))


# ----------------------------------
# ADMIN: TASK MANAGEMENT
# ----------------------------------

@app.route("/admin/tasks")
@admin_required
def admin_tasks():

    return render_template(
        "admin_tasks.html",
        tasks=tasks,
        users=users,
        is_overdue=is_overdue
    )


# ADMIN ADD TASK AND ASSIGN TO USER

@app.route("/admin/tasks/add", methods=["POST"])
@admin_required
def admin_add_task():

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium")
    due_date = request.form.get("due_date", "")
    status = request.form.get("status", "Pending")
    assigned_user_id = request.form.get("user_id", type=int)

    if not title:
        flash("Please enter a task title.")
        return redirect(url_for("admin_tasks"))

    user = get_user_by_id(assigned_user_id)

    if not user or user.get("status") != "Active":
        flash("Please select a valid active user.")
        return redirect(url_for("admin_tasks"))

    if priority not in ["Low", "Medium", "High"]:
        priority = "Medium"

    if status not in ["Pending", "In Progress", "Completed"]:
        status = "Pending"

    new_task = {
        "id": next_id(tasks),
        "title": title,
        "description": description,
        "priority": priority,
        "status": "Pending",
        "due_date": due_date,
        "completed_at": None,
        "user": user["name"],
        "user_id": user["id"]
    }

    set_task_status(new_task, status)
    tasks.append(new_task)

    flash(f"Task successfully assigned to {user['name']}.")
    return redirect(url_for("admin_tasks"))


# ADMIN UPDATE TASK

@app.route("/admin/tasks/<int:task_id>/update", methods=["POST"])
@admin_required
def admin_update_task(task_id):

    task = get_task_by_id(task_id)

    if not task:
        flash("Task not found.")
        return redirect(url_for("admin_tasks"))

    title = request.form.get("title", "").strip()

    if title:
        task["title"] = title

    task["description"] = request.form.get(
        "description", task.get("description", "")
    ).strip()

    status = request.form.get("status", task["status"])

    if status in ["Pending", "In Progress", "Completed"]:
        set_task_status(task, status)

    flash("Task updated successfully.")
    return redirect(url_for("admin_tasks"))


# ADMIN DELETE TASK

@app.route("/admin/tasks/<int:task_id>/delete", methods=["POST"])
@admin_required
def admin_delete_task(task_id):

    global tasks

    task = get_task_by_id(task_id)

    if not task:
        flash("Task not found.")
        return redirect(url_for("admin_tasks"))

    tasks = [t for t in tasks if t["id"] != task_id]

    flash("Task deleted successfully.")
    return redirect(url_for("admin_tasks"))


# ----------------------------------
# LOGIN
# ----------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:

            session.clear()
            session["role"] = "admin"
            session["name"] = "Admin"

            return redirect(url_for("admin_dashboard"))

        user = next(
            (
                u for u in users
                if u["email"].lower() == email.lower()
                and u["password"] == password
            ),
            None
        )

        if not user:
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        if user["status"] != "Active":
            flash("Your account is inactive. Contact an administrator.")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ----------------------------------
# REGISTER
# ----------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirmPassword", "")

        if not name or not email or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        if any(u["email"].lower() == email.lower() for u in users):
            flash("This email is already registered.")
            return redirect(url_for("register"))

        if email.lower() == ADMIN_EMAIL.lower():
            flash("This email cannot be used for registration.")
            return redirect(url_for("register"))

        users.append({
            "id": next_id(users),
            "name": name,
            "email": email,
            "password": password,
            "role": "user",
            "status": "Active"
        })

        flash("Registration successful! Please sign in.")
        return redirect(url_for("login"))

    return render_template("register.html")


# ----------------------------------
# LOGOUT
# ----------------------------------

@app.route("/logout")
def logout():

    session.clear()
    flash("You have been logged out successfully.")

    return redirect(url_for("login"))


# ----------------------------------
# RUN APPLICATION
# ----------------------------------

if __name__ == "__main__":
    app.run(debug=True)
