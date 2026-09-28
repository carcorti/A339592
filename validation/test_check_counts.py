#!/usr/bin/env python3
"""Bounded, disposable checks for the independent A339592 validator."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'validation/check_counts.py'
NATIVE = ROOT / 'src/a339592'


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*args):
    return subprocess.run([str(x) for x in args], text=True,
                          capture_output=True, timeout=60)


def require(condition, message):
    if not condition:
        raise SystemExit('CHECKER TEST FAIL: ' + message)


def integer_series_graph(n):
    """Ordinary integer Motzkin recurrence and polynomial powers, no Lagrange formula."""
    m = [0] * n
    m[0] = 1
    for k in range(1, n):
        m[k] = (m[k-1] + sum(m[a] * m[k-2-a] for a in range(k-1))
                if k >= 2 else 1)
    p = [0] * n
    p[0] = 1
    a = [0] * n
    for j in range(1, n+1):
        p = [sum(p[d-t] * m[t] for t in range(d+1)) for d in range(n)]
        for i in range(j+1, n+1):
            if p[i-j-1] & 1:
                a[i-1] |= 1 << (j-1)
                a[j-1] |= 1 << (i-1)
    return a


def main():
    checker = load_module(CHECKER, 'a339592_checker')
    require(checker.adjacency(192) == integer_series_graph(192),
            'Lagrange graph differs from integer Motzkin series at 192')
    known = [int(line.split()[1]) for line in
             (ROOT/'data/b339592.txt').read_text().splitlines() if line.strip()]
    require(len(known) == 144, 'public data range')
    for n in range(1, 13):
        require(checker.independent_count(n) == known[n-1],
                f'known count mismatch at {n}')
    expired = checker.Progress()
    expired.n = 96
    expired.started = time.monotonic() - checker.SEGMENT_SECONDS - 1
    try:
        checker.independent_count(96, expired)
    except checker.Stopped:
        pass
    else:
        raise SystemExit('CHECKER TEST FAIL: expired active term was completed')

    with tempfile.TemporaryDirectory(prefix='a339592-checker-') as td:
        td = Path(td)
        native = td/'native'
        p = run(NATIVE, 'run', '16', native)
        require(p.returncode == 0, 'bounded native run 16 failed: '+p.stderr)
        check = td/'check'
        check.mkdir(mode=0o700)
        args = ('--from', '1', '--through', '16', '--state', check/'check.json')
        p = run('python3', CHECKER, native/'run.tsv', *args)
        require(p.returncode == 0 and '"status": "CHECKED_RANGE"' in p.stdout,
                'independent 1..16 check failed: '+p.stderr)
        state = (check/'check.json').read_bytes()
        p = run('python3', CHECKER, native/'run.tsv', *args)
        require(p.returncode == 0 and (check/'check.json').read_bytes() == state,
                'completed checker resume changed state')
        p = run('python3', CHECKER, native/'run.tsv', '--from', '01',
                '--through', '16', '--state', check/'check.json')
        require(p.returncode != 0, 'noncanonical checker CLI accepted')

        # Recompute the native snapshot checksum around a wrong n=13 row.
        # This tests mathematical disagreement, not a mere integrity failure.
        lines = (native/'run.tsv').read_bytes().splitlines(keepends=True)
        altered = []
        for line in lines[:-1]:
            altered.append(b'13\t105\n' if line.startswith(b'13\t') else line)
        altered.append(b'# sha256=' + hashlib.sha256(b''.join(altered)).hexdigest().encode() + b'\n')
        bad_native = td/'bad_native'
        bad_native.mkdir(mode=0o700)
        (bad_native/'meta.json').write_bytes((native/'meta.json').read_bytes())
        (bad_native/'run.tsv').write_bytes(b''.join(altered))
        bad_check = td/'bad_check'
        bad_check.mkdir(mode=0o700)
        p = run('python3', CHECKER, bad_native/'run.tsv', '--from', '1',
                '--through', '16', '--state', bad_check/'check.json')
        require(p.returncode == 1 and 'count mismatch at n=13' in p.stderr,
                'wrong but checksum-consistent n=13 count accepted: '+p.stderr)
        require((bad_check/'check.json').exists(), 'checker lost prior work')
        p = run('python3', CHECKER, native/'run.tsv', '--from', '1',
                '--through', '16', '--state', bad_check/'check.json')
        require(p.returncode == 1 and 'foreign checker/snapshot/range' in p.stderr,
                'checker accepted state from another snapshot')
    print('CHECKER TEST PASS: 18336 Lagrange/integer-series graph pairs, '
          'known 1..12, independent release 1..16, idempotent resume, '
          'CLI rejection, expired-term stop, checksum-consistent wrong row '
          'and foreign-state rejection')


if __name__ == '__main__':
    main()
