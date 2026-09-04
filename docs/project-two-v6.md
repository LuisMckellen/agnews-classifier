# Project Two — Text Classification (v6)

Planned 31 Aug 2026. v3 same day after W3 pre-work. v4 on 1 Sep after
reconciliation. v5 on 2 Sep after the collision and markup audit.
**v6 on 4 Sep — propagation pass. This document was the one file the
4 Sep corrections had not reached.**
Runs W3–W12 (14 Sep – 22 Nov).

Changes from v5 marked **[v6]**. v5 markers left in place where the
content is unchanged.

---

## The decision

**AG News topic classification.** 120,000 training samples, 4 balanced
classes, short news headlines and descriptions. Chosen because it is the
opposite of water potability in every way that mattered.

| | Water potability | AG News |
|---|---|---|
| Samples | 3,276 | 120,000 |
| Signal | none above r=0.05 | strong |
| Expected score | ~0.61 macro F1 | ~0.90 accuracy |
| Noise floor | 0.0168 | 0.0177 at n=5,000 (measured) |
| Classes | 61/39 imbalanced | 4-way balanced |
| Provenance | probably synthetic | real news wire |

The floor at n=5,000 is almost identical to water's at n=3,276. It does not
collapse because the corpus is large; it collapses because the *test set* is
large. The n=120,000 vs n=5,000 comparison is what W3 measures. Don't write
the collapse until it's on the terminal.

**[v5] Label noise — three routes, no ceiling yet.** Duplicate-title
sampling found 7 of 40 tail pairs filed under two classes. Scoped to
syndicated stories, not a corpus rate, and not a ceiling: the paired
texts are reworded, and a hard ceiling needs near-identical inputs.
Three independent estimates, none sufficient alone:

1. Syndication conflict rate — cheap, biased toward dual-category stories.
   **[v6]** The 7/40 is now counted programmatically rather than eyeballed;
   the value did not move.
2. Blind ambiguity review, 100 random rows — bounds *reader* ambiguity,
   not accuracy. Labels came from a systematic process (which desk ran
   the story) that leaves traces in the text.
3. W4–5 confident errors — the only route measured in the same currency
   as accuracy.

No target is written until at least two agree, and none may exceed the
~92% published results.

---

## What is genuinely new

**1. The vectorizer is part of the model.** Fitting `TfidfVectorizer` before
splitting leaks vocabulary *and* IDF weights. `Pipeline` makes it unwritable.
Leakage inflates the mean *and deflates the spread*; the second is the
dangerous one, because a shrunken floor makes every later comparison look
significant.

**[v5]** Leakage lives in things *fit* to data, not things *decided*. IDF
weights are estimated and freeze into the artifact. A hardcoded regex or
strip list applies identically to both sides and cannot leak — but safe
and useful are separate questions.

**2. OOV handling at inference.** `oov_fraction` plus
`below_training_length_floor`. The 100-char minimum is a training-distribution
property, not a validity rule — short input is classified and flagged, never
rejected. Reject only empty and >5,000 chars.

**3. Artifact size and shape.** `max_features`, `min_df`, image size, load
time.

**4. Inference latency.** p50/p95 at `/ping`, plus `sklearn_version`.

**5. Multiclass metrics.** Per-class visibility; Business and Sci-Tech
overlap. The corruption-skew sentence supporting this was deleted in v4 —
the widest skew is World–Business (0.1309), not Business–Sci-Tech (0.0944).
The overlap stands on its own evidence.

**6. Paired comparison.** Same seed, same split, both models, spread of the
per-seed *difference*. Bought 8× resolution in pre-work (0.0177 → 0.0022).

**7. Auditing your own tables — and auditing the audit.**
Balanced classes give a free identity: with equal class sizes the per-class
counts must sum to the total. Session 1 published figures that failed it by
849 rows; that failure was real and the check earned its place.

**[v6] The v5 version of this entry is retired.** It read: *"Session 2
published a total that failed it by one row and recorded the check as
'holds to one row' — a false pass. An exact identity has no tolerance."*
The total was **38,678 and always had been**. The 2 Sep "correction" to
38,679 came from `audit.py`, which retyped `bare_named` without the `\b`
that `clean.PATTERNS` carries; the looser pattern matches row 20884,
*"Israel Strikes Hamas Camp; 13 Are Killed"* — a headline semicolon on a
word ending in `amp`. Four-way count: canonical 38,678 under both strip
settings, retyped 38,679 under both.

Worse, the identity never had the resolution to adjudicate one row.
Published as 4dp *rates*, it sits on a 3-row grid (30,000 × 0.0001), so
7,601 and 7,602 both round to 0.2534 and the check carries roughly ±6
rows. Three lessons replace the retired one:

- **Publish the quantity the check runs on.** Counts, not rates. An audit
  against rounded figures inherits their tolerance.
- **Two checks agreeing is evidence only if they are independent.** A
  false-positive regex and a rounding-limited identity both returned
  38,679, for unrelated reasons, and the agreement read as confirmation.
- **A correction is a claim**, needing the same provenance as the figure
  it replaces. This one moved a right number to a wrong one and stood for
  two days.

**8. [v6] Corruption as token collision — the finding stands, the causal
claim does not.**
`39` never leaves the vocabulary after repair, because real 39s occur in
news text. Presence was the wrong instrument; document frequency with a
non-zero residual is the right one. Document frequency falls
29,828 → 169, and the two senses have diverging class profiles
(apostrophe skews Business, numeric skews Sports). One weight served two
meanings. **[v6]** Under case-folding — which is what the vectorizer
does — `lt`/`gt`/`amp` join them at residuals 18/11/8. They are
collisions, not pure artifacts. Numerics are unaffected; digits have no
case.

**[v6] v5 claimed this collision was "the mechanism behind the 2×2
result." It is not, and that claim is withdrawn.** The genuine sense of
`39` is 169 rows against 29,659 corrupted — 175:1, 0.57% of the token's
document frequency, 0.14% of the corpus. METHOD 23a killed the strip-list
experiment at ~212 rows; 169 is smaller. A mechanism acting on 0.14% of
rows cannot produce −0.0039 against a paired sd of 0.0022. The divergence
is a fact about this corpus, and a population rather than a sample, so it
has no error bars — but it is not a mechanism.

What is left as the account: `#39;` occurs in 24.7% of rows, and A−B holds
the model fixed while swapping test text. Two channels are available —
the mis-aimed coefficient learned on the corrupted token, and L2
renormalisation, since deleting a token rescales the row. C−D (−0.0002,
3/5) carries channel 2 without channel 1, which bounds renormalisation
below detection. So the account is the coefficient.
**Caveat: C is a pre-fix `repair` arm and is superseded. Do not cite this
account until the 2×2 is re-run.**

---

## Week by week

### W3 (14–20 Sep) — Data and floor

Pre-work done 31 Aug – 4 Sep. See LEARNINGS.md.

Done:
- [x] Verification: shape, balance, nulls, duplicates, lengths
- [x] Corruption analysis — 32.23% (**38,678** rows). **[v6] Published as
      per-class counts, rates derived:** Business 11,529 · Sports 10,851 ·
      Sci-Tech 8,697 · World 7,601. 76.8% of corrupted rows carry the lost
      apostrophe (29,696 / 38,678, recomputed 4 Sep; unmoved).
- [x] Corruption 2×2 at n=5,000 — repair training text. **[v5] Superseded:
      the C/D arms used the pre-fix `repair`. Re-run required.**
- [x] `clean.py` with `repair`. **[v6] Boundary fix shipped 4 Sep**
      (`_BOUNDARY = r" ?(?<!&)"`, token-neutral for `#39;`), with
      `test_letter_entity_rejoins_word` written first and watched fail
      7/25. **Suite is 25 tests**, not 8. `conftest.py` now raises on
      zero-selected.
- [x] Reconciliation of all published figures (1 Sep)
- [x] **[v5]** Collision audit; markup audit; single definition of `text`
- [x] **[v6] Case-parameterised collision re-run.** `lt`/`gt`/`amp`
      residuals 0/0/1 → 18/11/8 under `case=False`. Reclassified as
      collisions.
- [x] **[v6] Four-way provenance count** (`00_provenance.py`) settling
      38,678 against pattern and strip setting independently.
- [x] **[v6] Frame rebuild.** `load.py` + `data.py` merged into one
      `build_text`, labels 1–4 throughout, `class_name` in every table.
      Every pattern imported from `clean.py`. Branch `frame`.
- [x] **[v6] Corrections propagated** across LEARNINGS, METHOD,
      data-appendix and this file. See `CORRECTIONS.md`.

Remaining:

- [ ] **[v6] Merge PR #1.** Nothing downstream starts while the repo and
      the write-up disagree. *(Status as of the 4 Sep handoff: open, not
      merged. Confirm before ticking.)*
- [ ] **[v6] Add CI.** 25 tests and nothing runs them. The
      water-potability repo already has the workflow to copy.
- [ ] **[v6] Fix the `5244:1` NaN line in `02_collision.py`** — a ratio
      taken against zero.
- [ ] **[v6] Verify `_UNREPAIRED_BY_DESIGN` against the corpus.** The list
      came from the appendix census, not from a scan. ~96 occurrences,
      below resolution, but the provenance is wrong until scanned.
- [ ] **Re-run the corruption 2×2** with the fixed `repair`. Fill
      `A_SEED0_EXPECTED` from the old JSONL at full precision first: cell A
      is dirty/dirty, so the boundary fix cannot touch it and it must
      reproduce bit-for-bit. Keep the old numbers in LEARNINGS with the
      reason they changed. **[v6]** Only the boundary changed;
      `_REPAIRABLE_NUM` stays at 30–39/100–299 so the re-run isolates one
      edit.
- [ ] **[v6] Optional: isolate the `39` channel.** Zero the `39` column in
      `coef_` and leave the vectorizer untouched — the token still consumes
      norm share but stops contributing to the dot product. Three arms per
      seed (A, A-zeroed, B) give two deltas that must telescope exactly; a
      `39`-only repair arm (B′) would isolate cleanly at four arms per
      seed. Decide whether the cost is worth it *before* building it.
- [ ] **[v5] Markup strip experiment.** 5,241 rows (4.368%), class rate
      0.0210 Sports vs 0.0746 Business — a **3.55×** spread against ~1.5×
      for entity corruption. Clears the paired resolution, so pre-register:
      arms repair-only vs repair+strip, n=5,000, 5 seeds, prediction and
      both interpretations written before any code. **[v6]** The
      containment audit behind this was tautological — `&lt;\s*/?[A-Za-z]`
      requires an intact `&lt;`, which contains `lt;`, so both columns were
      forced by construction. The 5,241 count is real; the audit tested
      nothing.
- [ ] **[v5] Syndication label-conflict rate** — extend the tail
      duplicate-title sample. Reported scoped to syndicated pairs.
- [ ] **[v5] Blind ambiguity review** — 100 random rows, judgement
      recorded before the label is revealed. An upper bound on ambiguity,
      not a ceiling.
- [ ] **Near-duplicate detection.** Sparse `X @ X.T` on a mid-frequency
      blocking vocabulary — high-frequency terms excluded for cost (the
      operation scales as the sum over terms of documents²), low-frequency
      for precision (a high IDF weight lets one shared surname push two
      unrelated rows over threshold). **[v5] Calibrate recall against tail
      duplicate-title pairs on the description field only** — the title is
      the selection criterion and must stay outside the scored field.
      Precision from sampled pairs read by eye; the decision rule written
      before the first pair. Sweep the threshold and report the range
      (METHOD 22). **Output is a count**, and the count decides removal.
      **[v6] State the unit.** Three quantities were all being called
      5,636: distinct titles appearing more than once **4,697**; rows
      involved **10,333**; rows beyond the first of each **5,636**. The
      head is 212 occurrences = **2.1% of rows involved**, not 3.8% — the
      old figure divided occurrences by rows-beyond-first. The conclusion
      strengthens: the tail carries more of the mass.
- [ ] Class-conditional token analysis. Record the deployment assumption for
      `(AP)` / `Reuters` before deciding. Fit both ways, report the gap.
- [ ] **Experiment A** — full resample, 10 seeds, n=120,000 and n=5,000.
      **[v5] This supplies both floors**; B's spread is train-side only.
- [ ] **Experiment B** — two fixed 24k anchors (`random_state` 100, 200),
      10 seeds each, nested training prefixes
      4k/8k/16k/32k/64k/**80k** taken as prefixes of one shuffle per seed.
      All text repaired. Record `anchor` and `repaired` per row.
      **[v5] 80k, not 96k:** with two 24k anchors the pool is 96k, so at
      that prefix every seed trains on identical rows and the spread
      collapses to zero — an artifact of exhausting the pool, not a
      finding about scale. Cost: 16k rows unused, no point at the true
      maximum. Anchor 2 is the robustness check: parallel curves mean the
      shape is real; a constant offset means one anchor is easier, and
      only the slope transfers.
- [ ] Corruption rates on the quarantined 7,600 (distribution check only).

**[v6] Order.** Merge → CI → 2×2 re-run → `dedup.py` → Experiment B →
Experiment A. The re-run comes before dedup because a superseded transform
sits underneath every result currently on the page.

*Done when:* the floor is stated at both sizes, the learning curve exists,
the label-noise estimates agree, and the difference between floors is
explained by mechanism.

**Checkpoint 1** — bring: both floors, the learning curve, the label-noise
estimates, three example rows per class.

W3's floor characterises the dataset for the write-up. It is **not** the
significance test for W4–5; paired per-seed deltas do that.

### W4–5 (21 Sep – 4 Oct) — Baseline to model

- [ ] Everything inside `Pipeline`. No exceptions.
- [ ] Dummy first. ~0.10 macro F1 on 4 balanced classes, not 0.25.
      (Measured: 0.1006.)
- [ ] TF-IDF + LogReg, then LinearSVC, then one contrasting model.
- [ ] All comparisons paired: mean delta, spread, seed sign-agreement.
      **[v5]** When the mean sits inside its own standard error, the sign
      count is describing noise — say so.
- [ ] Per-class metrics; find the confusable pair.
- [ ] **[v5]** Read the confident errors: sort test predictions by
      confidence, take the top 50 wrong, count how many carry a defensible
      label. Confusion-matrix mass and the conflict rate share no
      denominator and are not comparable directly.
- [ ] Add heavy deps only in the week they're first imported.

**Checkpoint 2** — bring the paired comparison table and your call on which
gaps are real.

### W6 (5–11 Oct) — Tuning and explanation

- [ ] `min_df`, `max_features`, n-gram range, C. Search inside the Pipeline.
- [ ] Every reported gain checked with a paired delta.
- [ ] Expect `min_df` to shrink the artifact at little accuracy cost — an
      engineering result as well as a metric one.
- [ ] Explainability: top weighted tokens per class; SHAP on the confusable
      pair. If top tokens are boilerplate, that's a data finding — recurring
      column headers are known to be class-correlated. **[v5]** Watch for
      `strong`, `href`, `http` if markup is repaired rather than stripped.
- [ ] Save the per-class token weight export for W9.

### W7–8 (12–25 Oct) — Serve it

- [ ] FastAPI `POST /classify` — class, probabilities, `oov_fraction`,
      `below_training_length_floor`.
- [ ] Pipeline persisted as one artifact. Docker, CI, Render.
- [ ] Reject only empty and >5,000 chars.
- [ ] `/ping` exposes latency and `sklearn_version`.

**Checkpoint 3** — the live URL and the two-flag design.

### W9 (26 Oct – 1 Nov) — Demo

Streamlit: paste text → topic, probabilities, both flags, top driving tokens
from the W6 export.

### W10–11 (2–15 Nov) — Write it

- [ ] Three headline sections: the floor comparison plus learning curve; the
      data-quality arc (32.23% corruption, tested with a 2×2, found to be
      token *collision* rather than added noise — a tested null on the
      "borrowed signal" hypothesis); and the label-noise estimates with
      their scopes.
- [ ] **[v6] A fourth section is now available: the correction arc.** A
      right figure was corrected to a wrong one on the strength of two
      dependent checks, and reverted two days later by a four-way count.
      That is a better methods story than any of the metrics.
- [ ] Two benchmark numbers: dirty-trained on the official dirty test
      (comparable to published work) and the clean model (honest production
      estimate), with artifact rates explaining the gap.
- [ ] `LEARNINGS.md`, `METHOD.md` — both written incrementally since 31 Aug.

**Checkpoint 4** — the full README.

### W12 (16–22 Nov) — Freeze

No new features. Stories out loud, four minutes each.

---

## Repository shape

**[v6] As built on branch `frame`:**

```
src/agnews/   __init__ · data · clean · dedup · pipelines ·
              evaluate · runlog
scripts/      00_provenance · 01_verify · 02_collision ·
              03_experiment_2x2
tests/        conftest · test_clean · test_evaluate ·
              test_no_import_side_effects
results/      *.jsonl — committed; the evidence
docs/         ROADMAP · METHOD · LEARNINGS · data-appendix · CORRECTIONS
```

Still to come, in the week each is first needed: `03_dedup`,
`04_experiment_a`, `05_experiment_b`, `06_label_review`, `test_dedup`.
`dedup.py` exists but is deliberately empty; the design contract is in its
docstring. `audit.py`, `collision.py`, `dup.py`, `inspect_corruption.py`,
`floor.py`, `app/` and `train.py` are gone — `audit.py` in particular is
what produced 38,679.

`scripts/` holds the only `__main__` blocks. `runlog.py` stamps git SHA and
library versions so METHOD 25 can't be skipped. `evaluate.py` owns the
paired-delta code so two tables can't be computed two ways. `data.py` owns
the `text` definition. No `api/` or `demo/` until W7.

---

## Deferred, with triggers

**MLflow** — when W6 produces 40+ configs and you lose track. Partly
mitigated: JSONL with sklearn version and git SHA per row.
**Postgres behind the API** — dropped. Teaches an ORM, not SQL.
**Registry / feature store / orchestration** — when something retrains on a
schedule.

---

## Parallel track — SQL (W3–W10)

| Weeks | Focus |
|---|---|
| W3–4 | `SELECT`, `WHERE`, `JOIN` ×4, `GROUP BY`, `HAVING` |
| W5–6 | Subqueries, CTEs, `CASE` |
| W7–8 | Window functions, running totals |
| W9–10 | Query plans and indexes |

*Done when:* you can write a window-function query without looking it up.

---

## Rules carried forward

1. Noise floor before comparison.
2. Preprocessing inside a Pipeline.
3. EDA gets a signal check and a realness check.
4. A plausible explanation isn't a finding until tested.
5. AI edits prose, never facts.
6. Every number in the README came out of your terminal.
7. Comparisons are paired.
8. Predictions are pre-registered with their interpretations.
9. Nothing executes at import.
10. Every published figure must be reproducible from the tables around it.
    One definition, one script, one run.
11. Sample the tail, not the head.
12. **[v5] A rate belongs to the population it was sampled from.**
13. **[v5] Removal is a measurement.** Count the affected fraction and
    compare it to your resolution before deleting anything.
14. **[v6] Publish the quantity the check runs on.** *(Replaces v5's "an
    exact identity has no tolerance", which was drawn from a case that had
    no error in it.)* An audit against rounded figures inherits their
    tolerance. Counts are integers; rates at 4dp are not.
15. **[v6] Two checks agreeing is evidence only if they are independent.**
    Before treating agreement as support, ask what would have to be true
    for both to be wrong together.
16. **[v6] A correction is a claim**, and needs the provenance of the
    figure it replaces.
17. **[v6] A status is a claim too.** "Fixed" belongs in a document only
    after the terminal says so.
18. **[v6] Zero selected is not zero failed.** Guarded in `conftest.py`.
19. **[v6] An audit whose result is forced by construction is not an
    audit.**

---

## What I'll hold you to as reviewer

- No score without a spread; no *difference* without a paired delta and its
  sign-agreement count.
- No tuning before the floor is measured.
- No figure that can't be reproduced from the data on the page.
- **[v5]** No result carried forward across a change to the transform that
  produced it.
- **[v6]** No "done" in a document that hasn't been read off a terminal in
  the session that wrote it.
- **[v6]** No mechanism claimed for an effect without sizing the population
  it would have to act on.
- If the project stops teaching you things, we stop early.

---

## Before W3 opens (5–13 Sep)

1. Merge PR #1 and add CI.
2. Project one W2 leftovers — baseline re-run in the pinned CI environment,
   CI badge, leaky-vs-clean isolation.
3. Re-run the 2×2; then `dedup.py`.
4. Does the `title` / `description` concatenation hold up? Joining them
   asserts both fields carry the same kind of signal. Cheap W4 experiment.
   **[v5]** The separator is now fixed in `src/data.py`; the experiment is
   about whether the join is right, not which string joins it.
