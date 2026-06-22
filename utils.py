"""
Pulse — Utility Functions
===========================
Sentiment analysis, emotion detection, keyword extraction,
AI insights generation, and helper functions.
"""

import re
from collections import Counter
from textblob import TextBlob


# ---------------------------------------------------------------------------
# Stopwords for keyword extraction (common English words to exclude)
# ---------------------------------------------------------------------------
STOPWORDS = set(
    """
    the a an and or but if then else for to of in on at by with is are was were
    be been being this that these those it its as from i you he she we they
    them his her our your their not no do does did so very can will would
    should could just about into over under again further out up down my me
    have has had what which who whom there here when where why how all any
    both each few more most other some such only own same than too also
    really get got quite don doesn didn isn aren wasn weren won wouldn couldn
    ve ll re much still way well even much make made like use used one two
    thing things going go come came take took know knew want need us
    """.split()
)

# ---------------------------------------------------------------------------
# Emotion detection keyword sets (for rule-based classification)
# ---------------------------------------------------------------------------
EMOTION_KEYWORDS = {
    "Angry": {
        "angry", "furious", "outraged", "livid", "enraged", "infuriated",
        "irate", "mad", "pissed", "horrible", "terrible", "worst", "hate",
        "disgusting", "unacceptable", "ridiculous", "pathetic", "atrocious",
        "abysmal", "appalling", "dreadful", "outrageous", "scam", "fraud",
        "ripped", "steal", "stolen"
    },
    "Frustrated": {
        "frustrated", "annoyed", "irritated", "disappointed", "dissatisfied",
        "unhappy", "upset", "bothered", "inconvenient", "difficult", "confusing",
        "broken", "failed", "doesn't work", "not working", "poor", "bad",
        "slow", "delayed", "waiting", "waited", "wrong", "error", "issue",
        "problem", "complaint", "useless", "waste"
    },
    "Excited": {
        "excited", "amazing", "incredible", "fantastic", "phenomenal",
        "outstanding", "brilliant", "superb", "magnificent", "extraordinary",
        "thrilled", "blown away", "mind-blowing", "game-changer", "best ever",
        "love", "loving", "adore", "awesome", "wow", "perfect", "excellent",
        "exceptional", "remarkable", "wonderful"
    },
    "Happy": {
        "happy", "glad", "pleased", "delighted", "joyful", "cheerful",
        "thankful", "grateful", "appreciate", "thanks", "thank you",
        "great", "good", "nice", "lovely", "enjoy", "enjoyed", "pleasant",
        "comfortable", "friendly", "helpful", "kind", "warm", "welcoming"
    },
    "Satisfied": {
        "satisfied", "content", "fine", "okay", "decent", "reasonable",
        "adequate", "acceptable", "fair", "solid", "reliable", "consistent",
        "meets expectations", "as expected", "no complaints", "works well",
        "does the job", "sufficient", "appropriate"
    },
}


# ---------------------------------------------------------------------------
# Sentiment Analysis
# ---------------------------------------------------------------------------
def analyze_sentiment(text):
    """
    Run TextBlob sentiment analysis on the given text.
    Returns a tuple: (sentiment_label, polarity_score, subjectivity_score)

    Polarity ranges from -1.0 (very negative) to 1.0 (very positive).
    Subjectivity ranges from 0.0 (very objective) to 1.0 (very subjective).
    """
    blob = TextBlob(text)
    polarity = round(blob.sentiment.polarity, 4)
    subjectivity = round(blob.sentiment.subjectivity, 4)

    if polarity > 0.05:
        sentiment = "Positive"
    elif polarity < -0.05:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return sentiment, polarity, subjectivity


# ---------------------------------------------------------------------------
# Emotion Detection (rule-based)
# ---------------------------------------------------------------------------
def detect_emotion(text, polarity=0, subjectivity=0):
    """
    Detect basic emotion from text using a combination of
    keyword matching and polarity/subjectivity scores.

    Returns one of: Happy, Satisfied, Excited, Neutral, Frustrated, Angry
    """
    text_lower = text.lower()
    scores = {}

    # Score each emotion based on keyword matches
    for emotion, keywords in EMOTION_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                score += 1
        scores[emotion] = score

    # Find the emotion with the highest keyword match score
    max_emotion = max(scores, key=scores.get)
    max_score = scores[max_emotion]

    # If we have keyword matches, use them
    if max_score > 0:
        return max_emotion

    # Fallback: infer emotion from polarity and subjectivity
    if polarity >= 0.6:
        return "Excited"
    elif polarity >= 0.3:
        return "Happy"
    elif polarity >= 0.1:
        return "Satisfied"
    elif polarity <= -0.5:
        return "Angry"
    elif polarity <= -0.2:
        return "Frustrated"
    else:
        return "Neutral"


# ---------------------------------------------------------------------------
# Keyword Extraction
# ---------------------------------------------------------------------------
def extract_keywords(text, limit=10):
    """
    Extract common keywords from text, filtering out stopwords
    and very short tokens.
    Returns a comma-separated string of top keywords.
    """
    words = re.findall(r"[a-zA-Z']+", text.lower())
    meaningful = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    counter = Counter(meaningful)
    top_keywords = [word for word, count in counter.most_common(limit)]
    return ", ".join(top_keywords)


def get_keyword_frequencies(feedbacks, limit=10):
    """
    Build a word-frequency map across a list of feedback texts.
    Returns a list of (word, count) tuples.
    """
    counter = Counter()
    for fb in feedbacks:
        words = re.findall(r"[a-zA-Z']+", fb.feedback_text.lower())
        for word in words:
            if len(word) > 2 and word not in STOPWORDS:
                counter[word] += 1
    return counter.most_common(limit)


# ---------------------------------------------------------------------------
# AI Insights Generator
# ---------------------------------------------------------------------------
def generate_insights(feedbacks):
    """
    Dynamically generate natural language insights from feedback data.
    Returns a list of insight strings.
    """
    insights = []

    if not feedbacks:
        insights.append("No feedback data yet. Submit some feedback to see insights!")
        return insights

    total = len(feedbacks)
    sentiments = Counter(fb.sentiment for fb in feedbacks)
    categories = Counter(fb.category for fb in feedbacks)
    emotions = Counter(fb.emotion for fb in feedbacks)

    pos_count = sentiments.get("Positive", 0)
    neg_count = sentiments.get("Negative", 0)
    neu_count = sentiments.get("Neutral", 0)

    # Sentiment distribution insight
    pos_pct = (pos_count / total) * 100 if total > 0 else 0
    neg_pct = (neg_count / total) * 100 if total > 0 else 0

    if pos_pct >= 60:
        insights.append(f"🎉 Great news! {pos_pct:.0f}% of feedback is positive — customers are largely happy.")
    elif neg_pct >= 40:
        insights.append(f"⚠️ Attention needed: {neg_pct:.0f}% of feedback is negative.")
    elif pos_pct > neg_pct:
        insights.append(f"📊 Most feedback is positive ({pos_pct:.0f}%), but there's room for improvement.")
    else:
        insights.append(f"📊 Feedback is mixed — {pos_pct:.0f}% positive, {neg_pct:.0f}% negative.")

    # Category insights
    if categories:
        top_category = categories.most_common(1)[0]
        insights.append(f"📁 Most feedback is about \"{top_category[0]}\" ({top_category[1]} entries).")

        # Check for problem categories
        for cat, count in categories.items():
            cat_feedbacks = [fb for fb in feedbacks if fb.category == cat]
            cat_neg = sum(1 for fb in cat_feedbacks if fb.sentiment == "Negative")
            if cat_neg > 0 and (cat_neg / count) >= 0.5:
                insights.append(f"🔴 {cat}-related feedback has a high negative rate ({cat_neg}/{count}).")

    # Emotion insights
    if emotions:
        top_emotion = emotions.most_common(1)[0]
        if top_emotion[0] in ("Angry", "Frustrated"):
            insights.append(f"😤 Dominant emotion is \"{top_emotion[0]}\" — consider addressing pain points.")
        elif top_emotion[0] in ("Happy", "Excited"):
            insights.append(f"😊 Dominant emotion is \"{top_emotion[0]}\" — keep up the great work!")
        else:
            insights.append(f"🧠 Most common emotion detected: \"{top_emotion[0]}\".")

    # Average polarity insight
    avg_polarity = sum(fb.polarity_score for fb in feedbacks) / total if total > 0 else 0
    if avg_polarity > 0.3:
        insights.append(f"📈 Average sentiment score is strongly positive ({avg_polarity:.2f}).")
    elif avg_polarity > 0:
        insights.append(f"📈 Average sentiment score is mildly positive ({avg_polarity:.2f}).")
    elif avg_polarity < -0.3:
        insights.append(f"📉 Average sentiment score is strongly negative ({avg_polarity:.2f}).")
    elif avg_polarity < 0:
        insights.append(f"📉 Average sentiment score is mildly negative ({avg_polarity:.2f}).")

    # Subjectivity insight
    avg_subj = sum(fb.subjectivity_score for fb in feedbacks) / total if total > 0 else 0
    if avg_subj > 0.6:
        insights.append(f"💭 Feedback tends to be highly subjective (avg: {avg_subj:.2f}) — customers are sharing strong opinions.")
    elif avg_subj < 0.3:
        insights.append(f"📋 Feedback tends to be quite objective (avg: {avg_subj:.2f}) — more factual than emotional.")

    return insights


# ---------------------------------------------------------------------------
# Text Sanitization
# ---------------------------------------------------------------------------
def sanitize_text(text, max_length=2000):
    """
    Basic input sanitation:
    - Strip leading/trailing whitespace
    - Collapse internal whitespace
    - Limit max length
    """
    if text is None:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text[:max_length]


# ---------------------------------------------------------------------------
# Notification Helper
# ---------------------------------------------------------------------------
def create_notification(user_id, message):
    """
    Create and save a notification for the given user.
    Import here to avoid circular imports.
    """
    from .models import Notification
    from .extensions import db

    notification = Notification(user_id=user_id, message=message)
    db.session.add(notification)
    db.session.commit()
    return notification
