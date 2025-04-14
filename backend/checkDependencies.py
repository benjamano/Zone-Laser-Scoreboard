import subprocess
import sys

class start:
    def __init__(self):
        self.install(["flask", "flask_sqlalchemy", "waitress", "scapy", "flask_socketio", "threading", "eventlet", 
                     "winrt.windows.media.control", "pillow", "pyshark", "manuf", "pystray", "requests", "pyautogui",
                     "datetime", "psutil", "tkinter", "logging", "signal", "time", "flask_cors", "dmx", "serial",
                     "PyDMXControl", "socket", "webbrowser", "pyaudio", "sounddevice", "numpy", "spotipy", "winsdk",
                     "asyncio", "obsws_python", "winrt.windows.foundation", "json", "flask_migrate", "pythonnet", "smtplib"])
        
        #librosa
        
    def install(self, libraryNames):
        for libraryName in libraryNames:
            try:
                print("|----------------------------------------------------------------------------------------------|")
                print(f"Trying to import '{libraryName}'")
                __import__(libraryName)
            except ImportError:
                print(f"Package '{libraryName}' not found. Installing...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", libraryName])
            finally:
                try:
                    globals()[libraryName] = __import__(libraryName)
                except ImportError:
                    print(f"Package '{libraryName}' could not be imported.")
                    pass
                print(f"Package '{libraryName}' is now installed and imported.")
