import subprocess
import sys
import importlib

class VerifyDependencies:
    def __init__(self):
        self.packages = {
            "flask": "flask",
            "flask_sqlalchemy": "flask_sqlalchemy",
            "waitress": "waitress",
            "scapy": "scapy",
            "flask_socketio": "flask_socketio",
            "threading": "threading",
            "eventlet": "eventlet",
            "winrt.windows.media.control": "winrt.windows.media.control",
            "pillow": "PIL",
            "pyshark": "pyshark",
            "manuf": "manuf",
            "pystray": "pystray",
            "requests": "requests",
            "pyautogui": "pyautogui",
            "datetime": "datetime",
            "psutil": "psutil",
            "tkinter": "tkinter",
            "logging": "logging",
            "signal": "signal",
            "time": "time",
            "flask_cors": "flask_cors",
            "dmx": "dmx",
            "pyserial": "serial",
            "PyDMXControl": "PyDMXControl",
            "socket": "socket",
            "webbrowser": "webbrowser",
            "pyaudio": "pyaudio",
            "sounddevice": "sounddevice",
            "numpy": "numpy",
            "spotipy": "spotipy",
            "winsdk": "winsdk",
            "asyncio": "asyncio",
            "obsws_python": "obsws_python",
            "winrt.windows.foundation": "winrt.windows.foundation",
            "json": "json",
            "flask_migrate": "flask_migrate",
            "pythonnet": "clr",
            "smtplib": "smtplib",
            "python-dotenv": "dotenv",
            "pygetwindow": "pygetwindow",
            "GPUtil": "GPUtil",
            "setuptools": "setuptools",
            "pygetwindow": "pygetwindow",
            "pywin32": "win32gui",
            # NEED TO RESTART WHEN THIS IS DONE
            "win32gui": "win32gui",
            "win32con": "win32con",
            "win32com.client": "win32com.client",
            "pythoncom": "pythoncom",
        }
        self.installAll()

    def installAll(self):
        for pip_name, import_name in self.packages.items():
            line = f" Checking '{pip_name}' "
            border = "|" + line.center(78, "-") + "|"
            print(border)
            if not self.tryImport(import_name):
                self.installPackage(pip_name)
                if not self.tryImport(import_name):
                    print(f"Couldn't import '{import_name}' after installing '{pip_name}'")

    def tryImport(self, name):
        try:
            importlib.import_module(name)
            # print(f"Successfully imported '{name}'")
            return True
        except ImportError:
            print(f"Import failed: '{name}'")
            return False

    def installPackage(self, pipName):
        print(f"Installing '{pipName}' via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pipName])
        if pipName == "pywin32":
            raise "Please restart your computer to complete the installation of the dependancies.\nINFO: The Library 'Pywin32' requires the PC to be restarted before it's changes come into effect."