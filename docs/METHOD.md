# METHOD — principles, not results

Transferable rules. Data findings live in LEARNINGS.md.

## Measuring

1. A noise floor belongs to **dataset × split × model × metric**, not to the
   dataset. Don't lend one model's floor to another model's comparison.
2. **Compare paired**: same seed, both models, take the per-seed difference.
   Shared split luck cancels. Bought 8× resolution here (sd 0.0177 → 0.0022).
3. Report **mean delta, its spread, and how many seeds agreed in sign**.
   10/10 with a small mean beats 6/10 with a large one.
4. Shrinking a dataset changes two things: test noise (∝ 1/√n_test) and model
   variance. Fix the test set to isolate the second.
5. Nested subsets beat independent draws for learning curves — between sizes,
   only the added rows change, so a dip is attributable.
6. Explore cheap (small n, few seeds), confirm expensive (full n, 10 seeds).
   Few seeds answer "did the mean move?", not "did the spread move?".
6a. **When the mean is inside its own standard error, the sign count is
    describing noise.** Don't report 4/5 agreement on a delta of +0.0000.
6b. **A fixed test set measures train-side variance only.** Its spread is
    not a noise floor; it systematically understates what a future
    comparison must clear. Use the full resample for floors.

## Leaking

7. Leakage inflates the mean **and deflates the spread**. The second is worse:
   a shrunken floor makes everything downstream look significant.
8. `Pipeline` makes the fit-before-split bug unwritable. Prefer constructions
   that forbid the error over discipline that avoids it.
9. Leakage is defined **relative to deployment**, not intrinsic to a feature.
   Ask what the endpoint will actually receive; same token, opposite verdict.
10. An artifact present on *both* sides of the split is counted as real skill
    by the test score and cannot be caught by evaluation alone.
11. Deduplicate **before** splitting — but removal is a measurement, not a
    default. Count first, compare the affected fraction against your paired
    resolution, then decide. Variants on opposite sides inflate the score
    most for high-capacity models, distorting comparisons too. Keeping them
    is defensible if you state the number you chose to live with; keeping
    them silently is not.
12. Quarantine protects against *fitting* on held-out data, not against
    *knowing* things about it. Distribution checks are fine; labels are not.
12a. **Leakage lives in things fit to data, not things decided.** IDF weights
     are estimated and must be frozen into the artifact. A hardcoded regex
     or strip list applies identically to both sides and cannot leak. Safe
     and useful are separate questions — the second still needs an
     experiment.

## Predicting

13. Write the prediction down **and** what each outcome would mean, before
    running. Otherwise you rationalise whatever appears.
14. Being wrong with a recorded prediction is a finding. Both predictions in
    the 2×2 failed and the *sign* of the failure was the result.
15. A null result, tested properly, is publishable. "I found the artifact,
    quantified it, showed it didn't matter" beats "I removed it."

## Auditing your own numbers

16. **Cross-check tables against each other before publishing.** Balanced
    classes give a free identity: the mean of per-class rates must equal the
    overall rate. Any derivable relationship is an audit for free.
17. **A number that can't be reproduced from the data on the page is a
    liability**, however plausible. An invented "92%" survived a full session
    and reached a roadmap.
18. **State the unit.** Share-of-rows and share-of-occurrences answer
    different questions; an unqualified percentage is ambiguous even when
    correct.
19. **One definition, one script, one run.** Ad-hoc regexes typed at different
    times will not agree, and the disagreement surfaces later. Patterns and
    loaders live in modules and get imported, never retyped.
20. Recompute *every* dependent figure when a definition changes, in one pass,
    across every file. Partial propagation is a future reconciliation problem.
21. **An identity that must hold exactly holds exactly.** "Off by one" is a
    failure, not rounding. Recording a small discrepancy as a pass defeats
    the check you just built — the 38,678/38,679 gap was flagged and
    dismissed for a day.
21a. **Report both directions of a set difference.** A net figure hides
     compensating movement: four vocabulary terms lost and five gained nets
     to −1 and looks exactly like the predicted clean result.
21b. **Rule out the display before debugging the code.** Terminal encoding
     mangles non-ASCII after Python has finished, so `repr()` cannot see it.
     Set `PYTHONIOENCODING=utf-8` before concluding anything about odd
     output — and check whether a second, real anomaly is sitting beside the
     fake one.

## Deciding

22. When a parameter is arbitrary (a similarity threshold), don't hunt for the
    correct value. Show the conclusion is insensitive to it, or report a range
    with the assumption stated.
23. Look for naturally occurring ground truth before inventing a calibration
    procedure. Duplicate titles with reworded descriptions *are* labelled
    same-story pairs, free. Two conditions:
    (a) the selection criterion must sit **outside** the field being scored —
    pairs chosen by exact title and scored on title+description are
    high-similarity because of how they were chosen, and the threshold won't
    transfer;
    (b) a positives-only set measures **recall**, never precision. Eyeballing
    sampled pairs gives the other half. Do both.
23a. **Size the effect before designing the experiment.** An artifact
     touching a few hundred rows cannot clear a 0.002 paired resolution;
     saying so with the arithmetic is a stronger entry than a null result.
     One `grep -c` decides whether to pre-register or to act on principle.

## Building

24. Nothing executes at import. Modules define; scripts run.
25. Store the environment beside every metric — library version, git SHA.
    Version drift without that costs a week (xgboost 3.2.0 vs 3.4.1).
26. JSONL over CSV for results: appendable, typed, line-diffable, and it
    carries nested run metadata without flattening.
27. Commit intermediate results. They're the evidence; without them the
    README's numbers are assertions.
28. When a test fails, decide whether the **code or the test** is wrong before
    changing either. Don't take anyone's hand-written expected value on faith.
29. Guards should make violations *deliberate and visible in the diff*, not
    impossible. Put the reason in the docstring.
30. **A results file holds more than one experiment.** Filter by an
    `experiment` field rather than assuming every record belongs to the
    comparison in front of you.

## Serving

31. Out-of-distribution input gets **classified with a flag**, not rejected.
    Training-distribution properties (a 100-char floor) are not validity rules.
    Reject only what's genuinely invalid: empty, absurd.
32. The caller deserves an answer plus an honest account of how much to trust
    it. `imputed_fields` → `oov_fraction`, `below_training_length_floor`.

## Reading data

33. Round numbers are filters, not nature.
34. Two odd observations landing near each other numerically is coincidence,
    not corroboration. Keep separate evidence separate.
35. **Sample the tail, not the head.** A ranked distribution is sorted by the
    very thing that makes its head unrepresentative. Duplicate titles: the
    head is recurring columns (39× each), the tail is syndication (2–3× each),
    and nearly all distinct titles are in the tail. Reading the head and
    describing the whole gets it exactly backwards.
36. **Reading rows finds what counting rows cannot.** Label conflicts and raw
    HTML markup both surfaced from reading 40 examples, not from any
    aggregate.
37. Know your tokenizer before estimating an artifact's impact. `#39;s` under
    `\b\w\w+\b` is one junk token `39`, not garbled text.
38. **A rate measured on a selected subpopulation does not lift to the
    corpus.** Ask what the sample was selected *for*, and whether that
    property correlates with the thing being measured. Duplicate-title pairs
    were selected for running on multiple desks — the population most likely
    to be dual-category.
39. **Ambiguity to a reader is not a ceiling on a model.** Labels usually come
    from a systematic process that leaves traces in the text, so a model can
    learn a tendency a human can't call. If a published benchmark exceeds
    your ceiling estimate, the estimate is wrong.
40. **A transform is defined by what it leaves behind, not only what it
    replaces.** `repair` restored the codepoint and left the space that had
    replaced the `&`, splitting one word into two tokens. Check the boundary,
    not just the substitution.
41. **Corruption can overload an existing token rather than add a new one.**
    If the token also occurs naturally, absence is the wrong test. Use
    document frequency: residual zero is a pure artifact, residual above zero
    is a collision. Report it only when the two senses have diverging class
    profiles — a collision whose senses agree costs nothing. Apply the rule
    with no tolerance: `amp` at residual 1 was published as "pure artifact".
    And measure with the tokenizer's own case handling — case-sensitively
    `lt`/`gt`/`amp` showed residual 0; the vectorizer lowercases, and they
    are 18/11/8.
42. **Two checks agreeing is evidence only if they are independent.** On
    2 Sep a regex with a false positive and an identity with six rows of
    rounding slack both returned 38,679, for unrelated reasons, and the
    agreement read as confirmation. Before treating agreement as support,
    ask what would have to be true for both to be wrong together.
43. **A correction is a claim.** It needs the same provenance as the figure
    it replaces. The 2 Sep correction moved a right number to a wrong one
    because the two figures came from two regexes, one of them retyped.
44. **Publish the quantity the check runs on.** An audit against rounded
    figures inherits their tolerance: per-class rates at 4dp sit on a
    3-row grid, so the identity could never resolve one row. Publish
    counts and derive the rates.
45. **Zero selected is not zero failed.** `pytest -k` exits green having
    run nothing, and it looks identical to a pass at a glance. Guarded in
    `conftest.py`.
46. **A status is a claim too.** "Fixed" belongs in a document only after
    the terminal says so. The 2 Sep session recorded a boundary fix and a
    new test; neither existed, and both survived a full session unread.
47. **An audit whose result is forced by construction is not an audit.**
    The markup containment check asked whether rows matching `&lt;...`
    were also matched by a pattern for `lt;` — guaranteed, since the first
    string contains the second. It returned the expected answer and tested
    nothing.
