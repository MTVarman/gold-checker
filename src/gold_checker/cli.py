"""Command line: ``gold-checker check FILE`` or ``gold-checker demo finqa-test``."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .check import run_check
from .datasets import DATASETS, fetch
from .loaders import load_items
from .report import to_csv, to_json, to_markdown


def _run(path: Path, args, source: str) -> int:
    items, fmt = load_items(path, fmt=args.format)
    report = run_check(items, fmt=fmt, source=source, rel_tol=args.tolerance)
    if args.out:
        out = Path(args.out)
        writer = {'.json': to_json, '.md': to_markdown}.get(out.suffix.lower(), to_csv)
        out.write_text(writer(report) if writer is to_markdown else writer(report, not args.all))
        print(f'wrote {out}', file=sys.stderr)
    if args.json:
        print(json.dumps(report.summary(), indent=1))
    else:
        print(to_markdown(report, limit=args.show))
    return 1 if args.fail_on_disagree and report.summary()['disagree'] else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog='gold-checker', description=__doc__)
    p.add_argument('--version', action='version', version=__version__)
    sub = p.add_subparsers(dest='cmd', required=True)
    for name in ('check', 'demo'):
        c = sub.add_parser(name, help='check a benchmark file' if name == 'check'
                           else f'download and check a public benchmark ({", ".join(DATASETS)})')
        c.add_argument('target', help='file to check' if name == 'check' else 'dataset name',
                       **({} if name == 'check' else {'choices': list(DATASETS)}))
        c.add_argument('--format', default='auto', choices=['auto', 'finqa', 'convfinqa', 'generic'])
        c.add_argument('--tolerance', type=float, default=5e-3, help='relative tolerance (default 0.005)')
        c.add_argument('--out', help='write the flagged items to .csv, .json or .md')
        c.add_argument('--all', action='store_true', help='with --out, write every item, not only flagged ones')
        c.add_argument('--json', action='store_true', help='print the summary as JSON')
        c.add_argument('--show', type=int, default=25, help='disagreements to print (default 25)')
        c.add_argument('--fail-on-disagree', action='store_true', help='exit 1 if any disagreement (for CI)')
    args = p.parse_args(argv)
    if args.cmd == 'demo':
        return _run(fetch(args.target), args, DATASETS[args.target]['label'])
    return _run(Path(args.target), args, Path(args.target).name)


if __name__ == '__main__':
    sys.exit(main())
