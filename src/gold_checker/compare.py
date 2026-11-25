"""Compare a written gold answer with the gold value it is supposed to equal.

The written answer is compared at the precision it is written: "14.1%" agrees with 0.14096
because rounding (or truncation) to one decimal gives 14.1. Anything else must agree within a
relative tolerance (default 0.5%). Tolerances are relative, so a small fraction such as 0.004
is not waved through as "close to zero".

When the two do not agree, the disagreement is labelled:

value                 different number
sign                  same size, opposite sign
scale_x1000 ...       off by a power of ten: a factor of 1,000 or 1,000,000 on the number as
                      written or on its percent reading, so a written answer one tenth of the
                      gold value is labelled scale_/1000
yes/no                yes/no answers that disagree
number_vs_yes/no      one is a number, the other yes/no
empty_answer          no written answer
non_numeric_answer    written answer is not a number (a sentence, "1.371:1", ...)

Two percent slips are counted as format notes, not errors, because the number itself is right:
format_percent_units    "10.83%" where the gold value is 10.83 (already in percent)
format_missing_percent  "8.6" where the gold value is 0.086
"""
from __future__ import annotations

from .dsl import parse_number

DISAGREE = ('value', 'sign', 'scale_x1000', 'scale_/1000', 'scale_x1e6', 'scale_/1e6',
            'yes/no', 'number_vs_yes/no')
UNREADABLE = ('empty_answer', 'non_numeric_answer')
FORMAT = ('format_percent_units', 'format_missing_percent')


def values_match(a, b, rel_tol: float = 1e-3) -> bool:
    """True when two gold values agree (used for program result vs stored value)."""
    if isinstance(a, str) or isinstance(b, str):
        return str(a).strip().lower() == str(b).strip().lower()
    return abs(a - b) <= rel_tol * max(1.0, abs(b))


def classify_answer(answer, value, rel_tol: float = 5e-3):
    """Return None when the written answer agrees with value, else a label (see module doc)."""
    ans = '' if answer is None else str(answer).strip()
    if ans == '':
        return 'empty_answer'
    if ans.lower() in ('yes', 'no'):
        return None if str(value).strip().lower() == ans.lower() else 'yes/no'
    try:
        written = parse_number(ans)
    except ValueError:
        return 'non_numeric_answer'
    if isinstance(value, str):
        try:
            value = parse_number(value)
        except ValueError:
            return 'number_vs_yes/no'
    percent = ans.endswith('%')
    decimals = len(ans.rstrip('%').split('.')[1]) if '.' in ans else 0
    precision = 10 ** (-decimals) + 1e-9
    shown = written * 100 if percent else written

    def agrees(target):
        return abs(shown - target) <= precision or abs(shown - target) <= rel_tol * abs(target)

    target = value * 100 if percent else value
    if agrees(target):
        return None
    if percent and agrees(value):
        return 'format_percent_units'
    if not percent and agrees(value * 100):
        return 'format_missing_percent'
    alternatives = [value] if percent else [value * 100]
    if agrees(-target) or any(agrees(-a) for a in alternatives):
        return 'sign'
    for label, factor in (('scale_x1000', 1000), ('scale_/1000', 0.001),
                          ('scale_x1e6', 1e6), ('scale_/1e6', 1e-6)):
        if agrees(target * factor) or any(agrees(a * factor) for a in alternatives):
            return label
    return 'value'
