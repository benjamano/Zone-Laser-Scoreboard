import obsws_python as obs
from func import format
from func import Supervisor
from data.models import *

class OBS:
    """
    OBS class for controlling the OBS output.
    """
    def __init__(self, OBSSERVERIP:str, OBSSERVERPORT:int, OBSSERVERPASSWORD:str, dir:str, supervisor: Supervisor):
        try:
            self.IP = OBSSERVERIP
            self.PORT = OBSSERVERPORT
            self.PASSWORD = OBSSERVERPASSWORD
            
            self._supervisor : Supervisor.Supervisor = supervisor
            
            self.obs = obs.ReqClient(host=OBSSERVERIP, port=OBSSERVERPORT, password=OBSSERVERPASSWORD, timeout=3)
            
            self._dir = dir
            
            if self.obs != None:
                format.message("Successfully Connected to OBS", type="success")
            else:
                raise ConnectionError(f"Failed To Connect To OBS With Details: {OBSSERVERIP}, {OBSSERVERPORT}, {OBSSERVERPASSWORD}")

        except Exception as e:
            raise ConnectionError(f"Failed To Connect To OBS With Details: {OBSSERVERIP}, {OBSSERVERPORT}, {OBSSERVERPASSWORD}. ERROR: {e}")

    def switchScene(self, sceneName:str) -> bool:
        """
        Switches the current OBS scene to the specified scene name.
        
        Args:
            sceneName (str): The name of the scene to switch to in OBS
        """
        try:
            self.obs.set_current_program_scene(sceneName)
            
            return True
        except Exception as e:
            if getattr(e, "code", None) == 600:
                format.message(f"OBS Scene Not Found With Name: {sceneName}", type="error")
            else:
                ise : InternalServerError = InternalServerError()
            
                ise.service = "obs"
                ise.exception_message = str(f"Error switching to scene named '{sceneName}': {e}")
                ise.process = "OBS: Switch to Scene"
                ise.severity = "1"
                    
                self._supervisor.logInternalServerError(ise)
            
            return False
            
    def showWinners(self, playerName:str, teamName:str) -> bool:
        """
        Displays the winning player's name on the OBS output.
        """
        try:
            with open(fr"{self._dir}\data\display\WinningPlayer.txt", "w") as f:
                f.write(f"The Winning Team Is {teamName}!\n")
                f.write(f"And the Winning Player Is\n")
                f.write(f"{playerName}!")
            
            self.switchScene("Winners")
            
            return True
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            
            ise.service = "obs"
            ise.exception_message = str(f"Error showing winners screen: {e}")
            ise.process = "OBS: Show Winners Screen"
            ise.severity = "3"
                
            self._supervisor.logInternalServerError(ise)
            
            return False
        
    def showSleepMode(self) -> bool:
        try:
            """
            Displays the sleep mode message on the OBS output.
            """
            try:
                with open(fr"{self._dir}\data\display\OBSText.txt", "w") as f:
                    f.write("\t\t\tLaser Tag System Sleeping.... ")

            except Exception as e:
                pass
                
            self.switchScene("Test Mode")
            
            return True
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            
            ise.service = "obs"
            ise.exception_message = str(f"Error showing sleep screen: {e}")
            ise.process = "OBS: Show Sleep Screen"
            ise.severity = "3"
                
            self._supervisor.logInternalServerError(ise)
            
            return False

    def isConnected(self):
        return self.obs.base_client.ws.connected
    
    def resetConnection(self) -> bool:
        try:
            format.message(f"Reseting OBS Connection", type="warning")
            self.obs = None
            self.obs = self.obs = obs.ReqClient(host=self.IP, port=self.PORT, password=self.PASSWORD, timeout=3)
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            
            ise.service = "obs"
            ise.exception_message = str(f"Error resetting OBS connection: {e}")
            ise.process = "OBS: Reset Connection"
            ise.severity = "1"
                
            self._supervisor.logInternalServerError(ise)
            return False