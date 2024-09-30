"""My Python module

Description
"""
from copy import deepcopy
# from inspect import currentframe
# from re import sub
from subprocess import run
from re import sub
# from time import time

from .config import (
    HOSTNAME_CMD_PATH,
    GREP_CMD_PATH,
    CAT_CMD_PATH,
    SENSORS_CMD_PATH,
    NVIDIA_CMD_PATH,
)


class Collector:
    TEMPLATE = {'temperature': None, 'method': None, 'source': None}

    def __init__(self, logger=None):
        self.logger = logger
        self._last_cpu_data = deepcopy(self.TEMPLATE)
        self._last_gpu_data = deepcopy(self.TEMPLATE)
        self._last_probe = {'epoch': 0}

        self.device = None
        self._identify()

    def _probe_lm_sensors(self) -> dict:
        """Update self._last_cpu_data property with data from the sensors command"""
        self._log_debug('Start sensors probe')

        filters = ('Package', 'Tctl', 'CPU', 'GPU', 'edge')
        cmd = '{s} | {g} -e {f} | {g} °C'.format(
            s=SENSORS_CMD_PATH, f=' -e '.join(filters), g=GREP_CMD_PATH,
        )

        try:
            res = self._run_os_command(cmd)
            self._log_debug(f'Command returned: {res}')  # expected: ['Package id 0:      +70.0°C ... ']

            if not res['stdout']:
                raise OSError('no sensors data')

        except OSError as e:
            if 'not found' in str(e):
                e = 'update variables SENSORS_CMD_PATH and GREP_CMD_PATH in the env.toml file and then check .env'
            raise OSError(f'Could not probe sensors: install lm_sensors, if possible\n{e}')

        data = {}
        for line in res['stdout']:
            chunks = line.split(':')
            key = chunks[0].strip()
            val = sub(r'[^0-9.+-]', '', chunks[1].split()[0])
            data[key] = float(val)
        self._log_debug(f'Parsed data: {data}')

        res = {}
        fetch = {
            'cpu': ('Package id 0', 'Tctl', 'CPU', 'coretemp'),
            'gpu': ('GPU', 'GPU temp', 'edge'),
        }

        for unit, keys in fetch.items():
            for key in keys:
                if key in data:
                    if unit not in res:
                        res[unit] = {}

                    res[unit][key] = data[key]

        return res

    def _fetch_thermal_zones_files(self) -> dict:
        """Update self._last_cpu_data property with data from CPU thermal zones (cores)

        Some hardware handle temperature in files that can be catted.
        """
        self._log_debug('Start thermal zone fetch')

        cmd = f'{CAT_CMD_PATH} /sys/class/thermal/thermal_zone*/temp'

        try:
            res = self._run_os_command(cmd)
            self._log_debug(f'Command returned: {res}')  # expected: ['20000', '47050', '61050',]

            if not res['stdout']:
                raise OSError('no thermal zone data')

        except OSError as e:
            if 'not found' in str(e):
                e = 'update variable CAT_CMD_PATH in the env.toml file and then check .env'
            raise OSError(f'Could not fetch thermal zones: hardware may not report thermal zones\n{e}')

        data = [round(float(t) / 1000, 3) for t in res['stdout']]
        self._log_debug(f'Fetched data: {data}')

        res = {'cpu': data} if data else {}
        return res

    def _probe_nvidia_gpu(self) -> dict:
        """Probe GPU temperatures from the nvidia modules

        Returns:
            (float): a single value returned from the nvidia-smi call
        """
        self._log_debug('Start nvidia probe')

        cmd = f'{NVIDIA_CMD_PATH} --query-gpu=temperature.gpu --format=csv'

        try:
            res = self._run_os_command(cmd)
            self._log_debug(f'Command returned: {res}')  # expected: ['temperature.gpu', '49']

            if not res['stdout']:
                raise OSError('no nvidia data')

        except OSError as e:
            if 'not found' in str(e):
                e = 'update variable NVIDIA_CMD_PATH (nvidia-smi) in the env.toml file and then check .env'
            raise OSError(f'Could not probe sensors: install lm_sensors, if possible\n{e}')

        data = None if len(res['stdout']) < 2 else float(res['stdout'][1])
        self._log_debug(f'Fetched data: {data}')

        res = {'gpu': data} if data else {}
        return res

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
