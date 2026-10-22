import io

import pandas as pd

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from aspectra.aspects import ASPECT_KEYWORDS
from aspectra.load_data import load_reviews
from aspectra.qa import answer_question, group_themes, item_words
from aspectra.sentiment import analyse_all
from eval.evaluate import run_evaluation

app = FastAPI(title="Aspectra")

# The app's memory: the current reviews and their analysis.
# We start with our sample data; uploading a CSV replaces it.
state = {}


def use_reviews(reviews):
    state["reviews"] = reviews
    state["results"] = analyse_all(reviews)


use_reviews(load_reviews("data/reviews.csv"))


@app.get("/api/summary")
def summary():
    """Numbers for the dashboard: mentions per aspect, mood split, and top complaints."""
    results = state["results"]
    table = results.groupby(["aspect", "sentiment"]).size().unstack(fill_value=0)
    aspects = []
    for aspect in ASPECT_KEYWORDS:  # always the same order: price, quality, delivery, support
        if aspect not in table.index:
            continue
        row = table.loc[aspect]
        aspects.append({
            "aspect": aspect,
            "positive": int(row.get("positive", 0)),
            "negative": int(row.get("negative", 0)),
            "neutral": int(row.get("neutral", 0)),
        })
    # The complaints that come back most often (similar wordings grouped together)
    negatives = results[results["sentiment"] == "negative"]
    top = group_themes(negatives, item_words(state["reviews"]), split_by_aspect=True).head(5)
    top_complaints = top[["aspect", "sentence", "count", "wordings"]].to_dict(orient="records")
    return {"total_reviews": len(state["reviews"]), "aspects": aspects, "top_complaints": top_complaints}


class Question(BaseModel):
    question: str


@app.post("/api/ask")
def ask(q: Question):
    """Answer a question using only the reviews, with review IDs as proof."""
    return answer_question(q.question, state["reviews"], state["results"])


@app.get("/api/reviews")
def reviews(aspect: str = None, sentiment: str = None, limit: int = 50, offset: int = 0):
    """List analysed sentences, optionally filtered, e.g. /api/reviews?aspect=delivery&sentiment=negative
    Sentences that say the same thing are grouped, so each point appears once with the reviews that said it."""
    found = state["results"]
    if aspect:
        found = found[found["aspect"] == aspect]
    if sentiment:
        found = found[found["sentiment"] == sentiment]
    groups = group_themes(found, item_words(state["reviews"]), split_by_aspect=True)
    page = groups.iloc[offset:offset + limit]
    return {"total": len(groups), "mentions": len(found), "rows": page.to_dict(orient="records")}


@app.get("/api/review/{review_id}")
def review(review_id: str):
    """One full review and everything the app found in it."""
    reviews = state["reviews"]
    match = reviews[reviews["review_id"].astype(str) == review_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="Review not found")
    row = match.iloc[0]
    # The rating is optional and may be messy in uploaded files, so only show it if it's a number
    rating = pd.to_numeric(row.get("rating"), errors="coerce")
    results = state["results"]
    found = results[results["review_id"].astype(str) == review_id]
    return {
        "review_id": review_id,
        "product": str(row.get("product", "")),
        "rating": None if pd.isna(rating) else int(rating),
        "text": row["text"],
        "aspects": found[["aspect", "sentiment", "sentence"]].to_dict(orient="records"),
    }


# The evaluation only depends on our code and the answer keys, so we run it once at start-up
evaluation = {
    "exam": run_evaluation("eval/exam.csv"),        # sealed: labelled before the last fixes, scored once
    "old_exam": run_evaluation("eval/test.csv"),    # was sealed, then used to find the last fixes
    "practice": run_evaluation("eval/dev.csv"),     # used to improve the app from the start
}


@app.get("/api/eval")
def eval_results():
    """Accuracy on the sealed new exam, the old exam and the practice set."""
    return evaluation


@app.post("/api/upload")
async def upload(file: UploadFile):
    """Replace the reviews with an uploaded CSV (must have review_id and text columns)."""
    content = await file.read()
    try:
        reviews = load_reviews(io.BytesIO(content))
    except ValueError as error:  # our own clear messages, e.g. a missing column
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        raise HTTPException(status_code=400, detail="This file could not be read as a CSV")
    if reviews.empty:
        raise HTTPException(status_code=400, detail="The CSV has no reviews with text")
    if "product" not in reviews.columns:
        reviews["product"] = "Unknown"
    reviews["product"] = reviews["product"].fillna("Unknown").astype(str)
    if analyse_all(reviews).empty:
        raise HTTPException(status_code=400,
                            detail="None of these reviews mention price, quality, delivery or support")
    use_reviews(reviews)
    return {"message": f"Loaded {len(reviews)} review{'' if len(reviews) == 1 else 's'}"}


# The website: "/" shows the page, "/static/..." serves its CSS and JavaScript files
app.mount("/static", StaticFiles(directory="web"), name="static")


@app.get("/")
def home():
    return FileResponse("web/index.html")
