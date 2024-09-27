import logging
from json import dumps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from tempfile import gettempdir
from time import gmtime, strftime

from .config import SRC_BASE_PATH


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):  # noqa: D102
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class LogHook(logging.Formatter):
    @staticmethod
    def path2relative(s: str) -> str:  # noqa: D102
        return s.replace(f'{SRC_BASE_PATH}/', '').replace('.py:', ':')

    def format(self, record: logging.LogRecord) -> str:  # noqa: D102
        update = logging.Formatter.format(self, record)
        update = self.path2relative(update)
        return update


class Logger(metaclass=Singleton):  # dead: disable
    def __init__(
            self,
            name: str = __name__, log_level: str = 'INFO', logs_dir: str = gettempdir(),
            rotation_mb: float = 9, rotated_files: int = 9,
            cid: str = None,
    ):
        name = name.replace(' ', '-').lower()

        Path(logs_dir).mkdir(parents=True, exist_ok=True)
        log_filepath = '{}/{}.log'.format(logs_dir, name)
        rotation_bytes = int(1024 * 1024 * rotation_mb)

        _logger = logging.getLogger(name)
        _logger.setLevel(log_level)

        # Log all levels in file (from log_level)
        fh = RotatingFileHandler(log_filepath, maxBytes=rotation_bytes, backupCount=rotated_files)
        fh.setLevel(log_level)

        log_line = {
            'cid': cid or '',
            'ts': '%(asctime)s',
            'log': '%(levelname)s',
            'msg': '%(message)s',
        }
        if log_level == 'DEBUG':
            log_line['ref'] = '%(pathname)s:%(lineno)d'

        formatter = logging.Formatter(dumps(log_line))
        formatter.converter = gmtime
        fh.setFormatter(formatter)
        fh.namer = self.namer
        _logger.addHandler(fh)

        # Dump errors and higher levels to screen
        sh = logging.StreamHandler()
        sh.setLevel('INFO' if log_level == 'DEBUG' else 'WARNING')
        formatter = logging.Formatter('{} [%(levelname)s] %(message)s'.format(name))
        sh.setFormatter(formatter)
        _logger.addHandler(sh)

        for handler in _logger.handlers:
            # noinspection PyProtectedMember
            handler.setFormatter(LogHook(handler.formatter._fmt))

        _logger.debug(
            'stdout logs are in timezone {} (unaware, set by OS), from {}'.format(
                strftime('%Z'), logging.getLevelName(sh.level),
            ),
        )

        _logger.info(
            'stored logs are in UTC (unaware), from {}, rotating on {} bytes of log from {}'.format(
                logging.getLevelName(fh.level), rotation_bytes, log_filepath,
            ),
        )

        self._logger = None
        self.logger = _logger

    @property
    def logger(self):
        """The actual logging property to be used all around."""
        return self._logger

    @logger.setter
    def logger(self, _logger: logging):
        self._logger = _logger

    @staticmethod
    def namer(name):  # noqa: D102, D205
        """Set log (and rotated log files) to have *.N.log as suffix, instead of *.log.N.
        i.e.: project-name.log.1 (logging standard) becomes project-name.1.log
        """
        return name.replace('.log', '') + '.log'
