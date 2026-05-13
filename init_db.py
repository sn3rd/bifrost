import sqlite3

conn = sqlite3.connect("spam.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS content_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT,
    title TEXT,
    body TEXT,
    url TEXT,
    spam_score INTEGER,
    moderator_verdict TEXT
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
