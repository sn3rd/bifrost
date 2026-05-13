import sqlite3

conn = sqlite3.connect("spam.db")
c = conn.cursor()

# Individual Launchpad messages (comments)
c.execute("""
CREATE TABLE IF NOT EXISTS content_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bug_id INTEGER NOT NULL,
    message_self_link TEXT UNIQUE,
    author TEXT,
    body TEXT NOT NULL,
    spam_score INTEGER DEFAULT 0,
    moderator_verdict TEXT
)
""")

# Track scraped bugs
c.execute("""
CREATE TABLE IF NOT EXISTS scraped_bugs (
    bug_id INTEGER PRIMARY KEY
)
""")

# user votes
c.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER,
    reviewer TEXT,
    verdict TEXT
)
""")

# moderator ground truth
c.execute("""
CREATE TABLE IF NOT EXISTS moderator_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER,
    moderator TEXT,
    verdict TEXT
)
""")

conn.commit()
conn.close()
