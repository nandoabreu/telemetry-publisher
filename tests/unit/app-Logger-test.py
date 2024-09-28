import pytest
from pathlib import Path
from logging import getLevelName
from glob import glob

from app.Logger import Logger


@pytest.fixture(scope='module')
def default_level_var() -> str:
    return 'DEBUG'


@pytest.fixture(scope='module')
def rotation_limit_mb_var() -> float:
    return 0.001


@pytest.fixture(scope='module')
def rotated_files_var() -> int:
    return 3


@pytest.fixture(scope='function')
def singleton_object(app_name_var, work_dir_var, default_level_var, rotation_limit_mb_var, rotated_files_var):
    return Logger(
        name=app_name_var, log_level=default_level_var, logs_dir=work_dir_var,
        rotation_mb=rotation_limit_mb_var, rotated_files=rotated_files_var,
    )


def singleton_object_test(singleton_object):
    assert isinstance(singleton_object, object)


def object_singleton_test(singleton_object):
    instance = Logger()
    assert instance == singleton_object


def method_get_handler_test(singleton_object):
    handler = singleton_object.logger
    assert isinstance(handler, object)  # handler is instance to logging.Logger


@pytest.mark.parametrize('level_to_log', ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
def log_level_call_test(singleton_object, level_to_log, caplog):
    handler = singleton_object.logger
    handler.log(getLevelName(level_to_log), 'pytest [{}] log entry'.format(level_to_log.lower()))
    assert level_to_log in caplog.text and level_to_log.lower() in caplog.text


def log_rotation_test(work_dir_var, app_name_var, singleton_object, rotation_limit_mb_var, rotated_files_var):
    handler = singleton_object.logger

    message = 'pytest log entry'
    entries = int((rotation_limit_mb_var * 1024 * 1024) / (50 / rotated_files_var))  # Log entry generates 50-150 bytes

    for _ in range(entries):  # 10K entries should create 1.6MB
        handler.debug(message)

    path_to_logs = r'{}'.format(Path(work_dir_var) / '{}.*.log'.format(app_name_var))
    assert len(glob(path_to_logs)) == rotated_files_var


@pytest.mark.parametrize(
    'log_level, expected', (
            ('invalid', None),
            ('NOTSET', 'DEBUG'),
            ('DEBUG', 'DEBUG'),
            ('INFO', 'INFO'),
            ('WARNING', 'WARNING'),
            ('ERROR', 'WARNING'),
            ('CRITICAL', 'WARNING'),
    ),
)
def update_log_level_test(singleton_object, default_level_var, log_level, expected):
    singleton_object.level = log_level
    assert singleton_object.level == (expected or default_level_var)
