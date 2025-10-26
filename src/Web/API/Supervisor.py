import datetime
import os
import threading
import time as _time
from datetime import datetime, timedelta, time
from typing import TYPE_CHECKING

import GPUtil
import psutil
import pythoncom
import win32com.client
import win32con
import win32gui
from Utilities.format import Format
from Data.models import *
from flask import Flask
from flask_socketio import SocketIO

f = Format("Supervisor")

if TYPE_CHECKING:
    from Web.Archive.OBS_Old import OBS as _OBS
    from Web.API.DMXControl import dmx as _dmx
    from Web.API.DB import context as _context
    from src.Web.webApp import WebApp as _webApp 

class Supervisor:
    def __init__(self, dmx, context, socket, app, mApi):  
        f.message(f.colourText("Starting Supervisor", "green"), type="info")
              
        self._dmx = dmx
        self._context = context
        self._socket = socket
        self._app = app
        self._mApi = mApi
        self.devMode = False
        self._services = ["db", "dmx", "api"] # Should add MUSIC as an option here
        self.expectedProcesses = ["obs64"]

        f.message(f.colourText(f"Supervisor Started! Starting Background Processes...", "green"), type="info")
        
        threading.Thread(target=self.__checkForErrors, daemon=True).start() 
        threading.Thread(target=self.__processResourceUtilisation, daemon=True).start()

    def setDependencies(self, dmx: "_dmx | None" = None, db: "_context | None" = None, webApp: "_webApp | None" = None,
            socket=None, mApi=None):
        if dmx is not None:
            self._dmx: "_dmx | None" = dmx
        if db is not None:
            self._context: "_context" = db
        if webApp is not None:
            self._webApp: "_webApp" = webApp
            self.devMode = webApp.devMode
        if webApp is not None:
            self._app: Flask = webApp.app
        if socket is not None:
            self._socket: SocketIO = socket
        if mApi is not None:
            self._mApi = mApi
        
    def __processResourceUtilisation(self):
        while True:
            try:
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

                self._socket.emit(
                    'resourceUtilisation',
                    {
                        "message": {
                            "ramPercentage": ramUsagePercent,
                            "ramValue": ramUsageValue,
                            "gpu": gpuUsage,
                            "cpu": cpuUsage
                        }
                    }
                )

                _time.sleep(5)
                
            except Exception as e:
                f.message(f"Error getting resource utilization: {e}", type="error")
                return None

    def __checkForErrors(self):
        while True:
            _time.sleep(30)

            if self.devMode == False:
                try:
                    # Check Database Connection
                    if self._context != None and self.hasSevereErrorOccurred("db"):
                        f.message("Database Connection Error", type="error")
                        threading.Thread(target=self.__resetDatabaseConnection(), daemon=True).start()
                except Exception as e:
                    f.message(f"Error occured while checking Database status: {e}", type="error")

                try:
                    # Check DMX Connection
                    if self._dmx != None and self.hasSevereErrorOccurred("dmx"):
                        f.message("DMX Connection Error", type="error")
                        threading.Thread(target=self.resetDMXConnection(), daemon=True).start()
                except Exception as e:
                    f.message(f"Error occured while checking DMX status: {e}", type="error")
                    
            now = datetime.now().time()
                
            if self.devMode == False:
                try:
                    if time(0, 0, 0) <= now <= time(0, 5, 0):
                        self.__restartPC("Daily Restart")
                except Exception as e:
                    f.message(f"Error occurred while executing daily restart: {e}", type="error")          
                  
            if now >= time(21, 0, 0) or now <= time(10, 0, 0):
                self.executePendingRestarts()

            try:
                self._mApi.lookForSongsWith0BPM()
            except Exception as e:
                f.message(f"Error occurred while looking for songs to get a BPM for: {e}", type="error")

            self._mApi.lookForSongsToDownload()
            
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
        
    def getServiceHealth(self, serviceName: str):
        try:
            if self._context != None:
                notSetup = (
                    (serviceName.lower() == "dmx" and (self._dmx is None or self._dmx.isConnected() is False)) or 
                    (serviceName.lower() == "db" and self._context is None)
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