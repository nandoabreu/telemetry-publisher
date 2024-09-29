# -*- coding: utf-8 -*-
"""My Python module

Description
"""
from copy import deepcopy
from subprocess import run

from .config import HOSTNAME_CMD_PATH


class Collector:
    TEMPLATE = {'temperature': None, 'method': None, 'source': None, 'data': {}}

    def __init__(self, logger=None):
        self.logger = logger
        self._last_cpu_data = deepcopy(self.TEMPLATE)
        self._last_gpu_data = deepcopy(self.TEMPLATE)
        self._last_probe = {'epoch': 0}

        self.device = None
        self._log_debug('Request device identification')
        self._identify()

    def _identify(self):
        res = self._run_os_command(f'{HOSTNAME_CMD_PATH} -s')

        if not res['stdout']:
            raise OSError(f'Could not identify this device: {res["err"]}')

        self.device = res['stdout'][0]

    @staticmethod
    def _run_os_command(cmd: str) -> dict:
        data = {'cmd': cmd, 'err': None, 'stdout': []}

        try:
            res = run(cmd, shell=True, capture_output=True, text=True)
            stdout = res.stdout.strip()

            if res.returncode:
                err = 'Uncaught error'
                stderr = res.stderr.strip()

                if stderr:
                    err = [line for line in stderr.split('\n') if 'sh:' in line]

                raise OSError((err[-1] if err else stderr[-1]).strip())

            data['stdout'] = stdout.split('\n')

        except OSError as e:
            data['err'] = str(e)

        finally:
            return data

    def _log_debug(self, msg: str):
        if not self.logger:
            return

        self.logger.debug(msg)
