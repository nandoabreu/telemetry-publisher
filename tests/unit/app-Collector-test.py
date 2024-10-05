import pytest
from pathlib import Path
from logging import getLevelName
from glob import glob

from app.Collector import Collector


# @pytest.fixture(scope='module')
# def default_level_var() -> str:
#     return 'DEBUG'


# sensors_output1 = [
#   'Tctl:         +43.1°C  ',
#   'CPU:          +43.0°C  ',
#   'GPU:           +0.0°C  ',
#   'edge:         +41.0°C  ',
# ]
# sensors_output2 = [
#   'Package id 0:  +58.0°C  (high = +100.0°C, crit = +100.0°C)'
# ]


@pytest.fixture(scope='function')
def class_object():
    return Collector()


def class_object_test(class_object):
    assert isinstance(class_object, object)


def method_log_test(class_object, caplog):
    class_object._log_debug("pytest log entry")
    assert not caplog.text
