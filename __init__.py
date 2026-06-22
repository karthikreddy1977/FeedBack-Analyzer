"""
Pulse — Reports Blueprint
============================
Generate and download reports in CSV, Excel, and PDF formats.
"""

from flask import Blueprint

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

from . import routes  # noqa: E402, F401
