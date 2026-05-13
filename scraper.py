import os
import sqlite3
import httpx
import random
import sys

API = "https://api.launchpad.net/devel/bugs"
DB_PATH = os.getenv("DB_PATH", "/data/spam.db")


def db():
    return sqlite3.connect(DB_PATH)


def ensure_schema(conn):
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS scraped_bugs (
        bug_id INTEGER PRIMARY KEY
    )
    """)
    conn.commit()


def already_scraped(conn):
    c = conn.cursor()
    c.execute("SELECT bug_id FROM scraped_bugs")
    return {r[0] for r in c.fetchall()}


def pick_ids(n, seen):
    out = []
    while len(out) < n:
        x = random.randint(1, 200000)
        if x not in seen:
            out.append(x)
    return out


def scrape_bug(conn, bug_id):
    c = conn.cursor()

    try:
        bug_url = f"{API}/{bug_id}"
        r = httpx.get(bug_url, timeout=20)

        if r.status_code != 200:
            return

        bug = r.json()

        title = bug.get("title", f"Bug {bug_id}")
        url = bug.get("web_link") or bug.get("self_link") or bug_url

        messages_url = bug.get("messages_link") or f"{bug_url}/messages"
        mr = httpx.get(messages_url, timeout=20)

        if mr.status_code != 200:
            return

        messages = mr.json().get("entries", [])

        for m in messages:
            body = m.get("content")
            self_link = m.get("self_link")
            author = m.get("owner_link")

            if not body or not self_link:
                continue

            c.execute("""
                INSERT OR IGNORE INTO content_items
                (bug_id, bug_title, bug_url, message_self_link, author, body)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (bug_id, title, url, self_link, author, body))

        c.execute("INSERT OR IGNORE INTO scraped_bugs VALUES (?)", (bug_id,))
        conn.commit()

        print(f"Scraped {bug_id}")

    except Exception as e:
        print("Error:", e)


def main():
    n = int(sys.argv[1])

    conn = db()
    ensure_schema(conn)

    seen = already_scraped(conn)
    ids = pick_ids(n, seen)

    for i in ids:
        scrape_bug(conn, i)

    conn.close()


if __name__ == "__main__":
    main()
