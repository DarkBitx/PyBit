from core.agents import handler
from core.utils import config, common, log
from core.listener.util import LISTENERS

import socket
import threading
import time

printer = common.Print_str()


class TCP_Listener:
    def __init__(self, ip, port, name):
        self.ip = ip
        self.port = port
        self.name = name
        self.conn = None
        self.conn_type="tcp"
        self.status = "active"
        self.started_at = common.time_now_str()
        self.message = printer.success(f"Listener {self.name} created successfully")
        self.logger = log.get_logger(self.name)
        
    def run(self):
        try:
            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server:
                server.bind((self.ip, int(self.port)))
                server.listen(config.CONFIG.agent.max_connections)
                # server.settimeout(config.CONFIG.agent.timeout_seconds)
                self.conn = server
                LISTENERS[self.name] = self
                self.logger.info(f"Listener running at {self.ip}:{self.port}")
                while True:
                    conn,addr = server.accept()
                    if self.status == "paused":
                        time.sleep(1)
                        conn.close()
                        continue
                    
                    log.info(f"New agent connected on {addr[0]}:{addr[1]}")
                    threading.Thread(target=handler.handle, args=(self.conn_type, conn, addr), daemon=True).start()
                    
        except (OSError, PermissionError):
            self.message = printer.fail(F"Port {self.port} on IP {self.ip} is in use")

    def pause(self):
        match self.status:
            case "active":
                self.status = "paused"
                self.message = printer.success(f"Listener {self.name} on {self.ip}:{self.port} paused")
            case _:
                self.message = printer.warning(f"Listener {self.name} on {self.ip}:{self.port} is already paused")
                
    def resume(self):
        match self.status:
            case "paused":
                self.status = "active"
                self.message = printer.success(f"Listener {self.name} on {self.ip}:{self.port} resumed")
            case _:
                self.message = printer.warning(f"Listener {self.name} on {self.ip}:{self.port} is already active")

    def close(self):
        if self.conn:
            try:
                self.conn.close()
                self.message = printer.success(f"Listener {self.name} on {self.ip}:{self.port} closed")
            except Exception as e:
                self.message = printer.fail(f"Failed to close listener {self.name}: {e}")
            finally:
                LISTENERS.pop(self.name)
        else:
            self.message = printer.warning(f"Listener {self.name} not found")
            
def NewTCP_listener(ip, port, name):
    listener = TCP_Listener(ip, port, name)

    if listener.name in LISTENERS:
        listener.message = printer.fail(f"Listener {name} already exist")
        return listener.message
    
    for _listener in LISTENERS.values(): 
        if _listener.ip == listener.ip and _listener.port == listener.port:
            listener.message = printer.fail(F"Port {listener.port} on IP {listener.ip} is in use")
            return listener.message  
           
    threading.Thread(target=listener.run, args=(), daemon=True).start()
    time.sleep(0.5)
    return listener.message
