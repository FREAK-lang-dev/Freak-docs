"""Shared, fail-closed checks for publishable documentation evidence.

Three kinds of evidence are checked here:

* V3 release examples (``examples/``): compiled, executed, output compared.
* V3 release diagnostics (``diagnostics/v3/``): programs the compiler must
  reject, with the reviewed text its diagnostic has to contain.
* V4 development-snapshot examples (``examples-v4/``): a separate lane with its
  own report, pinned to one compiler commit. V3 evidence never certifies V4.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

EXPECTATION_KEYS = {'stdout_any_of', 'stdin', 'args', 'exit_code'}
DIAGNOSTIC_KEYS = {'contains', 'flags'}
V4_RUN_KEYS = {'stdout_any_of', 'exit_code'}
V4_REJECT_KEYS = {'rejected_with'}
EXAMPLE_REF = re.compile(r'\{\{example:([\w-]+)(?:\|source)?\}\}')
DIAGNOSTIC_REF = re.compile(r'\{\{diagnostic:([\w-]+)\}\}')
V4_REF = re.compile(r'\{\{v4:([\w-]+)\}\}')


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned_release(root: Path) -> str:
    release = (root / 'v3-release.txt').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'v\d+\.\d+\.\d+', release):
        raise ValueError('v3-release.txt must pin a stable vX.Y.Z release')
    return release


def pinned_snapshot(root: Path) -> str:
    """The one Freak-lang commit every V4 claim in the docs was checked against."""
    commit = (root / 'v4-snapshot.txt').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'[a-f0-9]{40}', commit):
        raise ValueError('v4-snapshot.txt must pin a full 40-character commit')
    return commit


def _digest(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode() + b'\0')
        digest.update(path.read_text(encoding='utf-8').replace('\r\n', '\n').encode() + b'\0')
    return digest.hexdigest()


def input_hash(root: Path) -> str:
    paths = [*root.glob('content/*.md'), *root.glob('examples/*.fk'),
             *root.glob('tools/*.py'), root / 'examples/expectations.json', root / 'v3-release.txt']
    # Rejected programs are V3 release evidence too; a repository without the
    # directory hashes exactly as it did before the lane existed.
    paths += [*root.glob('diagnostics/v3/*.fk')]
    extra = root / 'diagnostics/v3/expectations.json'
    if extra.exists():
        paths.append(extra)
    return _digest(root, paths)


def v4_input_hash(root: Path) -> str:
    paths = [*root.glob('examples-v4/*.fk'), root / 'examples-v4/expectations.json',
             root / 'v4-snapshot.txt', root / 'tools/verify_v4.py']
    return _digest(root, paths)


def _text_list(value, name: str, field: str, *, allow_empty: bool = False) -> None:
    if not isinstance(value, list) or (not value and not allow_empty) \
            or not all(isinstance(item, str) for item in value):
        raise ValueError(f'{name}: {field} must be a list of text')


def expectations(root: Path) -> dict:
    data = json.loads((root / 'examples/expectations.json').read_text(encoding='utf-8'))
    names = {p.stem for p in (root / 'examples').glob('*.fk')}
    if set(data) != names:
        raise ValueError('expectations must cover exactly the current example files')
    for name, expectation in data.items():
        choices = expectation.get('stdout_any_of')
        if not set(expectation) <= EXPECTATION_KEYS or not isinstance(choices, list) or not choices:
            raise ValueError(f'{name}: expected a nonempty stdout_any_of list')
        if not all(isinstance(s, str) for s in choices):
            raise ValueError(f'{name}: expected stdout must be text')
        if 'stdin' in expectation and not isinstance(expectation['stdin'], str):
            raise ValueError(f'{name}: stdin must be text')
        if 'args' in expectation:
            _text_list(expectation['args'], name, 'args', allow_empty=True)
        code = expectation.get('exit_code', 0)
        if isinstance(code, bool) or not isinstance(code, int) or not 0 <= code <= 255:
            raise ValueError(f'{name}: exit_code must be an integer from 0 to 255')
    return data


def diagnostic_expectations(root: Path) -> dict:
    """Reviewed diagnostics for programs the V3 release must reject."""
    folder = root / 'diagnostics/v3'
    names = {p.stem for p in folder.glob('*.fk')}
    listing = folder / 'expectations.json'
    if not listing.exists():
        if names:
            raise ValueError('rejected programs need diagnostics/v3/expectations.json')
        return {}
    data = json.loads(listing.read_text(encoding='utf-8'))
    if set(data) != names:
        raise ValueError('diagnostic expectations must cover exactly the rejected programs')
    for name, expectation in data.items():
        if not set(expectation) <= DIAGNOSTIC_KEYS:
            raise ValueError(f'{name}: unknown diagnostic expectation field')
        _text_list(expectation.get('contains'), name, 'contains')
        if any(not part.strip() for part in expectation['contains']):
            raise ValueError(f'{name}: an empty diagnostic fragment proves nothing')
        if 'flags' in expectation:
            _text_list(expectation['flags'], name, 'flags', allow_empty=True)
    return data


def v4_expectations(root: Path) -> dict:
    folder = root / 'examples-v4'
    data = json.loads((folder / 'expectations.json').read_text(encoding='utf-8'))
    names = {p.stem for p in folder.glob('*.fk')}
    if set(data) != names:
        raise ValueError('V4 expectations must cover exactly the current V4 example files')
    for name, expectation in data.items():
        keys = set(expectation)
        if keys and keys <= V4_REJECT_KEYS:
            fragment = expectation['rejected_with']
            if not isinstance(fragment, str) or not fragment.strip():
                raise ValueError(f'{name}: rejected_with must name the expected diagnostic')
        elif 'stdout_any_of' in keys and keys <= V4_RUN_KEYS:
            _text_list(expectation['stdout_any_of'], name, 'stdout_any_of')
            code = expectation.get('exit_code', 0)
            if isinstance(code, bool) or not isinstance(code, int) or not 0 <= code <= 255:
                raise ValueError(f'{name}: exit_code must be an integer from 0 to 255')
        else:
            raise ValueError(f'{name}: expected stdout_any_of (optionally exit_code) or rejected_with')
    return data


def _content_refs(root: Path, pattern: re.Pattern) -> list[tuple[str, str]]:
    found = []
    for path in sorted((root / 'content').glob('*.md')):
        for name in pattern.findall(path.read_text(encoding='utf-8')):
            found.append((path.name, name))
    return found


def validate(data: dict, root: Path) -> None:
    if data.get('schema_version') != 1 or data.get('generation') != 'v3' or data.get('channel') != 'release':
        raise ValueError('V3 publication requires release evidence (schema 1); re-run verification')
    for field in ['compiler', 'generated_utc']:
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f'missing or invalid {field}')
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
        wanted_exit = expected[name].get('exit_code', 0)
        if row.get('compiled') is not True or row.get('ran') is not True \
                or row.get('exit_code') != wanted_exit or row.get('errors'):
            raise ValueError(f'{name}: compilation and successful execution are required')
        if row.get('stdout') not in expected[name]['stdout_any_of']:
            raise ValueError(f'{name}: output does not match the reviewed expectation')
        if row.get('stdin', '') != expected[name].get('stdin', ''):
            raise ValueError(f'{name}: the program was not run with the reviewed input')
    if data.get('compiled') != len(rows) or data.get('passed') != len(rows):
        raise ValueError('verification counts do not match successful results')
    for page, name in _content_refs(root, EXAMPLE_REF):
        if name not in rows:
            raise ValueError(f'{page}: unknown example {name}')

    wanted = diagnostic_expectations(root)
    rejected = data.get('diagnostics', {})
    if set(rejected) != set(wanted):
        raise ValueError('verification must cover every rejected program')
    for name, row in rejected.items():
        source = (root / 'diagnostics/v3' / f'{name}.fk').read_text(encoding='utf-8')
        if row.get('source') != source or row.get('file') != f'{name}.fk':
            raise ValueError(f'{name}: source does not match the verified rejected program')
        message = row.get('message')
        if row.get('rejected') is not True or row.get('passed') is not True or not isinstance(message, str):
            raise ValueError(f'{name}: the compiler must reject this program with a diagnostic')
        if any(part not in message for part in wanted[name]['contains']):
            raise ValueError(f'{name}: diagnostic does not contain the reviewed text')
    for page, name in _content_refs(root, DIAGNOSTIC_REF):
        if name not in rejected:
            raise ValueError(f'{page}: unknown diagnostic {name}')


def validate_v4(data: dict, root: Path) -> None:
    """V4 claims are development evidence, pinned to exactly one commit."""
    if data.get('schema_version') != 1 or data.get('generation') != 'v4' or data.get('channel') != 'development':
        raise ValueError('V4 notes require development-snapshot evidence (schema 1)')
    snapshot = data.get('snapshot', {})
    if snapshot.get('commit') != pinned_snapshot(root):
        raise ValueError('V4 evidence does not match v4-snapshot.txt')
    for field in ['commit_date', 'repository']:
        if not isinstance(snapshot.get(field), str) or not snapshot[field].strip():
            raise ValueError(f'missing or invalid snapshot {field}')
    if not isinstance(data.get('generated_utc'), str) or not data['generated_utc'].strip():
        raise ValueError('missing or invalid generated_utc')
    if data.get('input_sha256') != v4_input_hash(root):
        raise ValueError('V4 verification is stale: V4 examples, the snapshot pin, or its tooling changed')
    expected = v4_expectations(root)
    rows = data.get('examples', {})
    if set(rows) != set(expected) or data.get('total') != len(expected):
        raise ValueError('V4 verification must cover every V4 example')
    for name, row in rows.items():
        source = (root / 'examples-v4' / f'{name}.fk').read_text(encoding='utf-8')
        if row.get('source') != source or row.get('file') != f'{name}.fk' or row.get('passed') is not True:
            raise ValueError(f'{name}: V4 example is not verified for the current source')
        want = expected[name]
        if 'rejected_with' in want:
            if row.get('built') is not False or want['rejected_with'] not in row.get('diagnostic', ''):
                raise ValueError(f'{name}: V4 must reject this program with the reviewed diagnostic')
        else:
            if row.get('built') is not True or row.get('exit_code') != want.get('exit_code', 0) \
                    or row.get('stdout') not in want['stdout_any_of']:
                raise ValueError(f'{name}: V4 output does not match the reviewed expectation')
    if data.get('passed') != len(rows):
        raise ValueError('V4 verification counts do not match successful results')
    for page, name in _content_refs(root, V4_REF):
        if name not in rows:
            raise ValueError(f'{page}: unknown V4 example {name}')


def uses_v4(root: Path) -> bool:
    """True when the repository carries a V4 lane or a page refers to one."""
    return (root / 'examples-v4').is_dir() or bool(_content_refs(root, V4_REF))
