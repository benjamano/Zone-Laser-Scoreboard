import subprocess
import sys

class start:
    def __init__(self):
        self.install(["flask"])
        self.install(["flask_sqlalchemy"])
        self.install(["waitress"])
        self.install(["scapy"])
        self.install(["flask_socketio"])
        self.install(["threading"])
        self.install(["eventlet"])
        self.install(["eventlet", "eventlet.wsgi", "pyshark", "manuf","pystray","requests","ctypes","pywin32","pypiwin32"]) 
        
    def install(self, LibaryNames):
        for LibaryName in LibaryNames:
            try:
                print("|----------------------------------------------------------------------------------------------|")
                
                print(f"Trying to import '{LibaryName}'")
                __import__(LibaryName)
            except ImportError:
                            
                print(f"Package '{LibaryName}' not found. Installing...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", LibaryName])
                            
            finally:
                globals()[LibaryName] = __import__(LibaryName)
                print(f"Package '{LibaryName}' is now installed and imported.")
            
