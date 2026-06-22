"""
Pulse — Application Configuration
===================================
Centralized configuration classes for different environments.
SQLite for development, PostgreSQL-ready for production.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Base configuration shared across all environments."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "pulse-dev-secret-key-change-in-production")

    # Database — SQLite by default, override with DATABASE_URL env var for PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, "avatars")
    FILES_FOLDER = os.path.join(UPLOAD_FOLDER, "files")
    EXPORT_DIR = os.path.join(BASE_DIR, "exports")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # Allowed file extensions
    ALLOWED_AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ALLOWED_DATA_EXTENSIONS = {"csv", "txt"}

    # Pagination
    DEFAULT_PER_PAGE = 10
    MAX_PER_PAGE = 100

    # Feedback constraints
    MAX_FEEDBACK_LENGTH = 2000


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    # In production, SECRET_KEY MUST be set via environment variable


# Map environment names to config classes
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
