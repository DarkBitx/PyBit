from core.transport import tcp
from functools import wraps
import time
        
def auth(func):
    @wraps(func)
    def wrapper(self, auth_status, *args, **kwargs):
        try:
            tcp.send_data(self.conn, self.username)
            tcp.send_data(self.conn, self.password)
            _,msg = tcp.recv_data(self.conn)

            if msg == "TRUE":
                auth_status = True
                return func(self, auth_status, *args, **kwargs)
            else:
                auth_status = False
                return func(self, auth_status, *args, **kwargs)
        except Exception:
            auth_status = False
            return func(self, auth_status, *args, **kwargs)
        
    return wrapper


@auth
def handle(self,auth_status):
    if not auth_status:
         self.insert_line("[-] Authentication Failed; exiting...", "light_red")
         time.sleep(2)
         self.on_close()
         
    self.insert_line("[+] Authentication succeed", "light_green")
       
    _,banner = tcp.recv_data(self.conn)
    self.insert_ansi(banner + "\n\n", False)
    
    _,server_name = tcp.recv_data(self.conn)
    parts = server_name.split(":")
    
    self.server_name = parts[1].strip()
    self.insert_ansi(server_name + "\n")
    
    while True:
        time.sleep(1)
        header, response = check_command(self)
        if header:
            match header:
                case "EXIT":
                    self.insert_ansi(response)
                    time.sleep(1)
                    self.on_close()
                case "INTERACT":
                    _, id = tcp.recv_data(self.conn)
                    self.agent_id = id
                    self.insert_ansi(response)
                case "SHELL":
                    _, shell = tcp.recv_data(self.conn)
                    self.agent_shell = shell
                    self.insert_ansi(response)
            continue
        if response:
            self.insert_ansi(response)
        

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