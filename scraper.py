import sqlite3
import httpx
import random
import sys

from scoring import compute_score

API = "https://api.launchpad.net/devel/bugs"
DB = "spam.db"


def db():
    return sqlite3.connect(DB)


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
        r = httpx.get(f"{API}/{bug_id}", timeout=20)
        if r.status_code != 200:
            return

        data = r.json()

        messages_url = data.get("messages_link") or f"{API}/{bug_id}/messages"
        mr = httpx.get(messages_url, timeout=20)

        if mr.status_code != 200:
            return

        messages = mr.json().get("entries", [])

        for m in messages:
            body = m.get("content")
            link = m.get("self_link")

            if not body or not link:
                continue

            score = compute_score(body)

            c.execute("""
                INSERT OR IGNORE INTO content_items
                (bug_id, message_self_link, body, spam_score)
                VALUES (?, ?, ?, ?)
            """, (bug_id, link, body, score))

        c.execute("""
            INSERT OR IGNORE INTO scraped_bugs (bug_id)
            VALUES (?)
        """, (bug_id,))

        conn.commit()
        print(f"Scraped bug {bug_id}")

    except Exception as e:
        print(f"Error bug {bug_id}: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <num_bugs>")
        return

    n = int(sys.argv[1])

    conn = db()
    seen = get_scraped(conn)

    targets = pick_bug_ids(n, seen)

    print(f"Scraping {len(targets)} bugs")

    for bid in targets:
        scrape_bug(conn, bid)

    conn.close()


if __name__ == "__main__":
    main()
