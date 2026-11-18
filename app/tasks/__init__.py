"""Tasks blueprint package."""

from flask import Blueprint

# Blueprint instance
tasks_bp = Blueprint('tasks', __name__)

# Import routes to register them with the blueprint
from . import routes  # noqa: F401

