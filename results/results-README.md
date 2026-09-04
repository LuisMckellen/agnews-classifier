# results/

Captured terminal output. Nothing here is generated at read time — these
are records of what specific code produced on a specific day.

## Current

| File | Produced by | Date |
|---|---|---|
| `01_verify.txt` | `scripts/01_verify.py` | 4 Sep |
| `02_collision.txt` | `scripts/02_collision.py` | 4 Sep |
| `corruption_2x2.jsonl` | `scripts/03_experiment_2x2.py` | mixed — filter by `experiment` |

`corruption_2x2.jsonl` holds more than one experiment: the 31 Aug 2×2, five
`dummy` records, and anything since. Always filter on the `experiment`
field; never assume every record belongs to the comparison in front of you.

## Superseded (`superseded/`)

Kept as provenance, not as figures. Cite nothing from here.

| File | Produced by | Why kept |
|---|---|---|
| `baseline_inspect.txt` | `inspect_corruption.py` | the run that gave 38,678 with the canonical pattern |
| `baseline_audit.txt` | `audit.py` | the only surviving record of the 38,679 run, and independent confirmation that `repair` was unfixed (vocab diff −1) |
| `baseline_dup.txt` | `dup.py` | duplicate-title counts before the unit was stated |
| `baseline_collision.txt` | `collision.py` | case-sensitive collision table |
| `baseline_pytest.txt` | `pytest -q` | the 8-test suite, before the boundary test existed |
| `audit.txt`, `collision.txt`, `tailreport.txt` | same scripts, earlier runs | earlier captures |

The scripts that produced these were removed in the 4 Sep frame rebuild
and live in git history. See `CORRECTIONS.md` for what changed and why.
