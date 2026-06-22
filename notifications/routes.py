"""
Pulse — Notifications Routes
===============================
Full-page notification management routes.
(JSON API endpoints are in the API blueprint.)
"""

from flask import render_template
from flask_login import login_required, current_user

from . import notifications_bp
from ..models import Notification


@notifications_bp.route("/")
@login_required
def notifications_page():
    """Full page view of all notifications."""
    notifications = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()).all()
    return render_template("notifications/list.html", notifications=notifications)
