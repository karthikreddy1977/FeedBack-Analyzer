"""
Pulse — Auth Blueprint
========================
Registration, login, logout, forgot password, change password.
"""

from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

from . import routes  # noqa: E402, F401 — register routes after blueprint creation
