from pathlib import Path

import pytest

from gold_checker import load_items, run_check
from gold_checker.loaders import detect_format

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'


@pytest.mark.parametrize('name', ['sample.csv', 'sample.jsonl'])
def test_sample_file(name):
    items, fmt = load_items(EXAMPLES / name)
    assert fmt == 'generic' and len(items) == 10
    s = run_check(items).summary()
    assert (s['agree'], s['format_notes'], s['disagree'], s['unreadable'], s['program_errors']) == (3, 1, 4, 1, 1)
    assert s['disagree_by_kind'] == {'value': 1, 'sign': 1, 'scale_/1000': 1, 'yes/no': 1}


def test_value_only_rows():
    data = 'id,answer,exe_ans\na,12%,0.12\nb,7,-7\n'
    items, _ = load_items(data, 'x.csv')
    kinds = [r.kind for r in run_check(items).results]
    assert kinds == [None, 'sign']


def test_rows_with_nothing_to_check_are_refused():
    with pytest.raises(ValueError):
        load_items('id,answer\na,1\n', 'x.csv')


def test_detect_format():
    assert detect_format([{'qa': {'program': 'add(1, 2)'}}]) == 'finqa'
    assert detect_format([{'annotation': {}, 'qa': {}}]) == 'convfinqa'
    assert detect_format([{'answer': '1', 'program': 'add(0, 1)'}]) == 'generic'
