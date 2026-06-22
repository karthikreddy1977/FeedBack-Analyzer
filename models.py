"""
Pulse — Database Models
========================
SQLAlchemy models for Users, Feedback, Reports, and Notifications.
All models use proper relationships and foreign keys for data isolation.
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from .extensions import db


class User(UserMixin, db.Model):
    """
    User model supporting both regular users and admin accounts.
    Passwords are stored as Werkzeug-hashed strings — never plain text.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_image = db.Column(db.String(256), default="default.png")
    is_admin = db.Column(db.Boolean, default=False)
    is_suspended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    feedbacks = db.relationship("Feedback", backref="author", lazy="dynamic",
                                cascade="all, delete-orphan")
    reports = db.relationship("Report", backref="owner", lazy="dynamic",
                              cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="recipient", lazy="dynamic",
                                    cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Feedback(db.Model):
    """
    Stores each piece of customer feedback along with analysis results:
    sentiment label, polarity score, subjectivity score, detected emotion,
    category classification, and extracted keywords.
    """
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    feedback_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="Other")  # Product/Service/Delivery/Support/Website/Other
    sentiment = db.Column(db.String(20), nullable=False)   # Positive/Negative/Neutral
    polarity_score = db.Column(db.Float, nullable=False)
    subjectivity_score = db.Column(db.Float, default=0.0)
    emotion = db.Column(db.String(30), default="Neutral")  # Happy/Satisfied/Excited/Neutral/Frustrated/Angry
    keywords = db.Column(db.Text, default="")               # Comma-separated keywords
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Feedback {self.id} — {self.sentiment}>"

    def to_dict(self):
        """Convert to dictionary for JSON API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "feedback_text": self.feedback_text,
            "category": self.category,
            "sentiment": self.sentiment,
            "polarity_score": self.polarity_score,
            "subjectivity_score": self.subjectivity_score,
            "emotion": self.emotion,
            "keywords": self.keywords,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }


class Report(db.Model):
    """
    Tracks generated reports (CSV, Excel, PDF) so users can
    re-download or manage their report history.
    """
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    report_name = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    format = db.Column(db.String(10), default="csv")  # csv / xlsx / pdf
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Report {self.report_name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "report_name": self.report_name,
            "format": self.format,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }


class Notification(db.Model):
    """
    In-app notification system. Notifications are created automatically
    on events like feedback submission, report generation, etc.
    """
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Notification {self.id} — {'read' if self.is_read else 'unread'}>"

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }
