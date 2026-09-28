#!/usr/bin/env python3
"""Read-only integrity and indexed-result audit of the retained A339592 run."""

import hashlib
import json
from pathlib import Path
import re

import check_counts as checker


ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    native = ROOT / 'results/native'
    raw, counts = checker.load(native / 'run.tsv')
    require(len(counts) == 144, 'native range is not 1..144')
    meta = json.loads((native / 'meta.json').read_text())
    report = json.loads((ROOT / 'results/audit.json').read_text())
    for path, key in (
        (ROOT / 'results/run_identity/a339592_v2.c', 'source_sha256'),
        (ROOT / 'results/run_identity/Makefile', 'make_sha256'),
        (ROOT / 'results/a339592', 'binary_sha256'),
    ):
        require(sha(path) == meta[key], f'run identity mismatch: {path.name}')
        require(sha(path) == report['native'][key], f'audit identity mismatch: {path.name}')
    require(meta['target'] == 144, 'metadata target')
    require(sha(native / 'run.tsv') == report['native']['snapshot_sha256'], 'native snapshot hash')
    require(sha(ROOT / 'validation/check_counts.py') == report['independent_checker']['source_sha256'],
            'checker source hash')
    require(sha(ROOT / 'results/check/check.json') == report['independent_checker']['state_sha256'],
            'checker state hash')
    require(sha(ROOT / 'results/native.log') == report['native']['log_sha256'], 'native log hash')
    require(sha(ROOT / 'results/check.log') == report['independent_checker']['log_sha256'],
            'checker log hash')

    base = {'schema': 1, 'sequence': 'A339592',
            'snapshot_sha256': checker.digest(raw),
            'checker_sha256': sha(ROOT / 'validation/check_counts.py'),
            'first': 1, 'last': 144, 'rows': []}
    state = checker.validate_state((ROOT / 'results/check/check.json').read_bytes(), base, counts)
    require(len(state['rows']) == 144, 'checker range is incomplete')

    braw = (ROOT / 'data/b339592.txt').read_bytes()
    require(braw.endswith(b'\n\n') and not braw.endswith(b'\n\n\n'),
            'b-file final blank line')
    rows = braw.decode('ascii').splitlines()
    require(rows[-1] == '' and len(rows) == 145, 'b-file row count')
    for n, (line, value) in enumerate(zip(rows[:-1], counts), 1):
        require(line == f'{n} {value}', f'b-file mismatch at {n}')
    previous = (ROOT / 'results/bfile_pre144.txt').read_text().splitlines()
    require(previous[:12] == rows[:12] and len(previous) == 13 and previous[-1] == '',
            'historical OEIS prefix')
    require(counts[12] == 104 and counts[143] == 4839167564472933081443,
            'endpoint values')

    c_log = (ROOT / 'results/native.log').read_text().splitlines()
    p_log = (ROOT / 'results/check.log').read_text().splitlines()
    c_start = [int(m.group(1)) for line in c_log
               if (m := re.fullmatch(r'START n=(\d+) completed_rows=\d+', line))]
    c_done = [int(m.group(1)) for line in c_log
              if (m := re.match(r'COMMITTED n=(\d+) ', line))]
    p_start = [int(m.group(1)) for line in p_log
               if (m := re.fullmatch(r'START n=(\d+) checked=\d+', line))]
    p_done = [json.loads(line) for line in p_log if line.startswith('{"status": "COMMITTED"')]
    expected = list(range(1, 145))
    require(c_start == c_done == p_start == [row['n'] for row in p_done] == expected,
            'start/commit log coverage')
    require([row['count'] for row in p_done] == [str(x) for x in counts],
            'checker log values')
    require(any('COMPLETE rows=144 target=144' in line for line in c_log),
            'native terminal log')
    require(any('"status": "CHECKED_RANGE"' in line and '"completed": 144' in line
                for line in p_log), 'checker terminal log')
    require(sum(line.strip() == 'Exit status: 0' for line in c_log) == 1 and
            sum(line.strip() == 'Exit status: 0' for line in p_log) == 1,
            'log process exit status')
    print('RETAINED EVIDENCE PASS: indexed native/checker/b-file rows 1..144, identities, logs')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        raise SystemExit(f'RETAINED EVIDENCE FAIL: {error}') from error
