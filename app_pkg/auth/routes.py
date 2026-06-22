"""
Pulse — Auth Routes
=====================
Handles user registration, login, logout, password management.
Passwords are hashed with Werkzeug — never stored in plain text.
"""

from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import auth_bp
from ..extensions import db
from ..models import User
from ..utils import create_notification

import re
import secrets


def _validate_password(password):
    """
    Validate password strength.
    Requirements: 8+ chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char.
    Returns (is_valid, error_message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/~`]", password):
        return False, "Password must contain at least one special character."
    return True, ""


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration with validation for unique username/email and strong password."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        errors = []

        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        elif len(username) > 80:
            errors.append("Username must be 80 characters or fewer.")
        elif not re.match(r"^[a-zA-Z0-9_]+$", username):
            errors.append("Username can only contain letters, numbers, and underscores.")

        if not email or "@" not in email:
            errors.append("Please enter a valid email address.")

        valid_pw, pw_err = _validate_password(password)
        if not valid_pw:
            errors.append(pw_err)

        if password != confirm_password:
            errors.append("Passwords do not match.")

        # Check uniqueness
        if User.query.filter_by(username=username).first():
            errors.append("Username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email is already registered.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("auth/register.html", username=username, email=email)

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        # Welcome notification
        create_notification(user.id, f"Welcome to Pulse, {username}! 🎉 Start by submitting your first feedback.")

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login with optional 'Remember Me'."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and check_password_hash(user.password_hash, password):
            if user.is_suspended:
                flash("Your account has been suspended. Contact an administrator.", "error")
                return render_template("auth/login.html")

            login_user(user, remember=remember)
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()

            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        else:
            flash("Invalid username/email or password.", "error")

    return render_template("auth/login.html")


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    """Log out the current user and redirect to home."""
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Forgot Password (placeholder — no email service)
# ---------------------------------------------------------------------------
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Placeholder forgot password workflow.
    Generates a reset token and displays it on screen.
    In production, this would send an email.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    token = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate a reset token (placeholder — display on screen)
            token = secrets.token_urlsafe(32)
            flash("Password reset token generated. In production, this would be emailed to you.", "info")
        else:
            # Don't reveal if email exists or not (security best practice)
            flash("If an account with that email exists, a reset link has been sent.", "info")

    return render_template("auth/forgot_password.html", token=token)


# ---------------------------------------------------------------------------
# Change Password
# ---------------------------------------------------------------------------
@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change password for the currently logged-in user."""
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        if not check_password_hash(current_user.password_hash, current_pw):
            flash("Current password is incorrect.", "error")
            return render_template("auth/change_password.html")

        valid_pw, pw_err = _validate_password(new_pw)
        if not valid_pw:
            flash(pw_err, "error")
            return render_template("auth/change_password.html")

        if new_pw != confirm_pw:
            flash("New passwords do not match.", "error")
            return render_template("auth/change_password.html")

        current_user.password_hash = generate_password_hash(new_pw)
        db.session.commit()

        create_notification(current_user.id, "Your password was changed successfully. 🔒")
        flash("Password changed successfully.", "success")
        return redirect(url_for("profile.profile_page"))

    return render_template("auth/change_password.html")
