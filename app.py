import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)
DB = "spam.db"


def db():
    return sqlite3.connect(DB)


@app.route("/")
def home():
    return redirect("/review")


# -------------------------
# REVIEWER VIEW
# -------------------------
@app.route("/review")
def review():
    reviewer = request.args.get("reviewer", "anonymous")

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT id, body, spam_score
        FROM content_items
        WHERE id NOT IN (
            SELECT content_id FROM reviews WHERE reviewer = ?
        )
        ORDER BY RANDOM()
        LIMIT 1
    """, (reviewer,))

    item = c.fetchone()
    conn.close()

    return render_template("review.html",
                           item=item,
                           reviewer=reviewer)


@app.route("/submit_review/<int:item_id>", methods=["POST"])
def submit_review(item_id):
    reviewer = request.form["reviewer"]
    verdict = request.form["verdict"]

    conn = db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO reviews (content_id, reviewer, verdict)
        VALUES (?, ?, ?)
    """, (item_id, reviewer, verdict))

    conn.commit()
    conn.close()

    return redirect(f"/review?reviewer={reviewer}")


# -------------------------
# MODERATOR VIEW
# -------------------------
@app.route("/moderator")
def moderator():

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT c.id, c.body, c.spam_score, COUNT(r.id)
        FROM content_items c
        LEFT JOIN reviews r ON c.id = r.content_id
        WHERE c.id NOT IN (
            SELECT content_id FROM moderator_reviews
        )
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
        INSERT INTO moderator_reviews (content_id, moderator, verdict)
        VALUES (?, ?, ?)
    """, (item_id, "moderator", verdict))

    c.execute("""
        UPDATE content_items
        SET moderator_verdict = ?
        WHERE id = ?
    """, (verdict, item_id))

    conn.commit()
    conn.close()

    return redirect("/moderator")


# -------------------------
# STATS
# -------------------------
@app.route("/stats/<reviewer>")
def stats(reviewer):

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*) FROM reviews WHERE reviewer = ?
    """, (reviewer,))
    total = c.fetchone()[0]

    c.execute("""
        SELECT COUNT(*)
        FROM reviews r
        JOIN content_items c ON r.content_id = c.id
        WHERE r.reviewer = ?
        AND r.verdict = c.moderator_verdict
    """, (reviewer,))
    correct = c.fetchone()[0]

    incorrect = total - correct

    conn.close()

    return render_template("stats.html",
                           reviewer=reviewer,
                           total=total,
                           correct=correct,
                           incorrect=incorrect)


# -------------------------
# LEADERBOARD
# -------------------------
@app.route("/leaderboard")
def leaderboard():

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT
            reviewer,
            COUNT(*) as total,
            SUM(CASE WHEN r.verdict = c.moderator_verdict THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN r.verdict != c.moderator_verdict THEN 1 ELSE 0 END) as incorrect
        FROM reviews r
        LEFT JOIN content_items c ON r.content_id = c.id
        GROUP BY reviewer
        ORDER BY total DESC, correct DESC, incorrect ASC
    """)

    rows = c.fetchall()
    conn.close()

    return render_template("leaderboard.html", rows=rows)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
