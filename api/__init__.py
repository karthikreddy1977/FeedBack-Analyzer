"""
Pulse — API Blueprint
========================
JSON API endpoints for dashboard data, search, and notifications.
"""

from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

from . import routes  # noqa: E402, F401
