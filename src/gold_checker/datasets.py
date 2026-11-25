"""Download the public demo benchmarks, pinned by SHA-256.

The files are fetched from the benchmarks' own GitHub repositories and cached locally
(``~/.cache/gold-checker`` by default, or ``$GOLD_CHECKER_CACHE``). They are not redistributed
with this package.
"""
from __future__ import annotations

import hashlib
import io
import os
import urllib.request
import zipfile
from pathlib import Path

GH = 'https://raw.githubusercontent.com'
FINQA = f'{GH}/czyssrs/FinQA/main/dataset'
CONVFINQA_ZIP = f'{GH}/czyssrs/ConvFinQA/main/data.zip'
CONVFINQA_SHA = 'd764271fae60d81b62e6d58dfc481807ebc8cfbcd633811241723c4a2101072a'

DATASETS = {
    'finqa-test': dict(label='FinQA test (1,147 items)', url=f'{FINQA}/test.json',
                       sha256='831dbfb2e785dbc227f895ce3f24046433467aec67b09db2bd6ac7692a8a30dc'),
    'finqa-dev': dict(label='FinQA dev (883 items)', url=f'{FINQA}/dev.json',
                      sha256='a847fb7e0d61a3125a1e2909852df6b89f1ee64d2c5ff1bf689e332214deee51'),
    'convfinqa-dev': dict(label='ConvFinQA dev (421 conversations)', url=CONVFINQA_ZIP,
                          sha256=CONVFINQA_SHA, member='data/dev.json'),
    'convfinqa-train': dict(label='ConvFinQA train (3,037 conversations)', url=CONVFINQA_ZIP,
                            sha256=CONVFINQA_SHA, member='data/train.json'),
}


def cache_dir() -> Path:
    d = Path(os.environ.get('GOLD_CHECKER_CACHE', Path.home() / '.cache' / 'gold-checker'))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _download(url: str, sha256: str, dest: Path) -> Path:
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == sha256:
        return dest
    with urllib.request.urlopen(url, timeout=120) as r:
        data = r.read()
    got = hashlib.sha256(data).hexdigest()
    if got != sha256:
        raise RuntimeError(f'{url} changed upstream (sha256 {got}, expected {sha256}); '
                           'results may differ from the published counts')
    dest.write_bytes(data)
    return dest


def fetch(name: str) -> Path:
    """Return a local path to the named demo benchmark, downloading it on first use."""
    if name not in DATASETS:
        raise KeyError(f'unknown dataset {name!r}; choose from {", ".join(DATASETS)}')
    d = DATASETS[name]
    raw = _download(d['url'], d['sha256'], cache_dir() / (Path(d['url']).name if 'member' in d
                                                         else f'{name}.json'))
    if 'member' not in d:
        return raw
    out = cache_dir() / f'{name}.json'
    if not out.exists():
        with zipfile.ZipFile(io.BytesIO(raw.read_bytes())) as z:
            out.write_bytes(z.read(d['member']))
    return out
