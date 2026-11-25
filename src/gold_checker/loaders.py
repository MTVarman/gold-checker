"""Read benchmark files into a common list of items.

Supported layouts
-----------------
finqa      FinQA JSON: a list of records with ``qa.program``, ``qa.answer``, ``qa.exe_ans``,
           ``table`` and ``filename``.
convfinqa  ConvFinQA JSON: conversations with ``qa`` (or ``qa_0``/``qa_1`` for two-part
           conversations); the conversation-level question of each part becomes one item.
generic    Any JSON list, JSONL or CSV with one row per item. Columns are matched by name:
             id        id, uid, qid                       (row number if missing)
             answer    answer, gold, gold_answer, label   (the written gold answer, required)
             program   program, gold_program, formula     (FinQA-style program, optional)
             value     exe_ans, value, gold_value, expected (stored gold value, optional)
             table     table                              (list of rows, or JSON text of one)
             question  question
             page      page, filename, doc, source        (used to count unique questions)
           At least one of program or value is needed, so there is something to check the
           written answer against.
"""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from pathlib import Path

from .dsl import parse_number


@dataclass
class Item:
    id: str
    answer: object
    program: str | None = None
    value: object = None
    table: list | None = None
    question: str = ''
    page: str = ''
    extra: dict = field(default_factory=dict)


ALIASES = {
    'id': ('id', 'uid', 'qid', 'item_id'),
    'answer': ('answer', 'gold', 'gold_answer', 'label', 'written_answer'),
    'program': ('program', 'gold_program', 'formula'),
    'value': ('exe_ans', 'value', 'gold_value', 'expected', 'executed_answer'),
    'table': ('table',),
    'question': ('question', 'prompt'),
    'page': ('page', 'filename', 'doc', 'source'),
}


def read_records(data: bytes | str | Path, name: str = '') -> list:
    """Parse JSON, JSONL or CSV into a list of records. ``data`` is a path or raw bytes/text."""
    if isinstance(data, Path) or (isinstance(data, str) and len(data) < 4096 and Path(data).is_file()):
        p = Path(data)
        name = name or p.name
        data = p.read_bytes()
    text = data.decode('utf-8-sig') if isinstance(data, bytes) else data
    lower = name.lower()
    if lower.endswith('.csv'):
        return list(csv.DictReader(io.StringIO(text)))
    if lower.endswith('.jsonl'):
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    stripped = text.lstrip()
    if stripped.startswith('[') or stripped.startswith('{'):
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        if isinstance(obj, dict):
            for key in ('data', 'items', 'examples', 'rows'):
                if isinstance(obj.get(key), list):
                    return obj[key]
            return [obj]
        return obj
    return list(csv.DictReader(io.StringIO(text)))


def detect_format(records: list) -> str:
    if not records or not isinstance(records[0], dict):
        raise ValueError('expected a list of records (objects or CSV rows)')
    first = records[0]
    if 'annotation' in first and ('qa' in first or 'qa_0' in first):
        return 'convfinqa'
    if isinstance(first.get('qa'), dict) and 'program' in first['qa']:
        return 'finqa'
    return 'generic'


def _value(v):
    """Stored gold values arrive as numbers, 'yes'/'no' or (from CSV) text."""
    if v is None or isinstance(v, (int, float)):
        return v
    s = str(v).strip()
    if s == '':
        return None
    try:
        return parse_number(s)
    except ValueError:
        return s


def _table(t):
    if t is None or t == '':
        return None
    if isinstance(t, str):
        try:
            t = json.loads(t)
        except json.JSONDecodeError:
            return None
    return t if isinstance(t, list) else None


def from_finqa(records: list) -> list[Item]:
    return [Item(id=str(e['id']), answer=e['qa'].get('answer'), program=e['qa'].get('program'),
                 value=e['qa'].get('exe_ans'), table=e.get('table'), question=e['qa'].get('question', ''),
                 page=e.get('filename', '')) for e in records]


def from_convfinqa(records: list) -> list[Item]:
    items = []
    for e in records:
        parts = [('qa', e['qa'])] if 'qa' in e else [(k, e[k]) for k in ('qa_0', 'qa_1') if k in e]
        for part, qa in parts:
            items.append(Item(id=f"{e['id']}:{part}", answer=qa.get('answer'), program=qa.get('program'),
                              value=qa.get('exe_ans'), table=e.get('table'), question=qa.get('question', ''),
                              page=e.get('filename', ''), extra={'conversation': e['id'], 'part': part}))
    return items


def _pick(row: dict, field_name: str, mapping: dict | None):
    if mapping and mapping.get(field_name):
        return row.get(mapping[field_name])
    lowered = {str(k).strip().lower(): k for k in row}
    for alias in ALIASES[field_name]:
        if alias in lowered:
            return row[lowered[alias]]
    return None


def from_generic(records: list, mapping: dict | None = None) -> list[Item]:
    items = []
    for i, row in enumerate(records):
        if not isinstance(row, dict):
            raise ValueError(f'row {i} is not an object')
        program = _pick(row, 'program', mapping)
        items.append(Item(
            id=str(_pick(row, 'id', mapping) or i),
            answer=_pick(row, 'answer', mapping),
            program=str(program) if program not in (None, '') else None,
            value=_value(_pick(row, 'value', mapping)),
            table=_table(_pick(row, 'table', mapping)),
            question=str(_pick(row, 'question', mapping) or ''),
            page=str(_pick(row, 'page', mapping) or ''),
        ))
    if items and all(it.program is None and it.value is None for it in items):
        raise ValueError('no program or stored-value column found; the written answer has nothing to be '
                         'checked against (expected a column named program or exe_ans/value)')
    return items


def load_items(data: bytes | str | Path, name: str = '', fmt: str = 'auto',
               mapping: dict | None = None) -> tuple[list[Item], str]:
    """Read a benchmark file and return (items, format used)."""
    records = read_records(data, name)
    fmt = detect_format(records) if fmt == 'auto' else fmt
    if fmt == 'finqa':
        return from_finqa(records), fmt
    if fmt == 'convfinqa':
        return from_convfinqa(records), fmt
    if fmt == 'generic':
        return from_generic(records, mapping), fmt
    raise ValueError(f'unknown format {fmt!r}')
