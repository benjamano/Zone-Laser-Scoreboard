from func.format import message
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
        
        message(f"Supervisor Started at {datetime.datetime.today()}", type="success")

        threading.Thread(target=self.__checkForErrors, daemon=True).start() 
    
    def setDependencies(self, obs, dmx, db, app):
        self._obs : _obs.OBS = obs
        self._dmx : _dmx.dmx = dmx
        self._context : _context.context = db
        self._app : Flask = app
        
    def __checkForErrors(self):
        while True:
            time.sleep(30)
            #time.sleep(5)
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
            
    def hasSevereErrorOccurred(self, service: str) -> bool:
        try:
            if self._context is None and service.lower() == "db":
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
        self._obs = self._obs.ResetConnection()
        
    def __resetDMXConnection(self):
        message("Restarting DMX Connection", type="warning")
        self._dmx = self._dmx.ResetConnection()
        
    def __restartPC(self, reason: str):
        message(f"Restarting PC. Reason {reason}", type="error")
        os.system("shutdown /r /f /t 0")
        
    def __closeApp(self, reason: str):
        message(f"Closing App. Reason {reason}", type="error")
        os.exit(1)
        
    def getServiceHealth(self, serviceName: str):
        try:
            if self._context != None:
                severeErrorOccured : bool = self.hasSevereErrorOccurred(str(serviceName).lower())
                moderateErrorOccured : bool = self.hasModerateErrorOccurred(str(serviceName).lower())
                
                if severeErrorOccured:
                    status = "Critical"
                elif moderateErrorOccured:
                    status = "Warning"
                else:
                    status = "OK"
                    
                numberOfRecentErrors = self.getRecentServiceErrors(str(serviceName).lower())
                
                return ServiceHealthDTO(
                    id=0,
                    serviceName=serviceName,
                    status= status,
                    numberOfRecentErrors=numberOfRecentErrors
                )
        except Exception as e:
            message(f"Error occurred while getting service health: {e}", type="error")
        
        return None

    def logInternalServerError(self, ise: InternalServerError):
        if self._context != None and ise != None:
            
            if ise.severity == 1:
                message(f"SEVERE EXCEPTION: Logging servere error from {ise.service}\nException Message: {ise.exception_message}", type="error")
            else:
                message(f"EXCEPTION: Logging error from {str(ise.service).upper()}: {ise.exception_message}", type="warning")
            
            ise.timestamp = datetime.datetime.now()

            self._context.db.session.add(ise)
            self._context.db.session.commit()
        
        return
        