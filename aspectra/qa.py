import re

import pandas as pd

from aspectra.aspects import ASPECT_KEYWORDS

# Words that tell us what kind of answer the person wants
NEGATIVE_WORDS = {"complain", "complaint", "complaints", "problem", "problems", "issue", "issues",
                  "bad", "worst", "wrong", "negative", "unhappy", "hate", "dislike"}
POSITIVE_WORDS = {"love", "loved", "liked", "good", "best", "positive", "happy", "praise", "great"}
# Yes/no questions ("Is the Yoga Mat good value?") deserve both sides, not just the good ones
YES_NO_STARTS = {"is", "are", "was", "were", "do", "does", "did", "can", "should", "would", "will"}
# Broad topic words: they pick an aspect but don't narrow it down
TOPIC_WORDS = {"price", "quality", "delivery", "support", "product", "service", "shipping", "value", "cost"}
# Little words that carry no meaning for searching
STOP_WORDS = {"what", "do", "does", "is", "are", "the", "a", "an", "about", "of", "to", "in", "and",
              "people", "customers", "say", "how", "why", "most", "biggest", "any", "with", "it", "for",
              "me", "i", "my", "you", "tell", "show", "give", "please", "can", "could", "there", "this",
              "that", "all", "everything", "anything", "something", "think", "know", "was", "were", "be"}


def words_in(text):
    return set(re.findall(r"[a-z']+", text.lower()))


def plain(value):
    """Turn a pandas/numpy number into a normal Python value so it can be sent as JSON."""
    return value.item() if hasattr(value, "item") else value


# ---------- Grouping similar sentences into "themes" ----------
# Real reviews say the same thing in different words ("my parcel showed up damaged" /
# "the package arrived damaged"). To count recurring points we compare the meaningful
# words of two sentences, after treating words with the same meaning as one word.
SAME_MEANING = {
    "parcel": "package", "box": "package", "order": "package",
    "showed": "arrived", "turned": "arrived", "came": "arrived",
    "hour": "time", "hours": "time", "day": "time", "days": "time", "week": "time", "weeks": "time",
    "month": "time", "months": "time", "year": "time", "years": "time",
    "great": "good", "excellent": "good", "fantastic": "good", "brilliant": "good", "amazing": "good",
    "terrible": "bad", "awful": "bad", "poor": "bad", "disappointing": "bad",
    "quick": "fast", "quickly": "fast",
    "emailed": "email", "emails": "email", "replied": "reply", "answered": "reply", "answer": "reply",
}
NUMBER_WORDS = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                "twice", "several", "few"}
FILLER_WORDS = STOP_WORDS | {"my", "i", "was", "were", "so", "overall", "have", "this", "that", "on",
                             "up", "really", "very", "super", "incredibly", "almost", "nearly", "just",
                             "me", "after", "be", "at", "all", "still", "too", "far"}


def item_words(reviews):
    """Words that name the products ("coffee", "maker", "watch"...), so they count as one word."""
    if "product" not in reviews.columns:
        return set()
    return {w for name in reviews["product"].astype(str).unique() for w in words_in(name)}


def key_words(sentence, items=()):
    """The meaningful words of a sentence, e.g. "My parcel showed up damaged." -> {package, arrived, damaged}"""
    words = set()
    for w in re.findall(r"[a-z']+|\d+", sentence.lower()):
        if w.isdigit() or w in NUMBER_WORDS:
            w = "<number>"
        elif w in items or w + "s" in items:
            w = "<product>"
        w = SAME_MEANING.get(w, w)
        if w not in FILLER_WORDS:
            words.add(w)
    return words


def similarity(a, b):
    """Share of words two sentences have in common: 1 = same words, 0 = nothing shared."""
    return len(a & b) / len(a | b) if a | b else 1


def group_themes(found, items=(), split_by_aspect=False, threshold=0.5):
    """Group sentences that say the same thing. Each theme gets its most common wording as a label,
    the reviews that said it, and how many different wordings were grouped."""
    keys = ["sentiment", "aspect"] if split_by_aspect else ["sentiment"]
    themes = []
    for _, part in found.groupby(keys, sort=False):
        groups = []
        for sentence in part["sentence"].value_counts().index:  # most common wording first
            words = key_words(sentence, items)
            for group in groups:
                if similarity(words, group["words"]) >= threshold:
                    group["sentences"].append(sentence)
                    break
            else:
                groups.append({"words": words, "sentences": [sentence]})
        for group in groups:
            rows = part[part["sentence"].isin(group["sentences"])]
            ids = [plain(i) for i in dict.fromkeys(rows["review_id"])]
            themes.append({"sentence": group["sentences"][0], "sentiment": rows["sentiment"].iloc[0],
                           "aspect": rows["aspect"].iloc[0], "review_ids": ids, "count": len(ids),
                           "wordings": len(group["sentences"])})
    if not themes:
        return pd.DataFrame(columns=["sentence", "sentiment", "aspect", "review_ids", "count", "wordings"])
    return pd.DataFrame(themes).sort_values("count", ascending=False, kind="stable").reset_index(drop=True)


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def understand_question(question, products):
    """Work out which aspects, mood and product the question is about."""
    words = words_in(question)
    first_word = (re.findall(r"[a-z']+", question.lower()) or [""])[0]
    aspects = [a for a, keywords in ASPECT_KEYWORDS.items() if words & set(keywords + [a])]
    if words & NEGATIVE_WORDS:
        mood = "negative"
    elif (words & POSITIVE_WORDS or "like about" in question.lower()) and first_word not in YES_NO_STARTS:
        mood = "positive"
    else:
        mood = None
    # A product counts as asked about if its full name or its last word ("earbuds", "watch") is in the question
    product = next((p for p in products if isinstance(p, str) and
                    (p.lower() in question.lower() or p.lower().split()[-1] in words)), None)
    return aspects, mood, product


def answer_question(question, reviews, results, max_themes=3):
    """Answer a question using only what the reviews say, citing review IDs."""
    aspects, mood, product = understand_question(question, reviews["product"].unique())

    # Retrieve: keep only the analysed sentences that match the question
    found = results
    if product:
        ids = reviews.loc[reviews["product"] == product, "review_id"]
        found = found[found["review_id"].isin(ids)]
    if aspects:
        found = found[found["aspect"].isin(aspects)]
        # A specific word like "battery" must really appear in the evidence,
        # otherwise we'd answer a battery question with general quality reviews
        all_keywords = {k for keywords in ASPECT_KEYWORDS.values() for k in keywords}
        specific = (words_in(question) & all_keywords) - TOPIC_WORDS
        if specific:
            found = found[found["sentence"].apply(lambda s: bool(words_in(s) & specific))]
    if mood:
        found = found[found["sentiment"] == mood]
    if not aspects and not mood:
        # Free-form question: keep sentences that share a meaningful word with it
        search_words = words_in(question) - STOP_WORDS
        found = found[found["sentence"].apply(lambda s: bool(words_in(s) & search_words))]

    if found.empty:
        message = "There is not enough evidence in the reviews to answer this question."
        return {"answer": message, "verdict": message, "breakdown": None, "by_aspect": {}, "evidence": []}

    # Count the moods of all matching mentions
    counts = found["sentiment"].value_counts()
    breakdown = {m: int(counts.get(m, 0)) for m in ["positive", "negative", "neutral"]}
    total = sum(breakdown.values())

    # Group sentences that say the same thing into "themes": who said it and how many
    themes = group_themes(found, item_words(reviews))

    # Pick the points to show: if no mood was asked for, show both sides
    if mood:
        picked = themes.head(max_themes)
    else:
        picked = pd.concat([themes[themes["sentiment"] == "positive"].head(2),
                            themes[themes["sentiment"] == "negative"].head(2)])
        if picked.empty:  # only neutral mentions: show those instead
            picked = themes.head(max_themes)

    # One-line verdict
    if aspects:
        topic = " and ".join(aspects) + (f" ({product})" if product else "")
    else:
        topic = f"the {product}" if product else "the products"
    reviews_used = found["review_id"].nunique()
    if mood:
        verdict = f"The most common {mood} points about {topic}, from {plural(reviews_used, 'review')}."
    else:
        pos, neg = breakdown["positive"] / total, breakdown["negative"] / total
        if pos >= 0.6:
            feeling = "Mostly positive"
        elif neg >= 0.6:
            feeling = "Mostly negative"
        elif breakdown["neutral"] / total >= 0.6:
            feeling = "Mostly neutral"
        elif neg == 0:
            feeling = "Leaning positive"   # some good, none bad, rest neutral
        elif pos == 0:
            feeling = "Leaning negative"
        else:
            feeling = "Mixed"
        verdict = f"{feeling}: {pos:.0%} of {plural(total, 'mention')} of {topic} {'is' if total == 1 else 'are'} positive and {neg:.0%} negative."

    evidence = [{"sentence": row.sentence, "sentiment": row.sentiment, "count": int(row.count),
                 "wordings": int(row.wordings), "review_ids": row.review_ids[:5]}
                for row in picked.itertuples()]

    # A plain-text version too, handy for the terminal
    lines = [verdict] + [f'- [{e["sentiment"]}] "{e["sentence"]}" ({e["count"]} reviews, e.g. #'
                         + ", #".join(map(str, e["review_ids"])) + ")" for e in evidence]
    # Mood split per aspect, so the website can draw a small chart
    by_aspect = {}
    for (aspect, sentiment), n in found.groupby(["aspect", "sentiment"]).size().items():
        by_aspect.setdefault(aspect, {"positive": 0, "neutral": 0, "negative": 0})[sentiment] = int(n)

    return {"answer": "\n".join(lines), "verdict": verdict, "breakdown": breakdown,
            "by_aspect": by_aspect, "evidence": evidence}

if __name__ == "__main__":
    from aspectra.load_data import load_reviews
    from aspectra.sentiment import analyse_all

    reviews = load_reviews("data/reviews.csv")
    results = analyse_all(reviews)

    questions = [
        "What do customers complain about with delivery?",
        "What are the biggest problems?",
        "Do people like the price of the Coffee Maker?",
        "How is the overall product quality?",
        "How long does the battery last?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        print(answer_question(q, reviews, results)["answer"])
