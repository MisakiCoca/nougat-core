class GPU:

    def __init__(self, name: str, brand: str, uuid: str, memory: dict, utilization: dict):
        self.name = name  # like: GeForce RTX 2080 Ti
        self.brand = brand  # like: GeForce
        self.uuid = uuid  # like: GPU-9dc5b813-e748-8391-53d4-ac5a0a62dc1c
        self.memory = memory  # {'total', 'used', 'free'}
        self.utilization = utilization  # {'gpu', 'memory'}
        self.disable = False  # disable GPU

    @classmethod
    def init_from_dict(cls, status_dict: dict):
        name, brand = status_dict['product_name'], status_dict['product_brand']
        uuid = status_dict['uuid']
        memory = {
            'total': int(status_dict['fb_memory_usage']['total'].split()[0]),
            'used': int(status_dict['fb_memory_usage']['used'].split()[0]),
            'free': int(status_dict['fb_memory_usage']['free'].split()[0])
        }
        utilization = {
            'gpu': int(status_dict['utilization']['gpu_util'].split()[0]),
            'memory': int(status_dict['utilization']['memory_util'].split()[0]),
        }
        return cls(name, brand, uuid, memory, utilization)

    def _get_available_memory(self):
        return self.memory['free'] if not self.disable else 0

    def __getattr__(self, item: str):
        if item == 'available_memory':
            return self._get_available_memory()

    def __str__(self):
        used_memory_str = str(self.memory['used']).zfill(len(str(self.memory['total'])))
        gpu_status_str = f'{self.uuid} | {self.name} | {used_memory_str}/{self.memory["total"]}'
        available = '' if not self.disable else f' | disable'
        return gpu_status_str + available
