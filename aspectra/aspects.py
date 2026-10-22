import re

# Our "aspect taxonomy": each aspect and the words that signal it
ASPECT_KEYWORDS = {
    "price": ["price", "priced", "overpriced", "expensive", "cheap", "cheaper", "value", "money", "worth",
              "cost", "costs", "bargain", "paid", "sale",
              # added after studying mistakes on the practice and old exam sets
              "pricey", "affordable", "spend", "rip", "charged"],
    "quality": ["quality", "broke", "broken", "flimsy", "plastic", "solid", "made", "works", "working", "job",
                "product", "sturdy", "premium", "sound", "battery", "screen", "snapped", "peeling",
                "scratches", "disconnecting", "design",
                # added after studying mistakes on the practice and old exam sets
                "durable", "faulty", "material", "stitching", "leaks", "display", "smell", "machine", "strap"],
    "delivery": ["delivery", "delivered", "shipping", "shipped", "arrived", "package", "post",
                 "courier", "parcel", "tracking", "packaging",
                 # added after studying mistakes on the practice and old exam sets
                 "arrive", "box"],
    "support": ["support", "service", "replied", "reply", "emails", "manual", "help", "agent", "chat",
                "team", "seller", "warranty", "refund", "emailed", "answer", "answered",
                # added after studying mistakes on the practice and old exam sets
                "helpline", "care", "staff", "respond"],
}


def split_sentences(text):
    # Split after . ! or ? followed by a space, and also at "but" / "though",
    # because the two halves often talk about different things ("Box was crushed but the watch was fine")
    parts = re.split(r"(?<=[.!?])\s+|,?\s+(?:but|though|although)\b", text)
    pieces = [p.strip() for p in parts if p and p.strip(" .,!?")]
    return [p[0].upper() + p[1:] for p in pieces]  # start each piece with a capital letter


# "cheap" usually means low price ("cheap and cheerful"), but "looks cheap", "feels cheap"
# or "cheap plastic" is about how the thing is made, so then it counts as quality instead
CHEAP_MEANS_QUALITY = re.compile(r"\b(?:looks?|looked|feels?|felt)\s+cheap\b|\bcheap\s+(?:plastic|material)\b")


def detect_aspects(text):
    """Return a list of (aspect, sentence) pairs found in one review."""
    found = []
    for sentence in split_sentences(text):
        words = re.findall(r"[a-z']+", sentence.lower())
        if CHEAP_MEANS_QUALITY.search(sentence.lower()):
            words = ["flimsy" if w == "cheap" else w for w in words]  # read it as a quality word
        for aspect, keywords in ASPECT_KEYWORDS.items():
            if any(word in keywords for word in words):
                found.append((aspect, sentence))
    return found


if __name__ == "__main__":
    from aspectra.load_data import load_reviews

    reviews = load_reviews("data/reviews.csv")

    # Show the aspects found in the first 5 reviews
    for _, row in reviews.head(5).iterrows():
        print(f"\nReview {row['review_id']}: {row['text']}")
        for aspect, sentence in detect_aspects(row["text"]):
            print(f"   -> {aspect}: {sentence}")

    # Count how often each aspect is mentioned across all reviews
    counts = {aspect: 0 for aspect in ASPECT_KEYWORDS}
    for text in reviews["text"]:
        for aspect in {a for a, _ in detect_aspects(text)}:
            counts[aspect] += 1
    print("\nHow many reviews mention each aspect:", counts)
