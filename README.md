# gold-checker

Find the benchmark items whose gold answer disagrees with itself.

Many numerical-reasoning benchmarks store two gold fields for every question: a **program** that
computes the answer (`subtract(5829, 5735), divide(#0, 5735)`) and a **written answer** (`1.6%`).
They are supposed to say the same thing. When they don't, at least one of them is wrong or the key
is ambiguous, and a correct model can be marked wrong depending on which field the scorer reads.

gold-checker reruns every gold program, compares the result with the stored value and the written
answer, and reports each disagreement with a label (wrong value, flipped sign, off by a power of ten, yes/no
mismatch, empty answer). It works as a Python library, a command-line tool and a Streamlit app.

## What it found

Run on the public files, unchanged, it reproduces the counts in my audit
([Varman 2026, doi:10.5281/zenodo.24520462](https://doi.org/10.5281/zenodo.24520462)):

| Benchmark | Items | Written answer disagrees with gold value | Also flagged |
|---|---|---|---|
| FinQA test | 1,147 | **78 (6.8%)**: 58 wrong value, 11 flipped sign, 7 off by a power of ten (10, 1,000 or 1,000,000), 2 yes/no | 24 empty or non-numeric answers; 4 programs that don't reproduce their stored value |
| FinQA dev | 883 | **56 (6.3%)** | 22 empty or non-numeric; 4 programs |
| ConvFinQA dev | 542 conversation questions (458 unique) | **27 of 458 unique questions flagged** (18 disagree, 9 empty or non-numeric) | ConvFinQA inherits these from FinQA |
| ConvFinQA train | 3,965 (3,321 unique) | **257 of 3,321 unique questions flagged** | |

Four of the flagged FinQA test items, recomputed by hand from the source filing in the audit. They show
why the checker flags rather than corrects: sometimes the written answer is wrong, sometimes the program,
sometimes both.

| Item | Written answer | Program gives | Recomputed from the filing | Which gold is wrong |
|---|---|---|---|---|
| CME/2010/page_91.pdf-1 | 29% | 27.3% | (11.2 - 8.8) / 8.8 = 27.3% | written answer |
| AMT/2014/page_149.pdf-2 | 63458 | 33458 | 28524 + 4934 = 33458 | written answer (digit slip) |
| MSI/2014/page_76.pdf-3 | 15.8% | 12.2% | (11.02 - 9.52) / 9.52 = 15.8% | program |
| UNP/2011/page_33.pdf-1 | 81.6% | 76.1% | 70.6 - 5.5 = 65.1% | both |

The full flagged lists are in [docs/demo_results.md](docs/demo_results.md), and the tests check that the
78 FinQA items are exactly the 78 in the published audit.

What "disagrees" does and doesn't mean: the checker proves the two gold fields are inconsistent, so a model that
matches one of them is marked wrong by the other. It doesn't say which is right. The counts are inconsistencies, not
hand-confirmed error rates; the audit hand-checked a sample of them.

## Try it

**In the browser:** `streamlit run streamlit_app.py`, then pick FinQA test in the sidebar. The app
downloads the file from FinQA's own GitHub repository, checks it in about a second, and shows the
counts, a chart of disagreement kinds, a filterable table of flagged items, a per-item view with the
program and source table, and CSV / JSON / Markdown downloads. You can also upload your own file.

**On the command line:**

```
pip install .
gold-checker demo finqa-test                       # download FinQA test and check it
gold-checker check examples/sample.csv             # check a file
gold-checker check my_benchmark.jsonl --out flagged.csv --tolerance 0.01
gold-checker check my_benchmark.jsonl --fail-on-disagree   # exit 1 in CI if anything disagrees
```

**From Python:**

```python
from gold_checker import load_items, run_check

items, fmt = load_items('my_benchmark.jsonl')
report = run_check(items, fmt=fmt)
print(report.summary())
for r in report.flagged:
    print(r.item.id, r.kind, r.item.answer, r.compared_with)
```

## Your own benchmark

FinQA and ConvFinQA files are read as they ship. For anything else, give one row per item
(JSON list, JSONL or CSV) with:

| Column | Needed | What it is |
|---|---|---|
| `answer` | yes | the written gold answer |
| `program` | one of these two | a FinQA-style program (`add`, `subtract`, `multiply`, `divide`, `exp`, `greater`, `table_sum/average/max/min`, `#N` step references, `const_N`) |
| `exe_ans` (or `value`) | one of these two | the stored gold value |
| `id`, `question`, `table`, `page` | no | `table` is a list of rows; `page` lets it count unique page-question pairs |

With both a program and a stored value, it checks the program against the value and the written answer
against the value. With only one, it checks the written answer against that one.

## How it compares answers

- A written answer is compared **at the precision it is written**: `14.1%` agrees with 0.14096.
- Otherwise it must agree within a **relative** tolerance (default 0.5%, `--tolerance` to change).
  Relative, so a small fraction such as 0.004 isn't waved through as "about zero".
- `12.5%` against a gold value of 12.5 (already in percent) is counted as a percent-format note, not an
  error, because the number is right. These are reported separately.
- Accounting brackets `(12)` read as -12, `$` and thousands commas are ignored.

## Tests

```
pip install ".[test]"
pytest
```

The unit tests run offline. `tests/test_reproduce.py` downloads FinQA and ConvFinQA from their GitHub
repositories, checks the SHA-256 of each file against the version the audit used, and asserts the 78,
the 27 of 458 and the 257 of 3,321. It skips itself when there is no network.

## Layout

```
src/gold_checker/dsl.py       program executor
src/gold_checker/compare.py   written answer vs gold value, with disagreement labels
src/gold_checker/loaders.py   FinQA, ConvFinQA and generic JSON/JSONL/CSV readers
src/gold_checker/check.py     runs the checks, builds the report
src/gold_checker/report.py    CSV, JSON and Markdown output
src/gold_checker/datasets.py  pinned downloads of the public demo files
src/gold_checker/cli.py       command line
streamlit_app.py              web app
tests/                        unit tests and the published-count reproduction
```

The core uses the Python standard library only (3.9+); the app needs `streamlit` and `pandas`.

## Credit and citation

Michael T. Varman, Morphogenesis Analytics (independent researcher).
ORCID [0009-0001-9453-0226](https://orcid.org/0009-0001-9453-0226).

The checks are the ones from my finance benchmark audit, which also covers TAT-QA, FinanceBench,
MultiHiertt, TAT-HQA and the FinBen/FLARE scoring code:
Varman, M. T. (2026). *Gold-Answer Errors in Financial Numerical-Reasoning Benchmarks.* Zenodo.
[doi:10.5281/zenodo.24520462](https://doi.org/10.5281/zenodo.24520462). Citation metadata is in
`CITATION.cff`.

I built this by directing AI coding assistants; the method, the checks and the hand verification
behind the published counts are from my audit.

FinQA (Chen et al., EMNLP 2021) and ConvFinQA (Chen et al., EMNLP 2022) are MIT-licensed and are
downloaded from their own repositories, not redistributed here. Code: MIT license.
