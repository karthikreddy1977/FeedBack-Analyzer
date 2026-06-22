"""
Pulse — API Routes
====================
JSON endpoints for dashboard statistics, search/filter/pagination,
and notification management. All data is scoped to the current user.
"""

from collections import Counter
from flask import jsonify, request
from flask_login import login_required, current_user

from . import api_bp
from ..extensions import db
from ..models import Feedback, Notification
from ..utils import (
    sanitize_text, get_keyword_frequencies, generate_insights
)


# ---------------------------------------------------------------------------
# Dashboard Stats (user-scoped)
# ---------------------------------------------------------------------------
@api_bp.route("/stats")
@login_required
def stats():
    """
    Returns comprehensive dashboard statistics for the current user:
    - Sentiment counts, average scores
    - Category distribution, emotion distribution
    - Monthly trends, top keywords
    - AI-generated insights
    """
    feedbacks = Feedback.query.filter_by(user_id=current_user.id).all()

    total = len(feedbacks)
    sentiments = Counter(fb.sentiment for fb in feedbacks)
    categories = Counter(fb.category for fb in feedbacks)
    emotions = Counter(fb.emotion for fb in feedbacks)

    # Average scores
    avg_polarity = sum(fb.polarity_score for fb in feedbacks) / total if total > 0 else 0
    avg_subjectivity = sum(fb.subjectivity_score for fb in feedbacks) / total if total > 0 else 0

    # Most common category and emotion
    most_common_category = categories.most_common(1)[0][0] if categories else "N/A"
    most_common_emotion = emotions.most_common(1)[0][0] if emotions else "N/A"

    # Monthly trend data (last 12 months)
    trend_rows = db.session.execute(
        db.text("""
            SELECT strftime('%Y-%m', created_at) AS month, sentiment, COUNT(*) AS c
            FROM feedback
            WHERE user_id = :uid
            GROUP BY month, sentiment
            ORDER BY month ASC
        """),
        {"uid": current_user.id}
    ).fetchall()

    trend_map = {}
    for row in trend_rows:
        month = row[0]
        trend_map.setdefault(month, {"Positive": 0, "Negative": 0, "Neutral": 0})
        trend_map[month][row[1]] = row[2]

    # Category distribution
    category_data = {cat: count for cat, count in categories.items()}

    # Emotion distribution
    emotion_data = {emo: count for emo, count in emotions.items()}

    # Top keywords across all user feedback
    keyword_freq = get_keyword_frequencies(feedbacks, limit=10)

    # AI insights
    insights = generate_insights(feedbacks)

    # Monthly growth (compare current month count vs previous month)
    months_sorted = sorted(trend_map.keys())
    monthly_growth = 0
    if len(months_sorted) >= 2:
        current_month_total = sum(trend_map[months_sorted[-1]].values())
        prev_month_total = sum(trend_map[months_sorted[-2]].values())
        if prev_month_total > 0:
            monthly_growth = round(((current_month_total - prev_month_total) / prev_month_total) * 100, 1)

    return jsonify({
        "total": total,
        "positive": sentiments.get("Positive", 0),
        "negative": sentiments.get("Negative", 0),
        "neutral": sentiments.get("Neutral", 0),
        "avg_polarity": round(avg_polarity, 4),
        "avg_subjectivity": round(avg_subjectivity, 4),
        "most_common_category": most_common_category,
        "most_common_emotion": most_common_emotion,
        "monthly_growth": monthly_growth,
        "trend": trend_map,
        "categories": category_data,
        "emotions": emotion_data,
        "keyword_freq": keyword_freq,
        "insights": insights,
    })


# ---------------------------------------------------------------------------
# Search / Filter / Paginate Feedback (user-scoped)
# ---------------------------------------------------------------------------
@api_bp.route("/search")
@login_required
def search_feedback():
    """
    Search + filter + sort + paginate feedback records for the current user.
    Query params:
      q         - keyword search within feedback_text
      sentiment - Positive / Negative / Neutral / All
      category  - Product / Service / Delivery / Support / Website / Other / All
      sort      - created_at / polarity_score / sentiment
      order     - asc / desc
      date_from - YYYY-MM-DD start date
      date_to   - YYYY-MM-DD end date
      page      - page number (default 1)
      per_page  - results per page (default 10, max 100)
    """
    keyword = sanitize_text(request.args.get("q", ""))
    sentiment = request.args.get("sentiment", "All")
    category = request.args.get("category", "All")
    sort_by = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    try:
        per_page = min(100, max(1, int(request.args.get("per_page", 10))))
    except ValueError:
        per_page = 10

    # Base query — always scoped to current user
    query = Feedback.query.filter_by(user_id=current_user.id)

    # Apply filters
    if keyword:
        query = query.filter(Feedback.feedback_text.ilike(f"%{keyword}%"))

    if sentiment in ("Positive", "Negative", "Neutral"):
        query = query.filter_by(sentiment=sentiment)

    if category in ("Product", "Service", "Delivery", "Support", "Website", "Other"):
        query = query.filter_by(category=category)

    if date_from:
        query = query.filter(Feedback.created_at >= date_from)

    if date_to:
        query = query.filter(Feedback.created_at <= date_to + " 23:59:59")

    # Sorting
    sort_column = getattr(Feedback, sort_by, Feedback.created_at)
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    total_results = query.count()
    total_pages = max(1, (total_results + per_page - 1) // per_page)
    results = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "results": [fb.to_dict() for fb in results],
        "total_results": total_results,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    })


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
@api_bp.route("/notifications")
@login_required
def get_notifications():
    """Get the current user's recent notifications and unread count."""
    notifications = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()).limit(20).all()

    unread_count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()

    return jsonify({
        "notifications": [n.to_dict() for n in notifications],
        "unread_count": unread_count,
    })


@api_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notif_id):
    """Mark a single notification as read."""
    notif = Notification.query.filter_by(
        id=notif_id, user_id=current_user.id
    ).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({"success": True})


@api_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for the current user."""
    Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True})
