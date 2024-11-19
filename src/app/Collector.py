"""My Python module

Description

todo: test `hwinfo --sensors`
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from psutil import cpu_percent, virtual_memory, disk_partitions
from shutil import disk_usage
from subprocess import run
from re import sub
from time import time

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

    @property
    def data(self) -> dict:
        """Retrieve all available CPU and GPU temperatures"""
        self._log('Start data retrieval')

        retrieval_threshold_sec: int = 20
        if (time() - self._last_probe['epoch']) < retrieval_threshold_sec:
            self._log(f'Return recent data (queried less than {retrieval_threshold_sec} seconds ago)')
            return self._last_probe

        self._last_probe = {'epoch': int(time())}

        checkpoint = time()
        with ThreadPoolExecutor() as thread:
            for future, config in {
                thread.submit(self._probe_lm_sensors): {'label': 'sensors', 'append_label': True},
                thread.submit(self._fetch_thermal_zones): {'label': 'thermal_zones', 'append_label': True},
                thread.submit(self._probe_nvidia_gpu): {'label': 'nvidia', 'append_label': True},
                thread.submit(self._fetch_networks): {'label': 'procfs', 'append_label': False},
                thread.submit(self._shutil_storage_use): {'label': 'shutil', 'append_label': False},
                thread.submit(self._psutil_cpu_general_usage): {'label': 'usage', 'append_label': True},
                thread.submit(self._psutil_memory_usage): {'label': 'usage', 'append_label': True},
                # Default config is to not append the label in net or storage, because both have single data sources
            }.items():
                label, append_label = config.values()

                try:
                    res = future.result()  # Get the return value from the method
                except Exception as e:
                    self._log(f'Task {label!r} raised an exception: {e}', 30)
                    continue

                if not res:
                    self._log(f'No data from {label}')
                    continue

                for data_point, values in res.items():
                    if data_point not in self._last_probe:
                        self._last_probe[data_point] = {}

                    if append_label:
                        self._last_probe[data_point][label] = values
                    else:
                        self._last_probe[data_point] = values

        self._log('Probe took {:.3f} seconds'.format(time() - checkpoint))
        return self._last_probe

    def _probe_lm_sensors(self) -> dict:
        """Update self._last_cpu_data property with data from the sensors command"""
        self._log('Start sensors probe')

        filters = ('Package', 'Tctl', 'CPU', 'GPU', 'edge')
        cmd = '{s} | {g} -e {f} | {g} °C'.format(
            s=SENSORS_CMD_PATH, f=' -e '.join(filters), g=GREP_CMD_PATH,
        )

        try:
            res = self._run_os_command(cmd)
            self._log(f'Command returned: {res}')  # expected: ['Package id 0:      +70.0°C ... ']

            if not res['stdout']:
                raise OSError('no sensors data')

        except OSError as e:
            if 'not found' in str(e):
                e = 'update variables SENSORS_CMD_PATH and GREP_CMD_PATH in the env.toml file and then check .env'
            raise OSError(f'Could not probe sensors: install lm-sensors, if possible\n{e}')

        data = {}
        for line in res['stdout']:
            chunks = line.split(':')
            key = chunks[0].strip()
            val = sub(r'[^0-9.+-]', '', chunks[1].split()[0])
            data[key] = float(val)

        self._log(f'Parsed data: {data}')

        fetch = {
            'cpu': ('Package id 0', 'Tctl', 'CPU', 'coretemp'),
            'gpu': ('GPU', 'GPU temp', 'edge'),
        }

        res = {}
        for data_point, keys in fetch.items():
            for key in keys:
                if key in data:
                    if data_point not in res:
                        res[data_point] = {}

                    res[data_point][key] = data[key]

        return res

    def _fetch_thermal_zones(self) -> dict:
        """Update self._last_cpu_data property with data from CPU thermal zones (cores)

        Some hardware handle temperature in files that can be catted.
        """
        self._log('Start thermal zone fetch')

        cmd = f'{CAT_CMD_PATH} /sys/class/thermal/thermal_zone*/temp'

        try:
            res = self._run_os_command(cmd)
            self._log(f'Command returned: {res}')  # expected: ['20000', '47050', '61050',]

            if not res['stdout']:
                raise OSError('no thermal zone data')

        except OSError as e:
            if 'not found' in str(e):
                e = 'update variable CAT_CMD_PATH in the env.toml file and then check .env'
            raise OSError(f'Could not fetch thermal zones: hardware may not report thermal zones\n{e}')

        data = [round(float(t) / 1000, 3) for t in res['stdout']]
        self._log(f'Fetched data: {data}')

        res = {'cpu': data} if data else {}
        return res

    def _probe_nvidia_gpu(self) -> dict:
        """Probe GPU temperatures from the nvidia modules

        Returns:
            (float): a single value returned from the nvidia-smi call
        """
        self._log('Start nvidia probe')

        cmd = f'{NVIDIA_CMD_PATH} --query-gpu=temperature.gpu --format=csv'

        try:
            res = self._run_os_command(cmd)
            self._log(f'Command returned: {res}')  # expected: ['temperature.gpu', '49']

            if not res['stdout']:
                raise OSError('no nvidia data')

        except OSError as e:
            if 'not found' in str(e):
                e = 'update variable NVIDIA_CMD_PATH (nvidia-smi) in the env.toml file and then check .env'
            raise OSError(f'Could not probe nvidia: install nvidia-smi, if compatible\n{e}')

        data = None if len(res['stdout']) < 2 else float(res['stdout'][1])
        self._log(f'Fetched data: {data}')

        res = {'gpu': data} if data else {}
        return res

    def _fetch_networks(self) -> dict:
        """Fetch data from network devices

        Returns:
            (dict): Having values as Megabits (Mb)
        """
        self._log('Start network devices fetch')

        cmd = f'{CAT_CMD_PATH} /proc/net/dev'

        try:
            res = self._run_os_command(cmd)
            self._log(f'Command returned: {res}')  # expected: ['20000', '47050', '61050',]

            if not res['stdout'] or len(res['stdout']) < 3:
                raise OSError('no network device data')

        except OSError as e:
            if 'not found' in str(e):
                e = 'update variable CAT_CMD_PATH in the env.toml file and then check .env'
            raise OSError(f'Could not fetch network devices: hardware may not report via /proc\n{e}')

        data = {}
        for line in res['stdout'][2:]:
            device, info = line.split(':')
            device = device.strip()
            if device in ('lo', 'podman', 'podman0', 'docker', 'docker0', 'veth0'):
                continue

            info = sub(r' +', ' ', info).split()
            mbits_in, mbits_out = (int(info[0]) * 8) / 1000 ** 2, (int(info[8]) * 8) / 1000 ** 2
            data[device] = {'in': round(mbits_in, 1), 'out': round(mbits_out, 1)}

        self._log(f'Fetched data: {data}')
        res = {'net': data} if data else {}
        return res

    def _shutil_storage_use(self) -> dict:
        """Fetch data from mounted partitions

        Returns:
            (dict): Having values in Mebibytes (MiB)
        """
        data = {}

        for partition in disk_partitions():
            if partition.mountpoint.startswith('/snap'):
                self._log(f'Skip shutil data for {partition.mountpoint}')
                continue

            data[partition.mountpoint] = {}

            usage = disk_usage(partition.mountpoint)
            self._log(f'shutil returned for {partition.mountpoint}: {usage}')

            for k in dir(usage):
                if k.startswith('_') or callable(usage.__getattribute__(k)):
                    continue

                val_bytes = usage.__getattribute__(k)
                mibytes = val_bytes / 1024 ** 2
                data[partition.mountpoint].update({k: round(mibytes, 1)})

        self._log(f'Fetched data: {data}')
        res = {'storage': data} if data else {}
        return res

    def _psutil_cpu_general_usage(self) -> dict:
        """Fetch data from CPU

        Returns:
            (dict): Having one value in load/usage percentage
        """
        usage = cpu_percent(interval=1)
        self._log(f'psutil returned for CPU usage: {usage}')

        res = {'cpu': usage}
        return res

    def _psutil_memory_usage(self) -> dict:
        """Fetch data from RAM

        Returns:
            (dict): Having one value in load/usage percentage
        """
        usage = virtual_memory().percent
        self._log(f'psutil returned for RAM usage: {usage}')

        res = {'ram': usage}
        return res

    def _identify(self):
        self._log('Start device identification')
        cmd = f'{HOSTNAME_CMD_PATH} -s'

        try:
            res = self._run_os_command(cmd)
            self._log(f"Command returned: {res}")

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

    def _log(self, msg: str, level: int = 10):
        if not self.logger:
            return

        self.logger.log(level, msg)
