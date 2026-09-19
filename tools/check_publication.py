"""Reject PRs whose committed static publication does not match their inputs."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from evidence import pinned_release, validate

ROOT = Path(__file__).resolve().parent.parent


def check(root: Path) -> None:
    report = json.loads((root / 'examples/verified.json').read_text(encoding='utf-8'))
    validate(report, root)
    if report['provenance']['release'] != pinned_release(root):
        raise ValueError('committed evidence does not match v3-release.txt')
    # Render from the committed, validated report first. The independent fresh
    # compiler run follows in CI and may have different OS-specific provenance.
    subprocess.run([sys.executable, str(root / 'tools/build_docs.py')], cwd=root, check=True)
    changes = subprocess.check_output(
        ['git', 'status', '--porcelain', '--untracked-files=all', '--', 'site/'],
        cwd=root, encoding='utf-8',
    )
    if changes.strip():
        raise ValueError('committed site is stale; run tools/refresh.py and commit its outputs:\n' + changes)


if __name__ == '__main__':
    try:
        check(ROOT)
    except (ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f'Publication check failed: {exc}', file=sys.stderr)
        raise SystemExit(1)
