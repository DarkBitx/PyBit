from core.transport import tcp
from functools import wraps
import time
        
def auth(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        _,banner = tcp.recv_data(self.conn)
        self.insert_ansi(banner + "\n\n", False)
        _,server_name = tcp.recv_data(self.conn)
        parts = server_name.split(":")
        self.server_name = parts[1].strip()
        self.insert_ansi(server_name + "\n")
        
        tcp.send_data(self.conn, self.username)
        tcp.send_data(self.conn, self.password)
        
        _,msg = tcp.recv_data(self.conn)

        if msg != "Authentication Failed":
            return func(self, *args, **kwargs)
        else:
            print("Authentication Failed")

    return wrapper


@auth
def handle(self):
    while True:
        time.sleep(1)
        header, response = check_command(self)
        if response:
            self.insert_ansi(response)
        if header:
            match header:
                case "EXIT":
                    time.sleep(1)
                    self.on_close()
        

def check_command(self):
    with self.lock:
        cmd = self.shared_cmd
        self.shared_cmd = None
    if cmd:
        return process_command(self.conn, cmd)
    return None, None 

def process_command(conn, cmd):
    tcp.send_data(conn, cmd)
    header, response = tcp.recv_data(conn)
    return header, response