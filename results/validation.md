# A339592 — local validation of campaign 1..144

Date: 2026-09-25. Owner: Carlo Corti. **RESULTS_VALIDATED_LOCAL** for the contiguous range 1..144; newly validated rows are 13..144 (132 terms). The first unresolved index under this campaign is 145. This report does not change the canonical b-file, OEIS, the frozen code or any campaign artifact.

## Exact result and identity

| Item | Observation |
|---|---|
| Native campaign | `campaign144/meta.json` SHA-256 `c3fd011fa1ccd993cc99128cb7fc6752a1550a50a5b2a4e6f0b5916572460474`; `campaign144/run.tsv` SHA-256 `cc2cbed062a2988705f1ce1e152def8822977c4eb8873825d54b24396fea55b2` |
| Native log | `native144.log` SHA-256 `6d19f02a2a77b288a58b50dc8558d6185575251cbb81a28919d61f39438c131c` |
| Native identity | C source `6a0a090df428ab36e5127e473f0b180e804faae1e794aed2faf612702ee82374`; Makefile `87bd9d642bbd4f6d843bd0d8311cb8dfc0df288faf6989f4a5d9dc2f6bb9fe93`; binary `80655158165d0a88adb1a7491f1be21cabcd9a37fc14e8490128614d6f17352f` |
| Python checker | `validation/check_counts.py` SHA-256 `df8c4cf77c0073e74c655a281bbc22c290868c9c8d0343c4c70f9ced4d3949e3` |
| Python state and log | `check144/check.json` SHA-256 `c765a94452e7ce776b6412f021e7b34267c6de6d3763657f7af9c074e47679c3`; `check144.log` SHA-256 `6e653f914750a25508a9e43bcb59416d6a982a7b13ce3f29f43f68266d3048df` |
| Known prefix | Indexed rows 1..12 agree with unchanged `data/b339592.txt` SHA-256 `e17bff5f69b3388e0fd757ba96c4df7a0090e77b83480df686b0e92716e8df18` |
| Endpoint examples | `a(13)=104`, `a(144)=4839167564472933081443`; all indexed values are in the frozen native snapshot and independently matched in the checker state. |

The native log has exactly one `START` and one `COMMITTED` for each index 1..144, in order, one `COMPLETE rows=144 target=144`, and `/usr/bin/time` exit 0. A fresh read-only `./src/a339592 verify campaign144` returned `INTEGRITY PASS rows=144 target=144 state=COMPLETE pending_tmp=none`. This checks committed-file integrity and binary identity, not the mathematics.

The Python log has exactly one `START` and one `COMMITTED` for each index 1..144, in order, one `CHECKED_RANGE` with `completed=144`, `last_completed=144`, `unchecked_rows=0` and the exact native snapshot hash, and `/usr/bin/time` exit 0. The canonical `check.json` checksum and binding to checker hash, snapshot hash and range 1..144 passed the checker source's read-only `validate_state` function. Each of its 144 `(n,count)` rows matches the same indexed native snapshot row and the corresponding log record. The state directories contain only their canonical persistent files, with no pending temporary file. The block-0 receipt hashes still match the untouched native files. The proposal-time 13-file freeze check passed again.

## Scientific scope and performance

The C counts independent sets by vertex deletion on a graph generated via Motzkin-series powers over GF(2). The Python checker constructs graph coefficients by integer Lagrange inversion and counts via a weighted enumeration of independent odd-vertex subsets. These are distinct coefficient and counting implementations. Both depend on the same mathematical graph definition and index convention. The earlier bounded graph, known-prefix, small-order and selected-high-order tests support the method; the official 1..144 comparison supplies the complete range evidence. The result is computational validation, not a formal proof of each large integer.

The native block used 13.17 seconds wall and 50,684 KiB peak RSS. The Python block used 4:25.88 wall, with 115.62 seconds user CPU, 148.06 seconds system CPU, 18,612 KiB peak RSS and 34,720,958 minor page faults. Its final state reports 265.849707606 seconds elapsed. Terms 143 and 144 each took about 96 seconds inside this run, versus roughly 10 and 9 seconds in prior single-order diagnostics. The cause of this marked variation is unconfirmed. It did not prevent completion within the 1200-second block ceiling; it **does prevent a reliable projection to 160 or 192**. Any later horizon needs new calibration and separate authorization. The source's numeric design capacity to 192 is unchanged.

## Admission boundary and next state

The local indexed comparison supports 1..144, including new exact computational values 13..144. Their canonical data source is `campaign144/run.tsv` together with the exact checker state and both logs. No theorem-derived values are mixed into this range. The original OEIS b-file still ends at 12. Preparing an updated b-file, an OEIS proposal, a public package, a manuscript or another campaign is a separate stage and requires its own scope. Preserve the native and checker states and original logs; do not rewrite or rerun them for reassurance.
