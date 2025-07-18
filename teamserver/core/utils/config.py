from core.utils import common
from dataclasses import dataclass
from typing import Dict

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
class BeaconConfig:
    max_connections: int
    timeout_seconds: int
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
class TeamServerConfig:
    ip: str
    port: str
    version: str
    server_name: str
    auth: AuthConfig
    logging: LoggingConfig
    beacon: BeaconConfig
    encryption: EncryptionConfig

def from_dict(data: dict) -> TeamServerConfig:
    return TeamServerConfig(
        ip=data["ip"],
        port=data["port"],
        version=data["version"],
        server_name=data["server_name"],
        auth=AuthConfig(**data["auth"]),
        logging=LoggingConfig(**data["logging"]),
        beacon=BeaconConfig(
            max_connections=data["beacon"]["max_connections"],
            timeout_seconds=data["beacon"]["timeout_seconds"],
            heartbeat_interval=data["beacon"]["heartbeat_interval"],
            http_profile=HTTPProfile(
                tls=TLSConfig(**data["beacon"]["http_profile"]["tls"]),
                get=HTTPGetProfile(**data["beacon"]["http_profile"]["get"]),
                post=HTTPPostProfile(**data["beacon"]["http_profile"]["post"]),
            ),
            proxy=ProxyConfig(**data["beacon"]["proxy"]),
        ),
        encryption=EncryptionConfig(**data["encryption"]),
    )

data = common.load_json_file("profile.json")
CONFIG = from_dict(data["teamserver"])
