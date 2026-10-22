"""
Make 400 fake (synthetic) customer reviews and save them to data/reviews.csv.

Real customers never write the exact same sentence, so instead of copying ready-made
sentences we BUILD each sentence from mix-and-match parts:

    "{The box|My parcel|The package} {showed up|arrived} {dented|crushed|damaged}."

Every {...} slot is filled with a random word from a small list, so the same idea
("the package arrived damaged") comes out worded in many different ways.
"""
import csv
import random

random.seed(42)  # same "random" reviews every time we run it

PRODUCTS = {
    # product name: the word customers use for it
    "Wireless Earbuds": "earbuds",
    "Smart Watch": "watch",
    "Coffee Maker": "coffee maker",
    "Yoga Mat": "mat",
}

# Words that fill the {slots} in the templates below
SLOTS = {
    "parcel": ["the package", "my parcel", "the parcel", "my package"],
    "arrived": ["arrived", "showed up", "turned up", "arrived"],
    "days": ["two", "three", "four", "five"],
    "weeks": ["two", "three", "almost three", "nearly four"],
    "very": ["really", "very", "super", "", "incredibly"],
    "good": ["great", "excellent", "fantastic", "brilliant"],
    "bad": ["terrible", "awful", "poor", "disappointing"],
    "times": ["twice", "three times", "four times", "several times"],
    "hours": ["an hour", "two hours", "a few hours"],
    "months": ["two months", "three months", "six months", "a year"],
    "short": ["a week", "two weeks", "ten days", "a month"],
}

# Templates for each aspect and mood. {item} becomes the product word, e.g. "watch".
TEMPLATES = {
    "price": {
        "positive": ["Great value for the money.",
                     "The price is {very} fair for what you get.",
                     "Cheaper than other brands and still {good}.",
                     "Worth every penny.",
                     "For this price the {item} is a real bargain.",
                     "Got it on sale, {good} value."],
        "negative": ["Way too expensive for what you get.",
                     "Totally overpriced for a {item}.",
                     "Not worth the price at all.",
                     "Too expensive, I paid far too much for this {item}.",
                     "The price is {bad} for such basic features.",
                     "Overpriced, you can find it for less elsewhere."],
        "neutral": ["The price is about what I expected.",
                    "Price is average for a {item}.",
                    "I paid the normal price for it."],
    },
    "quality": {
        "positive": ["The build quality of the {item} is {good}.",
                     "Feels solid and well made.",
                     "The {item} works perfectly after {months} of use.",
                     "{good} quality, it feels premium.",
                     "Very sturdy {item}, I'm impressed.",
                     "Still working like new after {months}."],
        "negative": ["The {item} broke after {short}.",
                     "Cheap plastic, feels flimsy.",
                     "Stopped working after {short}.",
                     "The quality is {bad}, it already looks broken.",
                     "Poorly made and flimsy, the {item} fell apart after {short}.",
                     "Flimsy {item}, the design feels {bad}."],
        "neutral": ["Quality is okay, nothing special.",
                    "It does the job, standard quality.",
                    "The {item} is made of plastic, as expected."],
    },
    "delivery": {
        "positive": ["Delivery was {very} quick.",
                     "{parcel} {arrived} a day early.",
                     "{parcel} came well packed and on time.",
                     "Quick delivery, {parcel} {arrived} in {days} days.",
                     "Shipping was quick and the tracking was {good}."],
        "negative": ["Delivery took {weeks} weeks.",
                     "{parcel} {arrived} damaged.",
                     "Shipping was late and nobody told me why.",
                     "{parcel} {arrived} crushed and the {item} was scratched.",
                     "The courier lost {parcel} for a week.",
                     "Delivery was {bad}, {weeks} weeks of waiting."],
        "neutral": ["Delivery took the usual week.",
                    "It was shipped by standard post.",
                    "{parcel} {arrived} in {days} days."],
    },
    "support": {
        "positive": ["Customer support was {very} helpful.",
                     "Support replied within {hours} and fixed it.",
                     "The support team was friendly and patient.",
                     "The seller sent a refund quickly, {good} service.",
                     "{good} customer service, they answered all my questions."],
        "negative": ["Support never answered my emails.",
                     "Customer service was rude.",
                     "I waited {days} days for support to reply.",
                     "I emailed support {times} and got no answer.",
                     "The seller ignored my refund request, {bad} service.",
                     "Support was useless and never fixed my problem."],
        "neutral": ["I contacted support once about setup.",
                    "Support sent me the standard manual.",
                    "I asked the seller about the warranty."],
    },
}

# Optional little starts, so reviews don't all begin the same way
OPENERS = ["", "", "", "Overall, ", "I have to say, ", "So, "]

NEGATIVE_CHANCE = {"price": 0.4, "quality": 0.3, "delivery": 0.7, "support": 0.5}
NEUTRAL_CHANCE = 0.15


def fill(template, item):
    """Replace every {slot} with a random word, and {item} with the product word."""
    words = {name: random.choice(options) for name, options in SLOTS.items()}
    sentence = template.format(item=item, **words)
    sentence = " ".join(sentence.split())        # remove double spaces left by an empty "{very}"
    return sentence[0].upper() + sentence[1:]    # start with a capital letter


def make_review(item):
    """One review: 1 to 3 aspects, each with a random mood. Returns the text and a star rating."""
    aspects = random.sample(list(TEMPLATES), k=random.randint(1, 3))
    parts, score = [], 0
    for aspect in aspects:
        r = random.random()
        if r < NEGATIVE_CHANCE[aspect]:
            mood = "negative"
        elif r < NEGATIVE_CHANCE[aspect] + NEUTRAL_CHANCE:
            mood, score = "neutral", score + 0.5
        else:
            mood, score = "positive", score + 1
        parts.append(fill(random.choice(TEMPLATES[aspect][mood]), item))
    opener = random.choice(OPENERS)
    if opener:
        first = parts[0] if parts[0].startswith("I ") else parts[0][0].lower() + parts[0][1:]
        parts[0] = opener + first
    rating = 1 + round(4 * score / len(aspects))  # mostly happy review = more stars
    return " ".join(parts), rating


rows = []
for review_id in range(1, 401):
    product = random.choice(list(PRODUCTS))
    text, rating = make_review(PRODUCTS[product])
    if review_id % 50 == 0:
        text = ""  # a few empty reviews on purpose, to test that we clean them out
    rows.append({"review_id": review_id, "product": product, "rating": rating, "text": text})

with open("data/reviews.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["review_id", "product", "rating", "text"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Made {len(rows)} reviews and saved them to data/reviews.csv")
