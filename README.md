# A339592: independent sets in Motzkin graphs

This v1.0.1 publication package accompanies Carlo Corti's manuscript
[`paper/A339592.tex`](paper/A339592.tex) and its [matching PDF](paper/A339592.pdf). For the Motzkin graph on `n`
vertices, `a(n)` counts all independent vertex sets, including the empty set.
The stored, locally cross-checked values cover `n = 1..144`. The added values
relative to the saved OEIS entry are `13..144`: `a(13) = 104` and
`a(144) = 4839167564472933081443`. The first unresolved index is 145.
The source's 192-vertex numeric capacity is not a computed result through 192.

## Contents

| Path | Role |
| --- | --- |
| `src/a339592.c`, `src/Makefile` | Stable public C17 source and build recipe, with documentary/path-only changes from the campaign files. |
| `results/run_identity/`, `results/a339592` | Exact historical source, Makefile, bounded fixtures and executable, retained for run identity. |
| `validation/check_counts.py` | Exact Python checker source used for the 144-row comparison; integer/Lagrange graph construction and weighted odd-subset count. |
| `validation/test_candidate.py`, `validation/test_check_counts.py`, `validation/graph_probe.c` | Bounded public-source tests with documented path and data-range adjustments. |
| `validation/check_package.py`, `validation/audit.py`, `validation/run.sh` | Complete-inventory, exact-diff, retained-evidence and bounded public test runner. |
| `results/native/`, `results/check/check.json` | Canonical C snapshot and complete independently computed Python state. |
| `results/native.log`, `results/check.log`, `results/audit.json` | Original execution logs and machine-readable local assessment. |
| `data/b339592.txt` | Consecutive indexed b-file, `1..144`, with a final blank line. |
| `results/validation.md`, `results/bfile_update.md` | Unmodified historical reports, written before and after the local b-file update respectively. |
| `results/bfile_pre144.txt`, `results/oeis_snapshot.md` | Saved 12-term predecessor and OEIS snapshot; historical references only. |
| `results/environment.txt`, `results/triage.md`, `results/tail_checks.txt`, `results/high_order.txt` | Pre-run environment and cited bounded diagnostics. |
| `paper/A339592.tex`, `paper/A339592.pdf` | Monolithic English manuscript with its own bibliography and matching rendered PDF. |
| `PROVENANCE.md`, `validation/summary.md`, `validation/run_manifest.tsv`, `SHA256SUMS` | Source mapping, scope, run telemetry, and byte identities. |

The snapshot of OEIS still shows 1..12 and keyword `more`; the local b-file
contains 1..144. The report `results/validation.md` accurately says the
b-file ended at 12 **when that report was written**. The subsequent change is
documented by `results/bfile_update.md`. No OEIS edit follows from this package.
There are no validated exact values beyond 144, so no auxiliary a-file is
useful at present.

The historical run metadata binds the **original** source and Makefile in
`results/run_identity/` and the original executable in `results/a339592`.
The public source and Makefile in `src/` have different hashes because of the
stable source name and documentary/path references. Their exact changes are
checked by `validation/check_package.py` and recorded in
`validation/public_delta.patch`. The public build did not produce the
historical 144-row snapshot.

## Build and bounded validation

Requirements: Linux with POSIX file operations and `/proc/self/exe`, GCC 13
(`gcc-13`, including `unsigned __int128`), `make`, Python 3.12, and `sha256sum`.
No third-party Python package is required. From the package root:

```sh
sh validation/run.sh
```

This checks the declared file hashes, rejects undeclared package files and
directories, and verifies the exact public-source transformation,
all 144 retained native/Python/b-file rows and original log coverage, runs the
original executable's **integrity** check, builds the public C source, and performs bounded C and Python tests
through order 16. The full Python 1..144 computation was completed in the
original campaign and its exact state and log are included. The command above
does **not** repeat that computational campaign. To independently recompute
the entire range later, create an empty state directory outside the native
snapshot and run, for example:

```sh
mkdir -p /tmp/a339592_check
python3 -B validation/check_counts.py results/native/run.tsv \
  --from 1 --through 144 --state /tmp/a339592_check/check.json
```

This latter command is an optional new computation, not part of the bounded
package check. The checker resumes a partial state. The historical state in
`results/check/check.json` must not be rewritten. To build the public C executable
without altering the retained historical binary, run `make -C src`, then use
`src/a339592 selftest`; `make -C src clean` removes the rebuilt copy. A new C
run uses `src/a339592 run N NEW_DIR`, with `N = 1..192`, but no result above
144 is supplied or implied here.

The graph definition and indexing are shared premises. The C program forms
adjacency from Motzkin coefficients over GF(2) and counts by vertex deletion;
the Python checker obtains exact integer coefficients through Lagrange
inversion and sums weights over independent odd-vertex subsets. The two full
computations agreed at every stored index; the integrity audit only checks
retained bytes and their consistency.

The TeX file is self-contained apart from standard LaTeX packages
(`lmodern`, AMS, `booktabs`, `microtype`, `geometry`, `hyperref`). The matching
PDF is included. Rebuilding requires `latexmk` and `pdflatex` with those
packages installed. To rebuild without writing auxiliary files into the
package, run from the package root:

```sh
mkdir -p /tmp/a339592_tex_build
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir=/tmp/a339592_tex_build paper/A339592.tex
```

The primary research papers are cited in its bibliography and may be acquired through their DOI or
arXiv links; third-party full texts are not redistributed here.

## Publication state

The repository is publicly available at
`https://github.com/carcorti/A339592`. This package revision is for GitHub
release `v1.0.1`; the predecessor `v1.0` is already published. The
author-designated Zenodo concept DOI is `10.5281/zenodo.23010698` (link:
`https://doi.org/10.5281/zenodo.23010698`). It identifies the release series,
not a specific deposited version. The v1.0 record has version DOI
`10.5281/zenodo.23010699`; consult the published Zenodo v1.0.1 record for
its version-specific DOI. `CITATION.cff` intentionally omits a release date;
the provider record supplies its authoritative publication date.
The MIT license covers Carlo Corti's original project software and documents.
The historical OEIS snapshot and predecessor prefix have separate source
attribution and license treatment in `OEIS_LICENSE.md`. See `PROVENANCE.md`
for exact copy and adaptation boundaries.
