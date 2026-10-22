import io

import pandas as pd

REQUIRED_COLUMNS = ["review_id", "text"]


def read_csv_any(path):
    """Read a CSV the way people actually save them: commas or semicolons (European Excel),
    UTF-8 or older Windows encodings."""
    if hasattr(path, "seek"):
        content = path.read()
    else:
        with open(path, "rb") as f:
            content = f.read()
    for encoding in ["utf-8-sig", "cp1252"]:
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("This doesn't look like a CSV text file")
    if not text.strip():
        raise ValueError("The file is empty")
    control = sum(1 for c in text if ord(c) < 32 and c not in "\r\n\t")
    if control > len(text) / 100:  # lots of invisible characters = not a text file
        raise ValueError("This doesn't look like a CSV text file")
    first_line = text.splitlines()[0]
    separator = ";" if first_line.count(";") > first_line.count(",") else ","
    try:
        return pd.read_csv(io.StringIO(text), sep=separator)
    except Exception:
        raise ValueError("This file could not be read as a CSV")


def load_reviews(path):
    df = read_csv_any(path)

    # 0. Tidy the column names, so "Review_ID " and "Text" also work
    df.columns = [str(c).strip().lower() for c in df.columns]

    # 1. Check the required columns exist
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"The CSV is missing required columns: {missing}")

    before = len(df)

    # 2. Remove reviews with empty text
    df["text"] = df["text"].fillna("").astype(str).str.strip()
    df = df[df["text"] != ""]

    # 3. Remove duplicate reviews
    df = df.drop_duplicates(subset="review_id")

    print(f"Loaded {before} rows, kept {len(df)}, removed {before - len(df)} empty or duplicate")
    return df.reset_index(drop=True)


if __name__ == "__main__":
    reviews = load_reviews("data/reviews.csv")
    print(reviews.head())
