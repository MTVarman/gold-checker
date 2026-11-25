import pytest

from gold_checker.dsl import ProgramError, parse_number, run_program


@pytest.mark.parametrize('text,value', [
    ('1,234', 1234.0), ('$ 5.5', 5.5), ('(12)', -12.0), ('12.5%', 0.125),
    ('const_100', 100.0), ('const_m1', -1.0), ('-3', -3.0),
])
def test_parse_number(text, value):
    assert parse_number(text) == pytest.approx(value)


def test_chained_steps():
    assert run_program('subtract(5829, 5735), divide(#0, 5735)') == pytest.approx(94 / 5735)


def test_constants_and_percent_operands():
    assert run_program('multiply(20%, const_100)') == pytest.approx(20)


def test_greater_gives_yes_no():
    assert run_program('greater(5, 3)') == 'yes'
    assert run_program('greater(3, 5)') == 'no'


def test_table_steps():
    table = [['', '2019', '2020'], ['revenue', '$ 1,200', '$ 1,350'], ['costs', '( 300 )', '( 420 )']]
    assert run_program('table_sum(revenue, none)', table) == 2550
    assert run_program('table_average(revenue, none)', table) == 1275
    assert run_program('table_max(revenue, none)', table) == 1350


def test_plain_number_is_a_lookup():
    assert run_program('206588') == 206588


@pytest.mark.parametrize('program', ['divide(1, 0)', 'frobnicate(1, 2)', 'add(#3, 1)', 'table_sum(x, none)', '',
                                     'exp(10, 1000)', 'exp(-8, 0.5)'])
def test_bad_programs_raise(program):
    with pytest.raises(ProgramError):
        run_program(program, [['y', '1']])


def test_table_that_is_not_rows_raises():
    with pytest.raises(ProgramError):
        run_program('table_sum(revenue, none)', [{'revenue': 1200}])


@pytest.mark.parametrize('text', ['nan', 'inf', '-inf'])
def test_parse_number_rejects_non_finite(text):
    with pytest.raises(ValueError):
        parse_number(text)
