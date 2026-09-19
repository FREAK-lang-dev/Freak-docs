"""Fetch a V3 release, recheck every example, and generate publishable docs."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from evidence import file_hash
from fetch_compiler import fetch

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', default='latest')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--fragments', type=Path, default=ROOT / '.work/fragments')
    args = parser.parse_args()
    metadata = fetch(args.release, ROOT / '.work/compiler')
    provenance = ROOT / '.work/compiler.json'
    provenance.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    subprocess.run([sys.executable, str(ROOT / 'tools/verify.py'), '--freak', metadata['binary'],
                    '--provenance', str(provenance), '--jobs', str(args.jobs)], cwd=ROOT, check=True)
    fragments = args.fragments.resolve()
    subprocess.run([sys.executable, str(ROOT / 'tools/build_docs.py'), '--fragments', str(fragments)], cwd=ROOT, check=True)
    subprocess.run(['node', str(ROOT / 'tools/search_smoke.js')], cwd=ROOT, check=True)
    report = ROOT / 'examples/verified.json'
    (fragments / 'verification.json').write_bytes(report.read_bytes())
    # The host site imports only this enumerated, checksummed file set.
    manifest = json.loads((fragments / 'manifest.json').read_text())
    names = [f"{page['slug']}.html" for page in manifest['pages']]
    names += ['manifest.json', 'search-index.json', 'verification.json']
    bundle = {
        'schema_version': 1, 'generation': 'v3', 'channel': 'release',
        'docs_repository': 'FREAK-lang-dev/Freak-docs',
        'docs_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'files': {name: file_hash(fragments / name) for name in sorted(names)},
    }
    (fragments / 'bundle.json').write_text(json.dumps(bundle, indent=2) + '\n', encoding='utf-8')
    print(f'Verified bundle ready: {fragments}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
