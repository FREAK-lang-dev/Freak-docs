"""Download an official stable compiler distribution and verify its checksum."""
from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

from evidence import file_hash

REPOSITORY = 'FREAK-lang-dev/Freak-lang'


def api(endpoint: str):
    return json.loads(subprocess.check_output(['gh', 'api', f'repos/{REPOSITORY}/{endpoint}'], encoding='utf-8'))


def fetch(release: str, work: Path) -> dict:
    if release != 'latest' and not re.fullmatch(r'v\d+\.\d+\.\d+', release):
        raise ValueError('expected latest or a stable vX.Y.Z release tag')
    info = api('releases/latest' if release == 'latest' else f'releases/tags/{release}')
    tag = info['tag_name']
    if info['draft'] or info['prerelease'] or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('V3 documentation must use a published stable release')
    system = {'Windows': 'windows', 'Linux': 'linux', 'Darwin': 'macos'}[platform.system()]
    arch = 'arm64' if platform.machine().lower() in ('aarch64', 'arm64') else 'x64'
    archive_name = f'freak-{system}-{arch}' + ('.zip' if system == 'windows' else '.tar.gz')
    work.mkdir(parents=True, exist_ok=True)
    download = Path(tempfile.mkdtemp(prefix=f'{tag}-', dir=work)).resolve()
    subprocess.run(['gh', 'release', 'download', tag, '--repo', REPOSITORY,
                    '--pattern', archive_name, '--pattern', 'SHA256SUMS', '--dir', str(download)], check=True)
    expected = {}
    for line in (download / 'SHA256SUMS').read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            expected[parts[1].lstrip('*')] = parts[0]
    archive = download / archive_name
    archive_sha = file_hash(archive)
    if expected.get(archive_name) != archive_sha:
        raise ValueError('release archive checksum mismatch')
    if system == 'windows':
        with zipfile.ZipFile(archive) as package:
            for item in package.infolist():
                (download / item.filename).resolve().relative_to(download)
                if (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('unexpected symlink in release archive')
            package.extractall(download)
    else:
        with tarfile.open(archive) as package:
            package.extractall(download, filter='data')
    binary = download / 'freak/bin' / ('freak.exe' if system == 'windows' else 'freak')
    if system != 'windows':
        binary.chmod(0o755)
    return {
        'binary': str(binary),
        'release': tag,
        'repository': REPOSITORY,
        'compiler_commit': api(f'commits/{tag}')['sha'],
        'archive': archive_name,
        'archive_sha256': archive_sha,
        'compiler_sha256': file_hash(binary),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', default='latest')
    parser.add_argument('--work', type=Path, default=Path('.work/compiler'))
    parser.add_argument('--output', type=Path, default=Path('.work/compiler.json'))
    args = parser.parse_args()
    result = fetch(args.release, args.work)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Verified {result['release']} distribution; metadata: {args.output}")
