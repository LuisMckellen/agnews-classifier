# LEARNINGS

Entries are append-only. Superseded figures are marked in place and kept —
the wrong version and the reason it changed are more useful than a clean
file.

**Corrections index**

| Figure | 31 Aug | Current | Where |
|---|---|---|---|
| Corruption rate | 31% (37,131) | **32.23% (38,678)** | 1 Sep, 4 Sep |
| Apostrophe share | 92% | **76.8% of rows** | 1 Sep |
| Widest class skew | Business–Sci-Tech | **World–Business** | 1 Sep |
| Duplicate titles | column headers | **head is, tail is syndication** | 1 Sep |
| `39` verdict | noise | **token collision** | 1 Sep, 2 Sep |
| 2×2 cells C/D | valid | **pre-fix `repair`, re-run pending** | 2 Sep |

---

## 31 Aug 2026 — W3 pre-work: data verification and the corruption 2×2

> **Superseded in part.** The corruption figures in this entry come from a
> throwaway regex narrower than `CORRUPT`; see 1 Sep. The 2×2's C and D
> arms used a `repair` with a word-boundary bug; see 2 Sep. Kept as
> written.

Setup day. No model tuned, no score reported. Everything below came out of
the terminal.

### Dataset

AG News, from the CharCnn_Keras mirror (the source torchtext points at),
MD5-verified. 120,000 train rows, 7,600 official test rows, 4 classes at
exactly 30,000 each. Columns: class index 1–4, title, description.
`text` = title + " " + description.

Provenance: AG corpus gathered by ComeToMyHead from 2,000+ news sources;
classification benchmark built from it by Xiang Zhang for the 2015
character-level CNN paper. Real newswire.

### Verification pass

| Check | Result |
|---|---|
| Shape | (120000, 4) |
| Class balance | 30,000 / 30,000 / 30,000 / 30,000 |
| Nulls | 0 in every column |
| Exact duplicates on `text` | 43 |
| Duplicates on `title` alone | 5,636 |
| Duplicates on `description` alone | 1,269 |
| Length | mean 236.3, sd 66.4, min 100, median 232, max 1012 |

### Five findings

**1. The corpus was deduplicated before I got it.**
Predicted 1,000 ± 200 exact duplicates (~0.8%, a reasonable prior for a wire
corpus). Actual: 43, or 0.036%. Off by 23×. Pre-registered interpretation
fired as agreed: syndication guarantees more than that, so somebody
deduplicated already. The dedup question is therefore *what survived their
filter*, not *what is naturally there*.

**2. They deduplicated on the concatenation, not on stories.**
Titles duplicate 130× more than the pair does. So story-level duplication is
still present, hiding in the component columns.

**3. Duplicate titles are mostly recurring column headers, not syndication.**
*(Superseded 1 Sep — true of the head, false of the whole.)*
"Today's schedule" (39), "Transactions" (39), "NL notables" (19), "Tech
Briefs" (7) — daily fixtures with the same headline and different content.
Nearly all Sports or Business, so this boilerplate is class-correlated.
Also present: scraper furniture ("Enter your e-mail:", "SI.com",
"Search Engine Forums Spotlight").

Initially I thought these 5,636 gave me a free ground-truth set of
same-story pairs for calibrating a similarity threshold. Reading them showed
they don't. Inference was too fast; reading the data corrected it.

**4. Minimum length is exactly 100 characters.**
A round number is a filter, not nature. Second sign of a cleaning pass.
Noted as separate evidence from finding 1 — two observations landing near
each other numerically is not corroboration.

**5. 31% of rows carry HTML entity corruption, and it is class-skewed.**
*(Superseded 1 Sep and 4 Sep — 32.23%, 38,678 rows.)*
Found via `#39;); //-- gt; Eye On Stocks` in the duplicate-title list.

- `bare_num` (`#39;` — lost its ampersand): 30,661 rows
- `bare_named` (`gt;`, `quot;`): 11,226 rows
- `intact` (`&amp;` — never unescaped at all): 5,243 rows

Two distinct processing failures, possibly from different pipeline stages.

Per-class rate: World 0.247, Sports 0.355, Business 0.383, Sci-Tech 0.281.
A 1.55× spread — and the heaviest skew falls across Business vs Sci-Tech,
the pair this dataset is known to confuse. *(Superseded 1 Sep: the widest
gap is World–Business.)*

Codepoint frequencies (`inspect_corruption.py`): `39` 44,316 · `36` 1,307 ·
`151` 750 · `146` 122 · `147` 66 · `148` 66, then a thin tail of Unicode
smart quotes and dashes (`8217`, `8212`, `8220`, `8221`), plus singletons
including `64257` (the ﬁ ligature — a PDF-extraction artifact, so at least
one document passed through a PDF pipeline).

**92% of all corruption is a single missing apostrophe.** Not garbled text.
*(Superseded 1 Sep — unreproducible; 76.8% of rows, 94.7% of occurrences.)*

### The 2×2

Reasoning that set it up: sklearn's default `token_pattern` is `\b\w\w+\b`,
so `"Last season #39;s UEFA"` tokenises to `last, season, 39, uefa` while the
repaired version gives `last, season, uefa`. The entire difference is one
spurious numeric token `39` appearing in 44,316 documents. Since it appears
in 37% of documents, TF-IDF already discounts it heavily.

Design: train on dirty/repaired × test on dirty/repaired. n=5,000, 5 seeds,
`TfidfVectorizer` + `LogisticRegression` inside a `Pipeline`.

Pre-registered predictions, both recorded before running:
- Claude: A ≈ B ≈ C ≈ D, all gaps below the noise floor; A highest
  (dirty training borrows artifact signal that the dirty test still counts)
- Me: all similar, possible C–D gap

Results:

| Cell | train | test | macro F1 | sd |
|---|---|---|---|---|
| A | dirty | dirty | 0.8625 | 0.0175 |
| B | dirty | repaired | 0.8664 | 0.0178 |
| C | repaired | dirty | 0.8662 | 0.0180 |
| D | repaired | repaired | 0.8664 | 0.0176 |

Paired deltas (same seed both sides, so split luck cancels):

| Delta | mean | sd | same sign |
|---|---|---|---|
| A−B | −0.0039 | 0.0022 | **5/5** |
| C−D | −0.0002 | 0.0017 | 3/5 |
| A−D | −0.0038 | 0.0017 | **5/5** |
| C−B | −0.0002 | 0.0016 | 3/5 |

**Both predictions were wrong, and the sign is the finding.** A is the
*worst* cell, not the best. `39` was never borrowed signal — it is noise
that costs a little accuracy. There was nothing to leak. *(Refined 1 Sep:
not noise either — a collision. See below.)*

C−D and C−B are null at 3/5 sign agreement: coin-flipping. My predicted C–D
gap does not appear. The TF-IDF renormalisation mechanism behind it is real
in principle but too small to measure here.

**Decision:** repair training text. Small, consistent, free.

### Method notes worth keeping

- **Pairing bought 8× resolution.** Marginal spread 0.0177; paired-delta sd
  0.0022. A −0.0039 effect is invisible marginally and unmissable paired.
  It would also have been undetectable in a 3-seed sweep.
- **A noise floor is a property of dataset × split protocol × model ×
  metric**, not of the dataset alone. So a LogReg-derived floor can't
  rigorously judge a LinearSVC gap. Paired per-seed deltas measure the noise
  of *that specific comparison* and need no borrowed floor. W3's floor
  characterises the dataset for the write-up; it is not the W4–5
  significance test.
- **Leakage inflates the mean and deflates the spread.** Fitting the
  vectorizer outside the seed loop would shrink the floor, making every
  later comparison look significant. The second failure mode is the
  dangerous one.
- **Leakage is defined relative to deployment, not intrinsic to a feature.**
  Whether `Reuters` is signal or a crutch depends on what `/classify` will
  actually receive. Same token, opposite verdict.
- **Quarantine protects against *fitting* on the test set, not against
  *knowing* things about it.** Distribution checks (corruption rates,
  lengths) are legitimate; anything touching labels is not.
- **A prediction is only useful if you decide in advance what each outcome
  would mean.** Otherwise you rationalise whatever comes out.
- **When a test fails, decide whether the code or the test is wrong before
  changing either.** `test_hash_number_not_an_entity` failed twice — both
  times the assertion was a hand-written guess, not measured behaviour. The
  frequency scan then showed `#12;` never occurs in this corpus at all.
- **Code that runs on import is code you can't control.** Exploration
  pasted into `load.py` executed on every import and produced a `NameError`
  that appeared to come from the calling script.

### API design consequence

The 100-char floor is a property of the training distribution, not of valid
input. A 60-character headline is legitimate; the model has simply never
seen one. So `/classify` should **not** reject short text with a 400 — it
should classify and return `below_training_length_floor: true` alongside the
OOV fraction. Reject only empty and absurd (>5,000 chars).

Same principle as water's `imputed_fields`: the caller gets an answer plus
an honest account of how much to trust it. Water reported which inputs were
imputed; this reports which inputs are out-of-distribution.

### Repo

`agnews-classifier`. `load.py` holds loading only and executes nothing on
import; `clean.py` holds `repair` and the corruption patterns; `floor.py`
holds the experiments. Results written as JSONL with `sklearn` version and
git SHA on every row — the xgboost 3.2.0 vs 3.4.1 episode cost a week
because the version wasn't stored beside the metric. 8 tests passing.

---

## 1 Sep 2026 — Reconciliation

> Reconstructed here from `LEARNINGS-session2.md` and the audit that
> followed. Check the figures against your own file before citing.

No new experiment. A day spent checking published numbers against each
other, which found four errors in figures already written down.

### The identity check

With balanced classes, the mean of the four per-class rates equals the
overall rate. The 31 Aug figures failed it by **849 rows** — the per-class
rates implied 37,980 and the total said 37,131, far outside anything
rounding to 3dp can explain.

Cause: the class rates were computed with `CORRUPT`, the total with a
throwaway `#3[0-9];` that missed codepoints 36, 146, 147, 148 and 151, and
missed bare `amp;` and `nbsp;`. Two definitions of the same thing, typed at
different times.

Corrected: `bare_num` 31,356 · `bare_named` 11,226 · **any bare 38,678**
*(changed to 38,679 on 2 Sep; that change was itself wrong and was
reverted 4 Sep — see below)*. Per class as counts: Business 11,529 ·
Sports 10,851 · Sci-Tech 8,697 · World 7,601. `intact` reported separately — it is a different failure
mode and shouldn't sit inside a corruption total.

### The 92% was never reproducible

Neither table on the page produces it. By rows: 29,696/38,678 = **76.8%**
(unchanged on recompute, 4 Sep).
By codepoint occurrences: 44,316/46,812 = **94.7%**. An unqualified
percentage is ambiguous even when correct — state the unit.

### The skew claim was backwards

Business–Sci-Tech is 0.0944. World–Business is **0.1309**. The corruption
skew is *not* concentrated on the confusable pair, so it cannot support the
Business/Sci-Tech overlap argument. Claim deleted.

### Sample the tail, not the head

The 31 Aug reading of duplicate titles came from the top of a
`value_counts()`. The head of a ranked distribution is sorted by exactly the
property that makes it unrepresentative — the top eight titles total 212
occurrences, **2.1%** of the 10,333 rows involved (the 3.8% figure
divided occurrences by rows-beyond-first — corrected 4 Sep).

Tail sample at count ≤ 3, n=40: **36 syndication**, 4 boilerplate, 0
coincidence. Nearly all *distinct* titles live in the tail. So both readings
were right about their own region and wrong about the corpus.

This restores the free ground-truth set that finding 3 discarded — with the
caveat added later that the pairs are selected by exact title, so
calibration must run on the description field alone.

### Label conflicts, and a claim scoped down

**7 of 40** tail pairs carry two different classes for the same story.
Interval roughly 7–33%.

First written as *"irreducible label noise caps achievable accuracy — no
model can cross it."* Both halves wrong. The sample was selected for
stories that ran on more than one desk, which is the population most likely
to be legitimately dual-category, so the rate doesn't lift to the corpus.
And the paired descriptions are *reworded* — different inputs — so it isn't
a hard ceiling.

Second attempt: *"15 of 100 random articles were plausibly dual-class, so
the human ceiling is ~85%."* Also wrong, and worth keeping. Ambiguity to a
reader is not a ceiling on a model: the label came from a systematic
process — which desk ran the story — that leaves traces in wire style,
source markers and section vocabulary. A model learns tendencies a reader
can't call. Published AG News results sit near 92%, so the theory was
refuted by the terminal before it was written. One annotator isn't a
ceiling either; that needs inter-annotator agreement.

Three routes to label noise, kept separate: syndication conflicts (biased),
blind ambiguity review (upper bound), and W4–5 confident errors — the only
one measured in the same currency as accuracy.

### `39` is a collision, not a noise token

Cells B, C and D sit within 0.0002 of each other; only A is depressed. The
same trained model with a `39` coefficient scores 0.8664 on repaired test
and 0.8625 on dirty test. A compromised feature costs nothing unless it
fires at inference — so this is an **interaction**, and either repair alone
recovers it.

The two train-side contrasts were never reported. Computed 2 Sep: A−C
−0.0036 (sd 0.0032, 4/5) and B−D +0.0000 (sd 0.0007). Note A−C is weaker
evidence than A−B despite a similar mean.

### Leakage lives in things fit to data, not things decided

`TfidfVectorizer` *estimates* IDF weights and freezes them into the
artifact, so estimating them on data you later test on flatters you and
shrinks the spread. `repair` and a hardcoded strip list are *constants* —
they apply identically to both sides and cannot leak. Safe and useful are
separate questions; `repair` needed the 2×2 regardless.

### Near-miss: Experiment B's top prefix

Two 24k anchors leave a 96k pool, and the largest nested prefix was 96k. At
that prefix all ten seeds train on identical rows — TF-IDF + LogReg is
order-invariant — so the spread collapses to zero and reads as "variance
vanishes at scale." Caught before running. Ladder now tops at **80k**.

### Dedup: reversed, then re-reversed

Removal → measure-and-keep → removal-pending-count, in one day.

The middle position came from arithmetic on the *head*: boilerplate
headers, ~212 rows, far below a 0.002 paired resolution. The tail sample
overturned it — if most distinct duplicate titles are syndication, the
affected population is plausibly thousands of rows.

Two lessons. An estimate built on the head of a ranked distribution is
wrong in a direction you can't predict. And a decision reversed twice in a
day was never resting on a measurement — get the count.

### Boilerplate is not duplication

Two failure modes, one detector. Near-copies are a **row**-level problem:
remove one side before splitting. Boilerplate is a **token**-level problem
in otherwise valid rows — deleting those rows discards real Sports and
Business examples, non-randomly, since the headers are class-correlated.

The strip-list experiment was **dropped on arithmetic**: ~212 rows cannot
clear a 0.002 resolution. Recording the calculation is a stronger entry
than a null result would have been. The strings still matter for W6
explainability.

---

## 2 Sep 2026 — Collision, boundary, and a false pass

### An exact identity was accepted as approximately holding

*(This entry was wrong in both directions. Corrected 4 Sep — see below.
Kept as written because the correction is the lesson.)*

The 1 Sep appendix published `any bare = 38,678` with the note *"identity
check: holds to one row."*

Under balanced classes that identity is **exact**. The four rates imply
38,679, and the terminal returns 38,679 under every candidate separator.
The per-class figures were right; the total was wrong by one.

The check worked. The reading of it didn't. One row off is a failure, and
the instinct to call a small discrepancy rounding is precisely what the
check exists to override — it had been added the day before to catch an
849-row version of the same error.

**4 Sep: 38,678 was right all along.** The "terminal returns 38,679" run
used `audit.py`, which retyped `bare_named` without the `\b` that
`clean.PATTERNS` has. That looser pattern matches row **20884** — *"Israel
Strikes Hamas Camp; 13 Are Killed"* — a headline semicolon on a word
ending in `amp`. A four-way count settles it: canonical 38,678 under both
strip settings, retyped 38,679 under both.

And the identity never had the resolution to adjudicate. 4dp rates sit on
a 3-row grid, so 7,601 and 7,602 both round to 0.2534 and the check
carries ±6 rows. Two apparently independent confirmations agreed on the
wrong answer for two unrelated reasons.

The general lesson survives and gets sharper: **publish the quantity the
check runs on.** Counts, not rates. And a correction is a claim needing
the same provenance as the figure it replaces.

### `repair` restored the character but not the word boundary

Bare entities carry a space where the `&` should be: `Ch #225;vez`,
`Congr #232;s`, `r #233;sum #233;`. `repair` substituted the codepoint and
left the space, yielding `Ch ávez` — so the tokenizer saw `ch` + `ávez`
rather than `chávez`.

Visible in `vocab_size` as **4 terms lost, 5 gained, net −1**.

- lost: `apos`, `nbsp`, `quot`, `vez`
- gained: `ávez`, `ès`, `és`, `ésum`, `ête`

The net matched the predicted "≈ 1" exactly and concealed the bug. Report
both directions of a set difference; a net figure hides compensating
movement.

Harmless for `#39;` — `Street 's` loses the orphan under `\b\w\w+\b` — and
word-splitting for every letter entity. None of the eight tests covered a
letter entity mid-word.

**Consequence:** the C and D arms of the 2×2 were trained on text produced
by the buggy function. `A−B = −0.0039, 5/5` describes the old `repair` and
must be re-run. If the new numbers come back nearly identical that is *not*
a null result — it means accented words are too rare to matter, which is a
different claim.

### Time lost to a terminal, not a bug

Repair output displayed as `ßvez`, `Φs`, `Θs`, `Ωte` and read as mojibake.
It was code page 437 rendering Latin-1 bytes: 0xE1 → `ß` not `á`, 0xE9 →
`Θ` not `é`, 0xEA → `Ω` not `ê`. Decoded, every example was correct —
`Chávez`, `Congrès`, `résumé`, `fête`.

`repr()` cannot reveal this; the mangling happens at the terminal, after
Python has finished. Set `PYTHONIOENCODING=utf-8` before concluding
anything about non-ASCII output.

The real bug was sitting in the same output and was nearly missed because
attention went to the fake anomaly beside it.

### Corruption overloaded an existing token

`39` does not leave the vocabulary after repair, and cannot — news text
contains real 39s. So the `vocab_size` check as designed ("dirty −
repaired ≈ 1 term") could never have worked. Presence was the wrong
instrument; **document frequency with a non-zero residual** is the right
one.

Document frequency 29,828 → 169, ratio 0.006. Non-zero residual, so:
collision. Class profiles of the two senses diverge —

| | corrupted | genuine |
|---|---|---|
| Business | 0.273 | 0.231 |
| Sports | 0.325 | 0.367 |
| Sci-Tech | 0.202 | 0.201 |
| World | 0.200 | 0.201 |

The apostrophe sense skews Business, the numeric sense skews Sports —
plausibly because sports text is full of real numbers. One weight served
two meanings pulling in opposite directions. That is the mechanism behind
−0.0039, stated in the data rather than the metric.

Generalises: any repaired entity whose token also occurs naturally is a
collision candidate. Residual zero → pure artifact, no collision. Residual
above zero → collision, but reportable only if the two senses' class
profiles diverge. A collision whose senses agree costs nothing.

Measurement caveat: the table used case-sensitive matching while the
vectorizer lowercases, which is why `lt`/`gt`/`amp` show residual 0 yet
survived in the vocabulary. Re-run pending.

### Markup is a repair-semantics problem, not a counting one

5,241 rows contain `&lt;`-style markup. All 5,241 are matched by
`bare_named` and by `intact`; **zero** by neither. The claim of a fourth
uncounted pattern was wrong.

The 5,241 also nearly exhausts the 5,243 rows counted as `intact` — that
category is HTML markup and two other rows. A category collapsing, not a
new one appearing.

Repair converts `&lt;strong&gt;` into `<strong>`, which tokenizes to
`strong`. Class rate 0.0210 Sports vs 0.0746 Business — **3.5×**, against
roughly 1.5× for entity corruption overall. The more class-correlated of
the two artifacts. At 4.37% of the corpus it clears the paired resolution,
so it earns a pre-registered experiment rather than a judgement call.

### Not an anomaly

`results/corruption_2x2.jsonl` holds five `experiment: "dummy"` records,
macro F1 0.1006 — the ~0.10 predicted for 4 balanced classes, with sklearn
version and git SHA logged. A results file holds more than one experiment;
filter by an `experiment` field rather than assuming every record belongs
to the comparison in front of you.

---

## Open / next

1. ~~Fix `repair` to consume the boundary space; add
   `test_letter_entity_rejoins_word`.~~ **Done 4 Sep.** It had been written
   up on 2 Sep as shipped; it was not. The test did not exist —
   `pytest -k letter_entity` returned `8 deselected / 0 selected` and
   exited green. Suite is now 25.
2. ~~`PYTHONIOENCODING=utf-8`.~~ Done.
3. Re-run the corruption 2×2. Keep the old numbers here with the reason.
   Fill `A_SEED0_EXPECTED` from the old JSONL at full precision first —
   cell A is dirty/dirty, so the boundary fix cannot touch it.
4. ~~`case=False` re-run of the collision table.~~ **Done 4 Sep.**
   `lt` / `gt` / `amp` residuals 0/0/1 → **18/11/8**. They are collisions,
   not pure artifacts. Numerics unaffected — digits have no case.
5. ~~Propagate every changed figure through all four docs in one pass.~~
   **Done 4 Sep**; see `CORRECTIONS.md`.
6. Pre-register the markup strip experiment: arms repair-only vs
   repair+strip, n=5,000, 5 seeds, prediction and both interpretations
   before any code.
7. `dedup.py` — output is a count; the count decides removal. Calibrate
   recall on description-only tail pairs, precision by eye, report a
   threshold range.
8. Experiment B — two 24k anchors, prefixes topping at **80k**.
9. Experiment A — full resample, 10 seeds, n=120,000 and n=5,000. **This
   supplies both floors**; B's spread is train-side only.
10. Blind ambiguity review, 100 random rows, judged before the label.
11. Class-conditional token analysis; record the deployment assumption for
    `(AP)` / `Reuters` first.
12. Corruption rates on the quarantined 7,600 (distribution check only).
13. Project one W2 leftovers before 14 Sep: baseline re-run in pinned CI
    env, CI badge, leaky-vs-clean isolation.
