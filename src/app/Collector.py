"""My Python module

Description
"""
from copy import deepcopy
from subprocess import run
from re import sub
from time import time

from .config import HOSTNAME_CMD_PATH, GREP_CMD_PATH, SENSORS_CMD_PATH


class Collector:
    TEMPLATE = {'temperature': None, 'method': None, 'source': None}

    def __init__(self, logger=None):
        self.logger = logger
        self._last_cpu_data = deepcopy(self.TEMPLATE)
        self._last_gpu_data = deepcopy(self.TEMPLATE)
        self._last_probe = {"epoch": 0}

        self.device = None
        self._identify()

    def _probe_lm_sensors(self):
        """Update self._last_cpu_data property with data from the sensors command"""
        self._log_debug('Start sensors probe')
        cmd = '{sensors} | {grep} -e Package -e Tctl -e CPU -e coretemp -e GPU -e edge | {grep} °C'.format(
            sensors=SENSORS_CMD_PATH, grep=GREP_CMD_PATH,
        )

        try:
            res = self._run_os_command(cmd)
            self._log_debug(f"Command returned: {res}")

            if not res['stdout']:
                raise OSError("no sensors data")

        except OSError as e:
            if 'not found' in str(e):
                e = 'update variables SENSORS_CMD_PATH and GREP_CMD_PATH in the env.toml file and then check .env'
            raise OSError(f'Could not probe sensors: install lm_sensors, if possible\n{e}')

        data = {}
        for line in res['stdout']:
            chunks = line.split(":")
            key = chunks[0].strip()
            val = sub(r'[^0-9.+-]', '', chunks[1].split()[0])
            data[key] = float(val)
        self._log_debug(f"Parsed data: {data}")

        self._last_cpu_data["temperature"] = \
            data.get("Package id 0") or data.get("Tctl") or data.get("CPU") or data.get("coretemp")

        self._last_gpu_data["temperature"] = \
            data.get("GPU") or data.get("GPU temp") or data.get("edge")

        if self._last_cpu_data["temperature"]:
            self._last_cpu_data["source"] = 'sensors'
            self._last_cpu_data["method"] = 'raw elected value'

        if self._last_gpu_data["temperature"]:
            self._last_gpu_data["source"] = 'sensors'
            self._last_gpu_data["method"] = 'raw elected value'

        self._last_probe.update({
            'epoch': int(time()),
            'cpu': self._last_cpu_data if self._last_cpu_data["temperature"] else {},
            'gpu': self._last_gpu_data if self._last_gpu_data["temperature"] else {},
            'data': {'sensors': data},
        })

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
