import obsws_python as obs
import pygetwindow as gw
from Utilities.format import Format
from Web.API import Supervisor
from Data.models import *
import psutil
import time
import os

format = Format("OBS")

class OBS:
    """
    OBS class for controlling the OBS output.
    """
    def __init__(self, OBSSERVERIP:str, OBSSERVERPORT:int, OBSSERVERPASSWORD:str, dir:str, supervisor: Supervisor, secrets : dict):
        try:
            self.IP = OBSSERVERIP
            self.PORT = OBSSERVERPORT
            self.PASSWORD = OBSSERVERPASSWORD
            self.AvailableMonitor = ""
            self.AvailableMonitors = []
            self.Secrets = secrets
            
            self._supervisor : Supervisor.Supervisor = supervisor
            
            self._dir = self._supervisor.getDir()
            
            self.obs = obs.ReqClient(host=OBSSERVERIP, port=OBSSERVERPORT, password=OBSSERVERPASSWORD, timeout=3)

            if self.obs != None:
                format.message("Successfully Connected to OBS", type="success")
            else:
                format.message("Failed To Connect To OBS", type="error")

        except Exception as e:
            format.message(f"Error Connecting to OBS: {e}", type="error")
            
        self._supervisor.setDependencies(obs=self)
        
    def getCurrentScene(self) -> str:
        if self.isConnected == False:
            return ""
        
        a = self.obs.get_current_program_scene()
        
        #format.message(vars(a))
        
        sceneName = a.scene_name
        
        return sceneName

    def isSceneSelected(self, sceneName : str) -> bool:
        if self.isConnected() == False:
            raise Exception("OBS is not connected")
        
        return (self.getCurrentScene()).lower() == sceneName.lower()

    def switchScene(self, sceneName : str) -> bool:
        """
        Switches the current OBS scene to the specified scene name.
        
        Args:
            sceneName (str): The name of the scene to switch to in OBS
        """
        
        if self.isConnected() == False:
            return False
        
        try:
            if (self.getCurrentScene()).lower() == sceneName.lower():
                return True
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            
            ise.service = "obs"
            ise.exception_message = str(f"Error checking current scene: {e}")
            ise.process = "OBS: Switch to Scene"
            ise.severity = "1"
        
            self._supervisor.logInternalServerError(ise)
        
        try:
            self.obs.set_current_program_scene(sceneName)
            
            return True
        except Exception as e:
            if getattr(e, "code", 0) == 600:
                ise : InternalServerError = InternalServerError()
            
                ise.service = "obs"
                ise.exception_message = str(f"OBS Scene Not Found With Name: {sceneName}: {e}")
                ise.process = "OBS: Switch to Scene"
                ise.severity = "2"
                    
                self._supervisor.logInternalServerError(ise)
            else:
                ise : InternalServerError = InternalServerError()
            
                ise.service = "obs"
                ise.exception_message = str(f"Error switching to scene named '{sceneName}': {e}")
                ise.process = "OBS: Switch to Scene"
                ise.severity = "1"
                    
                self._supervisor.logInternalServerError(ise)
            
            return False

    def showWinners(self, winningGunName: Gun, gunScore : int, teamName: str, teamScore : int) -> bool:
        """
        Displays the winning player's name on the OBS output.
        """
        try:
            # with open(fr"{self._dir}\data\display\WinningPlayer.txt", "w") as f:
            #     f.write(f"The Winning Team Is {teamName}!\n")
            #     f.write(f"And the Winning Player Is\n")
            #     f.write(f"{playerName}!")
            
            # self.switchScene("Winners")
            
            self.switchScene("DynamicRendering")
            
            self.obs.set_input_settings(
                name="DynamicRenderingBrowser",
                settings={"url": f"http://{self._supervisor._webApp._localIp}:8080/dynamicRendering/gameResults?mainText=Game%20Over!"},
                overlay=True
            )

            time.sleep(7)
            
            self.obs.set_input_settings(
                name="DynamicRenderingBrowser",
                settings={"url": f"http://{self._supervisor._webApp._localIp}:8080/dynamicRendering/gameResults?mode=team&teamName={teamName}%20Team&teamColor={teamName.lower()}&score={teamScore}"},
                overlay=True
            )

            time.sleep(7)

            self.obs.set_input_settings(
                name="DynamicRenderingBrowser",
                settings={"url": f"http://{self._supervisor._webApp._localIp}:8080/dynamicRendering/gameResults?mode=player&playerName={winningGunName}&score={gunScore}"},
                overlay=True
            )
            
            time.sleep(7)
            
            self.obs.set_input_settings(
                name="DynamicRenderingBrowser",
                settings={"url": f"http://{self._supervisor._webApp._localIp}:8080/dynamicRendering/gameResults?mainText=Please%20Return%20to%20the%20Starting%20Area"},
                overlay=True
            )

            time.sleep(20)

            self.switchScene("Laser Scores")
                        
            return True
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            
            ise.service = "obs"
            ise.exception_message = str(f"Error showing winners screen: {e}")
            ise.process = "OBS: Show Winners Screen"
            ise.severity = "3"
                
            self._supervisor.logInternalServerError(ise)
            
            return False
        
    def openProjector(self) -> bool:
        """
            Displays the projector screen on the OBS output.
        """
        
        try:
            if self.isPreviewOpen() == True:
                return True
                
            self.getMonitorsToProjectTo()
            
            self.obs.open_video_mix_projector("OBS_WEBSOCKET_VIDEO_MIX_TYPE_PREVIEW", monitor_index=self.AvailableMonitor["monitorIndex"])
            
            return True
        
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            
            ise.service = "obs"
            ise.exception_message = str(f"Error showing projector screen: {e}")
            ise.process = "OBS: Show Projector Screen"
            ise.severity = "2"
                
            self._supervisor.logInternalServerError(ise)
            
            return False
        
    def isPreviewOpen(self) -> bool:
        windows = gw.getAllTitles()
        for title in windows:
            if "(Preview)" in title:
                return True
            elif "Full-Screen Projector" in title:
                return True
        return False
        
    def getMonitorsToProjectTo(self) -> list:
        monitors = self.obs.get_monitor_list().monitors
        
        self.AvailableMonitors = monitors
        
        acceptedMonitors : list[str] = str(self.Secrets["MonitorsToProjectTo"]).split("/")
        
        monitorToProjectTo = next((monitor for monitor in monitors if monitor['monitorName'] in acceptedMonitors), monitors[0])
        
        self.AvailableMonitor = monitorToProjectTo
        
        return monitors
        
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

    def isConnected(self) -> bool:
        try:
            if self.obs != None:
                return self.obs.base_client.ws.connected
            else:
                return False
        except AttributeError:
            return False
        except Exception:
            raise
    
    def resetConnection(self) -> bool:
        try:
            format.message(f"Reseting OBS Connection", type="warning")
            
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'obs' in proc.info['name'].lower():
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                    except psutil.NoSuchProcess:
                        pass
                    except Exception as e:
                        pass
                        
            time.sleep(5)
            
            try:
                os.startfile(f"{self._dir}\\appShortcuts\\OBS.lnk", arguments='--disable-shutdown-check')
            except Exception as e:
                if (self._supervisor.devMode == False):
                    format.message(f"Error starting OBS: {e}", type="error")
                
                return False
            
            time.sleep(20)
            
            self.obs = None
            self.obs = self.obs = obs.ReqClient(host=self.IP, port=self.PORT, password=self.PASSWORD, timeout=3)
            
            self._supervisor.setDependencies(obs=self)
            
            return True
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            
            ise.service = "obs"
            ise.exception_message = str(f"Error resetting OBS connection: {e}")
            ise.process = "OBS: Reset Connection"
            ise.severity = "1"
                
            self._supervisor.logInternalServerError(ise)
            
            return False
        
    def tryConnect(self, IpAddress : str, Port : int, Password : str):
        try:
            self.obs = obs.ReqClient(host=IpAddress, port=Port, password=Password, timeout=3)
        except Exception as e:
            raise