# A339592 — local b-file update through n=144

Date: 2026-09-25. Owner: Carlo Corti. Scope: Carlo authorized an update of the **local** `data/b339592.txt` after completion of the reviewed native campaign and independent result validation. No OEIS submission, snapshot edit, new campaign, review dispatch or publication occurred.

## Inputs and transformation

- The pre-edit b-file had indexed rows 1..12 and SHA-256 `e17bff5f69b3388e0fd757ba96c4df7a0090e77b83480df686b0e92716e8df18`. Its exact 59 bytes are preserved at `outputs/history/b339592_pre144_v1.txt` with the same hash.
- The canonical result snapshot is `campaign144/run.tsv`, SHA-256 `cc2cbed062a2988705f1ce1e152def8822977c4eb8873825d54b24396fea55b2`; the full indexed independent comparison is `check144/check.json`, SHA-256 `c765a94452e7ce776b6412f021e7b34267c6de6d3763657f7af9c074e47679c3`. The unchanged phase-09 assessment is `outputs/result_validation144_v1.md` and its machine-readable audit is `outputs/result_audit144_v1.json`.
- Before writing, the exact old b-file bytes were matched against rows 1..12 of the native snapshot; the Python checker's canonical state checksum and its source/snapshot/range binding were revalidated; all 144 indexed checker values matched the snapshot. The candidate b-file was built from rows 1..144 only, with `n value` lines and exactly two terminal LF bytes, preserving the prior framing convention.
- The original file was copied exclusively to the history path and checked byte for byte. The candidate was written to a temporary file in `data/`, fsynced and atomically replaced into `data/b339592.txt`; the final bytes were checked against all 144 indexed native and checker rows.

## Post-edit result

| Item | Exact result |
|---|---|
| Current local b-file | `data/b339592.txt`, 144 consecutive rows 1..144, 2,252 bytes, SHA-256 `3e3ce882594bb712221b69393fdc6e0ebb5f7001ebf269e66b967ff658842177` |
| Preserved predecessor | `outputs/history/b339592_pre144_v1.txt`, rows 1..12, SHA-256 `e17bff5f69b3388e0fd757ba96c4df7a0090e77b83480df686b0e92716e8df18` |
| First new row | `13 104` |
| Last row | `144 4839167564472933081443` |
| Post-edit identity manifest | `outputs/bfile_update144_v1.sha256`, SHA-256 `12a810388c0c08f9870c5b669af987a87c721baef2f13c357051c8a5656ea497`; includes 14 current/historical files and passes `sha256sum -c` |

The native source, Makefile, executable, checker source, campaign metadata/snapshot, checker state, both original logs and OEIS snapshot retain their recorded SHA-256 identities. `./src/a339592 verify campaign144` still returns `INTEGRITY PASS rows=144 target=144 state=COMPLETE pending_tmp=none`. The old `freeze144_v1.sha256` is deliberately preserved as proposal/run-time provenance: its check now fails **only** for `data/b339592.txt`, as expected after this authorized edit. Its historical b-file hash is satisfied by the preserved predecessor; no historical manifest or result audit has been rewritten to pretend that the extended b-file existed during the run.

The updated local b-file is not yet an OEIS edit. `snapshot/A339592 - OEIS.md` still represents the pre-submission OEIS state, including keyword `more`. Any OEIS entry proposal, keyword removal, upload or publication requires its own subsequent instruction and current-state reconciliation.
