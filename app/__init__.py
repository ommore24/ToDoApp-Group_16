import os
# pyrefly: ignore[missing-import]
from flask import Flask, jsonify
from .config import Config
from .database import init_db,get_db



def create_app():
    """Application factory for the Todo app.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)
    # Load configuration
    app.config.from_object(Config)

    # Initialize database (lazy connection, handled in requests)
    init_db(app)

    # Register blueprints
    from .auth import auth_bp
    from .tasks import tasks_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")

    @app.route("/")
    def home():
     return "Todo App"

    # Simple health‑check endpoint
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

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

     except Exception as e:
        app.logger.exception("Database test failed")
        return jsonify({
            "database_status": "Failed",
            "error": str(e)
        }), 500


    return app

