import os
import sqlite3
import httpx
import random
import sys
import re

API = "https://api.launchpad.net/devel/bugs"
DB_PATH = os.getenv("DB_PATH", "/data/spam.db")

DEBUG = os.getenv("SCRAPER_DEBUG", "1") == "1"


def log(msg):
    if DEBUG:
        print(msg, flush=True)


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


# -----------------------------
# HEURISTIC (RE-ORIENTED)
# -----------------------------

SPAM_SIGNALS = [
    "http", "www.", "buy now", "crypto", "bitcoin",
    "loan", "casino", "viagra", "investment", "profit",
    "!!!", "$$$"
]


def looks_like_spam(text: str) -> bool:
    """
    TRUE  -> spam / suspicious (SHOW IN REVIEW QUEUE)
    FALSE -> likely clean (SKIP REVIEW QUEUE)
    """

    if not text:
        return False

    t = text.lower()

    # strong spam signals
    if any(s in t for s in SPAM_SIGNALS):
        return True

    # link-heavy
    if t.count("http") >= 1:
        return True

    # overly aggressive formatting
    if len(text) > 0 and (text.count("!") > 5 or text.count("$") > 3):
        return True

    # extremely long weird blobs
    if len(text) > 5000:
        return True

    # code/log heavy but still possibly spam-like injection attempts
    code_ratio = len(re.findall(r"[{}();=<>]", text)) / max(len(text), 1)
    if code_ratio > 0.15:
        return True

    return False


def classify(text: str) -> bool:
    return looks_like_spam(text)


# -----------------------------
# SCRAPER
# -----------------------------

def scrape_bug(conn, bug_id):
    c = conn.cursor()

    log(f"\n=== BUG {bug_id} ===")

    try:
        r = httpx.get(f"{API}/{bug_id}", timeout=20)
        if r.status_code != 200:
            log(f"[BUG {bug_id}] HTTP {r.status_code}")
            return

        bug = r.json()

        title = bug.get("title", f"Bug {bug_id}")
        url = bug.get("web_link") or bug.get("self_link") or f"{API}/{bug_id}"

        messages_url = bug.get("messages_link") or f"{API}/{bug_id}/messages"
        mr = httpx.get(messages_url, timeout=20)

        if mr.status_code != 200:
            return

        messages = mr.json().get("entries", [])

        log(f"[BUG {bug_id}] messages={len(messages)}")

        for i, m in enumerate(messages):
            body = m.get("content")
            self_link = m.get("self_link")
            author = m.get("owner_link")

            if not body or not self_link:
                continue

            is_spam = classify(body)

            # ------------------------------------
            # NEW RULE (your requirement)
            # ------------------------------------
            if is_spam:
                is_review_candidate = 1   # suspicious → REVIEW
                log(f"[BUG {bug_id}][MSG {i}] SPAM-LIKE → REVIEW")
            else:
                is_review_candidate = 0   # clean → SKIP REVIEW
                log(f"[BUG {bug_id}][MSG {i}] CLEAN → NOT REVIEW")

            c.execute("""
                INSERT OR IGNORE INTO content_items
                (bug_id, bug_title, bug_url, message_self_link, author, body, is_review_candidate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                bug_id,
                title,
                url,
                self_link,
                author,
                body,
                is_review_candidate
            ))

            if c.rowcount == 0:
                log(f"[BUG {bug_id}][MSG {i}] duplicate ignored")
            else:
                log(f"[BUG {bug_id}][MSG {i}] inserted")

        c.execute("INSERT OR IGNORE INTO scraped_bugs VALUES (?)", (bug_id,))
        conn.commit()

        log(f"[BUG {bug_id}] DONE")

    except Exception as e:
        log(f"[BUG {bug_id}] ERROR {e}")


def main():
    n = int(sys.argv[1])

    conn = db()
    ensure_schema(conn)

    seen = already_scraped(conn)
    ids = pick_ids(n, seen)

    log(f"Scraping {len(ids)} bugs")

    for i in ids:
        scrape_bug(conn, i)

    conn.close()


if __name__ == "__main__":
    main()
