import os
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, make_response

app = Flask(__name__)

DB_PATH = os.getenv("DB_PATH", "/data/spam.db")


# ---------------- DB ----------------

def db():
    return sqlite3.connect(DB_PATH)


# ---------------- USER ----------------

def get_user(conn, uuid_str):
    c = conn.cursor()
    c.execute("SELECT username, uuid, role FROM users WHERE uuid = ?", (uuid_str,))
    return c.fetchone()


def resolve_user():
    uuid_str = request.cookies.get("uuid")
    if not uuid_str:
        return None

    conn = db()
    user = get_user(conn, uuid_str)
    conn.close()
    return user


# ---------------- PROGRESS ----------------

def get_review_progress(conn, reviewer_uuid):
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM content_items WHERE is_review_candidate = 1")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM reviews WHERE reviewer_uuid = ?", (reviewer_uuid,))
    done = c.fetchone()[0]

    return done, total


def get_moderation_progress(conn):
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM content_items WHERE is_review_candidate = 1")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM content_items WHERE moderator_verdict IS NOT NULL")
    done = c.fetchone()[0]

    return done, total


# ---------------- AUTH ----------------

@app.route("/auth", methods=["GET", "POST"])
def auth():
    error = None

    if request.method == "POST":
        action = request.form.get("action")

        conn = db()
        c = conn.cursor()

        if action == "create":
            username = request.form["username"]
            new_uuid = str(uuid.uuid4())

            try:
                c.execute("""
                    INSERT INTO users (username, uuid, role)
                    VALUES (?, ?, 'reviewer')
                """, (username, new_uuid))
                conn.commit()
            except sqlite3.IntegrityError:
                conn.close()
                return render_template("auth.html", error="Username already exists")

            conn.close()

            resp = make_response(redirect("/review"))
            resp.set_cookie("uuid", new_uuid)
            return resp

        if action == "login":
            uuid_str = request.form["uuid"]

            user = get_user(conn, uuid_str)
            conn.close()

            if not user:
                return render_template("auth.html", error="Invalid UUID")

            resp = make_response(redirect("/review"))
            resp.set_cookie("uuid", uuid_str)
            return resp

    return render_template("auth.html", error=error)


@app.route("/logout")
def logout():
    resp = make_response(redirect("/auth"))
    resp.delete_cookie("uuid")
    return resp


# ---------------- REVIEW ----------------

def get_item(conn, reviewer_uuid):
    c = conn.cursor()

    c.execute("""
        SELECT id, bug_title, body, bug_url
        FROM content_items
        WHERE is_review_candidate = 1
        AND id NOT IN (
            SELECT content_id FROM reviews WHERE reviewer_uuid = ?
        )
        ORDER BY RANDOM()
        LIMIT 1
    """, (reviewer_uuid,))

    return c.fetchone()


@app.route("/")
def root():
    return redirect("/review")


@app.route("/review")
def review():
    user = resolve_user()
    if not user:
        return redirect("/auth")

    username, uuid_str, role = user

    # ❌ moderators cannot review
    if role != "reviewer":
        return render_template(
            "review.html",
            user=user,
            blocked=True,
            block_message="Reviews are only available to reviewers."
        )

    conn = db()

    item = get_item(conn, uuid_str)
    done, total = get_review_progress(conn, uuid_str)

    conn.close()

    return render_template(
        "review.html",
        item=item,
        user=user,
        progress_done=done,
        progress_total=total,
        blocked=False
    )


@app.route("/submit_review/<int:item_id>", methods=["POST"])
def submit_review(item_id):
    user = resolve_user()
    if not user:
        return redirect("/auth")

    _, uuid_str, _ = user
    verdict = request.form["verdict"]

    conn = db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO reviews (content_id, reviewer_uuid, verdict)
        VALUES (?, ?, ?)
    """, (item_id, uuid_str, verdict))

    conn.commit()
    conn.close()

    return redirect("/review")


# ---------------- MODERATOR ----------------

@app.route("/moderator")
def moderator():
    user = resolve_user()
    if not user:
        return redirect("/auth")

    username, uuid_str, role = user

    # ❌ reviewers cannot moderate
    if role != "moderator":
        return render_template(
            "moderator.html",
            user=user,
            blocked=True,
            block_message="Permission denied. Moderation is restricted to moderators only."
        )

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
        WHERE c.is_review_candidate = 1
        AND c.moderator_verdict IS NULL
        GROUP BY c.id
        ORDER BY COUNT(r.id) DESC
        LIMIT 1
    """)

    item = c.fetchone()

    done, total = get_moderation_progress(conn)

    conn.close()

    return render_template(
        "moderator.html",
        item=item,
        user=user,
        progress_done=done,
        progress_total=total,
        blocked=False
    )


@app.route("/submit_moderator/<int:item_id>", methods=["POST"])
def submit_moderator(item_id):
    user = resolve_user()
    if not user:
        return redirect("/auth")

    _, _, role = user

    if role != "moderator":
        return "Permission denied", 403

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
            u.username,
            COUNT(r.id),
            SUM(CASE WHEN r.verdict = c.moderator_verdict THEN 1 ELSE 0 END)
        FROM users u
        LEFT JOIN reviews r ON u.uuid = r.reviewer_uuid
        LEFT JOIN content_items c ON r.content_id = c.id
        WHERE u.role != 'moderator'
        GROUP BY u.username
        ORDER BY COUNT(r.id) DESC
    """)

    rows = c.fetchall()
    conn.close()

    return render_template("leaderboard.html", rows=rows)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
