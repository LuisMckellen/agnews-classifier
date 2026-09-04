# Project Two — Text Classification (v5)

Planned 31 Aug 2026. v3 same day after W3 pre-work. v4 on 1 Sep after
reconciliation. **v5 on 2 Sep after the collision and markup audit.**
Runs W3–W12 (14 Sep – 22 Nov).

Changes from v4 marked **[v5]**.

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

**7. Auditing your own tables.** Balanced classes give a free identity: the
mean of per-class rates must equal the overall rate. Session 1 published
figures that failed it by 849 rows. **[v5]** Session 2 published a total
that failed it by one row and recorded the check as *"holds to one row"* —
a false pass. An exact identity has no tolerance.

**8. [v5] Corruption as token collision, not token addition.** `39` never
leaves the vocabulary after repair, because real 39s occur in news text.
Document frequency falls 29,828 → 169 with a non-zero residual, and the
two senses have diverging class profiles (apostrophe skews Business,
numeric skews Sports). One weight served two meanings. That is the
mechanism behind the 2×2 result, and it is a better story than "a noise
token."

---

## Week by week

### W3 (14–20 Sep) — Data and floor

Pre-work done 31 Aug – 2 Sep. See LEARNINGS.md.

Done:
- [x] Verification: shape, balance, nulls, duplicates, lengths
- [x] Corruption analysis — **[v5] 32.23% (38,678 rows)**, class counts
      11,529 / 10,851 / 8,697 / 7,601, 76.8% of corrupted rows carry the
      lost apostrophe
- [x] Corruption 2×2 at n=5,000 — repair training text. **[v5] Superseded:
      the C/D arms used the pre-fix `repair`. Re-run required.**
- [x] `clean.py` with `repair`, 8 tests passing
- [x] Reconciliation of all published figures (1 Sep)
- [x] **[v5]** Collision audit; markup audit; `src/data.py` as the single
      definition of `text`

Remaining:

- [ ] **[v5] Fix `repair` to consume the boundary space.** Bare entities
      carry a space where the `&` was, so `Ch #225;vez` repaired to
      `Ch ávez` — two tokens where the source has one. Add
      `test_letter_entity_rejoins_word`.
- [ ] **[v5] Re-run the corruption 2×2** with the fixed function. Keep the
      old numbers in LEARNINGS with the reason they changed.
- [ ] **[v5] Document-frequency residual check**, replacing the
      `vocab_size` item. Vocabulary presence could never work: `39` occurs
      naturally. Residual 0 = pure artifact; residual > 0 = collision
      (applies with no tolerance — `amp` at residual 1 was wrongly
      published as pure artifact). Run the table case-insensitively: the
      vectorizer lowercases, and `lt`/`gt`/`amp` move to 18/11/8;
      report only where the two senses' class profiles diverge.
- [ ] **[v5] Re-run `lt`/`gt`/`amp` with `case=False`** — residual 0 under
      case-sensitive matching, yet they survived in the lowercased
      vocabulary.
- [ ] **[v5] Markup strip experiment.** 5,241 rows (4.37%), class rate
      0.0210 Sports vs 0.0746 Business — a 3.5× spread against ~1.5× for
      entity corruption. Clears the paired resolution, so pre-register:
      arms repair-only vs repair+strip, n=5,000, 5 seeds, prediction and
      both interpretations written before any code.
- [ ] **[v5] Syndication label-conflict rate** — extend the tail
      duplicate-title sample. Reported scoped to syndicated pairs.
- [ ] **[v5] Blind ambiguity review** — 100 random rows, judgement
      recorded before the label is revealed. An upper bound on ambiguity,
      not a ceiling.
- [ ] **Near-duplicate detection.** Sparse `X @ X.T` on a mid-frequency
      blocking vocabulary — high-frequency terms excluded for cost (the
      operation scales as the sum over terms of documents² ), low-frequency
      for precision (a high IDF weight lets one shared surname push two
      unrelated rows over threshold). **[v5] Calibrate recall against tail
      duplicate-title pairs on the description field only** — the title is
      the selection criterion and must stay outside the scored field.
      Precision from sampled pairs read by eye; the decision rule written
      before the first pair. Sweep the threshold and report the range
      (METHOD 22). **Output is a count**, and the count decides removal:
      head-of-distribution arithmetic suggested a few hundred rows, the
      tail sample suggests thousands.
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
      data-quality arc (**[v5]** 32.23% corruption, tested with a 2×2, found
      to be token *collision* rather than added noise — a tested null on the
      "borrowed signal" hypothesis); and the label-noise estimates with
      their scopes.
- [ ] Two benchmark numbers: dirty-trained on the official dirty test
      (comparable to published work) and the clean model (honest production
      estimate), with artifact rates explaining the gap.
- [ ] `LEARNINGS.md`, `METHOD.md` — both written incrementally since 31 Aug.

**Checkpoint 4** — the full README.

### W12 (16–22 Nov) — Freeze

No new features. Stories out loud, four minutes each.

---

## Repository shape

```
src/agnews/   data.py · clean.py · dedup.py · pipelines.py ·
              evaluate.py · runlog.py
scripts/      01_verify · 02_corruption · 03_dedup ·
              04_experiment_a · 05_experiment_b · 06_label_review
tests/        test_clean · test_dedup · test_evaluate ·
              test_no_import_side_effects
results/      *.jsonl — committed; the evidence
docs/         ROADMAP · METHOD · LEARNINGS · data-appendix
```

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
14. **[v5] An exact identity has no tolerance.** Off by one is a failure.

---

## What I'll hold you to as reviewer

- No score without a spread; no *difference* without a paired delta and its
  sign-agreement count.
- No tuning before the floor is measured.
- No figure that can't be reproduced from the data on the page.
- **[v5]** No result carried forward across a change to the transform that
  produced it.
- If the project stops teaching you things, we stop early.

---

## Before W3 opens (1–13 Sep)

1. Project one W2 leftovers — baseline re-run in the pinned CI environment,
   CI badge, leaky-vs-clean isolation.
2. Does the `title` / `description` concatenation hold up? Joining them
   asserts both fields carry the same kind of signal. Cheap W4 experiment.
   **[v5]** The separator is now fixed in `src/data.py`; the experiment is
   about whether the join is right, not which string joins it.
