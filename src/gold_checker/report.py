"""Write a report as CSV, JSON or Markdown."""
from __future__ import annotations

import csv
import io
import json

from .check import Report

COLUMNS = ['id', 'status', 'kind', 'question', 'written_answer', 'gold_value', 'executed',
           'program_vs_stored', 'program', 'page', 'error']


def to_csv(report: Report, flagged_only: bool = True) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS)
    w.writeheader()
    for r in (report.flagged if flagged_only else report.results):
        w.writerow(r.row())
    return buf.getvalue()


def to_json(report: Report, flagged_only: bool = True) -> str:
    rows = [r.row() for r in (report.flagged if flagged_only else report.results)]
    return json.dumps({'summary': report.summary(), 'items': rows}, indent=1, default=str)


def to_markdown(report: Report, limit: int = 25) -> str:
    s = report.summary()
    lines = [f"# Gold-answer check: {s['source'] or 'uploaded file'}", '',
             f"Format: {s['format']}. Relative tolerance: {s['relative_tolerance']:g}.", '',
             '| Result | Items |', '|---|---|',
             f"| Checked | {s['items']} |",
             f"| Written answer agrees with gold value | {s['agree']} |",
             f"| Percent-format slips (number right) | {s['format_notes']} |",
             f"| **Written answer disagrees with gold value** | **{s['disagree']}** |",
             f"| Written answer empty or not a number | {s['unreadable']} |",
             f"| Program result differs from stored value | {s['program_vs_stored']} |",
             f"| Program would not run | {s['program_errors']} |"]
    if s.get('unique_questions'):
        u = s['unique_questions']
        lines += ['', f"Counting each page-question pair once: {u['flagged']} of {u['questions']} unique "
                      f"questions flagged ({u['disagree']} disagree, {u['unreadable']} empty or not a number)."]
    if s['disagree_by_kind']:
        lines += ['', 'Disagreements by kind: ' + ', '.join(f'{k} {v}' for k, v in s['disagree_by_kind'].items()) + '.']
    flagged = [r for r in report.flagged if r.status == 'disagree'][:limit]
    if flagged:
        lines += ['', f'## First {len(flagged)} disagreements', '',
                  '| id | kind | written | gold value | question |', '|---|---|---|---|---|']
        for r in flagged:
            q = r.item.question.replace('|', '/')
            lines.append(f"| {r.item.id} | {r.kind} | {r.item.answer} | {r.compared_with} | {q} |")
    return '\n'.join(lines) + '\n'
