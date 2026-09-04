"""Near-duplicate detection. DELIBERATELY EMPTY.

Removal is a measurement, not a default (METHOD 11, v5 rule 13). The
output is a count and the count decides removal -- head arithmetic said a
few hundred rows, the tail sample says thousands, and that decision was
reversed twice in one day because it never rested on a number.

Design before code, in this order:

1. Blocking vocabulary: mid-frequency terms only. High-frequency excluded
   for cost (the operation scales as the sum over terms of documents^2),
   low-frequency for precision (one shared surname with a high IDF weight
   pushes two unrelated rows over threshold).
2. Recall calibrated against tail duplicate-title pairs on the
   DESCRIPTION field only. The title is the selection criterion and must
   stay outside the scored field, or the threshold will not transfer
   (METHOD 23a).
3. Precision from sampled pairs read by eye, with the decision rule
   written before the first pair.
4. Sweep the threshold, report a range, show the conclusion is
   insensitive to it (METHOD 22).

Blocks Experiment B: near-copies split across the train/test boundary
inflate scores most at the small prefixes, which is exactly where the
learning curve's shape lives.
"""