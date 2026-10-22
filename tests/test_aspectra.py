"""Small checks that each part of Aspectra still works. Run with:  python -m pytest"""
import io

import pytest
from fastapi.testclient import TestClient

from aspectra.aspects import detect_aspects, split_sentences
from aspectra.load_data import load_reviews
from aspectra.sentiment import sentence_sentiment
from eval.evaluate import run_evaluation


def csv_file(text):
    return io.BytesIO(text.encode("utf-8"))


# ---------- 1. Loading and checking the CSV ----------
def test_loader_removes_empty_and_duplicate_reviews():
    reviews = load_reviews(csv_file("review_id,text\n1,Great price\n1,Great price\n2,\n3,Slow delivery\n"))
    assert list(reviews["review_id"]) == [1, 3]


def test_loader_explains_missing_columns():
    with pytest.raises(ValueError, match="missing required columns"):
        load_reviews(csv_file("id,comment\n1,Nice\n"))


def test_loader_accepts_semicolons_and_capital_column_names():
    reviews = load_reviews(csv_file("Review_ID;Text\n1;Arrived late\n"))
    assert reviews.loc[0, "text"] == "Arrived late"


# ---------- 2. Finding aspects ----------
def test_split_at_but():
    assert split_sentences("Box was crushed but the watch was fine.") == ["Box was crushed", "The watch was fine."]


def test_finds_each_aspect():
    found = {aspect for aspect, _ in detect_aspects(
        "Too expensive. The strap broke. Delivery took two weeks. Support never replied.")}
    assert found == {"price", "quality", "delivery", "support"}


def test_cheap_rule():
    assert [a for a, _ in detect_aspects("The watch looks cheap.")] == ["quality"]
    assert [a for a, _ in detect_aspects("Cheap and cheerful.")] == ["price"]


def test_no_aspect_in_vague_review():
    assert detect_aspects("Five stars, would buy again.") == []


# ---------- 3. Scoring mood ----------
@pytest.mark.parametrize("sentence, mood", [
    ("Delivery took three weeks.", "negative"),
    ("The support team was patient and polite.", "positive"),
    ("The package arrived on Tuesday.", "neutral"),
])
def test_mood(sentence, mood):
    assert sentence_sentiment(sentence)[0] == mood


# ---------- 4. The sealed exam score (guards against accidental changes) ----------
def test_sealed_exam_score_is_unchanged():
    result = run_evaluation("eval/exam.csv")
    assert result["labels"] == 49 and result["reviews"] == 36
    assert result["detection"]["all"]["f1"] == 0.81


# ---------- 5. The web API ----------
@pytest.fixture(scope="module")
def client():
    from aspectra.api import app
    return TestClient(app)


def test_summary(client):
    data = client.get("/api/summary").json()
    assert data["total_reviews"] > 0
    assert [a["aspect"] for a in data["aspects"]] == ["price", "quality", "delivery", "support"]


def test_answer_cites_review_ids(client):
    data = client.post("/api/ask", json={"question": "What do customers complain about with delivery?"}).json()
    assert data["evidence"] and all(item["review_ids"] for item in data["evidence"])


def test_says_when_there_is_no_evidence(client):
    data = client.post("/api/ask", json={"question": "Is the wifi password secure?"}).json()
    assert "not enough evidence" in data["answer"]
    assert data["evidence"] == []


def test_bad_upload_is_refused_and_data_is_kept(client):
    before = client.get("/api/summary").json()["total_reviews"]
    response = client.post("/api/upload", files={"file": ("bad.csv", b"id,comment\n1,Nice\n", "text/csv")})
    assert response.status_code == 400
    assert client.get("/api/summary").json()["total_reviews"] == before


def test_website_loads(client):
    assert "Aspectra" in client.get("/").text
