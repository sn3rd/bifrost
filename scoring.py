SPAM_KEYWORDS = [
    "crypto",
    "bitcoin",
    "casino",
    "viagra",
    "loan",
    "investment",
    "profit",
    "seo",
    "marketing",
]

def compute_score(text):
    score = 0

    lower = text.lower()

    for word in SPAM_KEYWORDS:
        if word in lower:
            score += 20

    score += lower.count("http") * 10

    if len(text) < 20:
        score += 10

    return min(score, 100)
