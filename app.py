"""
Pulse — Customer Feedback Sentiment Analyzer (SaaS Edition)
============================================================
Entry point. Uses the application factory pattern.
Run with: python app.py
"""

from app_pkg import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
