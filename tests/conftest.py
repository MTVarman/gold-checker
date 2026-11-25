import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


@pytest.fixture(scope='session')
def dataset():
    """Return a function that fetches a pinned public benchmark, or skips the test when offline."""
    from gold_checker.datasets import fetch

    def get(name):
        try:
            return fetch(name)
        except Exception as err:  # no network, proxy, or upstream file changed
            pytest.skip(f'could not fetch {name}: {err}')
    return get
