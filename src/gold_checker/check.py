"""Run the gold-answer checks over a list of items.

For each item:
  1. If it has a program, execute it. A program that will not run is flagged program_failed.
  2. If it also has a stored value (FinQA's exe_ans), the executed result must match it;
     otherwise it is flagged program_vs_stored.
  3. The written answer is compared with the stored value (or, when there is none, with the
     executed result) by compare.classify_answer.

Each item gets one status: ok, format_note, disagree, unreadable or program_failed
(program_vs_stored is reported as its own flag alongside the answer check).
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from .compare import DISAGREE, FORMAT, UNREADABLE, classify_answer, values_match
from .dsl import ProgramError, run_program
from .loaders import Item


@dataclass
class Result:
    item: Item
    status: str
    kind: str | None = None
    executed: object = None
    compared_with: object = None
    program_vs_stored: bool = False
    error: str = ''

    def row(self) -> dict:
        it = self.item
        return {
            'id': it.id, 'status': self.status, 'kind': self.kind or '',
            'question': it.question, 'written_answer': '' if it.answer is None else str(it.answer),
            'gold_value': '' if self.compared_with is None else self.compared_with,
            'executed': '' if self.executed is None else self.executed,
            'program_vs_stored': self.program_vs_stored, 'program': it.program or '',
            'page': it.page, 'error': self.error,
        }


@dataclass
class Report:
    results: list[Result]
    fmt: str = ''
    source: str = ''
    rel_tol: float = 5e-3
    unique: dict = field(default_factory=dict)

    @property
    def flagged(self) -> list[Result]:
        return [r for r in self.results if r.status in ('disagree', 'unreadable', 'program_failed')
                or r.program_vs_stored or r.error]

    def summary(self) -> dict:
        st = Counter(r.status for r in self.results)
        kinds = Counter(r.kind for r in self.results if r.kind)
        s = {
            'source': self.source, 'format': self.fmt, 'relative_tolerance': self.rel_tol,
            'items': len(self.results),
            'agree': st['ok'],
            'format_notes': st['format_note'],
            'disagree': st['disagree'],
            'unreadable': st['unreadable'],
            'program_errors': sum(bool(r.error) for r in self.results),
            'nothing_to_compare': st['program_failed'],
            'program_vs_stored': sum(r.program_vs_stored for r in self.results),
            'disagree_by_kind': {k: kinds[k] for k in DISAGREE if kinds[k]},
            'unreadable_by_kind': {k: kinds[k] for k in UNREADABLE if kinds[k]},
            'format_notes_by_kind': {k: kinds[k] for k in FORMAT if kinds[k]},
        }
        if self.unique:
            s['unique_questions'] = self.unique
        return s


def check_item(item: Item, rel_tol: float = 5e-3, exe_tol: float = 1e-3) -> Result:
    executed = None
    error = ''
    mismatch = False
    if item.program:
        try:
            executed = run_program(item.program, item.table)
        except ProgramError as err:
            error = str(err)
        if item.value is not None and executed is not None:
            mismatch = not values_match(executed, item.value, exe_tol)
    target = item.value if item.value is not None else executed
    if target is None:
        return Result(item, 'program_failed', executed=executed, error=error or 'nothing to compare with')
    kind = classify_answer(item.answer, target, rel_tol)
    if kind is None:
        status = 'ok'
    elif kind in FORMAT:
        status = 'format_note'
    elif kind in UNREADABLE:
        status = 'unreadable'
    else:
        status = 'disagree'
    return Result(item, status, kind, executed, target, mismatch, error)


def _norm(q: str) -> str:
    return re.sub(r'\W+', ' ', q.lower()).strip()


def unique_counts(results: list[Result]) -> dict:
    """Count each (page, question) pair once. A pair is flagged if any copy of it is."""
    groups: dict = {}
    for r in results:
        groups.setdefault((r.item.page, _norm(r.item.question)), []).append(r)
    out = Counter()
    for rs in groups.values():
        out['questions'] += 1
        statuses = {r.status for r in rs}
        if 'disagree' in statuses:
            out['disagree'] += 1
        elif 'unreadable' in statuses:
            out['unreadable'] += 1
    out['flagged'] = out['disagree'] + out['unreadable']
    return dict(questions=out['questions'], flagged=out['flagged'], disagree=out['disagree'],
                unreadable=out['unreadable'])


def run_check(items: list[Item], fmt: str = '', source: str = '', rel_tol: float = 5e-3,
              exe_tol: float = 1e-3, unique: bool | None = None) -> Report:
    """Check every item. ``unique`` adds page-question counts (on by default when items carry pages)."""
    results = [check_item(it, rel_tol, exe_tol) for it in items]
    report = Report(results, fmt, source, rel_tol)
    if unique or (unique is None and any(it.page for it in items)):
        report.unique = unique_counts(results)
    return report
