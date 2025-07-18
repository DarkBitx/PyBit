from core.utils import common, config
from core.agents import handler
from core.listener import tcp_listener, http_listener
from core.transport import tcp

from prettytable import PrettyTable

printer = common.Print_str()

MAIN_COMMANDS = {
    "status": {
        "msg": "Show server status",
        "header": "STATUS"
    },
    "list": {
        "msg": "List active sessions",
        "header": "LIST"
    },
    "listener": {
        "msg": "Create listener",
        "header": "LISTENER"
    },
    "interact": {
        "msg": "Interact with a session",
        "header": "INTERACT"
    },
    "exit": {
        "msg": "Exit the session",
        "header": "EXIT"
    },
    "help": {
        "msg": "Show this help message",
        "header": "HELP"
    }
}

def status():
    CONFIG = config.CONFIG
    AGENTS = handler.AGENTS
    style = common.TextStyle()
    
    table = PrettyTable()

    table.title = "Teamserver"
    table.field_names = ["Config",  "Value"]
    table.align["Config"] = "l"  
    table.add_rows([
        ["Server Name", CONFIG.server_name],
        ["Version", CONFIG.version],
        ["IP",CONFIG.ip],
        ["Port", CONFIG.port],
        ["Auth Method", CONFIG.auth.method],
        ["Encryption Method", CONFIG.encryption.method],
        ["Agents", len(AGENTS)],
        ["Active ", sum(1 for a in AGENTS.values() if a.status == "active")],
        ["Dead Agents", sum(1 for a in AGENTS.values() if a.status != "active")]
    ])
    return str(table) + "\n"

def list_agent():
    AGENTS = handler.AGENTS
    table = PrettyTable()
    table.title = "Agents"
    table.field_names = ["ID", "IP Address", "Username", "Hostname", "Connection Type", "Status"]
    table.align["Username"] = "l"  
    table.sortby = "ID"
    table.border = True
    table.header = True

    for agent in AGENTS.values():
        if not agent:
            break
        table.add_row([agent.id, agent.ip, agent.username, agent.hostname, agent.conn_type, agent.status])
        
    return str(table) + "\n"
    

def list_listener():
    TCP_LISTENERS = tcp_listener.TCP_LISTENERS
    HTTP_LISTENERS = http_listener.HTTP_LISTENERS
    table = PrettyTable()
    table.title = "Listeners"
    table.field_names = ["Name", "IP Address", "Port","Connection Type", "Status", "Started At"]
    table.align["Name"] = "l"  
    table.sortby = "Name"
    table.border = True
    table.header = True

    for listener in TCP_LISTENERS.values():
        if not listener:
            break
        table.add_row([listener.name, listener.ip, listener.port, listener.conn_type, listener.status, listener.started_at])

    for listener in HTTP_LISTENERS.values():
        if not listener:
            break
        table.add_row([listener.name, listener.ip, listener.port, listener.conn_type, listener.status, listener.started_at])
        
    return str(table) + "\n"

def list(arg):

    match arg:
        case "agent":
            return list_agent()
        case "listener":
            return list_listener()
        case _:
            return list_help()

def listener(listener_data, name):

    raw = listener_data.split(":")
    if len(raw) != 3:
        return listener_help()
    else:
        listener_type, ip, port = raw
        
    match listener_type:
        case "tcp":
            if tcp_listener.NewTCP_listener(ip, port, name):
                return printer.success(f"Listener {name} created successfully")
        case "http":
            pass
        case _:
            return listener_help()
            


def exit():
    return printer.task("Exiting...")

def help():
    help_lines = ["Available Commands:\n"]

    for cmd, info in MAIN_COMMANDS.items():
        msg = info["msg"] if isinstance(info, dict) else info
        help_lines.append(f"  - {cmd:<20} {msg}")
        
    return printer.info("\n".join(help_lines))




# Helps

def list_help():
    return printer.info("Usage: list <agent>|<listener>")

def listener_help():
    return printer.info("Usage: listener <type:tcp|http> <name>")