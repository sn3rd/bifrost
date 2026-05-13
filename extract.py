import os
import sqlite3
import json
import argparse

DB_PATH = os.getenv("DB_PATH", "/data/spam.db")


def db():
    return sqlite3.connect(DB_PATH)


def fetch_spam_items(conn):
    c = conn.cursor()

    c.execute("""
        SELECT
            bug_id,
            bug_title,
            bug_url,
            message_self_link,
            body,
            moderator_verdict
        FROM content_items
        WHERE moderator_verdict = 'spam'
        ORDER BY bug_id ASC
    """)

    return c.fetchall()


def to_jsonl(rows, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for r in rows:
            bug_id, title, url, msg_link, body, verdict = r

            record = {
                "bug_id": bug_id,
                "bug_title": title,
                "bug_url": url,
                "message_link": msg_link,
                "content": body,
                "label": verdict
            }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extract moderator-labelled spam content")
    parser.add_argument(
        "--output",
        default="/data/spam_export.jsonl",
        help="Output JSONL file path"
    )

    args = parser.parse_args()

    conn = db()

    rows = fetch_spam_items(conn)

    conn.close()

    print(f"[extract] exporting {len(rows)} spam items -> {args.output}")

    to_jsonl(rows, args.output)

    print("[extract] done")


if __name__ == "__main__":
    main()
