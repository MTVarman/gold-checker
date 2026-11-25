"""gold-checker: find benchmark items whose gold answer disagrees with its own gold program."""
__version__ = '0.1.0'

from .check import Report, Result, check_item, run_check  # noqa: E402
from .compare import classify_answer, values_match  # noqa: E402
from .dsl import ProgramError, parse_number, run_program  # noqa: E402
from .loaders import Item, load_items  # noqa: E402

__all__ = ['Item', 'ProgramError', 'Report', 'Result', 'check_item', 'classify_answer',
           'load_items', 'parse_number', 'run_check', 'run_program', 'values_match']
