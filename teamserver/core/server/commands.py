from core.utils import common, config
from core.agents import handler
from core.agents.utils import task as taskmng
from core.listener import tcp_listener, http_listener, util

from tabulate import tabulate

printer = common.Print_str()

MAIN_COMMANDS = {
    "status": {
        "msg": "Show server status",
        "header": "STATUS"
    },
    "list": {
        "msg": "List agents or listeners",
        "header": "LIST"
    },
    "listener": {
        "msg": "Create listener",
        "header": "LISTENER"
    },
    "interact": {
        "msg": "Interact with an agent",
        "header": "INTERACT"
    },
    "clear": {
        "msg": "Clear the screen",
        "header": "CLEAR"
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

    title = "Teamserver"
    headers = ["Config",  "Value"]
    rows = [
        ["Server Name", CONFIG.server_name],
        ["Version", CONFIG.version],
        ["IP",CONFIG.ip],
        ["Port", CONFIG.port],
        ["Auth Method", CONFIG.auth.method],
        ["Encryption Method", CONFIG.encryption.method],
        ["Agents", len(AGENTS)],
        ["Active ", sum(1 for a in AGENTS.values() if a.status == "active")],
        ["Dead Agents", sum(1 for a in AGENTS.values() if a.status != "active")]
    ]
    output = f"{title}\n{tabulate(rows, headers=headers, tablefmt='fancy_grid')}\n"
    return output

def list_agent():
    AGENTS = handler.AGENTS
    title = "Agents"
    headers = ["ID", "IP Address", "Username", "Hostname", "OS", "Connection Type", "Status"]
    rows = []
    
    agents = AGENTS.values()
    if not agents:
        return printer.warning(f"No agent found")

    for agent in agents:
        rows.append([agent.id, agent.ip, agent.username, agent.hostname, agent.arch, agent.conn_type, agent.status])

    output = f"{title}\n{tabulate(rows, headers=headers, tablefmt='fancy_grid')}\n"
    return output
    

def list_listener():
    LISTENERS = util.LISTENERS
    title = "Listeners"
    headers = ["Name", "Host", "Port","Connection Type", "Status", "Started At"]
    rows = []

    listeners = LISTENERS.values()
    if not listeners:
        return printer.warning(f"No listener found")

    for listener in listeners:
        rows.append([listener.name, listener.ip, listener.port, listener.conn_type, listener.status, listener.started_at])

    output = f"{title}\n{tabulate(rows, headers=headers, tablefmt='fancy_grid')}\n"
    return output

def list_tasks(agent_id=None):
    
    if agent_id:
        title = f"Agent {agent_id} Tasks"
        headers = ["ID", "Command", "Status", "Created At"]
        rows = []
        
        tasks = taskmng.get_all_tasks(agent_id)
        for t in tasks:
            rows.append([t.id, t.command, t.status, t.created_at])
    else:
        title = "All Tasks"
        headers = ["ID", "Agent ID", "Command", "Status", "Created At"]
        rows = []
        
        agents = taskmng.get_all()
        for tasks in agents:
            for t in tasks:
                rows.append([t.id, t.agent_id, t.command, t.status, t.created_at])

    output = f"{title}\n{tabulate(rows, headers=headers, tablefmt='fancy_grid')}\n"
    return output


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