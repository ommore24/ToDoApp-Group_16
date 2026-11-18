"""Authentication blueprint package."""

from flask import Blueprint

# Blueprint instance
auth_bp = Blueprint('auth', __name__)

# Import routes to register them with the blueprint
from . import routes  # noqa: F401

