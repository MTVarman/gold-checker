"""Reproduce the published FinQA and ConvFinQA counts (Varman 2026, doi:10.5281/zenodo.24520462).

These tests download the public files from the benchmarks' GitHub repositories, pinned by
SHA-256, and are skipped when offline.
"""
from pathlib import Path

import pytest

from gold_checker import load_items, run_check

pytestmark = pytest.mark.data
EXPECTED = Path(__file__).resolve().parent / 'expected'


def check(path):
    items, fmt = load_items(path)
    return run_check(items, fmt=fmt)


def test_finqa_test_78(dataset):
    report = check(dataset('finqa-test'))
    s = report.summary()
    assert s['items'] == 1147
    assert s['disagree'] == 78
    assert s['disagree_by_kind'] == {'value': 58, 'sign': 11, 'scale_x1000': 2, 'scale_/1000': 4,
                                     'scale_x1e6': 1, 'yes/no': 2}
    assert s['unreadable'] == 24
    assert s['unreadable_by_kind'] == {'empty_answer': 14, 'non_numeric_answer': 10}
    assert s['format_notes'] == 28
    assert s['program_vs_stored'] == 4
    assert s['program_errors'] == 0


def test_finqa_test_same_78_items_as_published(dataset):
    report = check(dataset('finqa-test'))
    ids = sorted(r.item.id for r in report.results if r.status == 'disagree')
    assert ids == (EXPECTED / 'finqa_test_answer_vs_exe_ids.txt').read_text().split()


def test_finqa_dev(dataset):
    s = check(dataset('finqa-dev')).summary()
    assert (s['items'], s['disagree'], s['unreadable'], s['program_vs_stored']) == (883, 56, 22, 4)


def test_convfinqa_dev_27_of_458(dataset):
    s = check(dataset('convfinqa-dev')).summary()
    assert s['items'] == 542
    assert s['unique_questions'] == {'questions': 458, 'flagged': 27, 'disagree': 18, 'unreadable': 9}


def test_convfinqa_train_257_of_3321(dataset):
    s = check(dataset('convfinqa-train')).summary()
    assert s['unique_questions']['questions'] == 3321
    assert s['unique_questions']['flagged'] == 257


def test_tolerance_is_a_setting(dataset):
    loose = run_check(load_items(dataset('finqa-test'))[0], rel_tol=0.05).summary()
    assert loose['disagree'] < 78
