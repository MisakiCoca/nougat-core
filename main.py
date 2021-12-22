import json
import os
from datetime import datetime
from pathlib import Path
from time import sleep

from models.node import Node

if __name__ == '__main__':
    hosts_file = Path(f'data/config/host.json')
    hosts_json = hosts_file.read_text()
    hosts_dict = json.loads(hosts_json)
    nodes = [Node(host=x) for x in hosts_dict]

    listen_memory = 54000
    print(f'listening for {listen_memory}MB memory')


    def show_notification(title: str, text: str):
        os.system("""osascript -e 'display notification "{}" with title "{}"'""".format(text, title))


    def check_available() -> bool:
        for node in nodes:
            node.update_from_server()
            if node.available_memory >= listen_memory:
                show_notification(f'{node.host} available', f'{node.available_memory}MB remains')
                return True
        return False


    while not check_available():
        print(f'{datetime.now()} | no gpu available')
        sleep(5)
