from flask import Response
from core.utils.config import CONFIG

class HTTPRequest:
    def __init__(self):
        self.method = None
        self.uri = None
        self.headers = {}
        self.data = ""
        self.remote_addr = ""
        self.header_separator = CONFIG.agent.seperator
        self.header = ""
        self.data = ""
        self.task_id = ""
        self.status = 200
        

    def set_request(self, req):
        self.method = req.method
        self.headers = req.headers
        self.data = req.data
        self.remote_addr = req.remote_addr

    def set_task_id(self, task_id, binary=False):
        self.task_id = task_id if binary else task_id.decode() if isinstance(task_id, bytes) else task_id
        
    def set_data(self, data, binary=False):
        self.data = data if binary else data.decode() if isinstance(data, bytes) else data

    def set_header_separator(self, separator):
        self.header_separator = separator if isinstance(separator, str) else separator.decode()
        
    def set_header(self, header):
        self.header = header if isinstance(header, str) else header.decode()

    def set_status(self, status):
        self.status = status if isinstance(status, int) else int(status)

    def get_ip(self):
        return self.remote_addr

    def send(self):
        
        parts = ["", "", ""]

        if self.header:
            parts[0] = self.header
        if self.task_id:
            parts[1] = self.task_id
        if self.data:
            parts[2] = self.data
            
        payload = self.header_separator.join(parts)

        response = Response(payload, self.status)
        response.headers["Content-Type"] = "application/octet-stream"
        response.headers["Content-Length"] = str(len(payload.encode()))
        return response

    def recv(self, binary=False):
        
        if isinstance(self.data, str):
            raw_data = self.data.encode()
        else:
            raw_data = self.data

        parts = raw_data.split(self.header_separator.encode(), 2)
        
        header = b""
        task_id = b""
        data = b""
        
        if len(parts) == 3:
            header,task_id, data = parts
        elif len(parts) == 2:
            task_id, data = parts
        else:
            data = parts[0]

        self.header = header if binary else header.decode(errors="ignore")
        self.task_id = task_id if binary else task_id.decode(errors="ignore")
        self.data = data if binary else data.decode(errors="ignore")
        return True

def generate_response(task_id=None, data=None, header=None, status=None, header_separator=None, binary=False):
    try:
        r = HTTPRequest()
        if task_id:
            r.set_task_id(task_id)
        if header_separator:
            r.set_header_separator(header_separator)
        if header:
            r.set_header(header)
        if status:
            r.set_status(status)
        if data:
            r.set_data(data, binary)
        return r.send()
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return Response("Internal Server Error", status=500)

def parse_request(req, binary=False):
    try:
        r = HTTPRequest()
        r.set_request(req)
        r.recv(binary)
        return r.header, r.task_id, r.data
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return None, None, None

def get_ip(req):
    r = HTTPRequest()
    r.set_request(req)
    return r.get_ip()
