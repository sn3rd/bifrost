import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "/data/spam.db")


def db():
    return sqlite3.connect(DB_PATH)


def main():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        uuid TEXT UNIQUE,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS content_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bug_id INTEGER,
        bug_title TEXT,
        bug_url TEXT,
        message_self_link TEXT UNIQUE,
        author TEXT,
        body TEXT,
        moderator_verdict TEXT,
        is_review_candidate INTEGER DEFAULT 1
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_id INTEGER,
        reviewer_uuid TEXT,
        verdict TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS scraped_bugs (
        bug_id INTEGER PRIMARY KEY
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
