from datetime import date, timedelta
from flask import Flask, jsonify, render_template, session, redirect, url_for, request, flash

from .config import Config
from .database import init_db, get_db

SUPER_ADMIN_EMAIL = "admin1@gmail.com"


def is_overdue(task):
    due = task.get("due_date")
    if not due or str(task.get("status", "")).lower() == "completed":
        return False
    if isinstance(due, str):
        due = date.fromisoformat(due[:10])
    return due < date.today()


def get_current_admin(cursor):
    """Return admin user dict if logged-in user is an active admin, else None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    cursor.execute(
        "SELECT id, username, email, role, active FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()
    if not user or not user["active"] or user["role"] != "admin":
        return None
    return user


def build_admin_context(cursor, current_admin=None):
    """Fetch normalized users, tasks, stats, and chart series for admin pages."""
    cursor.execute("SELECT id, username, email, role, active FROM users ORDER BY id ASC")
    raw_users = cursor.fetchall()
    users = [
        {
            "id": u["id"],
            "name": u["username"],
            "email": u["email"],
            "role": u["role"],
            "active": u["active"],
            "status": "Active" if u["active"] else "Inactive",
        }
        for u in raw_users
    ]
    user_map = {u["id"]: u["name"] for u in users}

    cursor.execute(
        """
        SELECT id, user_id, title, description, status, priority, due_date, created_at, updated_at
        FROM tasks
        ORDER BY created_at DESC
        """
    )
    raw_tasks = cursor.fetchall()
    tasks = []
    for t in raw_tasks:
        raw_status = (t.get("status") or "pending").lower()
        display_status = (
            "In Progress" if raw_status == "in_progress"
            else raw_status.capitalize()
        )
        tasks.append({
            **t,
            "user": user_map.get(t["user_id"], "Unassigned"),
            "raw_status": raw_status,
            "status": display_status,
            "priority": (t.get("priority") or "medium").capitalize(),
        })

    total = len(tasks)
    completed = sum(1 for t in tasks if t["raw_status"] == "completed")
    pending = sum(1 for t in tasks if t["raw_status"] == "pending")
    in_progress = sum(1 for t in tasks if t["raw_status"] == "in_progress")
    overdue = sum(1 for t in tasks if is_overdue(t))

    stats = {
        "total": total,
        "completed": completed,
        "pending": pending,
        "in_progress": in_progress,
        "overdue": overdue,
    }

    def pct(val):
        return round((val / total) * 100) if total else 0

    chart = [
        {"label": "Completed", "value": completed, "percent": pct(completed), "class_name": "green"},
        {"label": "In Progress", "value": in_progress, "percent": pct(in_progress), "class_name": "blue"},
        {"label": "Pending", "value": pending, "percent": pct(pending), "class_name": "orange"},
        {"label": "Overdue", "value": overdue, "percent": pct(overdue), "class_name": "red"},
    ]

    user_progress = []
    for u in users:
        u_tasks = [t for t in tasks if t["user_id"] == u["id"]]
        user_progress.append({
            "id": u["id"],
            "name": u["name"],
            "total": len(u_tasks),
            "completed": sum(1 for t in u_tasks if t["raw_status"] == "completed"),
            "pending": sum(1 for t in u_tasks if t["raw_status"] == "pending"),
        })

    # Last 7 days productivity line chart
    today = date.today()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    productivity_labels = [d.strftime("%b %d") for d in last_7_days]
    palette = ["#6c5ce7", "#00b894", "#fdcb6e", "#0984e3", "#e17055", "#a29bfe", "#55efc4"]

    productivity_datasets = []
    for idx, u in enumerate(users):
        daily_counts = []
        for d in last_7_days:
            count = 0
            for t in tasks:
                if t["user_id"] == u["id"] and t["raw_status"] == "completed":
                    ts = t.get("updated_at") or t.get("created_at")
                    if ts:
                        ts_date = ts.date() if hasattr(ts, "date") else date.fromisoformat(str(ts)[:10])
                        if ts_date == d:
                            count += 1
            daily_counts.append(count)

        color = palette[idx % len(palette)]
        productivity_datasets.append({
            "label": u["name"],
            "data": daily_counts,
            "borderColor": color,
            "backgroundColor": color,
            "tension": 0.3,
            "fill": False,
        })

    current_admin_email = (current_admin["email"] if current_admin else session.get("email", "")) or ""

    return {
        "users": users,
        "tasks": tasks,
        "stats": stats,
        "chart": chart,
        "user_progress": user_progress,
        "productivity_labels": productivity_labels,
        "productivity_datasets": productivity_datasets,
        "is_overdue": is_overdue,
        "overdue_count": overdue,
        "super_admin_email": SUPER_ADMIN_EMAIL,
        "current_admin_email": current_admin_email,
    }


def create_app():
    """Create and configure the Flask application."""

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize database
    init_db(app)

    from .admin.setup import create_default_admin

    with app.app_context():
        create_default_admin()

    # Register blueprints
    from .auth import auth_bp
    from .tasks import tasks_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # -------------------------
    # HEALTH CHECK
    # -------------------------

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    # -------------------------
    # DATABASE TEST
    # -------------------------

    @app.route("/db-test")
    def db_test():
        try:
            db = get_db()
            cursor = db.cursor()

            cursor.execute("SELECT DATABASE() AS db_name")
            result = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM tasks")
            task_count = cursor.fetchone()

            cursor.close()

            return jsonify({
                "database_status": "Connected",
                "database_name": result["db_name"],
                "total_tasks": task_count["total"]
            })

        except Exception:
            app.logger.exception("Database test failed")

            return jsonify({
                "database_status": "Failed",
                "error": "Database connection failed"
            }), 500

    # -------------------------
    # PAGE ROUTES
    # -------------------------

    @app.route("/")
    def home():
        return render_template("login.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login_page"))

    @app.route("/dashboard")
    def dashboard():
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login_page"))

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "SELECT * FROM tasks WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            tasks = cursor.fetchall()
        finally:
            cursor.close()

        stats = {
            "total": len(tasks),
            "completed": sum(1 for t in tasks if t["status"] == "completed"),
            "pending": sum(1 for t in tasks if t["status"] == "pending"),
            "in_progress": sum(1 for t in tasks if t["status"] == "in_progress"),
            "overdue": sum(1 for t in tasks if is_overdue(t)),
        }

        return render_template(
            "dashboard.html",
            tasks=tasks,
            stats=stats,
            is_overdue=is_overdue,
            overdue_count=stats["overdue"]
        )

    @app.route("/tasks")
    @app.route("/tasks", endpoint="task_list")
    def tasks_page():
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login_page"))

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "SELECT * FROM tasks WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            tasks = cursor.fetchall()
        finally:
            cursor.close()

        overdue_count = sum(1 for t in tasks if is_overdue(t))
        return render_template(
            "tasks.html",
            tasks=tasks,
            is_overdue=is_overdue,
            overdue_count=overdue_count
        )

    # -------------------------
    # ADMIN PAGE ROUTES
    # -------------------------

    @app.route("/admin")
    def admin_dashboard():
        db = get_db()
        cursor = db.cursor()
        try:
            admin = get_current_admin(cursor)
            if not admin:
                session.clear()
                return redirect(url_for("login_page"))
            ctx = build_admin_context(cursor, admin)
            return render_template("admin_dashboard.html", **ctx)
        finally:
            cursor.close()

    @app.route("/admin/users")
    def admin_users():
        db = get_db()
        cursor = db.cursor()
        try:
            admin = get_current_admin(cursor)
            if not admin:
                session.clear()
                return redirect(url_for("login_page"))
            ctx = build_admin_context(cursor, admin)
            return render_template("admin_users.html", **ctx)
        finally:
            cursor.close()

    @app.route("/admin/tasks")
    def admin_tasks():
        db = get_db()
        cursor = db.cursor()
        try:
            admin = get_current_admin(cursor)
            if not admin:
                session.clear()
                return redirect(url_for("login_page"))
            ctx = build_admin_context(cursor, admin)
            return render_template("admin_tasks.html", **ctx)
        finally:
            cursor.close()

    # -------------------------
    # ADMIN ACTION ROUTES
    # -------------------------

    @app.route("/admin/tasks/add", methods=["POST"])
    def admin_add_task():
        db = get_db()
        cursor = db.cursor()
        try:
            if not get_current_admin(cursor):
                return redirect(url_for("login_page"))

            title = (request.form.get("title") or "").strip()
            description = (request.form.get("description") or "").strip() or None
            user_id = request.form.get("user_id")
            priority = (request.form.get("priority") or "medium").lower()
            raw_status = (request.form.get("status") or "pending").lower().replace(" ", "_")
            due_date = request.form.get("due_date") or None

            if priority not in {"low", "medium", "high"}:
                priority = "medium"
            if raw_status not in {"pending", "in_progress", "completed"}:
                raw_status = "pending"

            if title and user_id:
                cursor.execute(
                    """
                    INSERT INTO tasks (user_id, title, description, status, priority, due_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, title, description, raw_status, priority, due_date),
                )
                db.commit()
                flash("Task assigned successfully.")

            return redirect(url_for("admin_tasks"))
        finally:
            cursor.close()

    @app.route("/admin/tasks/<int:task_id>/update", methods=["POST"])
    def admin_update_task(task_id):
        db = get_db()
        cursor = db.cursor()
        try:
            if not get_current_admin(cursor):
                return redirect(url_for("login_page"))

            title = (request.form.get("title") or "").strip()
            description = (request.form.get("description") or "").strip() or None
            raw_status = (request.form.get("status") or "pending").lower().replace(" ", "_")

            if raw_status not in {"pending", "in_progress", "completed"}:
                raw_status = "pending"

            if title:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET title = %s, description = %s, status = %s
                    WHERE id = %s
                    """,
                    (title, description, raw_status, task_id),
                )
                db.commit()
                flash("Task updated successfully.")

            return redirect(url_for("admin_tasks"))
        finally:
            cursor.close()

    @app.route("/admin/tasks/<int:task_id>/delete", methods=["POST"])
    def admin_delete_task(task_id):
        db = get_db()
        cursor = db.cursor()
        try:
            if not get_current_admin(cursor):
                return redirect(url_for("login_page"))

            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            db.commit()
            flash("Task deleted successfully.")
            return redirect(url_for("admin_tasks"))
        finally:
            cursor.close()

    @app.route("/admin/users/<int:user_id>/role", methods=["POST"])
    def change_user_role(user_id):
        db = get_db()
        cursor = db.cursor()
        try:
            admin = get_current_admin(cursor)
            if not admin:
                return redirect(url_for("login_page"))

            # Only admin1@gmail.com can promote/demote roles
            if (admin["email"] or "").lower() != SUPER_ADMIN_EMAIL:
                flash("Only the primary administrator (admin1@gmail.com) can change user roles.")
                return redirect(url_for("admin_users"))

            cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
            target = cursor.fetchone()
            if not target or (target["email"] or "").lower() == SUPER_ADMIN_EMAIL:
                flash("The primary administrator's role cannot be changed.")
                return redirect(url_for("admin_users"))

            new_role = (request.form.get("role") or "").lower()
            if user_id != admin["id"] and new_role in {"admin", "user"}:
                cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
                db.commit()
                flash(f"User role updated to {new_role}.")

            return redirect(url_for("admin_users"))
        finally:
            cursor.close()

    @app.route("/admin/users/<int:user_id>/status", methods=["POST"])
    def change_user_status(user_id):
        db = get_db()
        cursor = db.cursor()
        try:
            admin = get_current_admin(cursor)
            if not admin:
                return redirect(url_for("login_page"))

            cursor.execute("SELECT id, email, role FROM users WHERE id = %s", (user_id,))
            target = cursor.fetchone()
            if not target:
                return redirect(url_for("admin_users"))

            is_super_admin = (admin["email"] or "").lower() == SUPER_ADMIN_EMAIL
            target_is_super = (target["email"] or "").lower() == SUPER_ADMIN_EMAIL

            if target_is_super or (target["role"] == "admin" and not is_super_admin):
                flash("You do not have permission to change this administrator's status.")
                return redirect(url_for("admin_users"))

            new_status = request.form.get("status")
            if user_id != admin["id"] and new_status in {"Active", "Inactive"}:
                active_val = 1 if new_status == "Active" else 0
                cursor.execute("UPDATE users SET active = %s WHERE id = %s", (active_val, user_id))
                db.commit()
                flash(f"User account marked as {new_status}.")

            return redirect(url_for("admin_users"))
        finally:
            cursor.close()

    @app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
    def delete_user(user_id):
        db = get_db()
        cursor = db.cursor()
        try:
            admin = get_current_admin(cursor)
            if not admin:
                return redirect(url_for("login_page"))

            cursor.execute("SELECT id, email, role FROM users WHERE id = %s", (user_id,))
            target = cursor.fetchone()
            if not target:
                return redirect(url_for("admin_users"))

            is_super_admin = (admin["email"] or "").lower() == SUPER_ADMIN_EMAIL
            target_is_super = (target["email"] or "").lower() == SUPER_ADMIN_EMAIL

            if target_is_super or (target["role"] == "admin" and not is_super_admin):
                flash("You do not have permission to delete this administrator account.")
                return redirect(url_for("admin_users"))

            if user_id != admin["id"]:
                cursor.execute("DELETE FROM tasks WHERE user_id = %s", (user_id,))
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                db.commit()
                flash("User account and associated tasks deleted.")

            return redirect(url_for("admin_users"))
        finally:
            cursor.close()

    return app