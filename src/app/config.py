# -*- coding: utf-8 -*-
"""Main configuration file for the project.

*** UPDATE env.toml AND RUN `make` or `make self-test` TO SET .env ***

All env vars values and fallback or default values to be used in the Application.
This module must only be updated in order to:
- Add/remove vars imported from .env
- Update fallback values

Using the Makefile for every command will keep .env updated:
- Values in .env file are not persistent: update env.toml instead
- The .env file may be deployed to Production after build

About prettyconf, dependency responsible for fetching env vars:
- From env vars, Application vars are set
- Precedence is: command line var > .env > fallback value (if set)
"""
from prettyconf import config
from pathlib import Path
from tempfile import gettempdir

LOG_LEVEL: str = config('LOG_LEVEL', default='INFO')

APP_NAME: str = config('APP_NAME', default='App Name')
APP_VERSION: str = config('APP_VERSION', default='1.0.0')
PROJECT_NAME: str = config('PROJECT_NAME', default=APP_NAME).replace(' ', '-').lower()
# PROJECT_DESCRIPTION: str = config('PROJECT_DESCRIPTION', default='{} v{}'.format(APP_NAME, APP_VERSION))

LOGS_DIR: str = config('LOGS_DIR', default='/tmp/{}'.format(PROJECT_NAME))
APP_DIR: str = config('APP_DIR', default='app')
SRC_BASE_PATH = Path(__file__).resolve().parent.as_posix()
LOGS_DIR: Path = Path(config('LOGS_DIR', default=f'/{gettempdir()}/{PROJECT_NAME}')).resolve()
APP_DIR: Path = Path(config('APP_DIR', default='app')).resolve()
SRC_BASE_DIR: Path = Path(__file__).resolve().parent.parent
PROJECT_ROOT_DIR: Path = SRC_BASE_DIR.parent

LOG_ROTATION_MAX_MB: float = config('LOG_ROTATION_MAX_MB', cast=float, default='9')
LOG_MAX_ROTATED_FILES: int = config('LOG_MAX_ROTATED_FILES', cast=int, default='5')

HOSTNAME_CMD_PATH: str = config('HOSTNAME_CMD_PATH', default='/usr/bin/hostname')
KAFKA_BROKERS: list = sorted(d for d in config('KAFKA_BROKERS', default='').split(','))
KAFKA_PARTITIONS: int = config('KAFKA_PARTITIONS', cast=int, default='1')
KAFKA_RETENTION_DAYS: int = config('KAFKA_RETENTION_DAYS', cast=int, default='3')
KAFKA_TOPIC: str = config('KAFKA_TOPIC', default=PROJECT_NAME)
