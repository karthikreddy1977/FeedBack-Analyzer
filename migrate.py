"""
Pulse — Database Migration Script
====================================
Migrates existing feedback data from the old schema (no user_id) to the new schema.
Assigns all existing feedback to the admin user.

Usage: python -m migrations.migrate
"""

import os
import sys
import sqlite3
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(BASE_DIR, "database.db")
BACKUP = os.path.join(BASE_DIR, "database_backup.db")


def migrate():
    """
    Migration steps:
    1. Backup the existing database
    2. Read old feedback data
    3. The new app factory will create new tables via SQLAlchemy
    4. Insert old feedback into the new schema under admin user
    """
    import shutil

    if not os.path.exists(DATABASE):
        print("No existing database found. Skipping migration.")
        return

    # Backup
    print(f"Backing up database to {BACKUP}...")
    shutil.copy2(DATABASE, BACKUP)
    print("Backup complete.")

    # Read old data
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    try:
        old_feedback = conn.execute(
            "SELECT feedback_text, sentiment, polarity_score, created_at FROM feedback"
        ).fetchall()
        print(f"Found {len(old_feedback)} existing feedback entries.")
    except sqlite3.OperationalError:
        print("Old feedback table not found. Nothing to migrate.")
        old_feedback = []

    conn.close()

    if not old_feedback:
        print("No data to migrate.")
        return

    # Delete old database so SQLAlchemy can create fresh schema
    os.remove(DATABASE)

    # Create new app and tables
    from app_pkg import create_app
    app = create_app()

    with app.app_context():
        from app_pkg.extensions import db
        from app_pkg.models import User, Feedback
        from app_pkg.utils import analyze_sentiment, detect_emotion, extract_keywords

        # Find admin user (created by seed)
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            print("ERROR: Admin user not found after seeding.")
            return

        # Migrate old feedback
        print("Migrating old feedback data...")
        for row in old_feedback:
            text = row["feedback_text"]
            old_sentiment = row["sentiment"]
            old_polarity = row["polarity_score"]
            old_created = row["created_at"]

            # Re-analyze for new fields
            _, _, subjectivity = analyze_sentiment(text)
            emotion = detect_emotion(text, old_polarity, subjectivity)
            keywords = extract_keywords(text)

            fb = Feedback(
                user_id=admin.id,
                feedback_text=text,
                category="Other",
                sentiment=old_sentiment,
                polarity_score=old_polarity,
                subjectivity_score=subjectivity,
                emotion=emotion,
                keywords=keywords,
                created_at=datetime.strptime(old_created, "%Y-%m-%d %H:%M:%S") if old_created else datetime.now(timezone.utc),
            )
            db.session.add(fb)

        db.session.commit()
        print(f"Successfully migrated {len(old_feedback)} feedback entries to admin user.")
        print("Migration complete!")


if __name__ == "__main__":
    migrate()
