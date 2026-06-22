"""
Pulse — Profile Routes
========================
View/edit user profile, upload avatar, change password redirect.
"""

import os
import re
from flask import (
    render_template, request, redirect, url_for,
    flash, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import profile_bp
from ..extensions import db
from ..models import Feedback


# ---------------------------------------------------------------------------
# Profile Page
# ---------------------------------------------------------------------------
@profile_bp.route("/")
@login_required
def profile_page():
    """Display user profile with statistics."""
    total_feedback = Feedback.query.filter_by(user_id=current_user.id).count()
    return render_template("profile/profile.html", total_feedback=total_feedback)


# ---------------------------------------------------------------------------
# Update Profile
# ---------------------------------------------------------------------------
@profile_bp.route("/update", methods=["POST"])
@login_required
def update_profile():
    """Update username and email."""
    from ..models import User

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()

    errors = []

    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters.")
    elif not re.match(r"^[a-zA-Z0-9_]+$", username):
        errors.append("Username can only contain letters, numbers, and underscores.")

    if not email or "@" not in email:
        errors.append("Please enter a valid email address.")

    # Check uniqueness (excluding current user)
    existing_user = User.query.filter(
        User.username == username, User.id != current_user.id
    ).first()
    if existing_user:
        errors.append("Username is already taken.")

    existing_email = User.query.filter(
        User.email == email, User.id != current_user.id
    ).first()
    if existing_email:
        errors.append("Email is already registered.")

    if errors:
        for error in errors:
            flash(error, "error")
        return redirect(url_for("profile.profile_page"))

    current_user.username = username
    current_user.email = email
    db.session.commit()

    flash("Profile updated successfully.", "success")
    return redirect(url_for("profile.profile_page"))


# ---------------------------------------------------------------------------
# Upload Avatar
# ---------------------------------------------------------------------------
@profile_bp.route("/avatar", methods=["POST"])
@login_required
def upload_avatar():
    """Upload or update profile picture."""
    if "avatar" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("profile.profile_page"))

    file = request.files["avatar"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("profile.profile_page"))

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed = current_app.config.get("ALLOWED_AVATAR_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"})

    if ext not in allowed:
        flash(f"Allowed image formats: {', '.join(allowed)}", "error")
        return redirect(url_for("profile.profile_page"))

    # Save with unique filename
    filename = secure_filename(f"user_{current_user.id}.{ext}")
    avatar_dir = current_app.config.get("AVATAR_FOLDER", "static/uploads/avatars")
    os.makedirs(avatar_dir, exist_ok=True)

    filepath = os.path.join(avatar_dir, filename)
    file.save(filepath)

    # Delete old avatar if it exists and is different
    if current_user.profile_image and current_user.profile_image != "default.png":
        old_path = os.path.join(avatar_dir, current_user.profile_image)
        if os.path.exists(old_path) and old_path != filepath:
            os.remove(old_path)

    current_user.profile_image = filename
    db.session.commit()

    flash("Profile picture updated.", "success")
    return redirect(url_for("profile.profile_page"))
