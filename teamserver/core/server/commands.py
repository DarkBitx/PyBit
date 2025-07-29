from core.utils import common, config
from core.agents import handler
from core.agents.utils import task as taskmng
from core.listener import tcp_listener, http_listener, util

from prettytable import PrettyTable, HRuleStyle

printer = common.Print_str()

MAIN_COMMANDS = {
    "status": {
        "cmd": "Show server status",
        "header": "STATUS"
    },
    "list": {
        "cmd": "List agents or listeners",
        "header": "LIST"
    },
    "listener": {
        "cmd": "Create listener",
        "header": "LISTENER"
    },
    "interact": {
        "cmd": "Interact with an agent",
        "header": "INTERACT"
    },
    "clear": {
        "cmd": "Clear the screen",
        "header": "CLEAR"
    },
    "exit": {
        "cmd": "Exit the session",
        "header": "EXIT"
    },
    "help": {
        "cmd": "Show this help message",
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
    table.field_names = ["ID", "IP Address", "Username", "Hostname", "OS", "Connection Type", "Status"]
    table.align["Username"] = "l"  
    table.sortby = "ID"
    table.border = True
    table.header = True
    table.hrules = HRuleStyle.ALL
    agents = AGENTS.values()
    if not agents:
        return printer.warning(f"No agent found")

    for agent in agents:
        table.add_row([agent.id, agent.ip, agent.username, agent.hostname, agent.arch, agent.conn_type, agent.status])
        
    return str(table) + "\n"
    

def list_listener():
    LISTENERS = util.LISTENERS
    table = PrettyTable()
    table.title = "Listeners"
    table.field_names = ["Name", "Host", "Port","Connection Type", "Status", "Started At"]
    table.align["Name"] = "l"  
    table.sortby = "Name"
    table.border = True
    table.header = True
    table.hrules = HRuleStyle.ALL
    listeners = LISTENERS.values()
    if not listeners:
        return printer.warning(f"No listener found")

    for listener in listeners:
        table.add_row([listener.name, listener.ip, listener.port, listener.conn_type, listener.status, listener.started_at])
    
    return str(table) + "\n"

def list_tasks(agent_id=None):
    table = PrettyTable()
    table.align["Command"] = "l"
    table.border = True
    table.header = True
    table.hrules = HRuleStyle.ALL

    if agent_id:
        table.title = f"Agent {agent_id} Tasks"
        table.field_names = ["ID", "Command", "Status", "Created At"]
        tasks = taskmng.get_all_tasks(agent_id)
        rows = [[t.id, t.command, t.status, t.created_at] for t in tasks]
    else:
        table.title = "All Tasks"
        table.field_names = ["ID", "Agent ID", "Command", "Status", "Created At"]
        agents = taskmng.get_all()
        for tasks in agents:
            for t in tasks:
                rows = [[t.id, t.agent_id, t.command, t.status, t.created_at] for t in tasks]

    table.sortby = "ID"
    for row in rows:
        table.add_row(row)

    return str(table) + "\n"


def list(arg, agent_id=None):

    match arg:
        case "agents":
            return list_agent()
        case "listeners":
            return list_listener()
        case "tasks":
            return list_tasks(agent_id)
        case _:
            return list_help()

def listener(listener_data, name=None):

    raw = listener_data.split(":")
    if len(raw) == 3:
        if not name:
            return listener_help()
        cmd, ip, port = raw
    elif len(raw) == 2:
        cmd, name= raw
    else:
        return listener_help()
        
        
    match cmd:
        case "tcp":
            return tcp_listener.NewTCP_listener(ip, port, name)
        case "http":
            return http_listener.NewHTTP_listener(ip, port, name)
        case "pause":
            return util.pause(name)
        case "resume":
            return util.resume(name)
        case "close":
            return util.close(name)
        case _:
            return printer.fail("Invalid listener manage command")
            
def interact(conn, id):
    AGENTS = handler.AGENTS
    if id not in AGENTS:
        return printer.fail(f"Agent with id [{id}] not found")
    return handler.handle_interact(conn, id)

def exit():
    return printer.task("Exiting...")


# Helps

def help():
    help_lines = ["Available Commands:\n"]

    for cmd, info in MAIN_COMMANDS.items():
        cmd = info["msg"] if isinstance(info, dict) else info
        help_lines.append(f"  - {cmd:<20} {cmd}")
        
    return printer.info("\n".join(help_lines))

def list_help():
    return printer.info("Usage: list | ls <agents|listeners> | <tasks> <agent_id>")

def listener_help():
    return printer.info("Usage:\ntype: tcp|http - command: close|pause|resume\nlistener | lr <type:ip:port> <name>\nlistener | lr <command:name>")

def interact_help():
    return printer.info("Usage: interact | i <id>")