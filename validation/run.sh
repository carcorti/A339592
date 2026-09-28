#!/bin/sh
# Bounded source checks and read-only retained evidence audit; no new campaign.
set -eu
cd "$(dirname "$0")/.."
trap 'make -C src clean >/dev/null' EXIT
sha256sum -c SHA256SUMS >/dev/null
python3 -B validation/check_package.py
python3 -B validation/audit.py
results/a339592 verify results/native
make -C src test
python3 -B validation/test_check_counts.py
printf 'PUBLIC BOUNDED VALIDATION PASS: retained evidence and small-order tests\n'
