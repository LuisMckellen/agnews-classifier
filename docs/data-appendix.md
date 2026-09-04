# Data appendix — agnews-classifier

All figures from terminal output. Corpus = 120k working split only.
Corruption figures corrected 1 Sep. **The 2 Sep change 38,678 → 38,679
was itself an error and is reverted: the total is 38,678 (4 Sep).**
Collision table re-run with case as a parameter, 4 Sep.

## Verification (31 Aug)

| Check | Value |
|---|---|
| Shape | (120000, 3) — headerless CSV, `label` / `title` / `description` |
| Labels | 1 World · 2 Sports · 3 Business · 4 Sci-Tech |
| Class balance | 30,000 × 4 |
| Nulls | 0 |
| Exact dupes — `text` | 43 |
| Exact dupes — `title` | 5,636 |
| Exact dupes — `description` | 1,269 |
| Length | mean 236.3 · sd 66.4 · min 100 · med 232 · max 1012 |

`text` = `title` + `" "` + `description`. Defined once in `src/data.py`;
no script builds it independently.

## Corruption (2 Sep — authoritative)

`CORRUPT` = bare entities only. `intact` reported separately.

| Pattern | Rows |
|---|---|
| bare_num `#\d{2,4};` | 31,356 |
| bare_named `(?:lt\|gt\|quot\|amp\|nbsp\|apos);` | 11,226 |
| intact `&(?:#\d+\|\w+);` (separate) | 5,243 |
| **any bare** | **38,678 — 32.23%** |

Per class, as **counts** (rates derived, not published):

| Class | Count | Rate |
|---|---|---|
| Business | 11,529 | 0.3843 |
| Sports | 10,851 | 0.3617 |
| Sci-Tech | 8,697 | 0.2899 |
| World | **7,601** | 0.2534 |
| **Total** | **38,678** | 0.32232 |

**Identity check.** With balanced classes the counts sum to the total
exactly, and `01_verify.py` asserts it. Counts, not rates: 4dp rates sit
on a 3-row grid (30,000 × 0.0001), so 7,601 and 7,602 both round to
0.2534 and the identity carries roughly ±6 rows of slack. Published as
rates it implied 38,679 — which is why the 2 Sep change looked confirmed.

**The 2 Sep correction was the error.** `audit.py` retyped `bare_named`
without the `\b` that `clean.PATTERNS` has. The looser pattern matches one
extra row, index **20884**, World desk:

> Israel Strikes Hamas **Camp;** 13 Are Killed …

A headline using a semicolon as a clause separator; the word ends in
`amp`. Nothing is corrupted. Four-way count (`00_provenance.py`):
canonical gives 38,678 under both strip settings, retyped gives 38,679
under both. Strip is irrelevant; the pattern is everything.

Two checks agreed on 38,679 for unrelated reasons — a false-positive regex
and a rounding-limited identity. **Agreement is evidence only when the
checks are independent.**

Rows containing `#39;`: **29,696 = 76.8% of corrupted rows** (29,696 /
38,678, recomputed 4 Sep; the value does not move).
(Occurrence-level share of numeric codepoints is 94.7%, a different unit
and not a claim about all corruption.)

Widest class skew: **World–Business 0.1309**. Business–Sci-Tech is 0.0944 —
the skew is *not* concentrated on the confusable pair.

Codepoint occurrences: 39: 44,316 · 36: 1,307 · 151: 750 · 146: 122 ·
147: 66 · 148: 66 · 8217: 28 · 38: 27 · 8212: 21 · 8220: 14 · 8221: 12 ·
145: 11 · 233: 11 · 038: 10 · 160: 10 · 133: 8 · 149: 8 · 163: 4 · 8211: 4 ·
37: 4 · 8482: 3 · 225: 2 · singletons: 232, 0151, 64257, 91, 93, 234, 8364, 153

Note `#\d{2,4};` cannot match the five-digit 64257. One singleton; the
ceiling is deliberate.

## Bare entities carry a space (2 Sep)

The `&` is replaced by a space, not deleted: `Ch #225;vez`,
`Congr #232;s`, `r #233;sum #233;`.

`repair` as written substituted the codepoint and left the space, so
`Ch #225;vez` became `Ch ávez` — two tokens where the source has one.
Harmless for `#39;` (`Street 's` loses the orphan under `\b\w\w+\b`),
word-splitting for every letter entity.

Surfaced in `vocab_size`: 4 terms lost, 5 gained, **net −1**. The net
matched the predicted "≈ 1" and concealed the bug.

- lost: `apos`, `nbsp`, `quot`, `vez`
- gained: `ávez`, `ès`, `és`, `ésum`, `ête`

`repair` boundary fix was **written up 2 Sep but not shipped**. The
function on disk still produced `Ch ávez`, and
`test_letter_entity_rejoins_word` did not exist — `pytest -k letter_entity`
returned `8 deselected / 0 selected` and exited green. Shipped **4 Sep**:
`_BOUNDARY = r" ?(?<!&)"`, verified token-neutral for `#39;`. Suite is now
25 tests. **All results produced by the pre-fix function are marked
below and must be re-run.**

## Collision (2 Sep)

`39` does not leave the vocabulary after repair, and cannot — real 39s
occur in news text. Vocabulary presence was never a valid check; document
frequency with a non-zero residual is.

| token | dirty_df | residual | ratio | verdict |
|---|---|---|---|---|
| 39 | 29,828 | 169 | 0.006 | collision |
| 36 | 1,133 | 200 | 0.177 | collision |
| 151 | 583 | 20 | 0.034 | collision |
| 146 | 104 | 22 | 0.212 | collision |
| 147 | 52 | 11 | 0.212 | collision |
| 148 | 60 | 19 | 0.317 | collision |
| 160 | 146 | 138 | 0.945 | ~untouched |
| 133 | 22 | 15 | 0.682 | collision |
| 145 | 41 | 32 | 0.780 | collision |
| 149 | 27 | 25 | 0.926 | ~untouched |
| 38 | 256 | 230 | 0.898 | ~untouched |
| 37 | 183 | 180 | 0.984 | untouched |
| lt | 5,244 | 0 | 0.000 | see case note |
| gt | 5,293 | 0 | 0.000 | see case note |
| amp | 1,467 | 1 | 0.001 | see case note |
| quot | 4,746 | 0 | 0.000 | pure artifact |
| nbsp | 29 | 0 | 0.000 | pure artifact |
| apos | 1 | 0 | 0.000 | pure artifact |

**Case re-run, 4 Sep.** The table above is case-sensitive; the vectorizer
lowercases, so these are the rows describing what the model saw:

| token | residual case=True | residual case=False | verdict |
|---|---|---|---|
| lt | 0 | **18** | collision |
| gt | 0 | **11** | collision |
| amp | 1 | **8** | collision |

`lt` / `gt` / `amp` are **collisions, not pure artifacts**. `amp` at
residual 1 was published as pure artifact against the project's own rule
that residual > 0 means collision — the same tolerance-creep as recording
an exact identity as *"holds to one row"*.

Numerics are unaffected: digits have no case, so every `39`/`36`/`151`
row is identical either way and that half of the table was always sound.
`quot`, `nbsp`, `apos` unchanged at residual 0.

Residual 0 → the token existed only as an artifact; no collision.
Residual > 0 → two senses shared one weight.

### `39` — the two senses have different class profiles

29,659 rows lost the token to repair.

| | corrupted | genuine |
|---|---|---|
| Business | 0.273 | 0.231 |
| Sports | 0.325 | 0.367 |
| Sci-Tech | 0.202 | 0.201 |
| World | 0.200 | 0.201 |

The apostrophe sense skews Business, the numeric sense skews Sports —
plausibly because sports text carries real numbers. One weight serving
two meanings that pull in opposite directions. This is the mechanism
behind the 2×2 result, stated in the data rather than the metric.

Diverging profiles make a collision reportable; matching profiles would
make it harmless.

## Raw HTML markup (2 Sep)

5,241 rows contain `&lt;`-style markup (`&lt;strong&gt;`, `&lt;A HREF=`).

- matched by `bare_named`: 5,241
- matched by `intact`: 5,241
- **matched by neither: 0**

**This audit was tautological and is retained only as a record.** The
markup pattern `&lt;\s*/?[A-Za-z]` requires an intact `&lt;`, which
*contains* `lt;`. Both containment columns are guaranteed by regex
construction, and "matched by neither: 0" could not have come out
otherwise. The conclusion is true — these rows are inside the 38,678 —
but nothing here tested it. The 5,241 count itself is real. The 5,241 also all but exhausts the 5,243
rows counted as `intact` — that category is HTML markup and two other
rows.

It is a repair-semantics problem, not a counting one: `#39;` wants
unescaping, markup wants stripping, and `repair` treats both the same
way. `&lt;strong&gt;` becomes `<strong>`, which tokenizes to `strong`.

**Class rate:** World 0.0319 · Sports 0.0210 · Business 0.0746 ·
Sci-Tech 0.0472. A **3.55×** spread, against roughly 1.5× for entity
corruption overall — the more class-correlated of the two artifacts.

4.368% of the corpus, which clears the paired resolution (~0.002), so
this earns a pre-registered experiment rather than a judgement call.
Prediction and both interpretations to be written before any code.

## Duplicate titles

**State the unit (4 Sep).** Three different quantities were being called
5,636:

| Quantity | Value |
|---|---|
| distinct titles appearing more than once | 4,697 |
| rows involved in those titles | 10,333 |
| rows beyond the first of each | **5,636** |

Head (recurring columns and scraper furniture):
Today's schedule 39 · Transactions 39 · SI.com 34 · Enter your e-mail: 34 ·
NL notables 19 · Search Engine Forums Spotlight 18 · SportsNetwork Game
Preview 15 · Baseball Today (AP) 14

The head totals 212 **occurrences**, which is **2.1% of the 10,333 rows
involved** — not 3.8%. The old figure divided occurrences by
rows-beyond-first, two different units. The conclusion strengthens: the
head is a smaller share of the mass, so the tail carries more.

**Tail sample, n=40, count ≤ 3** — syndication **36** · boilerplate 4 ·
coincidence 0. Nearly all distinct titles are in the tail.

**Label conflicts: 7 of 40** tail pairs carry two different classes for
the same story — Business/Sci-Tech ×4, World/Sports ×3. Binomial interval
roughly 7–33%.

*Scope: syndicated stories only.* The sample was selected for having run
on more than one desk, the population most likely to be legitimately
dual-category. The rate does not lift to the corpus, and no amount of
further sampling from duplicate titles will make it corpus-wide.

*Not a ceiling.* The paired descriptions are reworded, so the inputs
differ. A hard ceiling needs near-identical text carrying different
labels. This is label noise on distinguishable inputs.

## Ambiguity review (pending)

Blind read of 100 random rows, judgement recorded before the label is
revealed: could this plausibly have been filed under another class?
Result: **[RUN]**.

Upper bound on reader ambiguity, **not** on achievable accuracy. The
label came from a systematic process — which desk ran the story — that
leaves traces in the text, so a model can learn tendencies a reader
cannot call. Published AG News results near 92% bound any ceiling
estimate from above.

## Corruption 2×2 — n=5,000, 5 seeds, TF-IDF + LogReg

**Superseded. The C and D arms were trained on text produced by the
pre-fix `repair`, which split accented words. Re-run pending: [RUN].**
Figures retained for comparison.

| Cell | train | test | macro F1 | sd |
|---|---|---|---|---|
| A | dirty | dirty | 0.8625 | 0.0175 |
| B | dirty | repaired | 0.8664 | 0.0178 |
| C | repaired | dirty | 0.8662 | 0.0180 |
| D | repaired | repaired | 0.8664 | 0.0176 |

| Delta | mean | sd | majority sign |
|---|---|---|---|
| A−B (test side, dirty train) | −0.0039 | 0.0022 | 5/5 |
| C−D (test side, repaired train) | −0.0002 | 0.0017 | 3/5 |
| A−C (train side, dirty test) | −0.0036 | 0.0032 | 4/5 |
| B−D (train side, repaired test) | +0.0000 | 0.0007 | 4/5 pos |
| A−D (diagonal) | −0.0038 | 0.0017 | 5/5 |
| C−B (diagonal) | −0.0002 | 0.0016 | 3/5 |

B−D's mean sits inside its own standard error; the sign count there
describes noise, not agreement.

Both pre-registered predictions wrong. A is the worst cell, so `39` was
not borrowed signal.

**Nor is it a main effect.** B, C and D sit within 0.0002 of each other;
only A is depressed. The same trained model with a `39` coefficient
scores 0.8664 on repaired test (B) and 0.8625 on dirty test (A) — a
compromised feature costs nothing unless it fires at inference. This is
an interaction, and either repair alone recovers it.

Combined with the collision table: corruption did not add a noise token,
it **overloaded an existing one**.

Decision — repair training text. Marginal spread 0.0177 vs paired sd
0.0022: pairing bought 8× resolution.

## Results file

`results/corruption_2x2.jsonl` also holds five `experiment: "dummy"`
records — the baseline, macro F1 0.1006, matching the ~0.10 predicted for
4 balanced classes. Filter the census by `experiment`; these are not
anomalies.

## Tests — `tests/test_clean.py`

`test_bare_numeric_entity` · `test_bare_named_entity` ·
`test_intact_entity_still_unescaped` · `test_clean_text_untouched` ·
`test_idempotent` · `test_low_numbers_not_treated_as_entities` ·
`test_observed_entities_repaired` · `test_low_numbers_left_alone` ·
**`test_letter_entity_rejoins_word`** (4 Sep — `Ch #225;vez` → `Chávez`,
plus `Congrès`, `résumé`, `fête`, and a no-glue check. Written first and
watched fail 7/25 against the old `repair`.)
