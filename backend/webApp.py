import threading
import time
import eventlet
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import os
import signal
import ctypes
import datetime
import pyautogui
import obsws_python as obs
from scapy.all import sniff, conf, IP
from flask_cors import CORS
import requests
import psutil
import socket
import webbrowser
import asyncio
import random
import sys

try:
    import winrt.windows.media.control as wmc
except ImportError:
    print("Failed to import winrt.windows.media.control")

try:
    from func import format
    print("Imported functions") 
except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")
        
from func.BPM import MediaBPMFetcher
    
import logging

db = SQLAlchemy()

class WebApp:
    def __init__(self):
        self.app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Scoreboard.db'
        self.app.secret_key = 'SJ8SU0D2987G887vf76g87whgd87qwgs87G78GF987EWGF87GF897GH8'
        
        self.expecteProcesses = ["Spotify.exe", "obs64"]
        
        # self.goboModes = ["SpinningAll", "Static", "Stacked"]
        # self.colourModes  = ["BPM", "Static", "Rainbow"]
        # self.panTiltModes  = ["Crazy", "Normal", "Slow"]
            
        db.init_app(self.app)
        
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self._dir = os.path.dirname(os.path.realpath(__file__))

        self.OBSConnected = False
        self.devMode = "false"
        self.filesOpened = False
        self.spotifyControl = True
        self.DMXConnected = False
        self.spotifyStatus = "paused"
        self._localIp = ""
        self.rateLimit = False
        self.RestartRequested = False
        self.gameStatus = "stopped" #Either running or stopped
        self.endOfDay = False
        
        pyautogui.FAILSAFE = False

        format.message(f"Starting Web App at {str(datetime.datetime.now())}", type="warning")
        
        
        self._fixtureProfiles = {
            "Dimmer": {
                "Dimmer": list(range(0, 255)),
            },
            "Colorspot575XT": {
                "Pan": list(range(0, 255)),
                "Tilt": list(range(0, 255)),
                "Pan Fine": list(range(0, 255)),
                "Tilt Fine": list(range(0, 255)),
                "PanTilt Speed": {},
                "FanLamp Control": {},
                "Colour 1": {
                "White": 0,
                "Light blue": 13,
                "Red": 26,
                "Blue": 38,
                "Light green": 51,
                "Yellow": 64,
                "Magenta": 77,
                "Cyan": 90,
                "Green": 102,
                "Orange": 115,
                "Rainbow": list(range(128, 255)),
                },
                "Colour 2": {
                "White": 0,
                "Deep Red": 12,
                "Deep Blue": 24,
                "Pink": 36,
                "Cyan": 48,
                "Magenta": 60,
                "Yellow": 72,
                "5600K Filter": 84,
                "3200K Filter": 96,
                "UV": 108
                },
                "Prism": {
                "Open": 0,
                "Rotation": list(range(1, 127)),
                },
                "Macros": {},
                "Gobos": {
                "Open": list(range(0, 7)),
                "1": list(range(8, 15)), 
                "2": list(range(16, 23)), 
                "3": list(range(24, 31)), 
                "4": list(range(32, 39)), 
                "5": list(range(40, 47)), 
                "6": list(range(48, 55)), 
                "7": list(range(56, 63)), 
                "8": list(range(64, 71)), 
                "9": list(range(72, 79)), 
                "1 Shaking": list(range(80, 95)), 
                "2 Shaking": list(range(96, 111)), 
                "3 Shaking": list(range(112, 127)), 
                "4 Shaking": list(range(128, 143)), 
                "5 Shaking": list(range(144, 159)), 
                "6 Shaking": list(range(160, 175)), 
                "7 Shaking": list(range(176, 191)), 
                "8 Shaking": list(range(192, 207)), 
                "9 Shaking": list(range(208, 223)), 
                "Rotation Slow Fast": list(range(224, 255)), 
                },
                "Rotating Gobos": {    
                "Open": list(range(0, 31)),
                "1": list(range(32, 63)), 
                "2": list(range(64, 95)), 
                "3": list(range(96, 127)), 
                "4": list(range(128, 159)), 
                "5": list(range(160, 191)), 
                "6": list(range(192, 223)), 
                "Rotation Slow Fast": list(range(224, 255)), 
                },
                "Rotation Speed": {
                "Indexing": list(range(0, 127)),    
                "Rotation": list(range(128, 255)),    
                },
                "Iris": {
                "Open": 0,
                "MaxToMin": list(range(1, 179)),   
                "Closed": list(range(180, 191)),   
                "Pulse Close Slow Fast": list(range(192, 223)),   
                "Pulse Open Fast Slow": list(range(224, 225)),   
                },
                "Focus": list(range(0, 255)),
                "Strobe / Shutter": {
                "Closed": list(range(0, 32)),   
                "Open": list(range(32, 63)),   
                "Strobe Slow Fast": list(range(64, 95)),   
                "Pulse Slow Fast": list(range(128, 159)),   
                "Random Slow Fast": list(range(192, 223)),   
                },
                "Dimmer": list(range(0, 255)),
            },
            "Colorspot250AT": {
                "Pan": list(range(0, 255)),
                "Pan Fine": list(range(0, 255)),
                "Tilt": list(range(0, 255)),
                "Tilt Fine": list(range(0, 255)),
                "PanTilt Speed": {
                "Max": 0,
                "Speed": list(range(1, 255)),
                },
                "Special Functions": {},
                "PanTilt Macros": {},
                "PanTilt Macros Speed": {},
                "Colour 1": {
                "White": 0,
                "Dark green": 11,
                "Red": 23,
                "Light azure": 34,
                "Magenta": 46,
                "UV filter": 58,
                "Yellow": 70,
                "Green": 81,
                "Pink": 93,
                "Blue": 105,
                "Deep red": 117,
                "Rotation": list(range(190, 243)),
                "Audio": list(range(224, 249)),
                "Random Fast Slow": list(range(250, 255)),
                },
                "Colour Fine Position": list(range(0, 255)),
                "Spinning Gobos": {
                "Open": list(range(0, 3)),
                "1": list(range(4, 7)),   
                "2": list(range(8, 11)),   
                "3": list(range(12, 15)),   
                "4": list(range(16, 19)),   
                "5": list(range(20, 23)),   
                "6": list(range(24, 27)),   
                "7": list(range(28, 31)),   
                "1 Rotating": list(range(32, 35)),
                "2 Rotating": list(range(36, 39)),
                "3 Rotating": list(range(40, 43)),
                "4 Rotating": list(range(44, 47)),
                "5 Rotating": list(range(48, 51)),
                "6 Rotating": list(range(52, 55)),
                "7 Rotating": list(range(56, 59)),
                "1 Shaking Slow Fast": list(range(60, 69)),
                "2 Shaking Slow Fast": list(range(70, 79)),
                "3 Shaking Slow Fast": list(range(80, 89)),
                "4 Shaking Slow Fast": list(range(90, 99)),
                "5 Shaking Slow Fast": list(range(100, 109)),
                "6 Shaking Slow Fast": list(range(110, 119)),
                "7 Shaking Slow Fast": list(range(120, 139)),
                "1 Shaking Fast Slow": list(range(130, 139)),
                "2 Shaking Fast Slow": list(range(140, 149)),
                "3 Shaking Fast Slow": list(range(150, 159)),
                "4 Shaking Fast Slow": list(range(160, 169)),
                "5 Shaking Fast Slow": list(range(170, 179)),
                "6 Shaking Fast Slow": list(range(180, 189)),
                "7 Shaking Fast Slow": list(range(190, 199)),
                "Rotation": list(range(202, 243)),
                "Audio": list(range(244, 249)),
                "Random Fast Slow": list(range(250, 255)),
                },
                "Rotating Gobos": {
                "No Rotation": 0,
                "Rotation": list(range(1, 255)),  
                },
                "Gobo Fine Position": list(range(0, 255)),
                "Prism": {
                "Open position (hole)": list(range(0, 19)),
                "3-facet": list(range(20, 159)),
                "Macro 1": list(range(160, 167)),
                "Macro 2": list(range(168, 175)),
                "Macro 3": list(range(176, 183)),
                "Macro 4": list(range(184, 191)),
                "Macro 5": list(range(192, 199)),
                "Macro 6": list(range(200, 207)),
                "Macro 7": list(range(208, 215)),
                "Macro 8": list(range(216, 223)),
                "Macro 9": list(range(224, 231)),
                "Macro 10": list(range(232, 239)),
                "Macro 11": list(range(240, 247)),
                "Macro 12": list(range(248, 255)),
                },
                "Prism Rotation": {
                "No Rotation": 0,
                "Rotation": list(range(1, 255)), 
                },
                "Focus": list(range(1, 255)),
                "Focus Fine": list(range(1, 255)),
                "StrobeShutter": {
                "Closed": list(range(0, 31)),
                "Open": list(range(32, 63)),
                "Strobe Slow Fast": list(range(64, 95)),
                "Pulse Slow Fast": list(range(128, 143)),
                "Pulse Fast Slow": list(range(144, 159)),
                "Random Slow Fast": list(range(192, 223)),
                },
                "Dimmer": list(range(0, 255)),
                "DimmerFine": list(range(0, 255)),
            },
            "Colorwash250AT": {
                "Pan": list(range(0, 255)),
                "Pan Fine": list(range(0, 255)),
                "Tilt": list(range(0, 255)),
                "Tilt Fine": list(range(0, 255)),
                "PanTilt Speed": {
                "Max": 0,
                "Speed": list(range(1, 255)),
                },
                "Special Functions": {},
                "PanTilt Macros": {},
                "PanTilt Macros Speed": {},
                "Colour 1": {
                "White": 0,
                "Red": 18,
                "Blue": 36,
                "Green": 54,
                "3200K Filter": 72,
                "6000K Filter": 90,
                "UV": list(range(190, 243)),
                "Audio": list(range(244, 249)),
                "Random Fast Slow": list(range(250, 255)),
                },
                "Colour Fine Position": list(range(0, 255)),
                "Cyan": list(range(0, 255)),
                "Magenta": list(range(0, 255)),
                "Yellow": list(range(0, 255)),
                "CMYDimmerSpeed": list(range(0, 255)),
                "CMYMacros": {
                "Open": list(range(0, 7)),
                "Rainbow Fast Slow": list(range(240, 243)),
                "Audio": list(range(244, 249)),
                "Random Fast Slow": list(range(250, 255)),
                },
                "EffectWheel": {
                "Open": list(range(0, 70)),  
                "Beam Shaper": list(range(71, 179)),  
                "Swivelling Slow Fast": list(range(180, 199)),  
                "Frost": list(range(200, 255)),  
                },
                "Zoom": list(range(0, 255)),
                "StrobeShutter": {},
                "StrobeShutter": {
                "Closed": list(range(0, 31)),
                "Open": list(range(32, 63)),
                "Strobe Slow Fast": list(range(64, 95)),
                "Opening Pulse Slow Fast": list(range(128, 143)),
                "Closing Pulse Fast Slow": list(range(144, 159)),
                "Random": list(range(192, 223)),
                },
                "Dimmer": list(range(0, 255)),
                "DimmerFine": list(range(0, 255)),
            }
        }
        
        self.fixtures = {}
        
        self.fixtures["ColorSpot"] = {"type": "Colorspot575XT"}
        self.fixtures["BulkHeads"] = {"type": "Dimmer"}
        
        self.initLogging()
        self.socketio.init_app(self.app, cors_allowed_origins="*") 
        self.openFiles()
        
        self.setupRoutes()
        
        with self.app.app_context():
            db.create_all()
            self.seedDBData() 

    # -----------------| Starting Tasks |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
    
    def startFlask(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((self._localIp, 8080)) == 0:
                    format.message(f"Port 8080 is already in use on {self._localIp}", type="error")
                    raise RuntimeError("Port in use. Exiting application.")

            self.socketio.run(self.app, host=self._localIp, port=8080)
        except Exception as e:
            os._exit(1)
        
    def start(self):
        format.newline()    
        
        try:
            # Create a dummy socket connection to find the local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self._localIp = s.getsockname()[0]
            s.close()
        except Exception as e:
            format.message(f"Error finding local IP: {e}")
            
        format.message("Attempting to start Media status checker")
        
        try:
            self.mediaStatusCheckerThread = threading.Thread(target=self.mediaStatusChecker)
            self.mediaStatusCheckerThread.daemon = True
            self.mediaStatusCheckerThread.start()
            
        except Exception as e:
            format.message(f"Error starting Flask Server: {e}", type="error")
            
        format.message("Attempting to start Flask Server")
        
        try:
            self.flaskThread = threading.Thread(target=self.startFlask)
            self.flaskThread.daemon = True
            self.flaskThread.start()
            
        except Exception as e:
            format.message(f"Error starting Flask Server: {e}", type="error")

        format.message(f"Web App hosted on IP {self._localIp}", type="success")
        
        if self.devMode == "false":
            webbrowser.open(f"http://{self._localIp}:8080")
            
        try:
            self.obs_thread = threading.Thread(target=self.obs_connect)
            self.obs_thread.daemon = True
            self.obs_thread.start()
            
        except Exception as e:
            format.message(f"Error starting OBS Connection: {e}", type="error")
            
        try:
            self.DMXThread = threading.Thread(target=self.setUpDMX)
            self.DMXThread.daemon = True
            self.DMXThread.start()
            
        except Exception as e:
            format.message(f"Error starting DMX Connection: {e}", type="error")

        format.message("Web App Started, hiding console", type="success")
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
        try:
            self.sniffing_thread = threading.Thread(target=self.startSniffing)
            self.sniffing_thread.daemon = True
            self.sniffing_thread.start()
            
        except Exception as e:
            format.message(f"Error starting packet sniffer: {e}", type="error")
        
        if self.devMode == "false":
            self.process_checker_thread = threading.Thread(target=self.runProcessChecker)
            self.process_checker_thread.daemon = True
            self.process_checker_thread.start()
        
        format.message("Attempting to start BPM finder")
        
        self.flaskThread.join()
        
        format.newline()    

    def initLogging(self):
        #self.app.logger.disabled = True
        #logging.getLogger('werkzeug').disabled = True
        return
    
    def setUpDMX(self):
        #Requires USB to DMX with driver version of "libusb-win32"
        
        try:
            format.message("Setting up DMX Connection")
        
            from PyDMXControl.controllers import OpenDMXController

            from PyDMXControl.profiles.Generic import Dimmer

            self._dmx = OpenDMXController()
            
            self.fixtures = {}
            self._fixtureProfiles = {
                "Dimmer": {
                    "Dimmer": list(range(0, 255)),
                },
                "Colorspot575XT": {
                    "Pan": list(range(0, 255)),
                    "Tilt": list(range(0, 255)),
                    "Pan Fine": list(range(0, 255)),
                    "Tilt Fine": list(range(0, 255)),
                    "PanTilt Speed": {},
                    "FanLamp Control": {},
                    "Colour 1": {
                        "White": 0,
                        "Light blue": 13,
                        "Red": 26,
                        "Blue": 38,
                        "Light green": 51,
                        "Yellow": 64,
                        "Magenta": 77,
                        "Cyan": 90,
                        "Green": 102,
                        "Orange": 115,
                        "Rainbow": list(range(128, 255)),
                    },
                    "Colour 2": {
                        "White": 0,
                        "Deep Red": 12,
                        "Deep Blue": 24,
                        "Pink": 36,
                        "Cyan": 48,
                        "Magenta": 60,
                        "Yellow": 72,
                        "5600K Filter": 84,
                        "3200K Filter": 96,
                        "UV": 108
                    },
                    "Prism": {
                        "Open": 0,
                        "Rotation": list(range(1, 127)),
                    },
                    "Macros": {},
                    "Gobos": {
                        "Open": list(range(0, 7)),
                        "1": list(range(8, 15)), 
                        "2": list(range(16, 23)), 
                        "3": list(range(24, 31)), 
                        "4": list(range(32, 39)), 
                        "5": list(range(40, 47)), 
                        "6": list(range(48, 55)), 
                        "7": list(range(56, 63)), 
                        "8": list(range(64, 71)), 
                        "9": list(range(72, 79)), 
                        "1 Shaking": list(range(80, 95)), 
                        "2 Shaking": list(range(96, 111)), 
                        "3 Shaking": list(range(112, 127)), 
                        "4 Shaking": list(range(128, 143)), 
                        "5 Shaking": list(range(144, 159)), 
                        "6 Shaking": list(range(160, 175)), 
                        "7 Shaking": list(range(176, 191)), 
                        "8 Shaking": list(range(192, 207)), 
                        "9 Shaking": list(range(208, 223)), 
                        "Rotation Slow Fast": list(range(224, 255)), 
                    },
                    "Rotating Gobos": {    
                        "Open": list(range(0, 31)),
                        "1": list(range(32, 63)), 
                        "2": list(range(64, 95)), 
                        "3": list(range(96, 127)), 
                        "4": list(range(128, 159)), 
                        "5": list(range(160, 191)), 
                        "6": list(range(192, 223)), 
                        "Rotation Slow Fast": list(range(224, 255)), 
                    },
                    "Rotation Speed": {
                        "Indexing": list(range(0, 127)),    
                        "Rotation": list(range(128, 255)),    
                    },
                    "Iris": {
                        "Open": 0,
                        "MaxToMin": list(range(1, 179)),   
                        "Closed": list(range(180, 191)),   
                        "Pulse Close Slow Fast": list(range(192, 223)),   
                        "Pulse Open Fast Slow": list(range(224, 225)),   
                    },
                    "Focus": {list(range(0, 255))},
                    "Strobe / Shutter": {
                        "Closed": list(range(0, 32)),   
                        "Open": list(range(32, 63)),   
                        "Strobe Slow Fast": list(range(64, 95)),   
                        "Pulse Slow Fast": list(range(128, 159)),   
                        "Random Slow Fast": list(range(192, 223)),   
                    },
                    "Dimmer": {list(range(0, 255))},
                },
                "Colorspot250AT": {
                    "Pan": {list(range(0, 255))},
                    "Pan Fine": {list(range(0, 255))},
                    "Tilt": {list(range(0, 255))},
                    "Tilt Fine": {list(range(0, 255))},
                    "PanTilt Speed": {
                        "Max": 0,
                        "Speed": list(range(1, 255)),
                    },
                    "Special Functions": {},
                    "PanTilt Macros": {},
                    "PanTilt Macros Speed": {},
                    "Colour 1": {
                        "White": 0,
                        "Dark green": 11,
                        "Red": 23,
                        "Light azure": 34,
                        "Magenta": 46,
                        "UV filter": 58,
                        "Yellow": 70,
                        "Green": 81,
                        "Pink": 93,
                        "Blue": 105,
                        "Deep red": 117,
                        "Rotation": list(range(190, 243)),
                        "Audio": list(range(224, 249)),
                        "Random Fast Slow": list(range(250, 255)),
                    },
                    "Colour Fine Position": list(range(0, 255)),
                    "Spinning Gobos": {
                        "Open": list(range(0, 3)),
                        "1": list(range(4, 7)),   
                        "2": list(range(8, 11)),   
                        "3": list(range(12, 15)),   
                        "4": list(range(16, 19)),   
                        "5": list(range(20, 23)),   
                        "6": list(range(24, 27)),   
                        "7": list(range(28, 31)),   
                        "1 Rotating": list(range(32, 35)),
                        "2 Rotating": list(range(36, 39)),
                        "3 Rotating": list(range(40, 43)),
                        "4 Rotating": list(range(44, 47)),
                        "5 Rotating": list(range(48, 51)),
                        "6 Rotating": list(range(52, 55)),
                        "7 Rotating": list(range(56, 59)),
                        "1 Shaking Slow Fast": list(range(60, 69)),
                        "2 Shaking Slow Fast": list(range(70, 79)),
                        "3 Shaking Slow Fast": list(range(80, 89)),
                        "4 Shaking Slow Fast": list(range(90, 99)),
                        "5 Shaking Slow Fast": list(range(100, 109)),
                        "6 Shaking Slow Fast": list(range(110, 119)),
                        "7 Shaking Slow Fast": list(range(120, 139)),
                        "1 Shaking Fast Slow": list(range(130, 139)),
                        "2 Shaking Fast Slow": list(range(140, 149)),
                        "3 Shaking Fast Slow": list(range(150, 159)),
                        "4 Shaking Fast Slow": list(range(160, 169)),
                        "5 Shaking Fast Slow": list(range(170, 179)),
                        "6 Shaking Fast Slow": list(range(180, 189)),
                        "7 Shaking Fast Slow": list(range(190, 199)),
                        "Rotation": list(range(202, 243)),
                        "Audio": list(range(244, 249)),
                        "Random Fast Slow": list(range(250, 255)),
                    },
                    "Rotating Gobos": {
                        "No Rotation": 0,
                        "Rotation": list(range(1, 255)),  
                    },
                    "Gobo Fine Position": list(range(0, 255)),
                    "Prism": {
                        "Open position (hole)": list(range(0, 19)),
                        "3-facet": list(range(20, 159)),
                        "Macro 1": list(range(160, 167)),
                        "Macro 2": list(range(168, 175)),
                        "Macro 3": list(range(176, 183)),
                        "Macro 4": list(range(184, 191)),
                        "Macro 5": list(range(192, 199)),
                        "Macro 6": list(range(200, 207)),
                        "Macro 7": list(range(208, 215)),
                        "Macro 8": list(range(216, 223)),
                        "Macro 9": list(range(224, 231)),
                        "Macro 10": list(range(232, 239)),
                        "Macro 11": list(range(240, 247)),
                        "Macro 12": list(range(248, 255)),
                    },
                    "Prism Rotation": {
                        "No Rotation": 0,
                        "Rotation": list(range(1, 255)), 
                    },
                    "Focus": {list(range(1, 255))},
                    "Focus Fine": {list(range(1, 255))},
                    "StrobeShutter": {
                        "Closed": list(range(0, 31)),
                        "Open": list(range(32, 63)),
                        "Strobe Slow Fast": list(range(64, 95)),
                        "Pulse Slow Fast": list(range(128, 143)),
                        "Pulse Fast Slow": list(range(144, 159)),
                        "Random Slow Fast": list(range(192, 223)),
                    },
                    "Dimmer": {list(range(0, 255))},
                    "DimmerFine": {list(range(0, 255))},
                },
                "Colorwash250AT": {
                    "Pan": {{list(range(0, 255))}},
                    "Pan Fine": {{list(range(0, 255))}},
                    "Tilt": {{list(range(0, 255))}},
                    "Tilt Fine": {{list(range(0, 255))}},
                    "PanTilt Speed": {
                        "Max": 0,
                        "Speed": {list(range(1, 255))},},
                    "Special Functions": {},
                    "PanTilt Macros": {},
                    "PanTilt Macros Speed": {},
                    "Colour 1": {
                        "White": 0,
                        "Red": 18,
                        "Blue": 36,
                        "Green": 54,
                        "3200K Filter": 72,
                        "6000K Filter": 90,
                        "UV": list(range(190, 243)),
                        "Audio": list(range(244, 249)),
                        "Random Fast Slow": list(range(250, 255)),
                    },
                    "Colour Fine Position": {list(range(0, 255))},
                    "Cyan": {{list(range(0, 255))}},
                    "Magenta": {{list(range(0, 255))}},
                    "Yellow": {{list(range(0, 255))}},
                    "CMYDimmerSpeed": {{list(range(0, 255))}},
                    "CMYMacros": {
                        "Open": list(range(0, 7)),
                        "Rainbow Fast Slow": {{list(range(240, 243))}},
                        "Audio": {{list(range(244, 249))}},
                        "Random Fast Slow": {{list(range(250, 255))}},
                    },
                    "EffectWheel": {
                    "Open": list(range(0, 70)),  
                    "Beam Shaper": list(range(71, 179)),  
                    "Swivelling Slow Fast": list(range(180, 199)),  
                    "Frost": list(range(200, 255)),  
                    },
                    "Zoom": {list(range(0, 255))},
                    "StrobeShutter": {},
                    "StrobeShutter": {
                        "Closed": list(range(0, 31)),
                        "Open": list(range(32, 63)),
                        "Strobe Slow Fast": list(range(64, 95)),
                        "Opening Pulse Slow Fast": list(range(128, 143)),
                        "Closing Pulse Fast Slow": list(range(144, 159)),
                        "Random": list(range(192, 223)),
                    },
                    "Dimmer": {list(range(0, 255))},
                    "DimmerFine": {list(range(0, 255))},
                }
            }
            
            #try:
                #self._dmx.web_control()
                
            #except Exception as e:
                #format.message(f"Error starting DMX web control: {e}", type="error")
        
            try:
                format.message("Registering Red Bulk-Head Lights", type="info")
                self._DimmerBulkHeadLights = self._dmx.add_fixture(Dimmer, name="DimmerBulkHeadLights")
                
                self._DimmerBulkHeadLights._register_channel(f"{fixtureName}_Dimmer")
                
                self.fixtures[self._DimmerBulkHeadLights.name] = {"type": "Dimmer"}
                
            except Exception as e:
                format.message(f"Error registering Red Bulk-Head Lights: {e}", type="error")
                
            try:
                format.message("Registering Robe Colorspot 575 XT 0", type="info")
                self._Colorspot575XT_0 = self._dmx.add_fixture(Dimmer, name="Colorspot575XT_0")
                
                with self._Colorspot575XT_0 as light:
                    
                    fixtureName = light.name
                
                    light._register_channel(f"{fixtureName}_Pan")
                    light._register_channel(f"{fixtureName}_Tilt")
                    light._register_channel(f"{fixtureName}_Pan Fine")
                    light._register_channel(f"{fixtureName}_Tilt Fine")
                    light._register_channel(f"{fixtureName}_PanTilt Speed")
                    light._register_channel(f"{fixtureName}_FanLamp Control")
                    light._register_channel(f"{fixtureName}_Colour 1")
                    light._register_channel(f"{fixtureName}_Colour 2")
                    light._register_channel(f"{fixtureName}_Prism")
                    light._register_channel(f"{fixtureName}_Macros")
                    light._register_channel(f"{fixtureName}_Static Gobos")
                    light._register_channel(f"{fixtureName}_Rotating Gobos")
                    light._register_channel(f"{fixtureName}_Gobo Rotation Speed")
                    light._register_channel(f"{fixtureName}_Iris")
                    light._register_channel(f"{fixtureName}_Focus")
                    light._register_channel(f"{fixtureName}_Strobe / Shutter")
                    light._register_channel(f"{fixtureName}_Dimmer")
                    
                    self.fixtures[light.name] = {"type": "Colorspot575XT"}
                    
                    # Set to red for testing
                    light.set_channel(f"{fixtureName}_Colour 1", self._fixtureProfiles[f"{self.fixtures[light.name]["type"]}"]["Colour 1"]["Red"])
                    
            except Exception as e:
                format.message(f"Error registering Robe Colorspot 575 XT 0: {e}", type="error")
                
            try:
                format.message("Registering Robe Colorspot 575 XT 1", type="info")
                self._Colorspot575XT_1 = self._dmx.add_fixture(Dimmer, name="Colorspot575XT_1")
                
                # LIGHT MUST BE IN MODE 1
                
                with self._Colorspot575XT_1 as light:
                    
                    fixtureName = light.name
                
                    light._register_channel(f"{fixtureName}_Pan")
                    light._register_channel(f"{fixtureName}_Tilt")
                    light._register_channel(f"{fixtureName}_Pan Fine")
                    light._register_channel(f"{fixtureName}_Tilt Fine")
                    light._register_channel(f"{fixtureName}_PanTilt Speed")
                    light._register_channel(f"{fixtureName}_FanLamp Control")
                    light._register_channel(f"{fixtureName}_Colour 1")
                    light._register_channel(f"{fixtureName}_Colour 2")
                    light._register_channel(f"{fixtureName}_Prism")
                    light._register_channel(f"{fixtureName}_Macros")
                    light._register_channel(f"{fixtureName}_Static Gobos")
                    light._register_channel(f"{fixtureName}_Rotating Gobos")
                    light._register_channel(f"{fixtureName}_Gobo Rotation Speed")
                    light._register_channel(f"{fixtureName}_Iris")
                    light._register_channel(f"{fixtureName}_Focus")
                    light._register_channel(f"{fixtureName}_StrobeShutter")
                    light._register_channel(f"{fixtureName}_Dimmer")
                    
                    self.fixtures[light.name] = {"type": "Colorspot575XT"}
                    
                    # Set to orange for testing
                    light.set_channel(f"{fixtureName}_Colour 1", self._fixtureProfiles[f"{self.fixtures[light.name]["type"]}"]["Colour 1"]["Orange"])

            except Exception as e:
                format.message(f"Error registering Robe Colorspot 575 XT 1: {e}", type="error")
                
            try:
                format.message("Registering Robe Colorspot 250 AT 0", type="info")
                self._Colorspot250AT_0 = self._dmx.add_fixture(Dimmer, name="Colorspot250AT_0")
                
                # LIGHT MUST BE IN MODE 3
                
                with self._Colorspot250AT_0 as light:
                    
                    fixtureName = light.name
                
                    light._register_channel(f"{fixtureName}_Pan")
                    light._register_channel(f"{fixtureName}_Pan Fine")
                    light._register_channel(f"{fixtureName}_Tilt")
                    light._register_channel(f"{fixtureName}_Tilt Fine")
                    light._register_channel(f"{fixtureName}_PanTilt Speed")
                    light._register_channel(f"{fixtureName}_Special Functions")
                    light._register_channel(f"{fixtureName}_PanTilt Macros")
                    light._register_channel(f"{fixtureName}_PanTilt Macros Speed")
                    light._register_channel(f"{fixtureName}_Colour 1")
                    light._register_channel(f"{fixtureName}_Colour Fine Position")
                    light._register_channel(f"{fixtureName}_Spinning Gobos")
                    light._register_channel(f"{fixtureName}_Rotating Gobos")
                    light._register_channel(f"{fixtureName}_Gobo Fine Position")
                    light._register_channel(f"{fixtureName}_Prism")
                    light._register_channel(f"{fixtureName}_Prism Rotation")
                    light._register_channel(f"{fixtureName}_Focus")
                    light._register_channel(f"{fixtureName}_Focus Fine")
                    light._register_channel(f"{fixtureName}_StrobeShutter")
                    light._register_channel(f"{fixtureName}_Dimmer")
                    light._register_channel(f"{fixtureName}_DimmerFine")
                    
                    self.fixtures[light.name] = {"type": "Colorspot250AT"}
                    
                    # Set to pink for testing
                    light.set_channel(f"{fixtureName}_Colour 1", self._fixtureProfiles[f"{self.fixtures[light.name]["type"]}"]["Colour 1"]["Pink"])

            except Exception as e:
                format.message(f"Error registering Robe Colorspot 250 AT 0: {e}", type="error")
                
            try:
                format.message("Registering Robe Colorspot 250 AT 1", type="info")
                self._Colorspot250AT_1 = self._dmx.add_fixture(Dimmer, name="Colorspot250AT_1")
                
                # LIGHT MUST BE IN MODE 3
                
                with self._Colorspot250AT_1 as light:
                    
                    fixtureName = light.name
                
                    light._register_channel(f"{fixtureName}_Pan")
                    light._register_channel(f"{fixtureName}_Pan Fine")
                    light._register_channel(f"{fixtureName}_Tilt")
                    light._register_channel(f"{fixtureName}_Tilt Fine")
                    light._register_channel(f"{fixtureName}_PanTilt Speed")
                    light._register_channel(f"{fixtureName}_Special Functions")
                    light._register_channel(f"{fixtureName}_PanTilt Macros")
                    light._register_channel(f"{fixtureName}_PanTilt Macros Speed")
                    light._register_channel(f"{fixtureName}_Colour 1")
                    light._register_channel(f"{fixtureName}_Colour Fine Position")
                    light._register_channel(f"{fixtureName}_Spinning Gobos")
                    light._register_channel(f"{fixtureName}_Rotating Gobos")
                    light._register_channel(f"{fixtureName}_Gobo Fine Position")
                    light._register_channel(f"{fixtureName}_Prism")
                    light._register_channel(f"{fixtureName}_Prism Rotation")
                    light._register_channel(f"{fixtureName}_Focus")
                    light._register_channel(f"{fixtureName}_Focus Fine")
                    light._register_channel(f"{fixtureName}_StrobeShutter")
                    light._register_channel(f"{fixtureName}_Dimmer")
                    light._register_channel(f"{fixtureName}_DimmerFine")
                    
                    self.fixtures[light.name] = {"type": "Colorspot250AT"}
                    
                    # Set to magenta for testing
                    light.set_channel(f"{fixtureName}_Colour 1", self._fixtureProfiles[f"{self.fixtures[light.name]["type"]}"]["Colour 1"]["Magenta"])
                    
            except Exception as e:
                format.message(f"Error registering Robe Colorspot 250 AT 1: {e}", type="error")
        
            try:
                format.message("Registering Robe Colorwash 250 AT 0", type="info")
                self._Colorwash250AT_0 = self._dmx.add_fixture(Dimmer, name="Colorwash250AT_0")
                
                # LIGHT MUST BE IN MODE 3
                
                with self._Colorwash250AT_0 as light:
                    
                    fixtureName = light.name
                
                    light._register_channel(f"{fixtureName}_Pan")
                    light._register_channel(f"{fixtureName}_Pan Fine")
                    light._register_channel(f"{fixtureName}_Tilt")
                    light._register_channel(f"{fixtureName}_Tilt Fine")
                    light._register_channel(f"{fixtureName}_PanTilt Speed")
                    light._register_channel(f"{fixtureName}_Special Functions")
                    light._register_channel(f"{fixtureName}_PanTilt Macros")
                    light._register_channel(f"{fixtureName}_PanTilt Macros Speed")
                    light._register_channel(f"{fixtureName}_Colour 1")
                    light._register_channel(f"{fixtureName}_Colour Fine Position")
                    light._register_channel(f"{fixtureName}_Cyan")
                    light._register_channel(f"{fixtureName}_Magenta")
                    light._register_channel(f"{fixtureName}_Yellow")
                    light._register_channel(f"{fixtureName}_CMYDimmerSpeed")
                    light._register_channel(f"{fixtureName}_CMYMacros")
                    light._register_channel(f"{fixtureName}_EffectWheel")
                    light._register_channel(f"{fixtureName}_Zoom")
                    light._register_channel(f"{fixtureName}_StrobeShutter")
                    light._register_channel(f"{fixtureName}_Dimmer")
                    light._register_channel(f"{fixtureName}_DimmerFine")
                    
                    self.fixtures[light.name] = {"type": "Colorwash250AT"}
                    
                    # Set to red for testing
                    light.set_channel(f"{fixtureName}_Colour 1", self._fixtureProfiles[f"{self.fixtures[light.name]["type"]}"]["Colour 1"]["Red"])
                
            except Exception as e:
                format.message(f"Error registering Robe Colorwash 250 AT 0: {e}", type="error")
                
            try:
                format.message("Registering Robe Colorwash 250 AT 1", type="info")
                self._Colorwash250AT_1 = self._dmx.add_fixture(Dimmer, name="Colorwash250AT_1")
                
                # LIGHT MUST BE IN MODE 3
                
                with self._Colorwash250AT_1 as light:
                    
                    fixtureName = light.name
                
                    light._register_channel(f"{fixtureName}_Pan")
                    light._register_channel(f"{fixtureName}_Pan Fine")
                    light._register_channel(f"{fixtureName}_Tilt")
                    light._register_channel(f"{fixtureName}_Tilt Fine")
                    light._register_channel(f"{fixtureName}_PanTilt Speed")
                    light._register_channel(f"{fixtureName}_Special Functions")
                    light._register_channel(f"{fixtureName}_PanTilt Macros")
                    light._register_channel(f"{fixtureName}_PanTilt Macros Speed")
                    light._register_channel(f"{fixtureName}_Colour 1")
                    light._register_channel(f"{fixtureName}_Colour Fine Position")
                    light._register_channel(f"{fixtureName}_Cyan")
                    light._register_channel(f"{fixtureName}_Magenta")
                    light._register_channel(f"{fixtureName}_Yellow")
                    light._register_channel(f"{fixtureName}_CMYDimmerSpeed")
                    light._register_channel(f"{fixtureName}_CMYMacros")
                    light._register_channel(f"{fixtureName}_EffectWheel")
                    light._register_channel(f"{fixtureName}_Zoom")
                    light._register_channel(f"{fixtureName}_StrobeShutter")
                    light._register_channel(f"{fixtureName}_Dimmer")
                    light._register_channel(f"{fixtureName}_DimmerFine")
                    
                    self.fixtures[light.name] = {"type": "Colorwash250AT"}
                    
                    # Set to green for testing
                    light.set_channel(f"{fixtureName}_Colour 1", self._fixtureProfiles[f"{self.fixtures[light.name]["type"]}"]["Colour 1"]["Green"])
                
            except Exception as e:
                format.message(f"Error registering Robe Colorwash 250 AT 1: {e}", type="error")
        
            self.DMXConnected = True
            
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"CONNECTED", 'type': "dmxStatus"})
            
            format.message("DMX Connection set up successfully", type="success")
            
        except Exception as e:
            format.message(f"Error occured while setting up DMX connection! ({e})", type="error")
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"DISCONNECTED", 'type': "dmxStatus"})
            
    def seedDBData(self):
        if not Gun.query.first() and not Player.query.first():
            format.message("Empty DB Found! Seeding Data....", type="warning")
 
            gunAlpha = Gun(name="Alpha", defaultColor="Red")
            gunApollo = Gun(name="Apollo", defaultColor="Red")
            gunChaos = Gun(name="Chaos", defaultColor="Red")
            gunCipher = Gun(name="Cipher", defaultColor="Red")
            gunCobra = Gun(name="Cobra", defaultColor="Red")
            gunComet = Gun(name="Comet", defaultColor="Red")
            gunCommander = Gun(name="Commander", defaultColor="Red")
            gunCyborg = Gun(name="Cyborg", defaultColor="Red")
            gunCyclone = Gun(name="Cyclone", defaultColor="Red")
            gunDelta = Gun(name="Delta", defaultColor="Red")
            gunDodger = Gun(name="Dodger", defaultColor="Green")
            gunDragon = Gun(name="Dragon", defaultColor="Green")
            gunEagle = Gun(name="Eagle", defaultColor="Green")
            gunEliminator = Gun(name="Eliminator", defaultColor="Green")
            gunElite = Gun(name="Elite", defaultColor="Green")
            gunFalcon = Gun(name="Falcon", defaultColor="Green")
            gunGhost = Gun(name="Ghost", defaultColor="Green")
            gunGladiator = Gun(name="Gladiator", defaultColor="Green")
            gunHawk = Gun(name="Hawk", defaultColor="Green")
            gunHyper = Gun(name="Hyper", defaultColor="Green")
            gunInferno = Gun(name="Inferno", defaultColor="Green")
            
            db.session.add(gunAlpha)
            db.session.add(gunApollo)
            db.session.add(gunChaos)
            db.session.add(gunCipher)
            db.session.add(gunCobra)
            db.session.add(gunComet)
            db.session.add(gunCommander)
            db.session.add(gunCyborg)
            db.session.add(gunCyclone)
            db.session.add(gunDelta)
            db.session.add(gunDodger)
            db.session.add(gunDragon)
            db.session.add(gunEagle)
            db.session.add(gunEliminator)
            db.session.add(gunElite)
            db.session.add(gunFalcon)
            db.session.add(gunGhost)
            db.session.add(gunGladiator)
            db.session.add(gunHawk)
            db.session.add(gunHyper)
            db.session.add(gunInferno)
            
            db.session.commit()
            format.message("Data seeded successfully", type="success")
        else:
            format.message("Data already exists, skipping seeding.", type="info")

    def openFiles(self):
        try:
            f = open(fr"{self._dir}\data\keys.txt", "r")
        except Exception as e:
            format.message(f"Error opening keys.txt: {e}", type="error")
        finally:
            blank = f.readline()
            blank = f.readline()
            self.IP1 = str(f.readline().strip())
            self.IP2 = str(f.readline().strip())
            self.ETHERNET_INTERFACE = str(f.readline().strip())
            self.OBSSERVERIP = str(f.readline().strip())
            self.OBSSERVERPORT = int(f.readline().strip())
            self.OBSSERVERPASSWORD = str(f.readline().strip())
            self.DMXADAPTOR = str(f.readline().strip())
            self.SPOTIPY_CLIENT_ID = str(f.readline().strip())
            self.SPOTIPY_CLIENT_SECRET = str(f.readline().strip())
                        
            format.message("Files opened successfully", type="success")
            
            self.filesOpened = True

    def setupRoutes(self):           
        @self.app.route('/')
        def index():
            if not self.OBSConnected:
                OBSConnection = "DISCONNECTED"
            else:
                OBSConnection = "CONNECTED"
            
            if not self.DMXConnected:
                DMXConnection = "DISCONNECTED"
            else:
                DMXConnection = "CONNECTED"
            
            return render_template('index.html', OBSConnected=OBSConnection, DMXConnected=DMXConnection)
        
        @self.app.route('/text')
        def neonText():
            return render_template('neonFlicker.html')

        
        @self.app.route("/ping")
        def ping():   
            #format.message("|--- I'm still alive! ---|")
            return 'OK'
        
        @self.app.route("/api/availableFixtures", methods=["GET"])
        def availableFixtures():
            
            temp_fixtures = []
            for fixture_name, fixture_data in self.fixtures.items():
                fixture_type = fixture_data["type"]
                fixture_profile = self._fixtureProfiles.get(fixture_type, {})

                temp_fixtures.append({
                    "name": fixture_name,            
                    "type": fixture_type,          
                    "attributes": fixture_profile      
                })
            
            #format.message(f"Fixtures: {temp_fixtures}")
        
            return jsonify(temp_fixtures)
            
        @self.app.route('/end')
        def terminateServer():
            logging.shutdown()
            os.kill(os.getpid(), signal.SIGTERM)
            
        @self.socketio.on('connect')
        def handleConnect():
            format.message("Sniffer Client connected")
            
            emit('musicStatus', {'message': f"{self.spotifyStatus}"} )
            
            emit('response', {'message': 'Connected to server'})
            
        @self.socketio.on('toggleMusic')
        def togglePlayback():
            response = self.handleMusic("toggle")
            
            emit('musicStatus', {'message': f"{response}"})
            
        @self.socketio.on('restartSong')
        def restartSong():
            response = self.handleMusic("restart")
            
            emit('musicStatus', {'message': f"{response}"})
            
        @self.socketio.on('nextSong')
        def nextSong():
            response = self.handleMusic("next")
            
            emit('musicStatus', {'message': f"{response}"})
        
        @self.socketio.on('SpotifyControl')
        def handleSpotifyControl(json):
            #format.message(f"Spotify control = {json["data"]}")
            
            self.spotifyControl = json["data"]
            
        @self.socketio.on('playBriefing')
        def playBriefing():
            try:
                format.message("Playing briefing")
                if self.OBSConnected == True:
                    self.obs.set_current_program_scene("Video")
            except Exception as e:
                format.message(f"Error playing briefing: {e}", type="error")
    
        @self.app.route('/sendMessage', methods=['POST'])
        def sendMessage():
            message = request.form.get('message')
            type = request.form.get('type')
            #format.message(f"Sending message: {message} with type: {type}")
            if message:
                
                self.socketio.emit(f"{type}", {f"message": message})

                # match type.lower():
                #     case "start":
                #         #format.message("Sending start message")
                #         self.socketio.emit('start', {'message': message})
                #     case "end":
                #         #format.message("Sending end message")
                #         self.socketio.emit('end', {'message': message})
                #     case "server":
                #         #format.message("Sending server message")
                #         self.socketio.emit('server', {'message': message})
                #     case "timeleft":
                #         #format.message(f"Sending timeleft message, {message} seconds left")
                #         self.socketio.emit('timeleft', {'message': f"{message} seconds remaining"})
                #     case "gunscores":
                #         #format.message(f"Sending gunScore message, {message}")
                #         self.socketio.emit('gunScores', {'message': message})
                #     case "timeremaining":
                #         #format.message(f"Sending time left message, {message}")
                #         self.socketio.emit('timeRemaining', {'message': message})
                #     case "songname":
                #         #format.message(f"Sending Music Name, {message}")
                #         self.socketio.emit('songName', {'message': message})
                #     case "songbpm":
                #         #format.message(f"Sending Music BPM, {message}")
                #         self.socketio.emit('songBPM', {'message': message})       
                #     case "songalbum":
                #         #format.message(f"Sending Music Album, {message}")
                #         self.socketio.emit('songAlbum', {'message': message})
                        
            #format.newline()
                        
            return 'Message sent!'

    def obs_connect(self):
        if self.devMode == "false":
            try:
                format.message("Attempting to connect to OBS")
                # ws = obsws(self.OBSSERVERIP, self.OBSSERVERPORT, self.OBSSERVERPASSWORD)
                # ws.connect()
                
                self.obs = obs.ReqClient(host=self.OBSSERVERIP, port=self.OBSSERVERPORT, password=self.OBSSERVERPASSWORD, timeout=3)
                
                self.OBSConnected = True
                format.message("Successfully Connected to OBS", type="success")
                
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"CONNECTED", 'type': "obsStatus"})

            except Exception as e:
                format.message(f"Failed to connect to OBS: {e}", type="error")
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"DISCONNECTED", 'type': "obsStatus"})
        else:
            format.message("Development Mode, skipping OBS Connection", type="warning")
    
    # -----------------| Background Tasks |-------------------------------------------------------------------------------------------------------------------------------------------------------- # 
            
    def startSniffing(self):
        format.message("Starting packet sniffer...")
        try:
            sniff(prn=self.packetCallback, store=False, iface=self.ETHERNET_INTERFACE if self.devMode != "true" else None)
        except Exception as e:
            try:
                format.message(f"Error while trying to sniff, falling back to default adaptor", type="error")
                sniff(prn=self.packetCallback, store=False, iface=r"\Device\NPF_{65FB39AF-8813-4541-AC82-849B6D301CAF}" if self.devMode != "true" else None)
            except Exception as e:
                format.message(f"Error while sniffing: {e}", type="error")
            
    async def getPlayingStatus(self):
        sessions = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
        current_session = sessions.get_current_session()

        if current_session:
            info = await current_session.try_get_media_properties_async()
            playback_info = current_session.get_playback_info()
            timeline_properties = current_session.get_timeline_properties()

            # Get media playback status
            if playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                status = "playing"
            elif playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED:
                status = "paused"
            elif playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.STOPPED:
                status = "paused"
            else:
                status = "paused"
            
            currentPosition = timeline_properties.position.total_seconds()
            totalDuration = timeline_properties.end_time.total_seconds()

            return status, currentPosition, totalDuration
            
        else:
            return "paused", 0, 0
    
    def handleMusic(self, mode):
        if self.spotifyControl == True:
            if mode.lower() == "toggle":
                if self.spotifyStatus == "paused":
                    #format.message("Playing music", type="warning")
                    self.spotifyStatus = "playing"
                    pyautogui.press('playpause')
                    
                    result = self.spotifyStatus
                else:
                    #format.message("Pausing music", type="warning")
                    self.spotifyStatus = "paused"
                    pyautogui.press('playpause')
                    result = self.spotifyStatus
                
            elif mode.lower() == "next":
                pyautogui.hotkey('nexttrack')
                self.spotifyStatus = "playing"
                result = self.spotifyStatus
            
            elif mode.lower() == "previous":
                pyautogui.hotkey('prevtrack')
                pyautogui.hotkey('prevtrack')
                self.spotifyStatus = "playing"
                result = self.spotifyStatus
            
            elif mode.lower() == "restart":
                pyautogui.hotkey('prevtrack')
                result = self.spotifyStatus
                
            elif mode.lower() == "pause":
                if self.spotifyStatus == "paused":
                    return
                else:
                    #format.message("Pausing music", type="warning")
                    self.spotifyStatus = "paused"
                    pyautogui.press('playpause')
                    result = "playing"
            
            elif mode.lower() == "play":
                if self.spotifyStatus == "playing":
                    return
                else:
                    #format.message("Playing music", type="warning")
                    self.spotifyStatus = "playing"
                    pyautogui.press('playpause')
                    result = "paused"
                    
            time.sleep(2)
                
            try:
                self.bpm_thread = threading.Thread(target=self.findBPM)
                self.bpm_thread.daemon = True
                self.bpm_thread.start()
            except Exception as e:
                format.message(f"Error running BPM thread: {e}", type="error")
                
            return result
                    
        else:
            format.message("Spotify control is disabled", type="warning")
            
    def checkIfProcessRunning(self, processName):
        for proc in psutil.process_iter():
            try:
                if processName.lower() in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    def runProcessChecker(self):
        try:
            while True:
                time.sleep(600)
                for processName in self.expecteProcesses:
                    processFound = self.checkIfProcessRunning(processName)
                    #format.message(f"Process {processName} running: {processFound}")
                    
                    if not processFound:
                        try:
                            format.message(f"Process {processName} not found, starting it..", type="warning")
                            if processName.lower() == "spotify":
                                os.startfile(f"{self._dir}\\appShortcuts\\Spotify.lnk")
                            elif processName.lower() == "obs64":
                                os.startfile(f"{self._dir}\\appShortcuts\\OBS.lnk", arguments='--disable-shutdown-check')
                                time.sleep(15)
                                self.obs_connect()
                            else:
                                format.message(f"Process {processName} not recognized for auto-start", type="error")
                            # if self.DMXConnected == False:
                            #     format.message(f"DMX Connection lost, restarting DMX Network")
                            #     self.setUpDMX()
                            if self.OBSConnected == False:
                                format.message(f"OBS Connection lost, restarting OBS")
                                self.obs_connect()
                                
                        except Exception as e:
                            format.message(f"Error starting process {processName}: {e}", type="error")
                            
                # if self.RestartRequested == True and self.gameStatus == "stopped":
                #     format.message(f"Restart requested, restarting PC in 1 minute")
                #     self.AppRestartThread = threading.Thread(target=self.restartApp("Restart Requested"))
                #     self.AppRestartThread.daemon = True
                #     self.AppRestartThread.start()
                    
                if self.gameStatus == "stopped" and self.OBSConnected == True:
                    if self.endOfDay == True:
                        format.message(f"EOD, setting OBS output to Test Mode")
                        
                        try:
                            with open(fr"{self._dir}\data\OBSText.txt", "w") as f:
                                f.write("EndOfDay: Waiting for next game                            ")
                                
                        except Exception as e:
                            format.message(f"Error opening OBSText.txt: {e}", type="error")
                        
                        self.obs.set_current_program_scene("Test Mode")
                    else:
                        self.endOfDay = True
                
                elif self.gameStatus == "running":
                    self.endOfDay = False
                
        except Exception as e:
            format.message(f"Error occured while checking processes: {e}", type="error")
            
    def restartApp(self, reason="unknown"):
        format.message(f"Restarting App in 1 minute due to {reason}", type="warning")
        
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Restart", 'type': "createWarning"})
        
        time.sleep(60)
        
        format.message("Restarting App", type="warning")

        os._exit(1)
            
    def handleBPM(self, song, bpm, album):
        #format.message(f"Get Here with {song}, {bpm}, {album}")
        try:
            if (self.rateLimit == True and ((random.randint(1, 50)) == 10)) or self.rateLimit == False:
                
                if song == None or bpm  == None or bpm == "Song not found":
                    match song:
                        #This makes me want to die
                        #Implemented because these are local songs used specifically in the Arena, and aren't on spotify.
                        case "Main Theme":
                            bpm = "69"
                        case "Loon Skirmish":
                            bpm = "80"
                        case "Crainy Yum (Medium)":
                            bpm = "80"
                        case "Crainy Yum":
                            bpm = "80"
                        case "Thing Of It Is":
                            bpm = "87"
                        case "Bug Zap":
                            bpm = "87"
                        case "Bug Zap (Medium)":
                            bpm = "87"
                        case "Only Partially Blown Up (Medium)":
                            bpm = "87"
                        case "Only Partially Blown Up":
                            bpm = "87"
                        case "Baron von Bats":
                            bpm = "87"
                        case "Treasure Yeti":
                            bpm = "86"
                        case "Normal Wave (A) (Medium)":
                            bpm = "86"
                        case "Normal Wave A":
                            bpm = "86"
                        case "Normal Wave B":
                            bpm = "87"
                        case "Normal Wave (C) (High)":
                            bpm = "87"
                        case "Special Wave A":
                            bpm = "87"
                        case "Special Wave B":
                            bpm = "101"
                        case "Challenge Wave B":
                            bpm = "101"
                        case "Challenge Wave C":
                            bpm = "101"
                        case "Boss Wave (A)":
                            bpm = "93"
                        case "Boss Wave (B)":
                            bpm = "98"
                        case "The Gnomes Cometh (B)":
                            bpm = "90"
                        case "The Gnomes Cometh (C)":
                            bpm = "86"
                        case "Gnome King":
                            bpm = "95"
                        case "D Boss Is Here":
                            bpm = "90"
                        case "Excessively Bossy":
                            bpm = "93"
                        case "One Bad Boss":
                            bpm = "84"
                        case "Zombie Horde":
                            bpm = "84"
                        case "Marching Madness":
                            bpm = "58"
                        case "March Of The Brain Munchers":
                            bpm = "58"
                        case "SUBURBINATION!!!":
                            bpm = "86"
                        case "Splattack!":
                            bpm = "88"
                        case "Science Blaster":
                            bpm = "92"
                        case "Undertow":
                            bpm = "88"
                        case _:
                            bpm = "60"
            
                #format.message(f"Current song: {song}, BPM: {bpm}")
            
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{song}", 'type': "songName"})
            
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{str(round(int(bpm)))}", 'type': "songBPM"})
            
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{album}", 'type': "songAlbum"})
                
                self.rateLimit = False
                
        except Exception as e:
            if "Max Retries, reason: too many 429 error responses" in bpm:
                self.rateLimit = True
                return
            else:
                format.message(f"Error occured while handling BPM: {e}", type="warning")
        
    def findBPM(self):
        try:
            fetcher = MediaBPMFetcher(self.SPOTIPY_CLIENT_ID, self.SPOTIPY_CLIENT_SECRET)
            fetcher.fetch()  # Fetch the current song and BPM
            song, bpm, album = fetcher.get_current_song_and_bpm()

            self.handleBPM(song, bpm, album)
            
            temp_spotifyStatus, currentPosition, totalDuration = asyncio.run(self.getPlayingStatus())
            
            if temp_spotifyStatus != self.spotifyStatus:
                self.spotifyStatus = temp_spotifyStatus
                
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{self.spotifyStatus}", 'type': "musicStatus"})
                
                #format.message(f"Spotify manually changed to {self.spotifyStatus}", type="warning")
                
                try:
                    self.bpm_thread = threading.Thread(target=self.findBPM)
                    self.bpm_thread.daemon = True
                    self.bpm_thread.start()
                except Exception as e:
                    format.message(f"Error finding BPM at media status change: {e}", type="error")
                
        except Exception as e:
            format.message(f"Failed to find BPM: {e}", type="error")
   
    def mediaStatusChecker(self):
        while True:
            try:
                temp_spotifyStatus, currentPosition, totalDuration = asyncio.run(self.getPlayingStatus())
                
                if temp_spotifyStatus != self.spotifyStatus:
                    self.spotifyStatus = temp_spotifyStatus
                    
                    response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{self.spotifyStatus}", 'type': "musicStatus"})
                    
                if currentPosition and totalDuration:
                    response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{currentPosition}", 'type': "musicPosition"})
                    response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{totalDuration}", 'type': "musicDuration"})
                    
                time.sleep(5)
                
            except Exception as e:
                format.message(f"Error occured while checking media status: {e}", type="error")
                
                if e != "an integer is required":
        
                    format.message("Requesting app restart", type="warning")
                    
                    if self.gameStatus != "stopped":
                        pyautogui.press("playpause")
                    
                    self.RestartRequested = True
                    
                    self.AppRestartThread = threading.Thread(target=self.restartApp(f"Restart Requested - BPM Issue: {e}"))
                    self.AppRestartThread.daemon = True
                    self.AppRestartThread.start()
                
        
    # -----------------| Packet Handling |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
        
    def packetCallback(self, packet):
        try:
            if packet.haslayer(IP) and (packet[IP].src == self.IP1 or packet[IP].src == self.IP2) and packet[IP].dst == "192.168.0.255":
                
                #format.message(f"Packet 1: {packet}")
                
                packet_data = bytes(packet['Raw']).hex()
                #format.message(f"Packet Data (hex): {packet_data}, {type(packet_data)}")
                
                decodedData = (self.hexToASCII(hexString=packet_data)).split(',')
                #format.message(f"Decoded Data: {decodedData}")
                
                if decodedData[0] == "1":
                    # A timing packet is being transmitted as the Event Type = 31 (Hex) = 1
                    threading.Thread(target=self.timingPacket, args=(decodedData,)).start()
                
                elif decodedData[0] == "3":
                    # The game has ended and the final scores packets are arriving, because 33 (Hex) = 3 (Denary)
                    threading.Thread(target=self.finalScorePacket, args=(decodedData,)).start()
                
                elif decodedData[0] == "4":
                    # Either a game has started or ended as 34 (Hex) = 4 (Denary) which signifies a Game Start / End event.
                    threading.Thread(target=self.gameStatusPacket, args=(decodedData,)).start()
                
                elif decodedData[0] == "5":
                    # A shot has been confirmed as the transmitted Event Type = 35 (Hex) = 5
                    threading.Thread(target=self.shotConfirmedPacket, args=(decodedData,)).start()
                
        except Exception as e:
            format.message(f"Error handling packet: {e}", type="error")
        
    def gameStatusPacket(self, packetData):
        # 4,@015,0 = start
        # 4,@014,0 = end
        
        if self.OBSConnected == True:
            self.endOfDay = False
            self.obs.set_current_program_scene("Laser Scores")
        
        format.message(f"Game Status Packet: {packetData}, Mode: {packetData[0]}")
        
        if packetData[1] == "@015":
            self.gameStatus = "running"
            format.message(f"Game start packet detected at {datetime.datetime.now()}", type="success")
            self.gameStarted()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Started @ {str(datetime.datetime.now())}", 'type': "start"})
            #format.message(f"Response: {response.text}")
        
        elif packetData[1] == "@014":
            self.gameStatus = "stopped"
            format.message(f"Game Ended at {datetime.datetime.now()}", type="success") 
            self.gameEnded()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
            #format.message(f"Response: {response.text}")
            
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{packetData[0]}", 'type': "gameMode"})

    def timingPacket(self, packetData):
        timeLeft = packetData[3]
        
        format.message(f"Time Left: {timeLeft}")

        if int(timeLeft) <= 0:
            self.gameStatus = "stopped"
            format.message(f"Game Ended at {datetime.datetime.now()}", type="success") 
            self.gameEnded()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
            #format.message(f"Response: {response.text}")
        else:
            self.gameStatus = "running"
            if self.OBSConnected == True:
                self.endOfDay = False
                self.obs.set_current_program_scene("Laser Scores")
            format.message(f"{timeLeft} seconds remain!", type="success") 
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Started @ {str(datetime.datetime.now())}", 'type': "start"})
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{timeLeft}", 'type': "timeRemaining"})
        
        format.newline()
    
    def finalScorePacket(self, packetData):
        gunId = packetData[1]
        finalScore = packetData[3]
        accuracy = packetData[7]

        gunName = None
        
        try:
            with self.app.app_context():
                gunName = "name: "+ Gun.query.filter_by(id=gunId).first().name
        
        except Exception as e:
            format.message(f"Error getting gun name: {e}", type="error")
        
        if gunName == None:
            gunName = "id: "+gunId
            
        format.message(f"Gun {gunName} has a score of {finalScore} and an accuracy of {accuracy}", type="success")
        
        data = f"{gunId},{finalScore},{accuracy}"
        
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': data, 'type': "gunScores"})
        
    def shotConfirmedPacket(self, packetData):
        pass
    
    # -----------------| DMX Control |---------------------------------------------------------------------------------------------------------------------------------------------------------- #            
    
    
    
    # -----------------| Game Handling |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
    
    def gameStarted(self):
        format.message("Game started")
        
        try:
            self.handleMusic(mode="play")
        except Exception as e:
            format.message(f"Error handling music: {e}", type="error")
            
        try:
            #self.setFixtureBrightness(255)
            
            #self._RedBulkHeadLights.dim(255, 5000)
            
            pass
        except Exception as e:
            format.message(f"Error dimming red lights: {e}", type="error")
        
    def gameEnded(self):
        format.message("Game ended")
        
        try:
            self.handleMusic(mode="pause")
        except Exception as e:
            format.message(f"Error handling music: {e}", type="error")
            
        try:
            #self.setFixtureBrightness(0)
            
            pass
            
        except Exception as e:
            format.message(f"Error dimming red lights: {e}", type="error")

    # -----------------| Testing |-------------------------------------------------------------------------------------------------------------------------------------------------------- #    
    
    def sendTestPacket(self, type="server"):
        format.message(f"Sending {type} packet")
        match type.lower():
            case "server":
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': "Test Packet", 'type': "server"})
                format.message(f"Response: {response.text}")
            case "start":
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Start Test Packet sent @ {datetime.datetime.now()}", 'type': "start"})
                format.message(f"Response: {response.text}")
            case "end":
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game End Test Packet sent @ {datetime.datetime.now()}", 'type': "end"})
                format.message(f"Response: {response.text}")
        
    # -----------------| Utlities |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
        
    def hexToASCII(self, hexString):
        ascii = ""
     
        for i in range(0, len(hexString), 2):
     
            part = hexString[i : i + 2]
     
            ch = chr(int(part, 16))
     
            ascii += ch
            
            if ch == "\x00":
                break
         
        return ascii
    
# -----------------| DB Models |-------------------------------------------------------------------------------------------------------------------------------------------------------- #  
                   
class Gun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    defaultColor = db.Column(db.String(60), unique=False, nullable=False)
    
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    kills = db.Column(db.Integer, nullable=False)
    deaths = db.Column(db.Integer, nullable=False)
    gamesWon = db.Column(db.Integer, nullable=False)
    gamesLost = db.Column(db.Integer, nullable=False)
    
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    startTime = db.Column(db.DateTime, nullable=False)
    endTime = db.Column(db.DateTime, nullable=False)
    winningPlayer = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    winningTeam = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    loser = db.Column(db.String(60), nullable=True)
    
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    teamColour = db.Column(db.String(10), nullable=False)
    gamePlayers = db.relationship("GamePlayers", backref="team_ref", lazy=True)

class GamePlayers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gameID = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    gunID = db.Column(db.Integer, db.ForeignKey("gun.id"), nullable=False)
    playerID = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    playerWon = db.Column(db.Boolean, nullable=False)
    team = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
