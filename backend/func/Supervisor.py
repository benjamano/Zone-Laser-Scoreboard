from func.format import message
import threading, datetime
import time, os
from data.models import *

class Supervisor:
    def __init__(self, devMode: bool):        
        self._obs = None
        self._dmx = None
        self._context = None
        self.devMode = devMode
        
        message(f"Supervisor Started at {datetime.datetime.today()}", type="success")

        threading.Thread(target=self.__checkForErrors, daemon=True).start() 
    
    def setDependencies(self, obs, dmx, db):
        self._obs = obs
        self._dmx = dmx
        self._context = db
        
    def __checkForErrors(self):
        while True:
            time.sleep(120)
            try:
                # Check Database Connection
                if self._context != None and self.hasSevereErrorOccurred("context"):
                    message("Database Connection Error", type="error")
                    threading.Thread(target=self.__resetDatabaseConnection(), daemon=True).start()
            except Exception as e:
                message(f"Error occured while checking Database status: {e}", type="error")
                
            try:
                # Check OBS Connection
                if self._obs != None and self.hasSevereErrorOccurred("obs"):
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
        if (self._context == None and service.lower() == "db"):
            return True;
        
        ise: list[InternalServerError] = (self._context.session
            .query(InternalServerError)
            .filter(InternalServerError.service == service.lower())
            .filter(InternalServerError.severity == 1)
            .filter(InternalServerError.timestamp >= (datetime.datetime.now() - datetime.timedelta(minutes=2) )).all()
            .all())
        
        if ise and self.devMode == False:
            return True
        elif ise and self.devMode == True:
            message("Severe exception detected, ignoring as devmode is true.", type="warning")
            return False
        else:
            return False
        
    def __resetDatabaseConnection(self):
        self.__closeApp("Database Connection Error")
        
        message("Restarting App To Reconnect to Database", type="warning")
        os._exit(1)
        
    def __resetOBSConnection(self):
        self.__closeApp("OBS Connection Error")
        
        message("Restarting OBS Connection", type="warning")
        self._obs = self._obs.ResetConnection()
        
    def __resetDMXConnection(self):
        self.__closeApp("DMX Connection Error")
        
        message("Restarting DMX Connection", type="warning")
        self._dmx = self._dmx.ResetConnection()
        
    def __restartPC(self, reason: str):
        message(f"Restarting PC. Reason {reason}", type="error")
        os.system("shutdown /r /f /t 0")
        
    def __closeApp(self, reason: str):
        message(f"Closing App. Reason {reason}", type="error")
        #os.exit(1)
        
    def logInternalServerError(self, ise: InternalServerError):
        if self._context == None and ise != None:
            
            if ise.severity == 1:
                message(f"SEVERE EXCEPTION: Logging servere error from {ise.service}\nException Message: {ise.exception_message}", type="error")
            else:
                message(f"EXCEPTION: Logging error from {ise.service}\nException Message: {ise.exception_message}", type="warning")
            
            ise.timestamp = datetime.datetime.now()

            self._context.session.add(ise)
            self._context.session.commit()
        
        return
        