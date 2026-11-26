from datetime import date
from flask import Flask, jsonify, render_template, session, redirect, url_for

from .config import Config
from .database import init_db, get_db


def is_overdue(task):
    due = task.get("due_date")
    if not due or task.get("status") == "completed":
        return False
    if isinstance(due, str):
        due = date.fromisoformat(due[:10])
    return due < date.today()


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

    @app.route("/admin")
    def admin_dashboard():
        user_id = session.get("user_id")

        if not user_id:
            return redirect(url_for("login_page"))

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(
                "SELECT role, active FROM users WHERE id = %s",
                (user_id,)
            )

            user = cursor.fetchone()

            if not user or not user["active"]:
                session.clear()
                return redirect(url_for("login_page"))

            if user["role"] != "admin":
                return redirect(url_for("dashboard"))

            return render_template("admin_dashboard.html")

        finally:
            cursor.close()

    @app.route("/admin/users")
    def admin_users():
        user_id = session.get("user_id")

        if not user_id:
            return redirect(url_for("login_page"))

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(
                "SELECT role, active FROM users WHERE id = %s",
                (user_id,)
            )

            user = cursor.fetchone()

            if not user or not user["active"]:
                session.clear()
                return redirect(url_for("login_page"))

            if user["role"] != "admin":
                return redirect(url_for("dashboard"))

            return render_template("admin_users.html")

        finally:
            cursor.close()

    return app