from core.utils import common

printer = common.Print_str()

LISTENERS = {}

def pause(name):
    listener = LISTENERS.get(name, "")
    if not listener:
        return printer.warning(f"Listener {name} not found")
    listener.pause()
    return listener.message

def resume(name):
    listener = LISTENERS.get(name, "")
    if not listener:
        return printer.warning(f"Listener {name} not found")
    listener.resume()
    return listener.message

def close(name):
    listener = LISTENERS.get(name, "")
    if not listener:
        return printer.warning(f"Listener {name} not found")
    listener.close()
    return listener.message