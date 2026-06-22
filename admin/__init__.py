"""
Pulse — Admin Blueprint
=========================
Admin dashboard, user management, platform-wide analytics.
All routes restricted to admin users.
"""

from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import routes  # noqa: E402, F401
