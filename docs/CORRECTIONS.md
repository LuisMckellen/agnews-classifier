# Corrections — 4 Sep

One pass, all four docs (METHOD 20). Every line below traces to a terminal
run on 3–4 Sep.

## 1. The corruption total

**38,679 → 38,678** everywhere.

Cause: the 2 Sep "correction" was itself the error. `audit.py` retyped
`bare_named` without the `\b`, and the looser pattern matched one extra
row — index **20884**, World desk:

> Israel Strikes Hamas **Camp;** 13 Are Killed …

A headline using a semicolon as a clause separator. The word ends in
`amp`. Nothing is corrupted. The canonical `CORRUPT` in `clean.py` has
always returned 38,678, under both `strip` settings (four-way count).

## 2. Per-class: publish counts, not rates

| Class | Count | Rate (derived) |
|---|---|---|
| Business | 11,529 | 0.3843 |
| Sports | 10,851 | 0.3617 |
| Sci-Tech | 8,697 | 0.2899 |
| World | **7,601** | 0.2534 |
| **Total** | **38,678** | 0.32232 |

Rates at 4dp sit on a 3-row grid, so they cannot resolve one row: 7,601
and 7,602 both round to 0.2534. Published as rates, the identity implied
38,679 — the same wrong number `audit.py` gave, for an unrelated reason.
Counts are integers and the identity has no tolerance.

## 3. Duplicate titles: state the unit

- distinct titles appearing more than once — **4,697**
- rows involved — **10,333**
- rows beyond the first of each — **5,636**

**Head share 3.8% → 2.1%.** The old figure divided 212 *occurrences* by
5,636 *rows-beyond-first*. Correct denominator is rows involved:
212 / 10,333. The conclusion strengthens — the head is a smaller share of
the mass, so the tail carries more.

## 4. Unchanged, but recomputed

**76.8%** — 29,696 / 38,678 = 0.7677. Was 29,696 / 38,679. Still 76.8%.

**7 of 40** tail label conflicts — the eyeballed count was right, now
counted programmatically.

## 5. Status corrections

`repair` boundary fix: was written up 2 Sep as shipped. It was not.
Shipped 4 Sep. `test_letter_entity_rejoins_word` did not exist; the suite
was 8 tests, not 9. Now 25.

## 6. New METHOD entries

**Two checks agreeing is evidence only if they are independent.** On
2 Sep a false-positive regex and a rounding-limited identity both returned
38,679, for unrelated reasons, and the agreement read as confirmation.

**A correction is a claim.** It needs the same provenance as the figure it
replaces. The 2 Sep correction moved a right number to a wrong one.

**Publish the quantity the check runs on.** An audit against rounded
figures inherits their tolerance.

**Zero selected is not zero failed.** `pytest -k` exits green having run
nothing. Guarded in `conftest.py`.

## Retire

`LEARNINGS.md` 2 Sep: "an exact identity has no tolerance" — the lesson
holds, but the case it was drawn from had no error to catch. Re-anchor it
to §2 above, where publishing counts makes it true.
