from typing import TYPE_CHECKING
from subprocess import Popen

import psutil
from API.format import message, colourText
import threading, datetime
import time, os
from data.models import *
from flask import Flask

if TYPE_CHECKING:
    from API.OBS import OBS as _OBS
    from API.DMXControl import dmx as _dmx
    from API.DB import context as _context
    from webApp import WebApp as _webApp 

class Supervisor:
    def __init__(self):        
        self._obs = None
        self._dmx = None
        self._context = None
        self._app = None
        self._webApp = None
        self.devMode = False
        self._services = ["db", "obs", "dmx", "api"]
        self.expectedProcesses = ["Spotify.exe", "obs64"]
        self._dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        message(colourText(f"Supervisor Started!", "cyan"), type="info")
        
        threading.Thread(target=self.__checkForErrors, daemon=True).start() 
    
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
        message(colourText(f"Supervisor: Restarted Service, Setting dependencies...", "Red"), type="info")
        try:
            # TODO: NEED TO SET ALL OTHER DEPENDENCIES TO THE NEW DEPENDENCIES
            pass
        except Exception as e:
            message(f"Error occurred while resetting Web App's dependencies: {e}", type="error")
        
    def __checkForErrors(self):
        while True:
            time.sleep(3)

            try:
                # Check if all expected processes are running
                for processName in self.expectedProcesses:
                    try:
                        processFound : bool = self.__checkIfProcessRunning(processName)
                        if not processFound:
                            try:
                                message(f"Process {processName} not found, starting it..", type="warning")
                                if processName.lower() == "spotify":
                                    os.startfile(f"{self._dir}\\appShortcuts\\Spotify.lnk")
                                elif processName.lower() == "obs64":
                                    os.startfile(f"{self._dir}\\appShortcuts\\OBS.lnk", arguments='--disable-shutdown-check')
                                    time.sleep(30)
                                    self.__resetOBSConnection()
                            except Exception as e:
                                message(f"Error starting process {processName}: {e}", type="error")
                    except Exception as e:  
                        message(f"Error occurred while checking for expected processes: {e}", type="error")
            except Exception as e:
                message(f"Error occurred while checking for expected processes: {e}", type="error")
            
            try:
                # Check Database Connection
                if self._context != None and self.hasSevereErrorOccurred("db"):
                    message("Database Connection Error", type="error")
                    threading.Thread(target=self.__resetDatabaseConnection(), daemon=True).start()
            except Exception as e:
                message(f"Error occured while checking Database status: {e}", type="error")
                
            try:
                # Check OBS Connection
                if self._obs != None and (self.hasSevereErrorOccurred("obs") or self._obs.isConnected() == False):
                    message("OBS Connection Error", type="error")
                    threading.Thread(target=self.__resetOBSConnection(), daemon=True).start()
            except Exception as e:
                message(f"Error occured while checking OBS status: {e}", type="error")
                
            try:
                # Check DMX Connection
                if self._dmx != None and self.hasSevereErrorOccurred("dmx"):
                    message("DMX Connection Error", type="error")
                    threading.Thread(target=self.__resetDMXConnection(), daemon=True).start()
            except Exception as e:
                message(f"Error occured while checking DMX status: {e}", type="error")
                
            try:
                if self._obs.isConnected() == True:
                    self._obs.openProjector()
                    
                    if (self._obs.getCurrentScene()).lower() != "video":
                        # Check the time to enter sleep mode
                        with self._app.app_context():
                            foundGame : Game = (self._context.db.session
                                .query(Game)
                                .order_by(Game.startTime.desc())
                                .first())
                            
                            if foundGame != None and foundGame.endTime != None:
                                startTime = datetime.datetime.fromisoformat(foundGame.startTime) if isinstance(foundGame.startTime, str) else foundGame.startTime
                                timeToCheck = datetime.datetime.now() + datetime.timedelta(minutes=-30)
                                currentTime = datetime.datetime.now().time()
                                if startTime < timeToCheck and self._obs != None and (currentTime < datetime.time(11, 0) or currentTime > datetime.time(17, 0)):
                                    # message(f"Found game with end time: {foundGame.endTime}, time to check is {timeToCheck} setting OBS output to sleep mode.")
                                    self._obs.switchScene("Test Mode")
                                
            except Exception as e:
                pass
                message(f"Error occurred while switching to sleep mode: {e}", type="warning")
                
            # try:
            #     p = Popen("/update.bat", cwd=self._dir)
            #     message(p)

            # except Exception as e:
            #     message(f"Error occurred while trying to pull changes from github: {e}", type="error")
            
    def hasSevereErrorOccurred(self, service: str) -> bool:
        try:
            if self._context == None and service.lower() == "db":
                return True
            
            with self._app.app_context():
                ise: list[InternalServerError] = (self._context.db.session
                    .query(InternalServerError)
                    .filter(InternalServerError.service == service.lower())
                    .filter(InternalServerError.severity == 1)
                    .filter(InternalServerError.timestamp >= (datetime.datetime.now() - datetime.timedelta(seconds=30)))
                    .all())

            if ise and not self.devMode:
                return True
            else:
                return False
        except Exception as e:
            message(f"Error occurred while checking for severe {service} errors: {e}", type="error")
            return False

    def hasModerateErrorOccurred(self, service: str) -> bool:
        if (self._context == None and service.lower() == "db"):
            return True
        
        with self._app.app_context():
            ise: list[InternalServerError] = (self._context.db.session
                .query(InternalServerError)
                .filter(InternalServerError.service == service.lower())
                .filter(InternalServerError.severity == 2)
                .filter(InternalServerError.timestamp >= (datetime.datetime.now() - datetime.timedelta(seconds=30)))
                .all())
        
        if ise and self.devMode == False:
            return True
        else:
            return False
        
    def getRecentServiceErrors(self, serviceName: str) -> list[InternalServerError]:
        return (self._context.db.session
            .query(InternalServerError)
            .filter(InternalServerError.service == serviceName.lower())
            .filter(InternalServerError.timestamp >= (datetime.datetime.now() - datetime.timedelta(hours=8)))
            .order_by(InternalServerError.timestamp.desc())
            .all())
    
    def getServices(self) -> list[str]:
        return self._services
        
    def __resetDatabaseConnection(self):
        self.__closeApp("Database Connection Error")
        
    def __resetOBSConnection(self):
        self._obs.resetConnection()
        
    def __resetDMXConnection(self):
        self._dmx.resetConnection()
        
    def __restartPC(self, reason: str):
        message(f"Restarting PC. Reason {reason}", type="error")
        os.system("shutdown /r /f /t 0")
        
    def __closeApp(self, reason: str):
        message(f"Closing App. Reason {reason}", type="error")
        os.exit(1)
        
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
            message(f"Error occurred while getting service health: {e}", type="warning")
        
        return ServiceHealthDTO(
            serviceName=serviceName,
            status="Unknown",
            numberOfRecentErrors=-1,
            recentErrorList=-1
        )

    def logInternalServerError(self, ise: InternalServerError):
        try:
            if self._context != None and ise != None:
                
                if ise.severity == 1:
                    message(f"SEVERE EXCEPTION: Logging servere error from {ise.service}\nException Message: {ise.exception_message}", type="error")
                else:
                    message(f"EXCEPTION: Logging error from {str(ise.service).upper()}: {ise.exception_message}", type="warning")
                
                ise.timestamp = datetime.datetime.now()
                
                with self._app.app_context():
                    self._context.db.session.add(ise)
                    self._context.db.session.commit()
            
            return
        
        except Exception as e:
            message(f"Error occurred while logging internal server error: {e}", type="error")
            
            return