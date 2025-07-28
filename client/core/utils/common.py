from datetime import datetime, timezone
from colorama import init, Fore, Style
from random import random, uniform
from time import sleep
from sys import stdout
import json
import os

init(autoreset=True)

def time_now_str() -> str:
    return datetime.now(timezone.utc).strftime("[%H:%M:%S]")

def time_now():
    return datetime.now(timezone.utc)
    
def writer(text, end='\n', flush=True):

    for char in text:
        stdout.write(char)
        if flush:
            stdout.flush()
        
        if random() < 0.70:
            sleep(uniform(0.008, 0.02))
        else:
            sleep(uniform(0.05, 0.15))
    
    stdout.write(end)
    if flush:
        stdout.flush()

class TextStyle:
    def red(self,text):             return f"{Fore.RED}{text}{Style.RESET_ALL}"
    def green(self,text):           return f"{Fore.GREEN}{text}{Style.RESET_ALL}"
    def yellow(self,text):          return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    def blue(self,text):            return f"{Fore.BLUE}{text}{Style.RESET_ALL}"
    def magenta(self,text):         return f"{Fore.MAGENTA}{text}{Style.RESET_ALL}"
    def cyan(self,text):            return f"{Fore.CYAN}{text}{Style.RESET_ALL}"
    def white(self,text):           return f"{Fore.WHITE}{text}{Style.RESET_ALL}"

    def light_red(self,text):       return f"{Fore.LIGHTRED_EX}{text}{Style.RESET_ALL}"
    def light_green(self,text):     return f"{Fore.LIGHTGREEN_EX}{text}{Style.RESET_ALL}"
    def light_yellow(self,text):    return f"{Fore.LIGHTYELLOW_EX}{text}{Style.RESET_ALL}"
    def light_blue(self,text):      return f"{Fore.LIGHTBLUE_EX}{text}{Style.RESET_ALL}"
    def light_magenta(self,text):   return f"{Fore.LIGHTMAGENTA_EX}{text}{Style.RESET_ALL}"
    def light_cyan(self,text):      return f"{Fore.LIGHTCYAN_EX}{text}{Style.RESET_ALL}"
    def light_white(self,text):     return f"{Fore.LIGHTWHITE_EX}{text}{Style.RESET_ALL}"
    def gray(self,text):            return f"{Fore.LIGHTBLACK_EX}{text}{Style.RESET_ALL}"

    def bold(self,text):            return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"
    def dim(self,text):             return f"{Style.DIM}{text}{Style.RESET_ALL}"

class Print:
    def __init__(self):
        self.style = TextStyle()

    def info(self, msg):
        print(f"{self.style.gray('[i]')} {msg}")

    def success(self, msg):
        print(f"{self.style.light_green('[+]')} {msg}")

    def fail(self, msg):
        print(f"{self.style.light_red('[-]')} {msg}")

    def warning(self, msg):
        print(f"{self.style.light_yellow('[!]')} {msg}")

    def task(self, msg):
        print(f"{self.style.light_blue('[*]')} {msg}")

    def debug(self, msg):
        print(f"{self.style.yellow('[#]')} {msg}")

    def signal(self, msg):
        print(f"{self.style.light_white('[^]')} {msg}")

    def custom(self, tag, msg, color_func):
        """
        color_func should be a method from TextStyle, e.g., self.style.cyan
        """
        print(f"{color_func(f'[{tag}]')} {msg}")

class Write:
    def __init__(self):
        self.style = TextStyle()

    def info(self, msg):
        writer(f"{self.style.gray('[i]')} {msg}")

    def success(self, msg):
        writer(f"{self.style.light_green('[+]')} {msg}")

    def fail(self, msg):
        writer(f"{self.style.light_red('[-]')} {msg}")

    def warning(self, msg):
        writer(f"{self.style.light_yellow('[!]')} {msg}")

    def task(self, msg):
        writer(f"{self.style.light_blue('[*]')} {msg}")

    def debug(self, msg):
        writer(f"{self.style.yellow('[#]')} {msg}")

    def signal(self, msg):
        writer(f"{self.style.light_white('[^]')} {msg}")

    def custom(self, tag, msg, color_func):
        """
        color_func should be a method from TextStyle, e.g., self.style.cyan
        """
        writer(f"{color_func(f'[{tag}]')} {msg}")

def save_file(content, save_path: str, binary: bool = False) -> bool:
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        mode = "wb" if binary else "w"
        with open(save_path, mode) as f:
            f.write(content)
        return True
    except Exception as e:
        print("❌ File save error:", e)
        return False

def save_json_file(data: dict, save_path: str, indent: int = 2) -> bool:

    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        print("❌ JSON save error:", e)
        return False

def load_json_file(path: str) -> dict:

    try:
        if not os.path.isfile(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("❌ JSON load error:", e)
        return {}


