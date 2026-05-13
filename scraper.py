import os
import sqlite3
import httpx
import random
import sys

from scoring import compute_score

API_BASE = "https://api.launchpad.net/devel/bugs"

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


def get_scraped(conn):
    c = conn.cursor()
    c.execute("SELECT bug_id FROM scraped_bugs")
    return {r[0] for r in c.fetchall()}


def pick_bug_ids(n, seen):
    ids = []
    attempts = 0

    while len(ids) < n and attempts < n * 20:
        bid = random.randint(1, 200000)
        if bid not in seen:
            ids.append(bid)
        attempts += 1

    return ids


def scrape_bug(conn, bug_id):
    c = conn.cursor()

    try:
        bug_url = f"{API_BASE}/{bug_id}"

        r = httpx.get(bug_url, timeout=20)
        if r.status_code != 200:
            return

        bug = r.json()

        bug_title = bug.get("title", f"Bug {bug_id}")
        web_link = bug.get("web_link") or bug.get("self_link") or bug_url

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

            score = compute_score(body)

            c.execute("""
                INSERT OR IGNORE INTO content_items
                (bug_id, bug_title, bug_url, message_self_link, author, body, spam_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                bug_id,
                bug_title,
                web_link,
                self_link,
                author,
                body,
                score
            ))

        c.execute("""
            INSERT OR IGNORE INTO scraped_bugs (bug_id)
            VALUES (?)
        """, (bug_id,))

        conn.commit()

        print(f"Scraped bug {bug_id}: {bug_title}")

    except Exception as e:
        print(f"Error bug {bug_id}: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <num_bugs>")
        return

    n = int(sys.argv[1])

    conn = db()
    ensure_schema(conn)

    seen = get_scraped(conn)
    targets = pick_bug_ids(n, seen)

    print(f"Scraping {len(targets)} bugs...")

    for bid in targets:
        scrape_bug(conn, bid)

    conn.close()


if __name__ == "__main__":
    main()
