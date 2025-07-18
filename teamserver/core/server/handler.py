from core.utils.config import CONFIG
from core.server import commands
from core.utils import common
from core.transport import tcp
from functools import wraps

printer = common.Print_str()
MAIN_COMMANDS = commands.MAIN_COMMANDS

def auth(func):
    @wraps(func)
    def wrapper(conn, addr, *args, **kwargs):
        tcp.send_data(conn, common.banner())
        tcp.send_data(conn,printer.info(f"Server Name: {CONFIG.server_name}"))
        # tcp.send_data(conn,"username: ")
        _, username = tcp.recv_data(conn)
        # tcp.send_data(conn,"password: ")
        _, password = tcp.recv_data(conn)

        if password == CONFIG.auth.password:
            tcp.send_data(conn,printer.success(f"Authenticated as {username}"))
            return func(conn, addr, username, *args, **kwargs)
        else:
            tcp.send_data(conn,printer.fail("Authentication Failed"))

    return wrapper


@auth
def handle(conn, addr, username="operator"):
    while True:
        _, raw = tcp.recv_data(conn)
        if raw is None:
            print(f"[!] Connection from {addr} closed.")
            break

        cmd = raw.strip().split()
        if not cmd:
            continue

        args = cmd[1:]
        
        match cmd:
            case ["help"] | ["?"]:
                command = MAIN_COMMANDS.get("help")
                response = commands.help()
                tcp.send_data(conn, response, header=command["header"])

            case ["status"]:
                command = MAIN_COMMANDS.get("status")
                response = commands.status()
                tcp.send_data(conn, response, header=command["header"])

            case ["list"]:
                command = MAIN_COMMANDS.get("list")
                response = commands.list_help()
                tcp.send_data(conn, response, header=command["header"])

            case ["list", arg]:
                command = MAIN_COMMANDS.get("list")
                response = commands.list(arg)
                tcp.send_data(conn, response, header=command["header"])
                
            case ["listener"]:
                command = MAIN_COMMANDS.get("listener")
                response = commands.listener_help()
                tcp.send_data(conn, response, header=command["header"])
                
            case ["listener", arg]:
                command = MAIN_COMMANDS.get("listener")
                response = commands.listener_help()
                tcp.send_data(conn, response, header=command["header"])
                
            case ["listener", listener_data , name]:
                command = MAIN_COMMANDS.get("listener")
                response = commands.listener(listener_data, name)
                tcp.send_data(conn, response, header=command["header"])

            case ["interact"]:
                if not args:
                    tcp.send_data(conn, printer.warning("Usage: interact <id>"))
                    continue
                session_id = args[0]
                command = MAIN_COMMANDS.get("interact")

                response = f"Interacting with session {session_id}"
                tcp.send_data(conn, response, header=command["header"])

            case ["exit"]:
                command = MAIN_COMMANDS.get("exit")
                response = commands.exit()
                tcp.send_data(conn, response, header=command["header"])
                break

            case _:
                unknown = args[0]
                response = printer.warning(f"Unknown command: {unknown}")
                tcp.send_data(conn, response)
