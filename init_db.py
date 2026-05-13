import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "/data/spam.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS content_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    bug_id INTEGER NOT NULL,
    bug_title TEXT,
    bug_url TEXT,

    message_self_link TEXT UNIQUE,

    author TEXT,
    body TEXT NOT NULL,

    spam_score INTEGER DEFAULT 0,
    moderator_verdict TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS scraped_bugs (
    bug_id INTEGER PRIMARY KEY
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER,
    reviewer TEXT,
    verdict TEXT
)
""")

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
