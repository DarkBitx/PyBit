class Request:
    def __init__(self):
        self.conn = None
        self.header_separator = b'||'
        self.header = b''
        self.data = b''

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
        
        payload = sep + data
        if header:
            payload = sep + header + payload
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

        parts = body.split(self.header_separator, 2)

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

    def _recv_n_bytes(self, n):
        buffer = b''
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