"""Shared, fail-closed checks for publishable V3 documentation evidence."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_hash(root: Path) -> str:
    digest = hashlib.sha256()
    paths = [*root.glob('content/*.md'), *root.glob('examples/*.fk'),
             *root.glob('tools/*.py'), root / 'examples/expectations.json']
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode() + b'\0')
        digest.update(path.read_text(encoding='utf-8').replace('\r\n', '\n').encode() + b'\0')
    return digest.hexdigest()


def expectations(root: Path) -> dict:
    data = json.loads((root / 'examples/expectations.json').read_text(encoding='utf-8'))
    names = {p.stem for p in (root / 'examples').glob('*.fk')}
    if set(data) != names:
        raise ValueError('expectations must cover exactly the current example files')
    for name, expectation in data.items():
        choices = expectation.get('stdout_any_of')
        if set(expectation) != {'stdout_any_of'} or not isinstance(choices, list) or not choices:
            raise ValueError(f'{name}: expected a nonempty stdout_any_of list')
        if not all(isinstance(s, str) for s in choices):
            raise ValueError(f'{name}: expected stdout must be text')
    return data


def validate(data: dict, root: Path) -> None:
    if data.get('schema_version') != 1 or data.get('generation') != 'v3' or data.get('channel') != 'release':
        raise ValueError('V3 publication requires release evidence (schema 1); re-run verification')
    provenance = data.get('provenance', {})
    for key, length in [('compiler_commit', 40), ('compiler_sha256', 64), ('archive_sha256', 64)]:
        if not re.fullmatch(f'[a-f0-9]{{{length}}}', provenance.get(key, '')):
            raise ValueError(f'missing or invalid {key}')
    if not re.fullmatch(r'v\d+\.\d+\.\d+', provenance.get('release', '')):
        raise ValueError('V3 requires a stable release tag')
    if data.get('input_sha256') != input_hash(root):
        raise ValueError('verification is stale: documentation, examples, or tooling changed')
    expected = expectations(root)
    rows = data.get('examples', {})
    if not expected or set(rows) != set(expected) or data.get('total') != len(expected):
        raise ValueError('verification must cover every example; partial runs cannot be published')
    for name, row in rows.items():
        source = (root / 'examples' / f'{name}.fk').read_text(encoding='utf-8')
        if row.get('source') != source or row.get('file') != f'{name}.fk':
            raise ValueError(f'{name}: source does not match the verified program')
        if row.get('compiled') is not True or row.get('ran') is not True or row.get('exit_code') != 0 or row.get('errors'):
            raise ValueError(f'{name}: compilation and successful execution are required')
        if row.get('stdout') not in expected[name]['stdout_any_of']:
            raise ValueError(f'{name}: output does not match the reviewed expectation')
    if data.get('compiled') != len(rows) or data.get('passed') != len(rows):
        raise ValueError('verification counts do not match successful results')
    for path in (root / 'content').glob('*.md'):
        for name in re.findall(r'\{\{example:([\w-]+)(?:\|source)?\}\}', path.read_text(encoding='utf-8')):
            if name not in rows:
                raise ValueError(f'{path.name}: unknown example {name}')
