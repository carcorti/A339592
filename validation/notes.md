# Validation method and limits

The original C17 program and Python checker were each run across the entire
indexed range 1..144. The retained Python state records a match at every
native snapshot index; both original logs record 144 starts, commits, terminal
completion and process exit zero. `audit.py` checks those retained facts and
their original hashes without changing the historical states. The original
binary's `verify` command checks snapshot and build identity, but does not
recompute any independent-set count.

`run.sh` additionally checks the exact public-versus-historical source/build
delta, builds the public source, runs its self-test, compares
all 18,336 graph-pair bits against integer Motzkin-series coefficients and
performs bounded direct and independent checker counts through order 16.
This is a new small-order test, separate from the original 144-order campaign.
The Python checker itself remains byte-identical to that campaign. Public
bounded test files adjust paths and the expected b-file range. Their exact
diff with the historical source and Makefile is `public_delta.patch`.

`run_manifest.tsv` transcribes the two original `/usr/bin/time -v` log
records. Its `command_at_run` fields refer to the original workspace paths;
its `state` and `log` fields point to the equivalent package copies.
`peak_rss_kib` preserves the source log's kbyte label (Linux KiB meaning),
and `wall_seconds` is the clock conversion of the printed `0:13.17` and
`4:25.88`. The native and checker log files preserve finer details including
per-order timings. No separate thread count or forecast is inferred.

The methods share the Motzkin graph definition and vertex indexing. Full
cross-algorithm agreement is strong finite computational evidence; it is not
a proof for arbitrary orders. The numeric design ceiling of 192 does not
establish runtime feasibility or produce results past 144.
