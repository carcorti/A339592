#!/usr/bin/env python3
"""Bounded independent graph and count checks; never updates the b-file."""
import hashlib
import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile

root = pathlib.Path(__file__).resolve().parents[1]
exe = pathlib.Path(sys.argv[1]).resolve()
N = 192

def run(*args, **kw):
    return subprocess.run(args, text=True, capture_output=True, timeout=120, **kw)

def graph_reference():
    # Integer, rather than GF(2), Motzkin recurrence from M=1+zM+z^2M^2.
    m = [0] * N
    m[0] = 1
    for k in range(1, N):
        m[k] = m[k-1] + sum(m[a] * m[k-2-a] for a in range(k-1)) if k >= 2 else 1
    p = [0] * N
    p[0] = 1
    rows = []
    adjacency = [0] * N
    for j in range(1, N+1):
        q = [sum(p[d-t] * m[t] for t in range(d+1)) for d in range(N)]
        p = q
        if j < N:
            row = []
            for i in range(j+1, N+1):
                if p[i-j-1] & 1:
                    adjacency[i-1] |= 1 << (j-1)
                    adjacency[j-1] |= 1 << (i-1)
            # Output order is i major below, so we inspect adjacency afterward.
    for i in range(2, N+1):
        rows.append(''.join('1' if adjacency[i-1] >> (j-1) & 1 else '0' for j in range(1, i)))
    return rows, adjacency

def direct(adjacency, n):
    total = 0
    for s in range(1 << n):
        x = s
        good = True
        while x:
            v = (x & -x).bit_length()-1
            x &= x-1
            if x & adjacency[v]:
                good = False
                break
        total += good
    return total

def crafted_state(directory, metadata, target, values):
    directory.mkdir(mode=0o700)
    m = dict(metadata)
    m['target'] = target
    meta_text = json.dumps(m, separators=(',', ':')) + '\n'
    body = '# A339592 schema=1 meta_sha256=' + hashlib.sha256(meta_text.encode()).hexdigest() + '\n'
    body += ''.join(f'{i}\t{v}\n' for i, v in enumerate(values, 1))
    state_text = body + '# sha256=' + hashlib.sha256(body.encode()).hexdigest() + '\n'
    (directory/'meta.json').write_text(meta_text)
    (directory/'run.tsv').write_text(state_text)

with tempfile.TemporaryDirectory(prefix='a339592-test-') as td:
    td = pathlib.Path(td)
    source_sha = hashlib.sha256((root/'src/a339592_v2.c').read_bytes()).hexdigest()
    make_sha = hashlib.sha256((root/'src/Makefile').read_bytes()).hexdigest()
    probe = td/'graph_probe'
    cc = os.environ.get('CC', 'gcc-13')
    cmd = [cc, '-O3', '-std=c17', '-Wall', '-Wextra', '-Wpedantic', '-Wshadow', '-Wconversion', '-Wdouble-promotion', '-Wformat=2', f'-DSOURCE_SHA="{source_sha}"', f'-DMAKE_SHA="{make_sha}"', str(root/'validation/graph_probe_v2.c'), '-o', str(probe)]
    build = run(*cmd)
    if build.returncode: raise SystemExit(build.stderr)
    got = run(str(probe))
    if got.returncode: raise SystemExit(got.stderr)
    rows, adjacency = graph_reference()
    actual = got.stdout.splitlines()
    if actual != rows: raise SystemExit('FAIL: independent integer-series graph mismatch')
    known_rows = [tuple(map(int,line.split())) for line in (root/'data/b339592.txt').read_text().splitlines() if line.strip()]
    if [i for i,_ in known_rows] != list(range(1,13)): raise SystemExit('FAIL: known index range')
    known = [v for _,v in known_rows]
    values = [direct(adjacency, n) for n in range(1, 17)]
    if values[:12] != known: raise SystemExit('FAIL: published prefix mismatch')
    run_dir = td/'bounded_run'
    result = run(str(exe), 'run', '16', str(run_dir))
    if result.returncode: raise SystemExit(result.stderr)
    meta = json.loads((run_dir/'meta.json').read_text())
    if (meta['sequence'], meta['target'], meta['source_sha256'], meta['make_sha256'], meta['binary_sha256']) != ('A339592', 16, source_sha, make_sha, hashlib.sha256(exe.read_bytes()).hexdigest()):
        raise SystemExit('FAIL: run identity mismatch')
    output = (run_dir/'run.tsv').read_text().splitlines()
    indexed = [tuple(map(int, line.split('\t'))) for line in output if line and not line.startswith('#')]
    if indexed != list(enumerate(values, 1)): raise SystemExit('FAIL: release executable rows mismatch')
    for mode in ('verify','resume'):
        result = run(str(exe), mode, str(run_dir))
        if result.returncode: raise SystemExit(f'FAIL: {mode}: {result.stderr}')
    for label, prefix in (('zero', []), ('one', values[:1]), ('multiple', values[:12])):
        state_dir = td/label
        crafted_state(state_dir, meta, 20, prefix)
        checked = run(str(exe), 'verify', str(state_dir))
        if checked.returncode or f'rows={len(prefix)} target=20 state=PARTIAL' not in checked.stdout:
            raise SystemExit(f'FAIL: {label} partial state: {checked.stdout} {checked.stderr}')
        finished = run(str(exe), 'resume', str(state_dir))
        if finished.returncode or 'COMPLETE rows=20 target=20' not in finished.stderr:
            raise SystemExit(f'FAIL: {label} resume: {finished.stderr}')
        if run(str(exe), 'verify', str(state_dir)).returncode:
            raise SystemExit(f'FAIL: {label} completed integrity')
    temp = run_dir/'run.tmp'
    temp.write_text('uncommitted\n')
    checked = run(str(exe), 'verify', str(run_dir))
    if checked.returncode or 'pending_tmp=present' not in checked.stdout or temp.read_text() != 'uncommitted\n':
        raise SystemExit('FAIL: safe temporary state not reported non-mutatively')
    if run(str(exe), 'resume', str(run_dir)).returncode or temp.exists():
        raise SystemExit('FAIL: safe temporary state not discarded by resume')
    if 'pending_tmp=none' not in run(str(exe), 'verify', str(run_dir)).stdout:
        raise SystemExit('FAIL: missing temporary state not reported')
    outside = td/'outside'
    outside.write_text('outside\n')
    for kind in ('directory', 'symlink', 'hardlink'):
        if kind == 'directory': temp.mkdir()
        elif kind == 'symlink': temp.symlink_to(outside)
        else: os.link(outside, temp)
        for mode in ('verify', 'resume'):
            bad = run(str(exe), mode, str(run_dir))
            if bad.returncode == 0 or 'unsafe temporary state' not in bad.stderr:
                raise SystemExit(f'FAIL: {mode} accepted {kind} temporary state')
        if kind == 'directory': temp.rmdir()
        else: temp.unlink()
    if outside.read_text() != 'outside\n':
        raise SystemExit('FAIL: temporary-state test changed outside file')
    if run(str(exe), 'run', '16', str(run_dir)).returncode == 0: raise SystemExit('FAIL: clobber accepted')
    if run(str(exe), 'run', '193', str(td/'reject')).returncode == 0: raise SystemExit('FAIL: target 193 accepted')
    for bad in ('0', '193', '01', '-1', '+1', '1.0', ' 1'):
        if run(str(exe), 'run', bad, str(td/'reject')).returncode == 0:
            raise SystemExit(f'FAIL: invalid target accepted: {bad!r}')
    for args in ((), ('unknown',), ('run',), ('verify',), ('selftest', 'extra')):
        if run(str(exe), *args).returncode == 0: raise SystemExit(f'FAIL: invalid CLI accepted: {args!r}')
    partial_dir = td/'partial_run'
    proc = subprocess.Popen([str(exe), 'run', '112', str(partial_dir)], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    saw_start = False
    while True:
        line = proc.stderr.readline()
        if not line: break
        if line.startswith('START n=96 '):
            proc.send_signal(signal.SIGINT)
            saw_start = True
            break
    _, remaining = proc.communicate(timeout=30)
    if not saw_start or proc.returncode != 3 or 'PARTIAL rows=' not in remaining:
        raise SystemExit(f'FAIL: cooperative partial stop: code={proc.returncode} {remaining}')
    partial_verify = run(str(exe), 'verify', str(partial_dir))
    if partial_verify.returncode or 'state=PARTIAL' not in partial_verify.stdout:
        raise SystemExit('FAIL: partial integrity')
    continued = run(str(exe), 'resume', str(partial_dir))
    if continued.returncode or 'COMPLETE rows=112 target=112' not in continued.stderr:
        raise SystemExit(f'FAIL: resume from partial: {continued.stderr}')
    complete_verify = run(str(exe), 'verify', str(partial_dir))
    if complete_verify.returncode or 'rows=112 target=112 state=COMPLETE' not in complete_verify.stdout:
        raise SystemExit('FAIL: resumed state incomplete')
    (run_dir/'run.tsv').write_text((run_dir/'run.tsv').read_text().replace('13\t104', '13\t105'))
    if run(str(exe), 'verify', str(run_dir)).returncode == 0: raise SystemExit('FAIL: corrupted row accepted')
    print(f'PASS: {sum(map(len,rows))} graph pairs, integer Motzkin series; 16 direct subset counts; release run/verify/resume; zero/one/multiple/complete states; safe/unsafe temp states; partial-stop/resume; clobber/range/parser/tamper rejection')
