SPAM_KEYWORDS = [
    "crypto",
    "bitcoin",
    "casino",
    "viagra",
    "loan",
    "investment",
    "profit",
    "seo",
    "marketing"
]

def compute_score(text: str) -> int:
    score = 0
    t = text.lower()

    for kw in SPAM_KEYWORDS:
        if kw in t:
            score += 20

    score += t.count("http") * 10

    if len(text) < 20:
        score += 10

    return min(score, 100)
