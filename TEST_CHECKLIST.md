# Aspectra – manual test checklist

Tick each box as you go. If something doesn't match the **Expected** column, note the test number and send a screenshot.

**Before you start**
- Extract the latest `aspectra-website-update.zip` into `aspectra-v2` (it includes the `test_files` folder).
- In the VS Code terminal: `venv\Scripts\activate`, then `python data/make_reviews.py`, then `uvicorn aspectra.api:app --reload`.
- Open http://127.0.0.1:8000 and press **Ctrl + F5**.

> The expected numbers below come from the 400 reviews made by `data/make_reviews.py`. If you've uploaded a file, upload `data/reviews.csv` again (test U13) to get back to them.

---

## A. Start-up and top of the page

| # | Do this | Expected | ✓ |
|---|---|---|---|
| A1 | Look at the terminal after starting the server | "Application startup complete", no red errors | ☐ |
| A2 | Look at the page title area | "What **392** customers are *really* saying." | ☐ |
| A3 | Look at the 3 numbers under the buttons | Reviews **392** · Aspect mentions **780** · Biggest issue **Delivery** (they count up from 0) | ☐ |
| A4 | Look at the 3D cloud on the right | 4 glowing clusters labelled Price, Quality, Delivery, Support; dots fly in then gently sway | ☐ |
| A5 | Move your mouse over the cloud, then drag it | The cloud tilts with the mouse | ☐ |
| A6 | Read the cluster labels | Price 200 mentions · 35% negative · Quality 187 · 35% · Delivery 191 · 78% · Support 202 · 48% | ☐ |
| A7 | Click **Ask the reviews** | Page scrolls to section 02 | ☐ |
| A8 | Click the **aspectra.** logo | Page scrolls back to the top | ☐ |
| A9 | Click **See how accurate it is** | Page scrolls to section 04 | ☐ |
| A10 | Click each menu link: Aspects, Ask, Evidence, Evaluation, Method | Each one scrolls to its section; the title is **not** hidden under the top bar | ☐ |

## B. Section 01 – the four aspects

| # | Do this | Expected | ✓ |
|---|---|---|---|
| B1 | Look at the tiles | Order: **price, quality, delivery, support**. Scores: price **+11** and quality **+18** in green, delivery **−68** and support **−12** in red | ☐ |
| B2 | Read the small line on each tile | e.g. delivery "191 mentions · 20 positive · 149 negative" | ☐ |
| B3 | Click the **delivery** tile | Jumps to Ask; question box says "How do customers feel about delivery?"; answer "Mostly negative: 10% of 191 mentions of delivery are positive and 78% negative." | ☐ |
| B4 | Click each of the other 3 tiles | Each gives an answer that names that aspect | ☐ |
| B5 | Read **Top recurring complaints** | 5 items, first is "Delivery took two weeks." · delivery · 46 reviews + 22 similar wordings | ☐ |

## C. Section 02 – Ask the reviews (example buttons)

| # | Click this chip | Expected first line of the answer | ✓ |
|---|---|---|---|
| C1 | What are the biggest problems? | "The most common negative points about the products, from 269 reviews." Left: bars by aspect. Right: 3 red bars, first "Delivery took two weeks." (46) | ☐ |
| C2 | How is the overall product quality? | "Mixed: 53% of 187 mentions of quality are positive and 35% negative." Left: a donut showing 53% | ☐ |
| C3 | Is customer support helpful? | "Mixed: 36% of 202 mentions of support are positive and 48% negative." 2 green + 2 red bars | ☐ |
| C4 | Do people like the price of the Coffee Maker? | "Mixed: 47% of 47 mentions of price (Coffee Maker) are positive and 36% negative." | ☐ |
| C5 | How long does the battery last? | "There is not enough evidence in the reviews to answer this question." + "Aspectra won't guess" | ☐ |

## D. Section 02 – typed questions (type it, then press **Enter**)

| # | Type this | Expected | ✓ |
|---|---|---|---|
| D1 | What do customers complain about with delivery? | "The most common negative points about delivery, from 149 reviews." | ☐ |
| D2 | What do customers like about delivery? | "The most common **positive** points about delivery, from 20 reviews." (only green bars) | ☐ |
| D3 | What do customers like about the earbuds? | "…positive points about the Wireless Earbuds, from 51 reviews." | ☐ |
| D4 | Is the Yoga Mat good value? | "Mixed: 52% of 63 mentions of price (Yoga Mat)…" (both green and red bars) | ☐ |
| D5 | Are there problems with the Smart Watch? | "The most common negative points about the Smart Watch, from 66 reviews." | ☐ |
| D6 | What is wrong with support? | "…negative points about support, from 96 reviews." | ☐ |
| D7 | Is it worth the money? | "Mostly positive: 81% of 36 mentions of price…" | ☐ |
| D8 | refund | "Mixed: 56% of 36 mentions of support…" (only sentences containing "refund") | ☐ |
| D9 | colour | "There is not enough evidence…" | ☐ |
| D10 | tell me everything | "There is not enough evidence…" | ☐ |
| D11 | asdfgh | "There is not enough evidence…" | ☐ |
| D12 | (leave the box empty) and click **Ask** | "Type a question first." | ☐ |
| D13 | `<script>alert(1)</script>` | No pop-up appears; "There is not enough evidence…" | ☐ |
| D14 | Paste a very long line of random letters | "There is not enough evidence…"; page layout doesn't break | ☐ |

## E. Review pop-up

| # | Do this | Expected | ✓ |
|---|---|---|---|
| E1 | Ask anything with an answer, click a **#number** tag | A pop-up opens: "Review #… · product · N/5 stars", the full review, and "What Aspectra found" | ☐ |
| E2 | Check the review text | It really contains the sentence (or a similar wording) shown in the answer | ☐ |
| E3 | Click **Close** | Pop-up closes | ☐ |
| E4 | Open another, press **Esc** | Pop-up closes | ☐ |

## F. Section 03 – Explore the evidence

Set both filters, then click **Show more** until it disappears. Check the count line above the list.

| # | Aspect | Mood | Count line should say | ✓ |
|---|---|---|---|---|
| F1 | All | All | 780 mentions, grouped into **56** recurring points (10 at a time; Show more adds 10) | ☐ |
| F2 | All | positive | 282 mentions → 21 points | ☐ |
| F3 | All | neutral | 118 mentions → 11 points | ☐ |
| F4 | All | negative | 380 mentions → 24 points | ☐ |
| F5 | price | All | 200 mentions → 15 points | ☐ |
| F6 | quality | All | 187 mentions → 15 points | ☐ |
| F7 | delivery | All | 191 mentions → 12 points | ☐ |
| F8 | support | All | 202 mentions → 14 points | ☐ |
| F9 | delivery | positive | 20 mentions → 4 points, **no** Show more button | ☐ |
| F10 | quality | neutral | 23 mentions → 2 points | ☐ |

| # | Do this | Expected | ✓ |
|---|---|---|---|
| F11 | With All/All, click **Show more** 5 times | List grows 10 → 20 → … → 56, then the button disappears | ☐ |
| F12 | Change a filter after clicking Show more | List restarts at 10 for the new filter | ☐ |
| F13 | Click a sentence row | It opens and shows its #review tags; click again to close | ☐ |
| F14 | Click a #tag inside an opened row | Review pop-up opens | ☐ |
| F15 | Check the dots | Green = positive, grey = neutral, red/orange = negative, matching the Mood filter | ☐ |

## G. Section 04 – How accurate is it?

| # | Do this | Expected | ✓ |
|---|---|---|---|
| G1 | Look at the default tab | **New exam (sealed)** is highlighted. F1 **0.81**, Precision **0.97**, Recall **0.69**, Mood accuracy **76%** (on 34) | ☐ |
| G2 | F1 per aspect bars | price 0.91 · quality 0.48 · delivery 0.95 · support 1.00 · "49 hand-labelled examples from 36 reviews" | ☐ |
| G3 | Mood table | Green diagonal 12 · 0 · 14; red cells 3, 2, 1, 2 | ☐ |
| G4 | Read the yellow note | Practice 0.95, old exam 0.96, new exam 0.81, "went from 0.69 to 0.83" and "giving 0.81 on all 49" | ☐ |
| G5 | Failure cases | "Failure cases (24)", 6 shown, in order E4, E5, E7… | ☐ |
| G6 | Click **Show all**, then **Show fewer** | 24 shown, then back to 6 | ☐ |
| G7 | Click **Old exam** | F1 0.96, Recall 0.93, 13 failure cases | ☐ |
| G8 | Click **Practice set** | F1 0.95, Precision 0.98, 16 failure cases | ☐ |
| G9 | In the terminal: `python -m eval.evaluate eval/exam.csv` | Same numbers as G1 to G5 | ☐ |

## H. Section 05 – How it works and upload

Use the files in the `test_files` folder. Click **Choose CSV** and pick the file.

| # | Upload this | Expected message | ✓ |
|---|---|---|---|
| U1 | `1_good_sample.csv` | "Done: Loaded **11** reviews…" (12 rows, 1 empty one removed). Top shows 11 reviews; the pill top-right says "Your uploaded data" | ☐ |
| U2 | …then ask "What are the biggest problems?" | "…negative points about the products, from 6 reviews." Tags are S2, S4, S3 | ☐ |
| U3 | …then ask "How is support?" | "Mostly negative: 33% of 3 mentions of support…" | ☐ |
| U4 | …then ask "Is the lamp good value?" | "Mixed: 50% of 4 mentions of price (Desk Lamp)…" | ☐ |
| U5 | `2_excel_semicolons.csv` | "Done: Loaded 2 reviews" | ☐ |
| U6 | `3_capital_columns.csv` | "Done: Loaded 2 reviews" | ☐ |
| U7 | `4_missing_columns.csv` | "Could not use that file: The CSV is missing required columns…" (page keeps the old data) | ☐ |
| U8 | `5_no_reviews.csv` | "Could not use that file: The CSV has no reviews with text" | ☐ |
| U9 | `6_no_aspects.csv` | "Could not use that file: None of these reviews mention price, quality, delivery or support" | ☐ |
| U10 | `7_html_code.csv` | "Done: Loaded 1 review"; in Evidence the text shows the `<b>` and `<script>` as plain text, with no pop-up and no bold | ☐ |
| U11 | `8_picture_renamed.csv` | "Could not use that file: This doesn't look like a CSV text file" | ☐ |
| U12 | The same file twice in a row | It uploads again both times | ☐ |
| U13 | `data/reviews.csv` | "Done: Loaded 392 reviews"; numbers go back to section A | ☐ |
| U14 | Evaluation section after any upload | Unchanged (it uses the labelled exam files, not your upload) | ☐ |

## I. Phone and small screens

Press **F12** → click the phone/tablet icon (top-left of the panel) → pick "iPhone 12 Pro", then press Ctrl + F5.

| # | Check | Expected | ✓ |
|---|---|---|---|
| I1 | Scroll the whole page | Nothing sticks out sideways; there's no left-right scrolling | ☐ |
| I2 | Top of the page | 3D cloud first, then the headline | ☐ |
| I3 | Evidence rows | "delivery · 46 reviews · 23 wordings" sits on its own line under each sentence | ☐ |
| I4 | Ask and pop-up | Answer and pop-up fit the screen | ☐ |
| I5 | Pick "iPad Air" and repeat I1 | No sideways scrolling | ☐ |

## J. Behind the scenes (optional)

| # | Do this | Expected | ✓ |
|---|---|---|---|
| J1 | Open http://127.0.0.1:8000/docs | FastAPI page listing /api/summary, /api/ask, /api/reviews, /api/review/{id}, /api/eval, /api/upload | ☐ |
| J2 | Open http://127.0.0.1:8000/api/review/99999 | `{"detail":"Review not found"}` | ☐ |
| J3 | Press F12 → **Console** tab while using the site | No red errors (red "400" lines are fine during the U7 to U11 bad uploads) | ☐ |
| J4 | Stop the server (Ctrl + C) and click Ask | A message instead of a frozen page; restart and it works again | ☐ |
