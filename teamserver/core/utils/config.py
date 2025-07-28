from core.utils import common
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class TLSConfig:
    enabled: bool
    cert: str
    key: str

@dataclass
class HTTPGetProfile:
    uri: str
    headers: Dict[str, str]
    padding: bool
    jitter: int
    sleep: int

@dataclass
class HTTPPostProfile:
    uri: str
    headers: Dict[str, str]
    body_encoding: str
    padding: bool
    obfuscate: bool

@dataclass
class HTTPProfile:
    tls: TLSConfig
    get: HTTPGetProfile
    post: HTTPPostProfile

@dataclass
class ProxyConfig:
    enabled: bool
    listen_port: int

@dataclass
class AgentConfig:
    max_connections: int
    timeout_seconds: float
    seperator: str
    heartbeat_interval: int
    http_profile: HTTPProfile
    proxy: ProxyConfig

@dataclass
class AuthConfig:
    enabled: bool
    method: str
    password: str

@dataclass
class LoggingConfig:
    enabled: bool
    log_file: str
    log_level: str

@dataclass
class EncryptionConfig:
    enabled: bool
    method: str
    key: str

@dataclass
class RouteConfig:
    uri: str
    method: List[str]
    auth_required: bool


@dataclass
class HTTPListenerConfig:
    tls: TLSConfig
    routes: Dict[str, RouteConfig]

@dataclass
class ListenerConfig:
    http: HTTPListenerConfig


@dataclass
class TeamServerConfig:
    ip: str
    port: str
    version: str
    server_name: str
    auth: AuthConfig
    logging: LoggingConfig
    agent: AgentConfig
    listener: ListenerConfig
    encryption: EncryptionConfig
    
def from_dict(data: dict) -> TeamServerConfig:
    http_routes = {
        name: RouteConfig(**route)
        for name, route in data["listener"]["http"]["routes"].items()
    }

    return TeamServerConfig(
        ip=data["ip"],
        port=data["port"],
        version=data["version"],
        server_name=data["server_name"],
        auth=AuthConfig(**data["auth"]),
        logging=LoggingConfig(**data["logging"]),
        agent=AgentConfig(
            max_connections=data["agent"]["max_connections"],
            timeout_seconds=data["agent"]["timeout_seconds"],
            seperator=data["agent"]["seperator"],
            heartbeat_interval=data["agent"]["heartbeat_interval"],
            http_profile=HTTPProfile(
                tls=TLSConfig(**data["agent"]["http_profile"]["tls"]),
                get=HTTPGetProfile(**data["agent"]["http_profile"]["get"]),
                post=HTTPPostProfile(**data["agent"]["http_profile"]["post"]),
            ),
            proxy=ProxyConfig(**data["agent"]["proxy"]),
        ),
        listener=ListenerConfig(
            http=HTTPListenerConfig(
                tls=TLSConfig(**data["listener"]["http"]["tls"]),
                routes=http_routes
            )
        ),
        encryption=EncryptionConfig(**data["encryption"])
    )

data = common.load_json_file("profile.json")
CONFIG = from_dict(data["teamserver"])
