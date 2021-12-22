import json
from functools import reduce
from pathlib import Path

import paramiko
import xmltodict
from paramiko.rsakey import RSAKey

from models.gpu import GPU


class Node:

    def __init__(self, host: str):
        self.host = host  # nickname
        # server authorization
        self.hostname = 'xxx.xxx.xxx.xxx'
        self.port = 22
        self.username = 'root'
        self.password = '123456'
        self.private_key = None

        # server status
        self.driver_version = 0  # like: 460.67
        self.cuda_version = 0  # like: 11.2
        self.attached_gpus = 0  # like: 4
        self.gpus = []  # list of model GPU
        self.disable_gpus = []  # list of crash GPU

        # load authorization
        self._load_authorization()

    def _load_authorization(self):
        host_file = Path(f'data/config/host.json')
        host_json = host_file.read_text()
        host_dict = json.loads(host_json)[self.host]
        self.hostname = host_dict['hostname']
        self.port = host_dict['port'] if 'port' in host_dict else 22
        self.username = host_dict['username']
        self.password = host_dict['password'] if 'password' in host_dict else None
        self.disable_gpus = host_dict['disable_gpus'] if 'disable_gpus' in host_dict else []
        # check private key
        private_key_file = Path('../data/config/private_key')
        if not private_key_file.exists():
            return
        self.private_key = RSAKey.from_private_key_file(filename=str(private_key_file))

    def _get_available_memory(self):
        node_available_memory = reduce(lambda a, b: a + b, [gpu.available_memory for gpu in self.gpus])
        return node_available_memory

    def __getattr__(self, item: str):
        if item == 'available_memory':
            return self._get_available_memory()

    def update_from_server(self):
        # receive status xml from server
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.hostname, self.port, self.username, self.password, self.private_key)
        stdin, stdout, stderr = client.exec_command('nvidia-smi -q -x')
        status_xml = stdout.read().decode('utf-8')
        client.close()
        # parsing xml
        status_dict = xmltodict.parse(status_xml, process_namespaces=True)
        data = status_dict['nvidia_smi_log']
        self.driver_version = data['driver_version']
        self.cuda_version = data['cuda_version']
        self.attached_gpus = int(data['attached_gpus'])
        self.gpus = [GPU.init_from_dict(x) for x in (data['gpu'] if self.attached_gpus > 1 else [data['gpu']])]
        # disable GPU (if hardware crash)
        for x in self.disable_gpus:
            self.gpus[x].disable = True

    def __str__(self):
        node_str = f'host: {self.host} | ' \
                   f'cuda: {self.cuda_version} | ' \
                   f'gpus: {self.attached_gpus}' \
                   f'{"" if not len(self.disable_gpus) else f" ({len(self.disable_gpus)} disabled)"} | ' \
                   f'available: {self.available_memory}'
        gpus_str = [str(x) for x in self.gpus]
        node_str = reduce(lambda x, y: f'{x}\n{y}', [node_str] + gpus_str)
        return node_str
