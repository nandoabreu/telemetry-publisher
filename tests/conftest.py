import pytest
from pathlib import Path
from os import getpid


@pytest.fixture(scope='session')
def work_dir_var() -> Path:
    s = Path('/tmp/pytest')
    s.mkdir(exist_ok=True)
    return s


@pytest.fixture(scope='session')
def app_name_var() -> str:
    return 'pytest-{}'.format(getpid())
