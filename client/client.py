from core.client import core
from core.utils import common
import tkinter as tk
from tkinter import messagebox
import threading
import time
import sys
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
        master.geometry("300x260")
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

        
        self.window = tk.Toplevel()
        self.window.title("PyBit C2 - Terminal")
        self.window.configure(bg="#000000")
        self.window.geometry("700x500")
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
            
        self.insert_line(f"Trying to connect to {ip}:{port}...", "yellow")
        self.text.update()

        self.text.bind("<Return>", self.handle_enter)
        self.text.bind("<Key>", lambda e: self.scroll_to_end())
        
        self.conn = set_conn(self.ip, self.port)
        core.handle_client(self)

    def scroll_to_end(self):
        self.text.see("end")

    def insert_line(self, line, tag="white"):
        """Insert plain line with optional ANSI color tag (default: white)."""
        self.text.insert("end", line + "\n", tag)
        self.scroll_to_end()

    def insert_prompt(self):
        self.text.insert("end", f"\n{self.username}@{self.server_name}# ", "32")
        self.scroll_to_end()
        
    def handle_enter(self, event=None):
        cmd = self.text.get("end-2l", "end-1c").strip().split(">")[-1].strip()
        self.text.insert("end", "\n")
        self.set_command(cmd)
        return "break"
    
    def set_command(self, cmd):
        with self.lock:
            self.shared_cmd = cmd

    def insert_ansi(self, text, insert_status=True):
        import re

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
    
    def on_close(self):
        self.window.destroy()
        sys.exit(0)


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
