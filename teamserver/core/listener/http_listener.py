from core.utils import config, common
from core.agents import handler
from core.listener.util import LISTENERS

from dataclasses import dataclass
from flask import Flask
from gevent.pywsgi import WSGIServer
import threading
import time

printer = common.Print_str()


class HTTP_Listener:
    def __init__(self, ip, port, name):
        CONFIG = config.CONFIG
        self.ip = ip
        self.port = port
        self.name = name
        self.base_url = f"http://{self.ip}:{self.port}/"
        self.task = CONFIG.listener.http.routes["task"]
        self.result = CONFIG.listener.http.routes["result"]
        self.listener = Flask(self.name)
        self.server = None
        self.conn_type="http"
        self.status = "active"
        self.started_at = common.time_now_str()
        self.message = printer.success(f"Listener {self.name} created successfully")
        
    def setup_routes(self):
        self.listener.add_url_rule(
            rule=self.task.uri,
            endpoint='handle_task',
            view_func=handler.handle_task,
            methods=self.task.method
        )

        self.listener.add_url_rule(
            rule=self.result.uri,
            endpoint='handle_result',
            view_func=handler.handle_result,
            methods=self.result.method
        )

    def run(self):
        try:
            self.setup_routes()
            LISTENERS[self.name] = self
            self.server = WSGIServer((self.ip, int(self.port)), self.listener)
            self.server.serve_forever()

        except OSError or PermissionError or WindowsError:
            self.message = printer.fail(F"Port {self.port} on IP {self.ip} is in use")


    def pause(self):
        match self.status:
            case "active":
                self.status = "paused"
                self.server.stop()
                self.message = printer.success(f"Listener {self.name} on {self.ip}:{self.port} paused")
            case _:
                self.message = printer.warning(f"Listener {self.name} on {self.ip}:{self.port} is already paused")

    def resume(self):
        match self.status:
            case "paused":
                self.status = "active"
                threading.Thread(target=self.run, daemon=True).start()
                self.message = printer.success(f"Listener {self.name} on {self.ip}:{self.port} resumed")
            case _:
                self.message = printer.warning(f"Listener {self.name} on {self.ip}:{self.port} is already active")

    def close(self):
        if self.server:
            try:
                self.server.close()
                self.message = printer.success(f"Listener {self.name} on {self.ip}:{self.port} closed")
            except Exception as e:
                self.message = printer.fail(f"Failed to close listener {self.name}: {e}")
            finally:
                LISTENERS.pop(self.name)
        else:
            self.message = printer.warning(f"Listener {self.name} not found")
            
def NewHTTP_listener(ip, port, name):
    listener = HTTP_Listener(ip, port, name)

    if name in LISTENERS.values():
        listener.message = printer.fail(f"Listener {name} already exists")
        return listener.message

    for _listener in LISTENERS.values():
        if _listener.ip == ip and _listener.port == port:
            listener.message = printer.fail(f"Port {port} on IP {ip} is in use")
            return listener.message

    threading.Thread(target=listener.run, daemon=True).start()
    time.sleep(0.5)
    return listener.message

