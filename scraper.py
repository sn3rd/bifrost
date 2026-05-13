import sqlite3
import httpx
from bs4 import BeautifulSoup

from scoring import compute_score

URLS = [
    "https://answers.launchpad.net/launchpad",
    "https://bugs.launchpad.net/launchpad",
]

THRESHOLD = 30

def scrape():
    conn = sqlite3.connect("spam.db")
    c = conn.cursor()

    for url in URLS:
        try:
            r = httpx.get(url, timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")

            links = soup.find_all("a")

            for link in links[:50]:
                text = link.get_text(strip=True)

                if not text:
                    continue

                score = compute_score(text)

                if score >= THRESHOLD:
                    c.execute("""
                        INSERT INTO content_items
                        (source_type, title, body, url, spam_score)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        "launchpad",
                        text[:200],
                        text,
                        url,
                        score
                    ))

        except Exception as e:
            print("Scrape error:", e)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    scrape()
