"""
Pulse — Main Routes
=====================
Home page, feedback CRUD, dashboard, search/filter, file upload analysis.
All feedback routes enforce user-ownership for multi-user data isolation.
"""

import os
import csv
import io
from flask import (
    render_template, request, jsonify, redirect, url_for,
    flash, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import main_bp
from ..extensions import db
from ..models import Feedback
from ..utils import (
    analyze_sentiment, detect_emotion, extract_keywords,
    sanitize_text, create_notification
)


# ---------------------------------------------------------------------------
# Landing Page
# ---------------------------------------------------------------------------
@main_bp.route("/")
def index():
    """Public landing page. Redirects to dashboard if logged in."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("main/index.html")


# ---------------------------------------------------------------------------
# Submit Feedback
# ---------------------------------------------------------------------------
@main_bp.route("/submit", methods=["GET"])
@login_required
def submit_page():
    """Render the feedback submission form."""
    return render_template("main/submit.html")


@main_bp.route("/submit", methods=["POST"])
@login_required
def submit_feedback():
    """
    Process feedback submission via AJAX.
    Runs sentiment analysis, emotion detection, and keyword extraction.
    """
    try:
        data = request.get_json(silent=True) or {}
        feedback_text = sanitize_text(data.get("feedback_text", ""))
        category = data.get("category", "Other")

        # Validate category
        valid_categories = ["Product", "Service", "Delivery", "Support", "Website", "Other"]
        if category not in valid_categories:
            category = "Other"

        if not feedback_text:
            return jsonify({"success": False, "error": "Feedback text cannot be empty."}), 400

        # Run analysis
        sentiment, polarity, subjectivity = analyze_sentiment(feedback_text)
        emotion = detect_emotion(feedback_text, polarity, subjectivity)
        keywords = extract_keywords(feedback_text)

        # Store in database
        feedback = Feedback(
            user_id=current_user.id,
            feedback_text=feedback_text,
            category=category,
            sentiment=sentiment,
            polarity_score=polarity,
            subjectivity_score=subjectivity,
            emotion=emotion,
            keywords=keywords,
        )
        db.session.add(feedback)
        db.session.commit()

        # Notification
        create_notification(
            current_user.id,
            f"Feedback submitted: {sentiment} sentiment detected ({category}). ✅"
        )

        return jsonify({
            "success": True,
            "sentiment": sentiment,
            "polarity_score": polarity,
            "subjectivity_score": subjectivity,
            "emotion": emotion,
            "category": category,
            "keywords": keywords,
            "feedback_text": feedback_text,
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Something went wrong while processing your feedback."
        }), 500


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Render the enhanced dashboard. Data loaded client-side via /api/stats."""
    return render_template("main/dashboard.html")


# ---------------------------------------------------------------------------
# Feedback List (with search, filter, sort, pagination)
# ---------------------------------------------------------------------------
@main_bp.route("/feedback")
@login_required
def feedback_list():
    """Render the feedback management page."""
    return render_template("feedback/list.html")


# ---------------------------------------------------------------------------
# Feedback Detail
# ---------------------------------------------------------------------------
@main_bp.route("/feedback/<int:feedback_id>")
@login_required
def feedback_detail(feedback_id):
    """View a single feedback entry (owner only)."""
    feedback = Feedback.query.filter_by(id=feedback_id, user_id=current_user.id).first_or_404()
    return render_template("feedback/detail.html", feedback=feedback)


# ---------------------------------------------------------------------------
# Edit Feedback
# ---------------------------------------------------------------------------
@main_bp.route("/feedback/<int:feedback_id>/edit", methods=["GET", "POST"])
@login_required
def feedback_edit(feedback_id):
    """Edit a feedback entry (owner only). Re-runs analysis on updated text."""
    feedback = Feedback.query.filter_by(id=feedback_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        new_text = sanitize_text(request.form.get("feedback_text", ""))
        new_category = request.form.get("category", feedback.category)

        valid_categories = ["Product", "Service", "Delivery", "Support", "Website", "Other"]
        if new_category not in valid_categories:
            new_category = "Other"

        if not new_text:
            flash("Feedback text cannot be empty.", "error")
            return render_template("feedback/edit.html", feedback=feedback)

        # Re-run analysis
        sentiment, polarity, subjectivity = analyze_sentiment(new_text)
        emotion = detect_emotion(new_text, polarity, subjectivity)
        keywords = extract_keywords(new_text)

        feedback.feedback_text = new_text
        feedback.category = new_category
        feedback.sentiment = sentiment
        feedback.polarity_score = polarity
        feedback.subjectivity_score = subjectivity
        feedback.emotion = emotion
        feedback.keywords = keywords
        db.session.commit()

        flash("Feedback updated successfully.", "success")
        return redirect(url_for("main.feedback_detail", feedback_id=feedback.id))

    return render_template("feedback/edit.html", feedback=feedback)


# ---------------------------------------------------------------------------
# Delete Feedback
# ---------------------------------------------------------------------------
@main_bp.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
@login_required
def feedback_delete(feedback_id):
    """Delete a single feedback entry (owner only)."""
    feedback = Feedback.query.filter_by(id=feedback_id, user_id=current_user.id).first_or_404()
    db.session.delete(feedback)
    db.session.commit()
    flash("Feedback deleted.", "success")
    return redirect(url_for("main.feedback_list"))


# ---------------------------------------------------------------------------
# Bulk Delete Feedback
# ---------------------------------------------------------------------------
@main_bp.route("/feedback/bulk-delete", methods=["POST"])
@login_required
def feedback_bulk_delete():
    """Bulk delete feedback entries (owner only)."""
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])

    if not ids:
        return jsonify({"success": False, "error": "No feedback selected."}), 400

    deleted = Feedback.query.filter(
        Feedback.id.in_(ids),
        Feedback.user_id == current_user.id
    ).delete(synchronize_session=False)
    db.session.commit()

    create_notification(current_user.id, f"Bulk delete completed: {deleted} feedback entries removed. 🗑️")

    return jsonify({"success": True, "deleted": deleted})


# ---------------------------------------------------------------------------
# File Upload & Analysis
# ---------------------------------------------------------------------------
@main_bp.route("/upload", methods=["GET"])
@login_required
def upload_page():
    """Render the file upload page."""
    return render_template("feedback/upload.html")


@main_bp.route("/upload", methods=["POST"])
@login_required
def upload_file():
    """
    Process uploaded CSV or TXT files.
    Each line/row is analyzed and saved as individual feedback.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    # Check extension
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed = current_app.config.get("ALLOWED_DATA_EXTENSIONS", {"csv", "txt"})
    if ext not in allowed:
        return jsonify({"success": False, "error": f"Only {', '.join(allowed)} files are allowed."}), 400

    category = request.form.get("category", "Other")
    valid_categories = ["Product", "Service", "Delivery", "Support", "Website", "Other"]
    if category not in valid_categories:
        category = "Other"

    try:
        content = file.read().decode("utf-8", errors="ignore")

        entries = []
        if ext == "csv":
            reader = csv.reader(io.StringIO(content))
            for row in reader:
                text = " ".join(row).strip()
                if text and len(text) > 2:
                    entries.append(text)
        else:  # txt
            for line in content.splitlines():
                text = line.strip()
                if text and len(text) > 2:
                    entries.append(text)

        if not entries:
            return jsonify({"success": False, "error": "File is empty or contains no valid text."}), 400

        # Analyze and store each entry
        results = {"total": 0, "positive": 0, "negative": 0, "neutral": 0}
        for text in entries:
            text = sanitize_text(text)
            sentiment, polarity, subjectivity = analyze_sentiment(text)
            emotion = detect_emotion(text, polarity, subjectivity)
            keywords = extract_keywords(text)

            fb = Feedback(
                user_id=current_user.id,
                feedback_text=text,
                category=category,
                sentiment=sentiment,
                polarity_score=polarity,
                subjectivity_score=subjectivity,
                emotion=emotion,
                keywords=keywords,
            )
            db.session.add(fb)
            results["total"] += 1
            results[sentiment.lower()] += 1

        db.session.commit()

        create_notification(
            current_user.id,
            f"Bulk analysis completed: {results['total']} entries processed from {file.filename}. 📊"
        )

        return jsonify({"success": True, "results": results, "filename": file.filename})

    except Exception as e:
        return jsonify({"success": False, "error": "Error processing file."}), 500
