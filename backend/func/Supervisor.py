import psutil
from func.format import message, colourText
import threading, datetime
import time, os
from data.models import *
import func.OBS as _obs
import func.DB as _context
import func.DMXControl as _dmx
from flask import Flask

class Supervisor:
    def __init__(self, devMode: bool):        
        self._obs = None
        self._dmx = None
        self._context = None
        self._app = None
        self.devMode = devMode
        self._services = ["db", "obs", "dmx", "api"]
        self.expectedProcesses = ["Spotify.exe", "obs64"]
        self._dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        message(colourText(f"Supervisor Started!", "cyan"), type="info")
        
        threading.Thread(target=self.__checkForErrors, daemon=True).start() 
    
    def setDependencies(self, obs=None, dmx=None, db=None, app=None):
        if obs is not None:
            self._obs: _obs.OBS = obs
        if dmx is not None:
            self._dmx: _dmx.dmx = dmx
        if db is not None:
            self._context: _context.context = db
        if app is not None:
            self._app: Flask = app
        
    def __checkForErrors(self):
        while True:
            time.sleep(30)
            #time.sleep(5)
            
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
                                    time.sleep(10)
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
                if self._obs != None and (self.hasSevereErrorOccurred("obs") or not self._obs.isConnected()):
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
                # Check the time to enter sleep mode
                if datetime.datetime.now().hour >= 21 or datetime.datetime.now().hour <= 11 and self._obs != None:
                    self._obs.switchScene("Test Mode")
            except Exception as e:
                message(f"Error occurred while checking time for sleep mode: {e}", type="error")
            
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
        message("Restarting OBS Connection", type="warning")
        self._obs = self._obs.resetConnection()
        
    def __resetDMXConnection(self):
        message("Restarting DMX Connection", type="warning")
        self._dmx = self._dmx.resetConnection()
        
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
                notSetup : bool = (serviceName.lower() == "dmx" and self._dmx == None) or (serviceName.lower() == "db" and self._context == None) or (serviceName.lower() == "obs" and self._obs == None)
                
                severeErrorOccured : bool = self.hasSevereErrorOccurred(str(serviceName).lower())
                moderateErrorOccured : bool = self.hasModerateErrorOccurred(str(serviceName).lower())
                
                if severeErrorOccured or notSetup == True:
                    status = "Critical"
                elif moderateErrorOccured:
                    status = "Warning"
                else:
                    status = "OK"
                    
                recentErrors: list[dict] = [
                    error.to_dict() for error in self.getRecentServiceErrors(str(serviceName).lower())
                ]
                
                return ServiceHealthDTO(
                    id=0,
                    serviceName=serviceName,
                    status= status,
                    numberOfRecentErrors=len(recentErrors),
                    recentErrorList=recentErrors
                    
                )
        except Exception as e:
            message(f"Error occurred while getting service health: {e}", type="warning")
        
        return None

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