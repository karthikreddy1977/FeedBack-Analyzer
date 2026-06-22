"""
Pulse — Admin Routes
======================
Admin dashboard with platform statistics, user management
(view, suspend, delete), and system-wide analytics.
All routes protected by @admin_required.
"""

from collections import Counter
from flask import render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user

from . import admin_bp
from ..extensions import db
from ..models import User, Feedback, Report, Notification
from ..decorators import admin_required


# ---------------------------------------------------------------------------
# Admin Dashboard
# ---------------------------------------------------------------------------
@admin_bp.route("/")
@login_required
@admin_required
def admin_dashboard():
    """
    Admin dashboard with platform-wide statistics:
    total users, total feedback, sentiment breakdown, top categories.
    """
    total_users = User.query.count()
    total_feedback = Feedback.query.count()
    total_reports = Report.query.count()

    all_feedback = Feedback.query.all()
    sentiments = Counter(fb.sentiment for fb in all_feedback)
    categories = Counter(fb.category for fb in all_feedback)
    emotions = Counter(fb.emotion for fb in all_feedback)

    # Top 5 active users by feedback count
    top_users = db.session.execute(
        db.text("""
            SELECT u.username, COUNT(f.id) as fb_count
            FROM users u LEFT JOIN feedback f ON u.id = f.user_id
            GROUP BY u.id
            ORDER BY fb_count DESC
            LIMIT 5
        """)
    ).fetchall()

    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    stats = {
        "total_users": total_users,
        "total_feedback": total_feedback,
        "total_reports": total_reports,
        "positive": sentiments.get("Positive", 0),
        "negative": sentiments.get("Negative", 0),
        "neutral": sentiments.get("Neutral", 0),
        "categories": dict(categories.most_common(6)),
        "emotions": dict(emotions.most_common(6)),
        "top_users": [{"username": row[0], "count": row[1]} for row in top_users],
    }

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_users=recent_users,
    )


# ---------------------------------------------------------------------------
# Users List
# ---------------------------------------------------------------------------
@admin_bp.route("/users")
@login_required
@admin_required
def users_list():
    """View all registered users with their stats."""
    users = User.query.order_by(User.created_at.desc()).all()
    user_data = []
    for user in users:
        fb_count = Feedback.query.filter_by(user_id=user.id).count()
        user_data.append({
            "user": user,
            "feedback_count": fb_count,
        })
    return render_template("admin/dashboard.html", users=user_data, show_users=True)


# ---------------------------------------------------------------------------
# Suspend / Unsuspend User
# ---------------------------------------------------------------------------
@admin_bp.route("/users/<int:user_id>/suspend", methods=["POST"])
@login_required
@admin_required
def suspend_user(user_id):
    """Toggle suspend/unsuspend a user."""
    user = User.query.get_or_404(user_id)

    if user.is_admin:
        flash("Cannot suspend an admin user.", "error")
        return redirect(url_for("admin.admin_dashboard"))

    user.is_suspended = not user.is_suspended
    db.session.commit()

    action = "suspended" if user.is_suspended else "unsuspended"
    flash(f"User '{user.username}' has been {action}.", "success")
    return redirect(url_for("admin.admin_dashboard"))


# ---------------------------------------------------------------------------
# Delete User
# ---------------------------------------------------------------------------
@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user and all their data (cascade)."""
    user = User.query.get_or_404(user_id)

    if user.is_admin:
        flash("Cannot delete an admin user.", "error")
        return redirect(url_for("admin.admin_dashboard"))

    if user.id == current_user.id:
        flash("Cannot delete your own account from admin panel.", "error")
        return redirect(url_for("admin.admin_dashboard"))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f"User '{username}' and all their data have been deleted.", "success")
    return redirect(url_for("admin.admin_dashboard"))


# ---------------------------------------------------------------------------
# Admin API — Platform Stats (for charts)
# ---------------------------------------------------------------------------
@admin_bp.route("/api/stats")
@login_required
@admin_required
def admin_api_stats():
    """JSON endpoint for admin dashboard charts."""
    all_feedback = Feedback.query.all()
    sentiments = Counter(fb.sentiment for fb in all_feedback)
    categories = Counter(fb.category for fb in all_feedback)
    emotions = Counter(fb.emotion for fb in all_feedback)

    # Monthly trend (platform-wide)
    trend_rows = db.session.execute(
        db.text("""
            SELECT strftime('%Y-%m', created_at) AS month, sentiment, COUNT(*) AS c
            FROM feedback
            GROUP BY month, sentiment
            ORDER BY month ASC
        """)
    ).fetchall()

    trend_map = {}
    for row in trend_rows:
        month = row[0]
        trend_map.setdefault(month, {"Positive": 0, "Negative": 0, "Neutral": 0})
        trend_map[month][row[1]] = row[2]

    return jsonify({
        "total_feedback": len(all_feedback),
        "total_users": User.query.count(),
        "positive": sentiments.get("Positive", 0),
        "negative": sentiments.get("Negative", 0),
        "neutral": sentiments.get("Neutral", 0),
        "categories": dict(categories),
        "emotions": dict(emotions),
        "trend": trend_map,
    })
