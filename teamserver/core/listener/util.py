from core.utils import common, log

printer = common.Print_str()

LISTENERS = {}

def pause(name):
    listener = LISTENERS.get(name, "")
    if not listener:
        return printer.warning(f"Listener {name} not found")
    listener.pause()

    log.info(listener.message)
    return listener.message

def resume(name):
    listener = LISTENERS.get(name, "")
    if not listener:
        return printer.warning(f"Listener {name} not found")
    listener.resume()
    
    log.info(listener.message)
    return listener.message

def close(name):
    listener = LISTENERS.get(name, "")
    if not listener:
        return printer.warning(f"Listener {name} not found")
    listener.close()

    log.info(listener.message)
    return listener.message