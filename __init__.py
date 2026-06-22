"""
Pulse — Application Factory
==============================
Creates and configures the Flask application with all extensions
and blueprints registered. Call create_app() to get a fully
configured app instance.
"""

import os
from flask import Flask
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

from .extensions import db, login_manager
from config import config_map


def create_app(config_name=None):
    """
    Application factory pattern.
    Creates the Flask app, initializes extensions, registers blueprints,
    and sets up the database.
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
    )

    # Load configuration
    config_class = config_map.get(config_name, config_map["default"])
    app.config.from_object(config_class)

    # Ensure directories exist
    os.makedirs(app.config.get("UPLOAD_FOLDER", "static/uploads"), exist_ok=True)
    os.makedirs(app.config.get("AVATAR_FOLDER", "static/uploads/avatars"), exist_ok=True)
    os.makedirs(app.config.get("FILES_FOLDER", "static/uploads/files"), exist_ok=True)
    os.makedirs(app.config.get("EXPORT_DIR", "exports"), exist_ok=True)

    # ---------------------------------------------------------------------------
    # Initialize extensions
    # ---------------------------------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)

    # ---------------------------------------------------------------------------
    # User loader for Flask-Login
    # ---------------------------------------------------------------------------
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------------------------------------------------------------------------
    # Register Blueprints
    # ---------------------------------------------------------------------------
    from .auth import auth_bp
    from .main import main_bp
    from .api import api_bp
    from .reports import reports_bp
    from .profile import profile_bp
    from .admin import admin_bp
    from .notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)

    # ---------------------------------------------------------------------------
    # Error Handlers
    # ---------------------------------------------------------------------------
    from flask import render_template, jsonify

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error."}), 500

    # ---------------------------------------------------------------------------
    # Create tables and seed admin user
    # ---------------------------------------------------------------------------
    with app.app_context():
        db.create_all()
        _seed_admin(app)

    return app


def _seed_admin(app):
    """
    Create a default admin user if none exists.
    Credentials: admin / Admin@123
    """
    from .models import User

    admin = User.query.filter_by(is_admin=True).first()
    if admin is None:
        admin = User(
            username="admin",
            email="admin@pulse.local",
            password_hash=generate_password_hash("Admin@123"),
            is_admin=True,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(admin)
        db.session.commit()
        print(" * Seeded default admin user (admin / Admin@123)")
