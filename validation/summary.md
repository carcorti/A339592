# Local validation summary

Project owner: Carlo Corti.

Scope: A339592, native and separate Python enumerations at all `n = 1..144`.
Newly validated values are `13..144`, with `a(13) = 104` and
`a(144) = 4839167564472933081443`. The first unresolved index is 145.
The saved OEIS prefix is `1..12`, while the later local b-file is `1..144`.

The native campaign used the frozen C source and Makefile preserved in
`results/run_identity/`, with its original executable retained as
`results/a339592`. The public `src/` files are separately identified,
path/comment-normalized copies. The historical program formed graph
edges from GF(2) Motzkin-series powers and counted independent sets by vertex
deletion. The exact original `meta.json`, `run.tsv`, and log are included.
The Python checker used integer coefficients and Lagrange inversion for graph
construction, then a weighted sum over independent odd-vertex subsets. Its
complete original `check.json` and log are included. The original machine
audit is `results/audit.json`; the contemporaneous prose report is
`results/validation.md`. The later b-file action is `results/bfile_update.md`.
The historical source/Makefile hashes are
`6a0a090df428ab36e5127e473f0b180e804faae1e794aed2faf612702ee82374`
and `87bd9d642bbd4f6d843bd0d8311cb8dfc0df288faf6989f4a5d9dc2f6bb9fe93`;
the public source/Makefile hashes are
`51465aaeb2dc08572016f6b4f9283f0fdac6b167f530bd69ea290ee2ec22c99f`
and `9fd8d77cf47f1f15290037adb95a0454730c04aadf6b71d18ccb561bd2a3fcdb`.

The native run took about 13 seconds wall time with 50,684 KiB peak RSS. The
independent Python comparison took about 266 seconds wall time with 18,612 KiB
peak RSS. These are historical measurements from the original logs, not
package-check benchmarks. The included pre-run host record is
`results/environment.txt`. A compact exact telemetry index is
`validation/run_manifest.tsv`; the raw logs remain authoritative. No later
runtime forecast is supported.

From a package root, run `sh validation/run.sh`. It checks `SHA256SUMS`, rejects
undeclared package files and directories, verifies the declared path/comment-only
public source transformation, and compares the
144 retained indexed rows and log coverage, verifies native state integrity
with the original executable, compiles the public source and runs bounded C
and Python tests through order 16. It does not repeat the 144-term campaign.
The exact separate full Python CLI is in `README.md`; the original checker is
not reconstructed. The bounded public fixture changes are documented in
`validation/public_delta.patch` and checked by `validation/check_package.py`.

The runner requires Linux, GCC 13, Python 3.12, `make` and `sha256sum`. The
compiled test binary is cleaned on exit. The optional full checker is
restartable, but its fresh execution and any new C campaign remain outside
this draft-package check. Native `verify` proves file/identity integrity;
`validation/audit.py` compares retained data and logs; bounded tests recompute
small orders. These checks do not formally prove each 144-term value.

Publication state: the GitHub repository is public, and this package revision
is prepared for its first release, `v1.0`. The DOI is a literal placeholder
pending Zenodo synchronization. No distributed-release claim is made. The CFF
release date is intentionally pending a confirmed release date.
