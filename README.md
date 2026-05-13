# bifrost
A crowdsourced moderation and anti-spam system for Launchpad bugs and questions.

bifrost scrapes Launchpad bug comments, applies lightweight heuristic spam scoring, and presents suspicious content to human reviewers in a Tinder-style moderation queue.

The system is intentionally simple:

- Python
- Flask
- SQLite
- No ORM
- No JavaScript framework
- Single-container deployment

---

# Features

## Scraping

`scraper.py`:

- Scrapes Launchpad bugs via the public API
- Fetches bug metadata and comments
- Tracks previously scraped bug IDs
- Avoids duplicate comment imports
- Applies heuristic filtering before queueing content for review

Suspicious comments are stored with:

```text
is_review_candidate = 1
````

Likely-safe comments are stored with:

```text
is_review_candidate = 0
```

This reduces reviewer noise while still preserving data for future analysis.

---

## Reviewer Queue

Reviewers visit:

```text
/review
```

Reviewers are shown:

* Bug title
* Link to Launchpad bug
* Comment content

They can classify content as:

* Not Spam
* Not Sure
* Spam

Each review:

* is recorded in SQLite
* advances automatically to the next random item

Reviewers also see:

* progress bar
* leaderboard
* personal review progress

---

## Moderator Queue

Moderators visit:

```text
/moderator
```

Moderators:

* see reviewer vote counts
* make the final decision
* apply canonical verdicts

Reviewer accuracy is later compared against moderator verdicts.

Reviewers cannot moderate.
Moderators cannot review.

---

## Leaderboard

The leaderboard ranks reviewers based on:

1. Total reviews submitted
2. Correct reviews
3. Incorrect reviews

Moderators are excluded.

---

## Authentication

Authentication is intentionally minimal.

Users:

* create a username
* receive a UUID
* use the UUID as a login token

Sessions are maintained using cookies.

This is NOT secure authentication.

The UI intentionally warns users:

* not to use real secrets
* not to reuse credentials

---

# Architecture

## Components

| File         | Purpose                         |
| ------------ | ------------------------------- |
| `app.py`     | Flask web application           |
| `scraper.py` | Launchpad scraper               |
| `extract.py` | Export moderator-confirmed spam |
| `admin.py`   | Create moderator accounts       |
| `init_db.py` | Initialize SQLite schema        |
| `scoring.py` | Heuristic spam scoring          |
| `templates/` | HTML templates                  |
| `static/`    | Images and assets               |

---

# Database

SQLite database path:

```text
/data/spam.db
```

The database can be externalized using a Docker bind mount.

---

# Running

## Build

```bash
docker build -t bifrost .
```

---

## Run

```bash
docker run \
    -p 8000:8000 \
    -v $(pwd)/data:/data \
    bifrost
```

The application will be available at:

```text
http://localhost:8000
```

---

# Initialize Database

If needed:

```bash
docker run \
    -v $(pwd)/data:/data \
    bifrost \
    python init_db.py
```

---

# Scraping Launchpad

Scrape random Launchpad bugs:

```bash
docker run \
    -v $(pwd)/data:/data \
    bifrost \
    python scraper.py --count 100
```

The scraper:

* skips already-scraped bugs
* logs progress
* applies heuristic pre-filtering
* stores suspicious comments for review

---

# Creating Moderator Accounts

Use:

```bash
docker run -it \
    -v $(pwd)/data:/data \
    bifrost \
    python admin.py
```

This creates users with role:

```text
moderator
```

---

# Exporting Spam - Planned, prompted, and generated, but not reviewed or tested (insufficient time); included for completeness

Export moderator-confirmed spam:

```bash
docker run \
    -v $(pwd)/data:/data \
    bifrost \
    python extract.py
```

Output format:

```text
JSONL
```

Example:

```json
{
  "bug_id": 123,
  "bug_title": "Example bug",
  "bug_url": "https://bugs.launchpad.net/...",
  "message_link": "https://api.launchpad.net/...",
  "content": "spam message",
  "label": "spam"
}
```

This format is convenient for:

* ML pipelines
* anti-spam systems
* LLM evaluation
* analytics
* classifier training

---

# Heuristic Filtering

The current scoring model is intentionally simple.

Signals include:

* suspicious domains
* crypto keywords
* SEO spam phrases
* excessive links
* marketing language
* repeated spam patterns

The heuristic gate exists to reduce reviewer fatigue.

---

# Long-Term Direction

This MVP is designed to evolve toward:

* reviewer trust weighting
* disagreement analysis
* ML-assisted spam classification
* LLM-resistant moderation workflows
* coordinated spam campaign detection
* deterministic queue assignment
* semi-supervised training pipelines

---

# Security Warning

This project intentionally uses:

* UUID-based login
* SQLite
* simple cookies
* no CSRF protection
* no hardened authentication

It is suitable for:

* prototypes
* internal tools
* experimentation

It is NOT suitable for production deployment without additional hardening.

---

# License

MIT

