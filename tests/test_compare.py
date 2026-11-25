import pytest

from gold_checker.compare import classify_answer, values_match


@pytest.mark.parametrize('answer,value', [
    ('14.1%', 0.14096),     # compared at the precision written (rounding)
    ('14.0%', 0.14096),     # ...or truncation
    ('1,234', 1234.4),
    ('yes', 'yes'),
])
def test_agrees(answer, value):
    assert classify_answer(answer, value) is None


def test_relative_tolerance_does_not_wave_small_fractions_through():
    # an absolute tolerance would call these equal; a relative one does not
    assert classify_answer('0.004', 0.002) == 'value'


@pytest.mark.parametrize('answer,value,kind', [
    ('12.5%', -0.125, 'sign'),
    ('1.5', 1500.0, 'scale_/1000'),
    ('1500', 1.5, 'scale_x1000'),
    ('160', 150.0, 'value'),
    ('no', 'yes', 'yes/no'),
    ('5', 'yes', 'number_vs_yes/no'),
    ('', 3.0, 'empty_answer'),
    ('$ 5.5 million', 5.5, 'non_numeric_answer'),
    ('10.83%', 10.83, 'format_percent_units'),
    ('8.6', 0.086, 'format_missing_percent'),
])
def test_kinds(answer, value, kind):
    assert classify_answer(answer, value) == kind


def test_values_match():
    assert values_match(0.15556, 0.1555555)
    assert not values_match(0.16, 0.15)
    assert values_match('Yes', 'yes')
