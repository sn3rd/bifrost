import os
import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

DB_PATH = os.getenv("DB_PATH", "/data/spam.db")


def db():
    return sqlite3.connect(DB_PATH)


def get_random_item(conn, reviewer):
    c = conn.cursor()

    c.execute("""
        SELECT id, bug_title, body, bug_url
        FROM content_items
        WHERE id NOT IN (
            SELECT content_id FROM reviews WHERE reviewer = ?
        )
        ORDER BY RANDOM()
        LIMIT 1
    """, (reviewer,))

    return c.fetchone()


@app.route("/")
def root():
    return redirect("/review")


# ---------------- REVIEWER ----------------
@app.route("/review")
def review():
    reviewer = request.args.get("user", "anonymous")

    conn = db()
    item = get_random_item(conn, reviewer)
    conn.close()

    return render_template("review.html", item=item, user=reviewer)


@app.route("/submit_review/<int:item_id>", methods=["POST"])
def submit_review(item_id):
    user = request.form["user"]
    verdict = request.form["verdict"]

    conn = db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO reviews (content_id, reviewer, verdict)
        VALUES (?, ?, ?)
    """, (item_id, user, verdict))

    conn.commit()
    conn.close()

    return redirect(f"/review?user={user}")


# ---------------- MODERATOR ----------------
@app.route("/moderator")
def moderator():
    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT
            c.id,
            c.bug_title,
            c.body,
            c.bug_url,

            SUM(CASE WHEN r.verdict='spam' THEN 1 ELSE 0 END),
            SUM(CASE WHEN r.verdict='not sure' THEN 1 ELSE 0 END),
            SUM(CASE WHEN r.verdict='not spam' THEN 1 ELSE 0 END)

        FROM content_items c
        LEFT JOIN reviews r ON c.id = r.content_id
        WHERE c.moderator_verdict IS NULL
        GROUP BY c.id
        ORDER BY COUNT(r.id) DESC
        LIMIT 1
    """)

    item = c.fetchone()
    conn.close()

    return render_template("moderator.html", item=item)


@app.route("/submit_moderator/<int:item_id>", methods=["POST"])
def submit_moderator(item_id):
    verdict = request.form["verdict"]

    conn = db()
    c = conn.cursor()

    c.execute("""
        UPDATE content_items
        SET moderator_verdict = ?
        WHERE id = ?
    """, (verdict, item_id))

    conn.commit()
    conn.close()

    return redirect("/moderator")


# ---------------- LEADERBOARD ----------------
@app.route("/leaderboard")
def leaderboard():
    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT
            reviewer,
            COUNT(*) as total,
            SUM(CASE WHEN r.verdict = c.moderator_verdict THEN 1 ELSE 0 END) as correct
        FROM reviews r
        JOIN content_items c ON r.content_id = c.id
        GROUP BY reviewer
        ORDER BY total DESC, correct DESC
    """)

    rows = c.fetchall()
    conn.close()

    return render_template("leaderboard.html", rows=rows)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
