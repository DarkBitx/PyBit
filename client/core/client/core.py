from core.client import routes
from core.transport  import tcp
import threading
import socket

class Client:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = None
        
    def connect(self):
        threading.Thread(target=self._connect, daemon=True).start()

    def _connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, int(self.port)))
        except Exception as e:
            self.sock = None
            
    def get_socket(self):
        return self.sock
            
def handle_client(self):
    try:
        threading.Thread(target=routes.handle, args=(self, False), daemon=True).start()
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        tcp.close(self.conn)