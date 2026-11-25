"""Executor for the FinQA program language.

A program is a chain of steps such as ``subtract(5829, 5735), divide(#0, 5735)``.
``#N`` refers to the result of step N. Constants are written ``const_100`` (``const_m1``
is -1). Table steps (``table_sum``, ``table_average``, ``table_max``, ``table_min``)
take a row name and reduce the numbers in that row of the item's table.

The same language is used by FinQA and ConvFinQA, and by several benchmarks built on them.
"""
from __future__ import annotations

import math
import re
from typing import Sequence

STEP = re.compile(r'(\w+)\(([^)]*)\)')
CELL_NUMBER = re.compile(r'-?[\d,]*\.?\d+')

ARITHMETIC = {
    'add': lambda a, b: a + b,
    'subtract': lambda a, b: a - b,
    'multiply': lambda a, b: a * b,
    'divide': lambda a, b: a / b,
    'exp': lambda a, b: a ** b,
    'greater': lambda a, b: 'yes' if a > b else 'no',
}
TABLE = {
    'table_sum': sum,
    'table_average': lambda v: sum(v) / len(v),
    'table_max': max,
    'table_min': min,
}


class ProgramError(ValueError):
    """The program could not be executed (unknown step, missing table row, bad number...)."""


def parse_number(text) -> float:
    """Read a number the way FinQA writes them.

    Handles ``$``, thousands commas, spaces, accounting brackets ``(12)`` = -12,
    a trailing ``%`` (divided by 100) and ``const_`` constants.
    Raises ValueError when the text is not a number.
    """
    s = str(text).strip().replace(',', '').replace('$', '').replace(' ', '')
    negative = s.startswith('(') and s.endswith(')')
    s = s.strip('()')
    if s.startswith('const_'):
        s = s[6:]
        return -1.0 if s == 'm1' else float(s)
    percent = s.endswith('%')
    value = float(s.rstrip('%'))
    if not math.isfinite(value):
        raise ValueError(f'not a finite number: {text!r}')
    if percent:
        value /= 100
    return -value if negative else value


def steps(program: str) -> list[tuple[str, list[str]]]:
    """Split a program into (operation, [arguments]) steps."""
    return [(op, [a.strip() for a in args.split(',')]) for op, args in STEP.findall(program)]


def run_program(program: str, table: Sequence[Sequence[str]] | None = None):
    """Execute a program and return the value of its last step (a float, or 'yes'/'no').

    A program with no steps at all (ConvFinQA lookup turns) is read as a plain number.
    """
    program = (program or '').strip()
    if not program:
        raise ProgramError('empty program')
    if '(' not in program:
        try:
            return parse_number(program)
        except ValueError as err:
            raise ProgramError(f'not a program or number: {program!r}') from err
    results: list = []
    for op, args in steps(program):
        if op in TABLE:
            if not table:
                raise ProgramError(f'{op} needs a table and the item has none')
            rows = [r for r in table if isinstance(r, (list, tuple)) and r and str(r[0]).strip() == args[0]]
            if not rows:
                raise ProgramError(f'table row not found: {args[0]!r}')
            values = []
            for cell in rows[0][1:]:
                m = CELL_NUMBER.search(str(cell).replace('$', ''))
                if m:
                    values.append(float(m.group().replace(',', '')))
            if not values:
                raise ProgramError(f'no numbers in table row {args[0]!r}')
            results.append(TABLE[op](values))
            continue
        if op not in ARITHMETIC:
            raise ProgramError(f'unknown operation: {op}')
        if len(args) != 2:
            raise ProgramError(f'{op} takes 2 arguments, got {len(args)}')
        operands = []
        for a in args:
            if a.startswith('#'):
                i = int(a[1:])
                if i >= len(results):
                    raise ProgramError(f'{a} refers to a step that has not run yet')
                operands.append(results[i])
            else:
                try:
                    operands.append(parse_number(a))
                except ValueError as err:
                    raise ProgramError(f'not a number: {a!r}') from err
        try:
            value = ARITHMETIC[op](*operands)
        except ZeroDivisionError as err:
            raise ProgramError('division by zero') from err
        except OverflowError as err:
            raise ProgramError(f'{op} result is too large') from err
        except TypeError as err:
            raise ProgramError(f'{op} got a yes/no value') from err
        if isinstance(value, complex):
            raise ProgramError(f'{op} has no real result')
        results.append(value)
    if not results:
        raise ProgramError(f'no steps found in {program!r}')
    return results[-1]
