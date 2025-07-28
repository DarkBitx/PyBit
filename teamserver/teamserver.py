# Developed by DarkBit — © 2025
# Follow for updates: https://t.me/DarkBitx
    
from core.utils import common, config
from core.server import core
from core.server.commands import status

def main():
    
    print(common.banner())
    
    server = core.Server()
    server.run()

if __name__ == '__main__':
    main()
        