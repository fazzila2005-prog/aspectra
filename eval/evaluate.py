import sys

import pandas as pd

from aspectra.sentiment import analyse_review

ASPECTS = ["price", "quality", "delivery", "support"]
MOODS = ["positive", "neutral", "negative"]


def scores(rows):
    """Precision, recall and F1 for a set of lined-up rows."""
    tp = int((rows["match"] == "both").sum())        # found and correct
    fp = int((rows["match"] == "right_only").sum())  # found, but not in the answer key
    fn = int((rows["match"] == "left_only").sum())   # in the answer key, but we missed it
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {"precision": round(precision, 2), "recall": round(recall, 2), "f1": round(f1, 2)}


def run_evaluation(path):
    """Compare the app's answers with a hand-labelled answer key and return all the results."""
    rows = pd.read_csv(path)
    # A review with an empty aspect mentions none of our aspects: anything we find there is a mistake
    gold = rows.dropna(subset=["aspect"])

    # 1. Run our app on every hand-labelled review
    predicted = []
    for review_id, text in rows[["review_id", "text"]].drop_duplicates().itertuples(index=False):
        for r in analyse_review(review_id, text):
            predicted.append((review_id, r["aspect"], r["sentiment"]))
    pred = pd.DataFrame(predicted, columns=["review_id", "aspect", "sentiment"])
    # If an aspect appears twice in one review, keep the first sentence's sentiment
    pred = pred.drop_duplicates(subset=["review_id", "aspect"])

    # 2. Line up the answer key (gold) with our predictions
    both = gold.merge(pred, on=["review_id", "aspect"], how="outer",
                      suffixes=("_gold", "_pred"), indicator="match")

    # 3. Aspect detection scores, per aspect and overall
    detection = {aspect: scores(both[both["aspect"] == aspect]) for aspect in ASPECTS}
    detection["all"] = scores(both)

    # 4. Sentiment: for the aspects we found correctly, did we get the mood right?
    matched = both[both["match"] == "both"]
    accuracy = (matched["sentiment_gold"] == matched["sentiment_pred"]).mean()
    confusion = [[int(((matched["sentiment_gold"] == g) & (matched["sentiment_pred"] == p)).sum())
                  for p in MOODS] for g in MOODS]

    # 5. Failure cases: everything we got wrong, so we can learn from it
    texts = rows.drop_duplicates("review_id").set_index("review_id")["text"]
    failures = []
    for row in both.itertuples():
        if row.match == "left_only":
            problem = f"missed the {row.aspect} aspect"
        elif row.match == "right_only":
            problem = f"wrongly found a {row.aspect} aspect"
        elif row.sentiment_gold != row.sentiment_pred:
            problem = f"{row.aspect}: said {row.sentiment_pred}, should be {row.sentiment_gold}"
        else:
            continue
        failures.append({"review_id": row.review_id, "problem": problem, "text": texts[row.review_id]})

    # Sort failures by review number, so T2 comes before T10
    failures.sort(key=lambda f: (len(str(f["review_id"])), str(f["review_id"])))

    return {
        "file": path,
        "labels": len(gold),
        "reviews": int(rows["review_id"].nunique()),
        "detection": detection,
        "sentiment_accuracy": round(float(accuracy), 2),
        "sentiment_examples": len(matched),
        "moods": MOODS,
        "confusion": confusion,
        "failures": failures,
    }


if __name__ == "__main__":
    # Which answer key to use: "python -m eval.evaluate eval/test.csv" (default is the practice set)
    path = sys.argv[1] if len(sys.argv) > 1 else "eval/dev.csv"
    result = run_evaluation(path)
    print(f"Testing on {path}\n")

    print("ASPECT DETECTION")
    print(f"{'aspect':<10}{'precision':>10}{'recall':>8}{'F1':>8}")
    for aspect, s in result["detection"].items():
        print(f"{aspect.upper() if aspect == 'all' else aspect:<10}{s['precision']:>10.2f}{s['recall']:>8.2f}{s['f1']:>8.2f}")

    print(f"\nSENTIMENT accuracy on correctly found aspects: {result['sentiment_accuracy']:.2f} "
          f"({result['sentiment_examples']} examples)")
    print("\nConfusion matrix (rows = correct answer, columns = our answer):")
    print(pd.DataFrame(result["confusion"], index=MOODS, columns=MOODS))

    print("\nFAILURE CASES")
    for f in result["failures"]:
        print(f"- {f['review_id']}: {f['problem']}\n    \"{f['text']}\"")
