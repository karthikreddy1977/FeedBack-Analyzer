"""
Pulse — Custom Decorators
===========================
Reusable route decorators for authorization and access control.
"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    Decorator that restricts access to admin users only.
    Must be used AFTER @login_required so that current_user is available.

    Usage:
        @app.route("/admin")
        @login_required
        @admin_required
        def admin_dashboard():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Access denied. Admin privileges required.", "error")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
