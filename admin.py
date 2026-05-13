import sqlite3
import uuid
import os

DB_PATH = os.getenv("DB_PATH", "/data/spam.db")


def db():
    return sqlite3.connect(DB_PATH)


def create_moderator(username):
    conn = db()
    c = conn.cursor()

    u = str(uuid.uuid4())

    c.execute("""
    INSERT INTO users (username, uuid, role)
    VALUES (?, ?, 'moderator')
    """, (username, u))

    conn.commit()
    conn.close()

    print("Moderator created")
    print(username)
    print(u)


if __name__ == "__main__":
    import sys
    create_moderator(sys.argv[1])
