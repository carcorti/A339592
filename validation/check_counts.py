#!/usr/bin/env python3
"""A339592 independent trinomial / weighted-odd-subset checker.
Copyright (c) 2026 Carlo Corti. MIT license, as in the canonical C source.
Python >=3.11, Linux/POSIX, standard library only. Completed-term recovery;
an interrupted active term is recomputed. Hashes ensure integrity, not proof.
"""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time

MAX_N = 192
SEGMENT_SECONDS = 3500
POLL_VISITS = 1 << 18
KNOWN = (2, 3, 4, 7, 9, 13, 17, 26, 29, 48, 55, 95)
HEX = re.compile(r'[0-9a-f]{64}')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=True, separators=(',', ':'),
                       allow_nan=False) + '\n').encode('ascii')


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def decode(raw):
    value = json.loads(raw, object_pairs_hook=unique)
    if encode(value) != raw:
        raise ValueError('noncanonical JSON bytes')
    return value


def read_file(path, cap):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise ValueError('input must be a private regular file')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(cap)
        if len(raw) >= cap:
            raise ValueError('input exceeds capacity')
        return raw
    finally:
        os.close(fd)


def load(path):
    if path.name != 'run.tsv':
        raise ValueError('snapshot basename must be run.tsv')
    raw = read_file(path, 16384)
    mr = read_file(path.with_name('meta.json'), 2048)
    meta = decode(mr)
    keys = ['schema', 'sequence', 'target', 'source_sha256', 'make_sha256',
            'binary_sha256', 'segment_seconds']
    if not isinstance(meta, dict) or list(meta) != keys:
        raise ValueError('metadata fields/order')
    if (type(meta['schema']) is not int or meta['schema'] != 1 or
        meta['sequence'] != 'A339592' or type(meta['target']) is not int or
        not 1 <= meta['target'] <= MAX_N or
        type(meta['segment_seconds']) is not int or meta['segment_seconds'] != 3500):
        raise ValueError('metadata domain')
    if any(not isinstance(meta[k], str) or not HEX.fullmatch(meta[k])
           for k in keys[3:6]):
        raise ValueError('metadata digest grammar')
    lines = raw.splitlines(keepends=True)
    header = f'# A339592 schema=1 meta_sha256={digest(mr)}\n'.encode()
    if len(lines) < 2 or lines[0] != header:
        raise ValueError('snapshot header/metadata binding')
    if lines[-1] != f'# sha256={digest(b"".join(lines[:-1]))}\n'.encode():
        raise ValueError('snapshot checksum/trailer')
    rows = []
    for line in lines[1:-1]:
        match = re.fullmatch(rb'([1-9][0-9]{0,2})\t([1-9][0-9]{0,38})\n', line)
        if match is None:
            raise ValueError('noncanonical indexed row')
        n, value = map(int, match.groups())
        if n != len(rows) + 1 or n > meta['target'] or value >= 2**128:
            raise ValueError('snapshot index/count domain')
        if n <= len(KNOWN) and value != KNOWN[n-1]:
            raise ValueError('known prefix mismatch')
        rows.append(value)
    return raw, rows


class Stopped(Exception):
    """No count is available for the current term."""


class Progress:
    def __init__(self):
        self.started = self.heartbeat = time.monotonic()
        self.stopped = False
        self.n = 0

    def signal(self, signum, frame):
        self.stopped = True

    def poll(self):
        now = time.monotonic()
        if self.stopped or now - self.started >= SEGMENT_SECONDS:
            raise Stopped()
        if now - self.heartbeat >= 5:
            print(f'ACTIVE n={self.n} elapsed={now-self.started:.0f} s',
                  file=sys.stderr, flush=True)
            self.heartbeat = now


def motzkin_power_coefficient(j, degree):
    """[z^degree] M(z)^j via w=zM=z(1+w+w^2) and Lagrange inversion.

    j/(degree+j) * [w^degree](1+w+w^2)^(degree+j), for j>=1.
    This uses exact integer arithmetic, not the C GF(2) series recurrence.
    """
    total = degree + j
    trinomial = sum(math.comb(total, k) * math.comb(total-k, degree-2*k)
                    for k in range(degree//2 + 1))
    coefficient, remainder = divmod(j * trinomial, total)
    if remainder:
        raise ValueError('nonintegral Motzkin power coefficient')
    return coefficient


def adjacency(n):
    a = [0] * n
    for i in range(2, n+1):
        for j in range(1, i):
            if motzkin_power_coefficient(j, i-j-1) & 1:
                a[i-1] |= 1 << (j-1)
                a[j-1] |= 1 << (i-1)
    return a


def independent_count(n, progress=None):
    if type(n) is not int or not 1 <= n <= MAX_N:
        raise ValueError('count order outside 1..192')
    a = adjacency(n)
    even = sum(1 << i for i in range(1, n, 2))
    odd = list(range(0, n, 2))
    if any(a[i] & even for i in range(1, n, 2)):
        raise ValueError('even vertices are not independent')
    ticks = 0

    def enumerate_odd(k, chosen, free_even):
        nonlocal ticks
        ticks += 1
        if ticks == POLL_VISITS:
            ticks = 0
            if progress is not None:
                progress.poll()
        if k == len(odd):
            return 1 << free_even.bit_count()
        v = odd[k]
        total = enumerate_odd(k+1, chosen, free_even)
        if not a[v] & chosen:
            total += enumerate_odd(k+1, chosen | (1 << v), free_even & ~a[v])
        return total

    return enumerate_odd(0, 0, even)


def discard_temp(directory):
    try:
        st = os.stat('check.tmp', dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise ValueError('unsafe check.tmp')
    os.unlink('check.tmp', dir_fd=directory)
    os.fsync(directory)


def commit(directory, payload):
    raw = encode({'payload': payload, 'sha256': digest(encode(payload))})
    if len(raw) >= 65536:
        raise ValueError('checker state exceeds capacity')
    fd = os.open('check.tmp', os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                 os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(fd)
    finally:
        os.close(fd)
    os.rename('check.tmp', 'check.json', src_dir_fd=directory, dst_dir_fd=directory)
    os.fsync(directory)


def validate_state(raw, base, expected):
    envelope = decode(raw)
    if not isinstance(envelope, dict) or list(envelope) != ['payload', 'sha256']:
        raise ValueError('checker envelope fields')
    payload = envelope['payload']
    if not isinstance(payload, dict) or list(payload) != list(base):
        raise ValueError('checker payload fields')
    if envelope['sha256'] != digest(encode(payload)):
        raise ValueError('checker checksum mismatch')
    if any(type(payload[k]) is not type(base[k]) or payload[k] != base[k]
           for k in base if k != 'rows'):
        raise ValueError('foreign checker/snapshot/range')
    rows = payload['rows']
    if not isinstance(rows, list) or len(rows) > base['last']-base['first']+1:
        raise ValueError('checker row count')
    for n, row in enumerate(rows, base['first']):
        if (not isinstance(row, dict) or list(row) != ['n', 'count', 'elapsed_ns'] or
            type(row['n']) is not int or row['n'] != n or
            type(row['count']) is not str or row['count'] != str(expected[n-1]) or
            type(row['elapsed_ns']) is not int or not 0 <= row['elapsed_ns'] < 2**63):
            raise ValueError('invalid completed checker row')
    return payload


def positive(text):
    if not re.fullmatch(r'[1-9][0-9]{0,2}', text) or not 1 <= int(text) <= MAX_N:
        raise argparse.ArgumentTypeError('expected canonical integer 1..192')
    return int(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--from', dest='first', type=positive, required=True)
    parser.add_argument('--through', dest='last', type=positive, required=True)
    parser.add_argument('--state', type=Path, required=True)
    if any(sum(arg.split('=', 1)[0] == flag for arg in sys.argv[1:]) > 1 for flag in ('--from', '--through', '--state')):
        parser.error('duplicate option')
    args = parser.parse_args()
    if args.first > args.last or args.state.name != 'check.json':
        parser.error('require first<=last and state basename check.json')
    directory = None
    try:
        raw, expected = load(args.snapshot)
        if len(expected) < args.last:
            raise ValueError('requested range absent from snapshot')
        directory = os.open(args.state.parent, os.O_RDONLY | os.O_DIRECTORY |
                            os.O_NOFOLLOW | os.O_CLOEXEC)
        fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if os.path.samefile(args.state.parent, args.snapshot.parent):
            raise ValueError('checker state must be outside the native run directory')
        if set(os.listdir(directory)) - {'check.json', 'check.tmp'}:
            raise ValueError('unexpected checker directory entry')
        base = {'schema': 1, 'sequence': 'A339592', 'snapshot_sha256': digest(raw),
                'checker_sha256': digest(read_file(Path(__file__), 65536)),
                'first': args.first, 'last': args.last, 'rows': []}
        try:
            state_raw = read_file(args.state, 65536)
        except FileNotFoundError:
            payload = base
            fresh = True
        else:
            payload = validate_state(state_raw, base, expected)
            fresh = False
        discard_temp(directory)
        if fresh:
            commit(directory, payload)
        progress = Progress()
        signal.signal(signal.SIGINT, progress.signal)
        signal.signal(signal.SIGTERM, progress.signal)
        try:
            for n in range(args.first+len(payload['rows']), args.last+1):
                progress.n = n
                progress.poll()
                print(f'START n={n} checked={len(payload["rows"])}', file=sys.stderr, flush=True)
                start = time.monotonic_ns()
                value = independent_count(n, progress)
                if value != expected[n-1]:
                    raise ValueError(f'independent count mismatch at n={n}')
                row = {'n': n, 'count': str(value), 'elapsed_ns': time.monotonic_ns()-start}
                payload['rows'].append(row)
                commit(directory, payload)
                print(json.dumps({'status': 'COMMITTED', **row}), flush=True)
        except Stopped:
            pass
        complete = len(payload['rows']) == args.last-args.first+1
        print(json.dumps({'status': 'CHECKED_RANGE' if complete else 'PARTIAL',
                          'first': args.first, 'last': args.last,
                          'completed': len(payload['rows']),
                          'last_completed': payload['rows'][-1]['n'] if payload['rows'] else None,
                          'snapshot_sha256': digest(raw),
                          'unchecked_rows': len(expected)-len(payload['rows']),
                          'elapsed_seconds': time.monotonic()-progress.started}), flush=True)
        return 0 if complete else 3
    except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
        print(f'CHECK FAILED: {error}', file=sys.stderr)
        return 1
    finally:
        if directory is not None:
            os.close(directory)


if __name__ == '__main__':
    raise SystemExit(main())
