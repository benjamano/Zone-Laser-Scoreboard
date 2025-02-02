import obsws_python as obs
from func import format

class OBS:
    """
    OBS class for controlling the OBS output.
    """
    def __init__(self, OBSSERVERIP:str, OBSSERVERPORT:int, OBSSERVERPASSWORD:str, dir:str):
        try:
            format.message("Attempting to connect to OBS")
            
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
            format.message(f"Error switching scene: {e}", type="error")
            return False
        
    def showWinningPlayer(self, playerName:str) -> bool:
        """
        Displays the winning player's name on the OBS output.
        """
        try:
            with open(fr"{self._dir}\data\display\WinningPlayer.txt", "w") as f:
                f.write(playerName)
            
            self.switchScene("Winners")
            
            return True
        except Exception as e:
            format.message(f"Error writing to file: {e}", type="error")
            return False
