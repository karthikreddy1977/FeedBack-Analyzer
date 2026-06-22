"""
Pulse — Flask Extension Instances
====================================
Extensions are instantiated here (without an app) to avoid circular imports.
They are initialized with the app inside the factory function in __init__.py.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# ---------------------------------------------------------------------------
# SQLAlchemy ORM
# ---------------------------------------------------------------------------
db = SQLAlchemy()

# ---------------------------------------------------------------------------
# Flask-Login session management
# ---------------------------------------------------------------------------
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"
