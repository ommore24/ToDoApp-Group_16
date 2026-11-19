
from flask import Flask, jsonify, render_template

from .config import Config
from .database import init_db, get_db


def create_app():
    """Create and configure the Flask application."""

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize database
    init_db(app)

    # Register blueprints
    from .auth import auth_bp
    from .tasks import tasks_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")

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

    @app.route("/dashboard")
    def dashboard():
        return render_template("user_dashboard.html")

    @app.route("/tasks")
    def tasks_page():
        return render_template("tasks.html")

    @app.route("/admin")
    def admin_dashboard():
        return render_template("admin_dashboard.html")

    @app.route("/admin/users")
    def admin_users():
        return render_template("admin_users.html")

    return app
