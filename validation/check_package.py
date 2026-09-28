#!/usr/bin/env python3
"""Check the public inventory and declared changes from the frozen run."""

from pathlib import Path, PurePosixPath
import re


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'SHA256SUMS'

TRANSFORMS = (
    ('results/run_identity/a339592_v2.c', 'src/a339592.c', (
        (' * Release candidate: external review and campaign authorization are separate.\n'
         ' * Current review source basename: a339592_v2.c.\n',
         ' * Public package source: a339592.c.\n'),
    )),
    ('results/run_identity/Makefile', 'src/Makefile', (
        ('# Single canonical C17 build; private validation is make test.',
         '# C17 public build; bounded validation is make test.'),
        ('SOURCE = a339592_v2.c', 'SOURCE = a339592.c'),
        ('../validation/test_candidate_v2.py', '../validation/test_candidate.py'),
    )),
    ('results/run_identity/test_candidate_v2.py', 'validation/test_candidate.py', (
        ("root/'src/a339592_v2.c'", "root/'src/a339592.c'"),
        ("root/'validation/graph_probe_v2.c'", "root/'validation/graph_probe.c'"),
        ("if [i for i,_ in known_rows] != list(range(1,13)): raise SystemExit('FAIL: known index range')",
         "if [i for i,_ in known_rows] != list(range(1,145)): raise SystemExit('FAIL: public index range')"),
        ('known = [v for _,v in known_rows]', 'known = [v for _,v in known_rows[:12]]'),
    )),
    ('results/run_identity/graph_probe_v2.c', 'validation/graph_probe.c', (
        ('#include "../src/a339592_v2.c"', '#include "../src/a339592.c"'),
    )),
    ('results/run_identity/test_check_counts.py', 'validation/test_check_counts.py', (
        ("require(len(known) == 12, 'known prefix length')",
         "require(len(known) == 144, 'public data range')"),
    )),
)


def check_inventory():
    declared = set()
    for line in MANIFEST.read_text().splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        if match is None:
            raise ValueError('invalid SHA256SUMS record')
        name = match.group(2)
        path = PurePosixPath(name)
        if (path.is_absolute() or name != path.as_posix()
                or any(part in ('.', '..') for part in name.split('/'))
                or name == 'SHA256SUMS' or '.git' in path.parts):
            raise ValueError(f'invalid SHA256SUMS path: {name!r}')
        if name in declared:
            raise ValueError(f'duplicate SHA256SUMS path: {name!r}')
        declared.add(name)

    expected_files = declared | {'SHA256SUMS'}
    expected_dirs = set()
    for name in expected_files:
        parts = PurePosixPath(name).parts
        expected_dirs.update('/'.join(parts[:i]) for i in range(1, len(parts)))

    actual_files = set()
    actual_dirs = set()

    def visit(directory):
        for path in directory.iterdir():
            name = path.relative_to(ROOT).as_posix()
            if directory == ROOT and path.name == '.git':
                if path.is_symlink() or not (path.is_dir() or path.is_file()):
                    raise ValueError('invalid root .git metadata')
                continue
            if path.is_symlink():
                raise ValueError(f'symlink in public package: {name}')
            if path.is_dir():
                actual_dirs.add(name)
                visit(path)
            elif path.is_file():
                actual_files.add(name)
            else:
                raise ValueError(f'unsupported public package entry: {name}')

    visit(ROOT)
    if actual_files != expected_files:
        raise ValueError('public file inventory mismatch: '
                         f'missing={sorted(expected_files - actual_files)}, '
                         f'unexpected={sorted(actual_files - expected_files)}')
    if actual_dirs != expected_dirs:
        raise ValueError('public directory inventory mismatch: '
                         f'missing={sorted(expected_dirs - actual_dirs)}, '
                         f'unexpected={sorted(actual_dirs - expected_dirs)}')


def main():
    check_inventory()
    expected_src = {'a339592.c', 'Makefile'}
    actual_src = {p.name for p in (ROOT / 'src').iterdir()}
    if actual_src != expected_src:
        raise ValueError(f'unexpected public src inventory: {sorted(actual_src)}')
    for old_name, new_name, substitutions in TRANSFORMS:
        old = (ROOT / old_name).read_text()
        new = (ROOT / new_name).read_text()
        for before, after in substitutions:
            if old.count(before) != 1:
                raise ValueError(f'nonunique documented edit in {old_name}')
            old = old.replace(before, after)
        if new != old:
            raise ValueError(f'undeclared content change in {new_name}')
    for path in (ROOT / 'src').iterdir():
        if re.search(r'_v[0-9]+|\bversion(?:ed|ing)?\b|review source|release candidate',
                     path.read_text(), re.IGNORECASE):
            raise ValueError(f'versioning remains in public src: {path.name}')
    print('PUBLIC PACKAGE PASS: declared inventory and exact source transformations')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, UnicodeError) as error:
        raise SystemExit(f'PUBLIC PACKAGE FAIL: {error}') from error
