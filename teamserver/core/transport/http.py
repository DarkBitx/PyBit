from flask import Response, abort
from core.utils.config import CONFIG

class HTTPRequest:
    def __init__(self):
        self.method = None
        self.uri = None
        self.headers = {}
        self.body = b""
        self.remote_addr = ""
        self.header_separator = CONFIG.agent.seperator
        self.header = ''
        self.data = ''
        self.status = 200
        

    def set_request(self, req):
        self.method = req.method
        self.uri = req.uri
        self.headers = req.headers
        self.body = req.body
        self.remote_addr = req.remote_addr

    def set_header_separator(self, separator):
        self.header_separator = separator if isinstance(separator, str) else separator.decode()

    def set_header(self, header):
        self.header = header if isinstance(header, str) else header.decode()

    def set_data(self, status):
        self.status = status
        
    def set_data(self, data, binary=False):
        self.data = data if binary else data.decode() if isinstance(data, bytes) else data

    def get_ip(self):
        return self.remote_addr

    def send(self):
        sep = self.header_separator
        data = self.data
        status = self.status

        payload = sep + data
        if self.header:
            payload = f"{self.header}{sep}{self.data}"

        response = Response(payload, status)
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Length'] = str(len(payload.encode()))
        return response

    def recv(self, binary=False):
        parts = self.body.split(self.header_separator.encode(), 2)

        if len(parts) == 3:
            _, header, data = parts
        elif len(parts) == 2:
            _, data = parts
            header = b''
        else:
            header = b''
            data = parts[0]

        self.header = header if binary else header.decode(errors="ignore")
        self.data = data if binary else data.decode(errors="ignore")
        return True

def send(req, data, header=None, status=None, header_separator=None, binary=False):
    try:
        r = HTTPRequest()
        r.set_request(req)
        if header_separator:
            r.set_header_separator(header_separator)
        if header:
            r.set_header(header)
        if status:
            r.set_status(status)
        r.set_data(data, binary)
        return r.send()
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return Response("Internal Server Error", status=500)


def recv(req, binary=False):
    try:
        r = HTTPRequest()
        r.set_request(req)
        r.recv(binary)
        return r.header, r.data
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return None, None


def get_ip(req):
    r = HTTPRequest()
    r.set_request(req)
    return r.get_ip()
