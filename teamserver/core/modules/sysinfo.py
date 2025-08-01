import subprocess
import tempfile
import platform
import os

WINDOWS_COMMANDS = [
    "systeminfo",
    "net user",
    "whoami /groups",
    "ipconfig /all",
    "netstat -ano",
    "arp -a",
    "route print",
    "netsh winhttp show proxy",
    "powershell -Command Get-MpComputerStatus"
]

LINUX_COMMANDS = [
    "uname -a",
    "id",
    "whoami",
    "ifconfig -a || ip a",
    "netstat -tunap || ss -tunap",
    "arp -a",
    "route -n",
    "env",
    "cat /etc/resolv.conf"
]

def execute(cmd) -> str:
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        result = e.output
    return result.decode()

system = platform.system()
if system == "Windows":
    commands = WINDOWS_COMMANDS
    suffix = ".bat"
    content = "@echo off\n" + "\n".join(commands) + "\n"
else:
    commands = LINUX_COMMANDS
    suffix = ".sh"
    content = "#!/bin/bash\nset -e\n" + "\n".join(commands) + "\n"
    
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="w", encoding="utf-8") as tmp_file:
    tmp_file.write(content)
    tmp_path = tmp_file.name

if system != "Windows":
    os.chmod(tmp_path, 0o755)

result = execute(tmp_path)

os.remove(tmp_path)