# Aspectra – Evaluation report

All numbers in this report come from `python -m eval.evaluate <file>` on the code in this repository.
Nothing is estimated or rounded up. Raw outputs are saved in `eval/results/`.

## 1. What is measured

For each review, Aspectra predicts which **aspects** it talks about (price, quality, delivery, support)
and the **mood** (positive, neutral, negative) for each one. We compare those predictions with
hand-made answer keys.

| Metric | What it means |
|---|---|
| **Precision** | When Aspectra says a review mentions an aspect, how often that is true. |
| **Recall** | Of all aspects really mentioned, how many Aspectra found. |
| **F1** | One number that combines precision and recall (1.00 = perfect). |
| **Mood accuracy** | For the aspects found correctly, how often the mood is right. |
| **Confusion matrix** | Table of right answer (rows) vs what Aspectra said (columns). |

## 2. The three labelled sets

| File | Name on the site | Reviews | Labels | How it was used |
|---|---|---|---|---|
| `eval/dev.csv` | Practice set | 30 | 47 | Used from the start to improve the keyword list and mood words. |
| `eval/test.csv` | Old exam | 32 | 42 | Sealed during round 1, then its mistakes were used for round 2. |
| `eval/exam.csv` | **New exam** | 36 | 49 | E1–E30 written and labelled **before** round 2; E31–E36 added after it and scored once. Never used to change the code. |

**138 labelled review–aspect examples in total.** A "label" is one (review, aspect, mood) row.
One new-exam review ("Five stars, would buy again.") has no aspect on purpose: any aspect found there counts as a mistake.

**Who labelled what**

- Practice and old exam: labels were drafted with the help of an AI coding assistant.
- New exam: the 30 review texts were written by an AI assistant, with a deliberate mix of easy and tricky cases (sarcasm, "not" phrases, unusual words, a review with no aspect).
  The author labelled them independently, an AI assistant labelled them separately, and the two sets of labels agreed on all 30 reviews.
- New exam extension (E31–E36): 6 more reviews were added so the sealed exam has more than 40 labels. An AI assistant wrote and labelled them;
  the author checked and accepted the labels. They were scored exactly once and the code was not changed afterwards.

## 3. Results on the new exam (the honest score)

**Headline (all 49 labels, 36 reviews, current code):**

| Aspect | Precision | Recall | F1 |
|---|---|---|---|
| price | 1.00 | 0.83 | 0.91 |
| quality | 1.00 | 0.32 | **0.48** |
| delivery | 0.90 | 1.00 | 0.95 |
| support | 1.00 | 1.00 | 1.00 |
| **all** | **0.97** | **0.69** | **0.81** |

Mood accuracy: **0.76** (on the 34 aspects found correctly).

**Mood confusion matrix (new exam)**

| really ↓ / said → | positive | neutral | negative |
|---|---|---|---|
| **positive** | 12 | 0 | 3 |
| **neutral** | 0 | 0 | 2 |
| **negative** | 1 | 2 | 14 |

What this says: when Aspectra names an aspect it is almost always right (precision 0.97), but it
misses about 3 in 10 real mentions, almost all of them about **quality**. Mood is right about 3 times in 4,
and **neutral** is never predicted correctly.

**Before vs after round 2 (first 37 labels, E1–E30).** These were scored on the code before round-2 fixes,
then the fixes were made using **only** mistakes from the practice set and the old exam, then scored again.

| E1–E30 | Before round-2 fixes | After round-2 fixes |
|---|---|---|
| Aspect precision | 0.95 | 1.00 |
| Aspect recall | 0.54 | 0.70 |
| **Aspect F1** | 0.69 | **0.83** |
| Mood accuracy | 0.75 (on 20 found) | 0.85 (on 26 found) |

Adding E31–E36 lowered the score from 0.83 to **0.81**. That is expected on unseen reviews and was left as it is.

## 4. All sets side by side (current code)

| Set | Precision | Recall | F1 | Mood accuracy |
|---|---|---|---|---|
| Practice (dev) | 0.98 | 0.91 | 0.95 | 0.74 (43) |
| Old exam (test) | 1.00 | 0.93 | 0.96 | 0.74 (39) |
| **New exam** | **0.97** | **0.69** | **0.81** | **0.76 (34)** |

The practice set and old exam score higher than the new exam **because the code was improved
using their mistakes**. That is overfitting: it shows how well the app does on reviews it was
tuned on, not on new ones. The new exam is the number to quote.

## 5. How the code was improved (history)

| Round | What changed | Learned from | Sealed set, before → after |
|---|---|---|---|
| 1 | More keywords, split sentences at "but/though", 15 more mood words | Practice set | Old exam F1 **0.55 → 0.68** |
| 2 | "cheap" rule, 20 more keywords, 11 more mood words | Practice set + old exam | New exam (E1–E30) F1 **0.69 → 0.83** |

Round-2 details:

- **"cheap" rule.** "looks cheap", "feels cheap" and "cheap plastic" now count as **quality**; any other "cheap" counts as **price**. Before, "The watch looks cheap" was wrongly tagged as price (old exam T10).
- **New keywords** (each taken from a practice or old-exam mistake): pricey, affordable, spend, rip(-off), charged · durable, faulty, material, stitching, leaks, display, smell, machine, strap · arrive, box · helpline, care, staff, respond.
- **New mood words:** patient, polite, durable, affordable, fast (positive); pricey, faulty, leaks, dented, forever, rip (negative).

## 6. Failure cases on the new exam (24) and why they happen

**A. Quality words the keyword list doesn't know (12 cases), the biggest weakness**

| ID | Review | What went wrong |
|---|---|---|
| E5 | "The coffee maker stopped heating after a month." | "heating" not a quality word → quality missed |
| E9 | "Excellent watch for the money." | Praise of the product itself, no quality keyword → quality missed |
| E15 | "The mat is not as thick as the photos suggest." | "thick" unknown → quality missed |
| E16 | "Oh great, another charger that dies after two uses." | "dies" unknown, and sarcasm ("Oh great") → quality missed |
| E20 | "My daughter loves the colour." | "colour" unknown → quality missed |
| E22 | "Pricey for what it is, but the audio is clearer than my old pair." | "audio" unknown → quality missed (price found correctly) |
| E23 | "The app keeps crashing and the watch loses connection every hour." | "app", "crashing", "connection" unknown → quality missed |
| E28 | "The grip is fantastic even during hot yoga." | "grip" unknown → quality missed |
| E29 | "The instructions were confusing and the support email bounced." | "instructions" unknown → quality missed (support found correctly) |
| E33 | "Exactly as described and the courier left it safely with my neighbour." | "as described" not a quality phrase → quality missed (delivery found correctly) |
| E34 | "Cheapest one I could find and honestly it shows." | "cheapest" isn't matched by the "cheap" rule, and "it shows" has no aspect word → price and quality both missed (2 cases) |
| E35 | "I emailed about a missing part and got a reply the next morning with a new one on the way." | "missing part" unknown → quality missed |

**B. Vague praise or complaint with no aspect word (1 case)**

| E13 | "It's fine. Nothing to complain about, nothing to rave about." | No aspect word at all → quality missed |
|---|---|---|

**C. A mood word that points the wrong way (5 cases)**

| ID | Review | What went wrong |
|---|---|---|
| E4 | "Customer support solved my pairing problem in ten minutes." | "problem" pulls the score negative, but the experience was positive |
| E7 | "I had to call customer care four times before anyone helped me." | "helped" pulls the score positive, but it is a complaint |
| E27 | "Took three weeks to arrive and the price had dropped by the time it came." | "dropped" read as negative; the price part is really a neutral fact |
| E31 | "The refund came through in two days, no questions asked." | "no questions" reads as negative, but it is praise |
| E35 | (same review as above) | "missing" pulls support negative, but the reply was quick and helpful |

**D. "Not" phrases and hedging (2 cases)**

| ID | Review | What went wrong |
|---|---|---|
| E14 | "Not bad at all for under twenty pounds." | "pounds" (money) isn't a price keyword → price missed |
| E17 | "I wouldn't say the price is cheap, but you get what you pay for." | Hedged/neutral opinion read as negative |

**E. Several aspects in one short sentence (3 cases)**

| ID | Review | What went wrong |
|---|---|---|
| E32 | "Pretty good earbuds, but the case scratches easily and shipping cost extra." | "shipping" triggered **delivery**, but the complaint is about the cost (labelled price); price and quality share the second half of the sentence, and "Pretty good" pulled both to neutral (3 cases) |

## 7. Limitations

- **Small sets.** 49 labels on the new exam means one mistake moves recall by about 2 points. The numbers show a direction, not a precise score.
- **Keyword approach.** Aspects are found by matching a word list, so any wording not on the list is missed (section 6A). A sentence-embedding or zero-shot model would generalise better but needs more compute.
- **VADER is a general-purpose mood model.** It reads words, not meaning, so sarcasm (E16), "problem solved" (E4) and neutral facts (E27) go wrong. Neutral is the weakest class.
- **Mood accuracy is only measured on aspects that were found**, so it is computed on 34 of the 49 new-exam labels.
- **Test reviews are not real customer reviews.** They were written to be realistic but are synthetic. Scores on real reviews would likely be lower.
- **Labels.** The practice and old-exam labels were AI-drafted. The new exam was labelled by a person and an AI independently, but by only one person. E31–E36 were labelled by an AI assistant and checked by the author.
- **The Q&A step is not scored.** These metrics cover aspect detection and mood. Grouping similar sentences and choosing evidence for answers were checked by hand only.

## 8. How to reproduce

```
python -m eval.evaluate eval/exam.csv    # new exam (sealed)
python -m eval.evaluate eval/test.csv    # old exam
python -m eval.evaluate eval/dev.csv     # practice set
```

The website's **"How accurate is it?"** section shows the same numbers, computed live by the same code.
