from typing import TYPE_CHECKING
from subprocess import Popen

import requests
import psutil
import GPUtil
from API.format import Format
import threading, datetime
from datetime import datetime, timedelta, time
import time as _time
import os
from data.models import *
from flask import Flask
import pygetwindow as gw
import win32gui
import win32con
import pythoncom
import win32com.client

f = Format("Supervisor")

if TYPE_CHECKING:
    from API.OBS import OBS as _OBS
    from API.DMXControl import dmx as _dmx
    from API.DB import context as _context
    from webApp import WebApp as _webApp 

class Supervisor:
    def __init__(self):  
        f.message(f.colourText("Starting Supervisor", "green"), type="info")
              
        self._obs = None
        self._dmx = None
        self._context = None
        self._app = None
        self._webApp = None
        self.devMode = False
        self._services = ["db", "obs", "dmx", "api"] # Should add MUSIC as an option here
        self.expectedProcesses = ["Spotify.exe", "obs64"]
        self._dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        f.message(f.colourText(f"Supervisor Started! Starting Background Processes...", "green"), type="info")
        
        threading.Thread(target=self.__checkForErrors, daemon=True).start() 
        threading.Thread(target=self.__processResourceUtilisation, daemon=True).start()
        threading.Thread(target=self.setOtherDependencies, daemon=True).start()
    
    def setDependencies(self, obs: "_OBS" = None, dmx: "_dmx" = None, db: "_context" = None, webApp: "_webApp" = None):
        if obs is not None:
            self._obs: "_OBS" = obs
        if dmx is not None:
            self._dmx : "_dmx" = dmx
        if db is not None:
            self._context: "_context" = db
        if webApp is not None:
            self._webApp: "_webApp" = webApp
            self.devMode = webApp.devMode
        if webApp is not None:
            self._app: Flask = webApp.app
            
    def setOtherDependencies(self):
        while self._context == None:
            _time.sleep(0.5)
        
        f.message(f.colourText(f"Setting dependencies...", "Green"), type="info")
        try:
            # TODO: NEED TO SET ALL OTHER DEPENDENCIES TO THE NEW DEPENDENCIES
            self._context.setSupervisor(self)
            f.message(f.colourText(f"Dependancies Reset!", "Green"), type="info")
        except Exception as e:
            f.message(f"Error occurred while resetting dependencies: {e}", type="error")
        
    def getDir(self) -> str:
        return self._dir
        
    def __processResourceUtilisation(self):
        while True:
            try:
                if (self._webApp != None):
                    cpuUsage = psutil.cpu_percent(interval=1)

                    ram = psutil.virtual_memory()
                    ramUsagePercent = ram.percent
                    ramUsageValue = ram.used / (1024 ** 3) 
                    
                    gpuUsage = 0
                    try:
                        gpus = GPUtil.getGPUs()
                        if gpus:
                            gpuUsage = gpus[0].load * 100
                    except:
                        pass
                    
                    response = requests.post(
                        f"http://{self._webApp._localIp}:8080/sendmessage",
                        json={
                            "message": {
                                "ramPercentage": ramUsagePercent,
                                "ramValue": ramUsageValue,
                                "gpu": gpuUsage,
                                "cpu": cpuUsage
                            },
                            "type": "resourceUtilisation"
                        }
                    )

                _time.sleep(5)
                
            except Exception as e:
                f.message(f"Error getting resource utilization: {e}", type="error")
                return None
            
    def __focusWindow(self, title):
        try:
            pythoncom.CoInitialize()
            shell = win32com.client.Dispatch("WScript.Shell")
            hwnd = win32gui.FindWindow(None, title)

            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                shell.SendKeys('%')
                win32gui.SetForegroundWindow(hwnd)
            else:
                pass
        except Exception as e:
            f.message(f"Error focusing window: {e}", type="error")
            return None

    def __checkForErrors(self):
        while True:
            self.__focusWindow("Zone Laser Scoreboard")
            
            _time.sleep(30)

            if self.devMode == False:
                try:
                    # Check if all expected processes are running
                    for processName in self.expectedProcesses:
                        try:
                            processFound : bool = self.__checkIfProcessRunning(processName)
                            if not processFound:
                                try:
                                    f.message(f"Process {processName} not found, starting it..", type="warning")
                                    if processName.lower() == "spotify":
                                        os.startfile(f"{self._dir}\\appShortcuts\\Spotify.lnk")
                                    elif processName.lower() == "obs64":
                                        self.__resetOBSConnection()
                                except Exception as e:
                                    f.message(f"Error starting process {processName}: {e}", type="error")
                        except Exception as e:  
                            f.message(f"Error occurred while checking for expected processes: {e}", type="error")
                except Exception as e:
                    f.message(f"Error occurred while checking for expected processes: {e}", type="error")
                
                try:
                    # Check Database Connection
                    if self._context != None and self.hasSevereErrorOccurred("db"):
                        f.message("Database Connection Error", type="error")
                        threading.Thread(target=self.__resetDatabaseConnection(), daemon=True).start()
                except Exception as e:
                    f.message(f"Error occured while checking Database status: {e}", type="error")
                    
                try:
                    # Check OBS Connection
                    if self._obs != None and (self.hasSevereErrorOccurred("obs") or self._obs.isConnected() == False):
                        f.message("OBS Connection Error", type="error")
                        threading.Thread(target=self.__resetOBSConnection(), daemon=True).start()
                except Exception as e:
                    f.message(f"Error occured while checking OBS status: {e}", type="error")
                    
                try:
                    # Check DMX Connection
                    if self._dmx != None and self.hasSevereErrorOccurred("dmx"):
                        f.message("DMX Connection Error", type="error")
                        threading.Thread(target=self.resetDMXConnection(), daemon=True).start()
                except Exception as e:
                    f.message(f"Error occured while checking DMX status: {e}", type="error")
                    
            try:
                if self._obs != None and self._obs.isConnected() == True:
                    self._obs.openProjector()
                    
                    if (self._obs.getCurrentScene()).lower() != "video":
                        # Check the time to enter sleep mode
                        with self._app.app_context():
                            foundGame : Game = (self._context.db.session
                                .query(Game)
                                .order_by(Game.startTime.desc())
                                .first())
                            
                            if foundGame != None and foundGame.endTime != None:
                                startTime = datetime.fromisoformat(foundGame.startTime) if isinstance(foundGame.startTime, str) else foundGame.startTime
                                timeToCheck = datetime.now() + timedelta(minutes=-30)
                                currentTime = datetime.now().time()
                                if startTime < timeToCheck and self._obs is not None and (currentTime < time(11, 0) or currentTime > time(17, 0)):
                                    # f.message(f"Found game with end time: {foundGame.endTime}, time to check is {timeToCheck} setting OBS output to sleep mode.")
                                    self._obs.switchScene("Test Mode")
                                
            except Exception as e:
                pass
                f.message(f"Error occurred while switching to sleep mode: {e}", type="warning")
                
            now = datetime.now().time()
                
            if self.devMode == False:
                try:
                    if time(0, 0, 0) <= now <= time(0, 5, 0):
                        self.__restartPC("Daily Restart")
                except Exception as e:
                    f.message(f"Error occurred while executing daily restart: {e}", type="error")          
                  
            if now >= time(21, 0, 0) or now <= time(10, 0, 0):
                self.executePendingRestarts()
                
            # try:
            #     p = Popen("/update.bat", cwd=self._dir)
            #     f.message(p)

            # except Exception as e:
            #     f.message(f"Error occurred while trying to pull changes from github: {e}", type="error")
            
    def hasSevereErrorOccurred(self, service: str) -> bool:
        try:
            if self._context == None and service.lower() == "db":
                return True
            
            with self._app.app_context():
                ise: list[InternalServerError] = (self._context.db.session
                    .query(InternalServerError)
                    .filter(InternalServerError.service == service.lower())
                    .filter(InternalServerError.severity == 1)
                    .filter(InternalServerError.timestamp >= (datetime.now() - timedelta(seconds=30)))
                    .all())

            if ise and not self.devMode:
                return True
            else:
                return False
        except Exception as e:
            f.message(f"Error occurred while checking for severe {service} errors: {e}", type="error")
            return False

    def hasModerateErrorOccurred(self, service: str) -> bool:
        if (self._context == None and service.lower() == "db"):
            return True
        
        with self._app.app_context():
            ise: list[InternalServerError] = (self._context.db.session
                .query(InternalServerError)
                .filter(InternalServerError.service == service.lower())
                .filter(InternalServerError.severity == 2)
                .filter(InternalServerError.timestamp >= (datetime.now() - timedelta(seconds=30)))
                .all())
        
        if ise and self.devMode == False:
            return True
        else:
            return False
        
    def getRecentServiceErrors(self, serviceName: str) -> list[InternalServerError]:
        return (self._context.db.session
            .query(InternalServerError)
            .filter(InternalServerError.service == serviceName.lower())
            .filter(InternalServerError.timestamp >= (datetime.now() - timedelta(hours=8)))
            .order_by(InternalServerError.timestamp.desc())
            .all())
    
    def getServices(self) -> list[str]:
        return self._services
        
    def __resetDatabaseConnection(self):
        self.__closeApp("Database Connection Error")
        
    def __resetOBSConnection(self):
        self._obs.resetConnection()
        
    def resetDMXConnection(self):
        self._dmx.resetConnection()
        
    def __restartPC(self, reason: str):
        f.message(f"Restarting PC. Reason {reason}", type="error")
        os.system("shutdown /r /f /t 0")
        
    def __closeApp(self, reason: str):
        f.message(f"Closing App. Reason {reason}", type="error")
        os._exit(1)
        
    def executePendingRestarts(self) -> None:
        with self._app.app_context():
            PendingRestarts : list[RestartRequest] = self._context.db.session.query(RestartRequest).filter_by(complete=False).all()
            
            if len(PendingRestarts) >= 1:
                reasons = "; ".join([r.reason for r in PendingRestarts if r.reason])
                
                f.message("WARNING - Restarting Program due to pending restarts.", type="warning")
                f.message(f"Restart Request f.messages: {reasons}", type="warning")
                
                for PendingRestart in PendingRestarts:
                    PendingRestart.complete = True
                    self._context.db.session.commit()
                
                if self.devMode:
                    f.message("Won't restart program in dev mode, please restart manually.", type="warning")
                else:
                    if "RESTART PC" in reasons:
                        self.__restartPC("Restart Request by " + PendingRestarts[0].created_by_service_name + "with reason: " + reasons)
                    else: 
                        self.__closeApp((f"Restarting Program at {datetime.now()} due to: " + reasons))
        
        return None
        
    def __checkIfProcessRunning(self, processName):
        for proc in psutil.process_iter():
            try:
                if processName.lower() in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            
        return False
        
    def getServiceHealth(self, serviceName: str):
        try:
            if self._context != None:
                notSetup = (
                    (serviceName.lower() == "dmx" and (self._dmx is None or self._dmx.isConnected() is False)) or 
                    (serviceName.lower() == "db" and self._context is None) or
                    (serviceName.lower() == "obs" and (self._obs is None or self._obs.isConnected() is False))
                )
                
                severeErrorOccured : bool = self.hasSevereErrorOccurred(str(serviceName).lower())
                moderateErrorOccured : bool = self.hasModerateErrorOccurred(str(serviceName).lower())
                
                if notSetup:
                    status = "Disconnected"
                else:
                    if severeErrorOccured:
                        status = "Critical"
                    elif moderateErrorOccured:
                        status = "Warning"
                    else:
                        status = "OK"
                    
                recentErrors: list[dict] = [
                    error.to_dict() for error in self.getRecentServiceErrors(str(serviceName).lower())
                ]
                
                return ServiceHealthDTO(
                    serviceName=serviceName,
                    status=status,
                    numberOfRecentErrors=len(recentErrors),
                    recentErrorList=recentErrors
                )
        except Exception as e:
            f.message(f"Error occurred while getting service health: {e}", type="warning")
        
        return ServiceHealthDTO(
            serviceName=serviceName,
            status="Unknown",
            numberOfRecentErrors=-1,
            recentErrorList=-1
        )

    def logInternalServerError(self, ise: InternalServerError) -> None:
        def _log():
            try:
                if self._context is not None and ise is not None:
                    if ise.severity == 1:
                        f.message(f"SEVERE EXCEPTION: Logging severe error from {ise.service}. \tException Message: {ise.exception_message}", type="error")
                    else:
                        f.message(f"EXCEPTION: Logging error from {str(ise.service).upper()}: {ise.exception_message}", type="warning")

                    ise.timestamp = datetime.now()

                    with self._app.app_context():
                        self._context.db.session.add(ise)
                        self._context.db.session.commit()
            except Exception as e:
                f.message(f"Error occurred while logging internal server error: {e}", type="error")

        threading.Thread(target=_log, daemon=True).start()