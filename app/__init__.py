import os
from flask import Flask, jsonify
from .config import Config
from .database import init_db

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

    # Simple health‑check endpoint
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app

