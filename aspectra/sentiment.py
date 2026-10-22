import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from aspectra.aspects import detect_aspects

analyzer = SentimentIntensityAnalyzer()

# VADER is a general-purpose model, so we teach it a few words from the world of shopping.
# Numbers go from -4 (very negative) to +4 (very positive).
analyzer.lexicon.update({
    "support": 0,        # "support" is positive in normal English, but here it's just a topic
    "expensive": -2,
    "overpriced": -2.5,
    "flimsy": -2,
    "cheap": -1,
    "late": -1.5,
    "weeks": -1,         # "took three weeks" = slow
    "early": 1.5,
    "waited": -1.5,
    "never": -1.5,
    "slow": -1.5,
    "crushed": -2,
    "soaked": -2,
    "snapped": -2,
    "peeling": -1.5,
    "scratches": -1.5,
    "disconnecting": -1.5,
    "nobody": -1.5,
    "reasonable": 1.5,
    "decent": 1.5,
    "sturdy": 1.5,
    "premium": 1.5,
    "bargain": 2,
    "quick": 1.5,
    "fixed": 1.5,
    # added after studying mistakes on the practice and old exam sets
    "patient": 1.5,
    "polite": 1.5,
    "durable": 1.5,
    "affordable": 1.5,
    "fast": 1.5,
    "pricey": -1,
    "faulty": -2,
    "leaks": -1.5,
    "dented": -1.5,
    "forever": -1,
    "rip": -2,
})


def sentence_sentiment(sentence):
    score = analyzer.polarity_scores(sentence)["compound"]  # from -1 to +1
    if score >= 0.05:
        return "positive", score
    if score <= -0.05:
        return "negative", score
    return "neutral", score


def analyse_review(review_id, text):
    """Find each aspect in a review and decide if it's positive, negative or neutral."""
    results = []
    for aspect, sentence in detect_aspects(text):
        sentiment, score = sentence_sentiment(sentence)
        results.append({
            "review_id": review_id,
            "aspect": aspect,
            "sentiment": sentiment,
            "score": round(score, 3),
            "sentence": sentence,
        })
    return results


def analyse_all(reviews):
    """Run every review through the pipeline and return one big table."""
    rows = []
    for _, row in reviews.iterrows():
        rows.extend(analyse_review(row["review_id"], row["text"]))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from aspectra.load_data import load_reviews

    reviews = load_reviews("data/reviews.csv")
    results = analyse_all(reviews)

    print("\nFirst 8 findings:")
    print(results.head(8)[["review_id", "aspect", "sentiment", "sentence"]].to_string(index=False))

    print("\nSentiment per aspect:")
    print(pd.crosstab(results["aspect"], results["sentiment"]))
