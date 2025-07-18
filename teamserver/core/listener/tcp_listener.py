from core.agents import handler
from core.utils import config, common

from dataclasses import dataclass

import socket
import threading

TCP_LISTENERS = {}

@dataclass
class TCP_ListenerData:
    ip: str
    port: int
    name: str
    conn_type: str
    status: str
    started_at: str

class TCP_Listener:
    def __init__(self, ip, port, name):
        self.ip = ip
        self.port = port
        self.name = name

        
    def run(self):
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server:
            server.bind((self.ip, int(self.port)))
            server.listen(config.CONFIG.agent.max_connections)
            # server.settimeout(config.CONFIG.agent.timeout_seconds)
            
            TCP_LISTENERS[self.name] = TCP_ListenerData(
                    ip=self.ip,
                    port=self.port,
                    name=self.name,
                    conn_type="tcp",
                    status="active",
                    started_at=common.time_now_str()
                )
            while True:
                conn,addr = server.accept()
                print(f"[TCP_Listener] new connection [{addr}]")
                threading.Thread(target=handler.handle, args=(conn,addr), daemon=True).start()
                
def NewTCP_listener(ip, port, name):
    listener = TCP_Listener(ip, port, name)
    threading.Thread(target=listener.run, args=(), daemon=True).start()
    return True

