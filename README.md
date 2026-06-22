# Pulse — Customer Feedback Sentiment Analyzer

A full-stack Flask application that collects customer feedback, classifies its
sentiment with TextBlob, stores everything in SQLite, and visualizes the
results on a dashboard (Chart.js pie/bar/trend charts, a word cloud,
search + filter, pagination, and CSV export gated behind a simple admin login).

---

## 1. Features

- **Home page** — feedback form with instant AJAX sentiment analysis, shown
  as an animated polarity gauge (no page reload).
- **Sentiment engine** — TextBlob polarity score; classified as Positive
  (`> 0`), Negative (`< 0`), or Neutral (`= 0`).
- **SQLite storage** — every submission saved with text, sentiment, polarity
  score, and timestamp.
- **Dashboard** — total/positive/negative/neutral counts, pie chart, bar
  chart, a 14-day trend chart, a word cloud of frequent terms, and a
  paginated, searchable, filterable feedback table.
- **Search & filter** — keyword search plus sentiment filter, server-side
  pagination.
- **CSV export** — download all records; requires admin login
  (Flask-Login).
- **Dark mode** — toggle in the nav bar, preference saved in the browser.
- **Validation & error handling** — empty submissions are rejected with a
  friendly message; database errors return JSON errors instead of crashing.
- **Security basics** — all SQL uses parameterized queries (no string
  concatenation), input is trimmed/length-capped, secret key and admin
  credentials are read from environment variables.

---

## 2. Project structure

```
feedback-analyzer/
├── app.py                  # Flask app: routes, DB helpers, sentiment logic
├── requirements.txt
├── database.db             # created automatically on first run
├── templates/
│   ├── base.html            # nav bar, dark mode, flash messages
│   ├── index.html           # feedback form + result gauge
│   ├── dashboard.html        # stats, charts, search table
│   └── login.html
├── static/
│   ├── css/style.css
│   └── js/
│       ├── script.js         # home page logic
│       └── dashboard.js      # dashboard/chart/search logic
└── exports/                 # timestamped CSV export archive
```

---

## 3. Local setup

### Requirements
- Python 3.9+
- pip

### Steps

```bash
# 1. Move into the project folder
cd feedback-analyzer

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (First run only) TextBlob needs a small NLTK corpus for some features.
#    The core polarity/subjectivity scoring used by this app works without
#    extra downloads, but if you see corpus-related warnings, run:
python -m textblob.download_corpora
```

---

## 4. Running the app

```bash
python app.py
```

The app starts on **http://localhost:5000**. The SQLite database
(`database.db`) and `feedback` table are created automatically the first
time the app runs — no manual migration step needed.

### Admin login (for CSV export)
Default development credentials:

```
username: admin
password: admin123
```

Override them with environment variables before starting the app:

```bash
export SECRET_KEY="a-long-random-string"
export ADMIN_USERNAME="your_admin"
export ADMIN_PASSWORD="a-strong-password"
python app.py
```

(On Windows, use `set VAR=value` instead of `export`.)

---

## 5. Using the app

1. Open `/` and submit a piece of feedback — you'll see the sentiment,
   polarity score, and gauge instantly.
2. Open `/dashboard` to see aggregate stats, charts, the word cloud, and the
   searchable record table.
3. Use the search box and sentiment dropdown to filter records; use the
   pagination controls at the bottom of the table to page through results.
4. Log in at `/login` to unlock the **Export CSV** button on the dashboard.

---

## 6. Deployment notes

This app is structured to be deployment-ready for any standard Python host
(Render, Railway, Fly.io, a VPS, etc.).

1. **Use a production WSGI server** instead of Flask's dev server:
   ```bash
   gunicorn app:app --bind 0.0.0.0:8000 --workers 2
   ```
   (`gunicorn` is already listed in `requirements.txt`.)

2. **Set environment variables** on your host for `SECRET_KEY`,
   `ADMIN_USERNAME`, and `ADMIN_PASSWORD` — never ship the default dev
   credentials to production.

3. **Persist the database file.** `database.db` is a single SQLite file at
   the project root. On platforms with ephemeral filesystems (some
   container/PaaS setups), mount a persistent volume for the project
   directory, or swap in a hosted database if you need durability across
   redeploys.

4. **Disable debug mode.** The `app.run(debug=True)` line is only used when
   running `python app.py` directly for local development; gunicorn does
   not use it.

5. **HTTPS.** Put the app behind a reverse proxy (nginx, or your platform's
   built-in TLS termination) so cookies/login sessions are sent over HTTPS.

---

## 7. How the sentiment classification works

TextBlob's `.sentiment.polarity` returns a float from **-1.0** (very
negative) to **1.0** (very positive):

| Polarity        | Label    |
|------------------|----------|
| `> 0`            | Positive |
| `< 0`            | Negative |
| `= 0`            | Neutral  |

This score and label are stored alongside the original feedback text and a
timestamp, which is what powers every chart and table on the dashboard.

---

## 8. Troubleshooting

- **"No module named textblob"** — make sure your virtual environment is
  activated and `pip install -r requirements.txt` completed without errors.
- **Charts/word cloud don't show data** — submit a few feedback entries
  first; the dashboard reflects whatever is currently in `database.db`.
- **Export button missing** — you need to be logged in as admin; visit
  `/login`.
- **Port already in use** — run `python app.py` with a different port by
  editing the `app.run(...)` call at the bottom of `app.py`, or stop the
  process using port 5000.
