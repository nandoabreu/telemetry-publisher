"""My Python module

Description
"""
from copy import deepcopy
from subprocess import run

from .config import HOSTNAME_CMD_PATH


class Collector:
    TEMPLATE = {'temperature': None, 'method': None, 'source': None}

    def __init__(self, logger=None):
        self.logger = logger
        self._last_cpu_data = deepcopy(self.TEMPLATE)
        self._last_gpu_data = deepcopy(self.TEMPLATE)
        self._last_probe = {"epoch": 0}

        self.device = None
        self._log_debug('Request device identification')
        self._identify()

    def _identify(self):
        self._log_debug('Start device identification')
        cmd = f'{HOSTNAME_CMD_PATH} -s'

        try:
            res = self._run_os_command(cmd)
            self._log_debug(f"Command returned: {res}")

            if not res['stdout']:
                raise OSError("no hostname data")

        except OSError as e:
            if 'not found' in str(e):
                e = 'update the variable HOSTNAME_CMD_PATH in the env.toml file and then check .env'
            raise OSError(f'Could not identify this device: {e}')

        self.device = res['stdout'][0]

    @staticmethod
    def _run_os_command(cmd: str) -> dict:
        data = {'cmd': cmd, 'stdout': []}

        res = run(cmd, shell=True, capture_output=True, text=True)
        stdout = res.stdout.strip()

        if res.returncode:
            err = 'uncaught error'

            stderr = res.stderr.strip()
            if stderr:
                err = [line for line in stderr.split("\n") if "sh:" in line]

            err = (err[-1] if err else stderr[-1]).strip()
            if 'not found' in err:
                err += '. Declare paths in env.toml and check the .env file.'

            raise OSError(err)

        data['stdout'] = [line for line in stdout.split("\n") if line]

        return data

    def _log_debug(self, msg: str):
        if not self.logger:
            return

        self.logger.debug(msg)
