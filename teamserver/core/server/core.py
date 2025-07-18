from core.utils.config import CONFIG
from core.server import handler
from core.transport  import tcp
import threading
import socket

class Server:
    def __init__(self):
        self.ip = CONFIG.ip
        self.port = CONFIG.port

        
    def run(self):
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server:
            server.bind((self.ip, int(self.port)))
            server.listen(10)
            
            while True:
                conn,addr = server.accept()
                print(f"new connection [{addr}]")
                threading.Thread(target=handle_client, args=(conn,addr), daemon=True).start()

def handle_client(conn,addr):
    try:
        handler.handle(conn,addr)
    except Exception as e:
        tcp.send_data(conn, f"[!] Error: {str(e)}")
    finally:
        tcp.close(conn)