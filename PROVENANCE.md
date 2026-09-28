# Provenance and public-file mapping

Canonical project identity: **Carlo Corti**, from his explicit current
workspace instructions and the matching frozen source, manuscript and local
license. Historical manuscript and run identities are preserved; the stable
public source/build have distinct hashes.

| Original workspace path | Package path | Treatment |
| --- | --- | --- |
| `src/a339592_v2.c`, `src/Makefile` | `results/run_identity/` | Byte-identical reviewed and executed sources, kept as historical run identity. |
| `src/a339592_v2.c`, `src/Makefile` | `src/a339592.c`, `src/Makefile` | Separate public build identity: source basename and documentary comments; Makefile source/test paths and comment. Exact transformation is checked by `validation/check_package.py`. |
| `src/a339592` | `results/a339592` | Byte-identical original executable, for historical integrity verification. |
| `validation/check_counts.py` | `validation/check_counts.py` | Byte-identical original independent checker. |
| `validation/test_candidate_v2.py`, `validation/test_check_counts.py`, `validation/graph_probe_v2.c` | `results/run_identity/` | Byte-identical historical bounded fixtures, retained for exact comparison. |
| `validation/test_candidate_v2.py`, `validation/test_check_counts.py`, `validation/graph_probe_v2.c` | `validation/test_candidate.py`, `validation/test_check_counts.py`, `validation/graph_probe.c` | Public fixtures use stable paths and the 144-row b-file. Exact patch: `validation/public_delta.patch`. |
| `campaign144/meta.json`, `campaign144/run.tsv` | `results/native/` | Byte-identical canonical native state, bound to source, Makefile and binary hashes. |
| `check144/check.json` | `results/check/check.json` | Byte-identical complete Python checker state, bound to its original source and native snapshot hashes. |
| `native144.log`, `check144.log` | `results/native.log`, `results/check.log` | Byte-identical original logs; only names shortened. |
| `data/b339592.txt` | `data/b339592.txt` | Byte-identical post-update 144-row b-file. |
| `outputs/result_validation144_v1.md`, `outputs/result_audit144_v1.json` | `results/validation.md`, `results/audit.json` | Byte-identical historical report and audit. |
| `outputs/bfile_update144_v1.md`, `outputs/history/b339592_pre144_v1.txt` | `results/bfile_update.md`, `results/bfile_pre144.txt` | Byte-identical later update report and earlier b-file. |
| `snapshot/A339592 - OEIS.md` | `results/oeis_snapshot.md` | Byte-identical saved OEIS page; its 12-term state is historical. |
| `outputs/campaign_handoff/environment144_v1.txt`, `outputs/triage_checks.md` | `results/environment.txt`, `results/triage.md` | Byte-identical pre-run and small-order diagnostics. |
| `outputs/campaign_handoff/validation_tail144_v1.txt`, `outputs/campaign_handoff/high_order_comparison_v1.txt` | `results/tail_checks.txt`, `results/high_order.txt` | Byte-identical bounded high-order diagnostics; they are not extra campaign terms. |
| `paper/A339592_v3.tex` | `paper/A339592_v3.tex` | Byte-identical current provisional manuscript; no PDF. |

`validation/check_package.py`, `validation/audit.py` and `validation/run.sh`
are new public-package checks, not historical campaign code. The exact historical C and
Python hashes are in `results/native/meta.json` and `results/audit.json`;
`SHA256SUMS` covers the entire proposed public file inventory except itself.
The package checker compares that declared inventory with all packaged files
and directories, allowing only root `.git` metadata in a clone.
The saved OEIS snapshot and historical prefix are attributed separately in
`OEIS_LICENSE.md` under the OEIS content license.
Reports preserve their original workspace-relative path references as
historical statements; this mapping resolves them to the package.
The absolute checker path in `results/tail_checks.txt` likewise records the
original workspace; the packaged checker is `validation/check_counts.py`.
The historical `freeze144_v1.sha256` mentioned in `results/environment.txt`
and `results/bfile_update.md` is a pre-run manifest, not a public validation
command or a package file. It refers to the older 12-row b-file and would not
pass unchanged against the updated 144-row b-file. The retained run identities
are checked against `results/native/meta.json`, `results/audit.json`, and the
separate public `SHA256SUMS` manifest.

| Identity | C source SHA-256 | Makefile SHA-256 |
| --- | --- | --- |
| Historical run (`results/run_identity/`) | `6a0a090df428ab36e5127e473f0b180e804faae1e794aed2faf612702ee82374` | `87bd9d642bbd4f6d843bd0d8311cb8dfc0df288faf6989f4a5d9dc2f6bb9fe93` |
| Stable public build (`src/`) | `51465aaeb2dc08572016f6b4f9283f0fdac6b167f530bd69ea290ee2ec22c99f` | `9fd8d77cf47f1f15290037adb95a0454730c04aadf6b71d18ccb561bd2a3fcdb` |

The public hashes identify the source and Makefile, not a claim that the
historical run was rebuilt with them. The source/Makefile transformation and
bounded fixtures are documented in `validation/public_delta.patch` and checked
by `validation/check_package.py`.

The source and Makefile in `src/` have no lifecycle version suffixes or
review-version comments. Their hashes differ from those bound to the original
run. `validation/check_package.py` checks the exact transformation;
`results/a339592 verify results/native` uses the untouched original binary.
The original result-validation report predates the b-file update. The latter
report records the authorized transition to 1..144. The OEIS snapshot was not
updated. The current b-file is not evidence that OEIS already contains the
new terms. The independent checker and native run share the graph definition
and indexing, but use distinct coefficient construction and counting logic.

Third-party Riordan-graph papers consulted for the manuscript are cited by
their primary DOI/arXiv locators inside the TeX, without redistributing local
copies of their full text. Private code and manuscript reviews, obsolete
drafts, caches, temporary diagnostics, and local framework dossiers remain
outside this publication draft. No exact result beyond 144 is held here;
auxiliary a-file decision: **NO** (no later sparse exact term).
