from core.utils.config import CONFIG
from core.server import commands
from core.utils import common, log
from core.transport import tcp
from functools import wraps

printer = common.Print_str()
MAIN_COMMANDS = commands.MAIN_COMMANDS

def auth(func):
    @wraps(func)
    def wrapper(conn, addr, *args, **kwargs):
        # tcp.send_data(conn,"username: ")
        _, username = tcp.recv_data(conn)
        # tcp.send_data(conn,"password: ")
        _, password = tcp.recv_data(conn)

        if password == CONFIG.auth.password:
            tcp.send_data(conn, "TRUE")
            
            log.info(f"Client {username} authenticated")
            return func(conn, addr, username, *args, **kwargs)
        else:
            log.warning(f"Client {username} could not authenticate")
            tcp.send_data(conn, "FALSE")

    return wrapper


@auth
def handle(conn, addr, username="operator"):
    
    tcp.send_data(conn, common.banner())
    tcp.send_data(conn,printer.info(f"Server Name: {CONFIG.server_name}"))
    
    while True:
        _, raw = tcp.recv_data(conn)
        if raw is None:
            print(f"[!] Connection from {addr} closed.")
            break

        cmd = raw.strip().split()
        if not cmd:
            continue
        
        match cmd:
            case ["status"]:
                # header = MAIN_COMMANDS.get("status")["header"]
                response = commands.status()
                tcp.send_data(conn, response)

            case ["list"] | ["ls"]:
                # header = MAIN_COMMANDS.get("list")["header"]
                response = commands.list_help()
                tcp.send_data(conn, response)

            case ["list", arg] | ["ls", arg]:
                # header = MAIN_COMMANDS.get("list")["header"]
                response = commands.list(arg)
                tcp.send_data(conn, response)

            case ["list", arg, agent_id] | ["ls", arg, agent_id]:
                # header = MAIN_COMMANDS.get("list")["header"]
                response = commands.list(arg, agent_id)
                tcp.send_data(conn, response)
                
            case ["listener"] | ["lr"]:
                # header = MAIN_COMMANDS.get("listener")["header"]
                response = commands.listener_help()
                tcp.send_data(conn, response)
                
            case ["listener", listener_data] | ["lr", listener_data]:
                # header = MAIN_COMMANDS.get("listener")["header"]
                response = commands.listener(listener_data)
                tcp.send_data(conn, response)
                
            case ["listener", listener_data , name] | ["lr", listener_data , name]:
                # header = MAIN_COMMANDS.get("listener")["header"]
                response = commands.listener(listener_data, name)
                tcp.send_data(conn, response)
                
            case ["interact"] | ["i"]:
                # header = MAIN_COMMANDS.get("interact")["header"]
                response = commands.interact_help()
                tcp.send_data(conn, response)
                
            case ["interact", id] | ["i", id]:
                header = MAIN_COMMANDS.get("interact")["header"]
                response = commands.interact(conn, id)
                tcp.send_data(conn, response, header)
                tcp.send_data(conn, " ")
                

            case ["help"] | ["?"]:
                # header = MAIN_COMMANDS.get("help")["header"]
                response = commands.help()
                tcp.send_data(conn, response)

            case ["exit"]:
                header = MAIN_COMMANDS.get("exit")["header"]
                response = commands.exit()
                tcp.send_data(conn, response, header)
                break

            case _:
                unknown = " ".join(c for c in cmd)
                response = printer.warning(f"Unknown command: {unknown}")
                tcp.send_data(conn, response)
