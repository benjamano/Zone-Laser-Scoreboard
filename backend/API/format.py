import datetime
import logging
import requests
import socket
import os
from dotenv import dotenv_values

reset = "\033[0m"
colours = {
        "Info": "\033[94m",    
        "Warning": "\033[93m", 
        "Error": "\033[91m",  
        "Success": "\033[92m",
        "Red": "\033[31m",
        "Green": "\033[32m",
        "Yellow": "\033[33m",
        "Blue": "\033[34m",
        "Magenta": "\033[35m",
        "Cyan": "\033[36m", 
        "Black": "\033[30m"
}

logFilePath = fr"{os.path.abspath(os.path.join(os.path.dirname(__file__), "..")).replace("backend\\", "")}\app.log"
logging.basicConfig(filename=logFilePath, level=logging.DEBUG, filemode="a")

_dir = os.path.dirname(os.path.realpath(__file__))
        
secrets = dotenv_values(_dir.replace("\\backend", "").replace("\\API", "") + "\\.env")

class Format:
    def __init__(self, ServiceName=""):
        self.serviceName = ServiceName
        self.logger = logging.getLogger("webAppLogger")
        self._localIp = ""
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self._localIp = s.getsockname()[0]
            s.close()
        except Exception as e:
            self.message(f"Error finding local IP: {e}")

    def message(self, message, type="Info", date=True, newline=False):
        """
        Possible types: Info, Warning, Error, Success.
        date : defaults to true, this should be kept true as it will break the look of the log if false.
        newline : defaults to false, if true, will add a new line before the message.
        """
        try:
            type = type.title()
            logtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            color = colours.get(type, "\033[94m")
            parts = []

            if newline:
                parts.append("")

            if date:
                parts.append(f"{logtime}")

            serviceWidth = 10  
            if self.serviceName:
                padded_service = f"{self.serviceName:<{serviceWidth}}"
                parts.append(padded_service)
            else:
                parts.append(" " * serviceWidth)

            parts.append(f"{type}")

            formatted = " | ".join(parts)
            formatted = f"{color}{formatted}{reset} : {message}"

            print(formatted)

            if type == "Error":
                self.logger.error(f"{logtime} | {self.serviceName} | {type} | {message}")
                self.sendEmail(message, type)
            elif type == "Warning":
                self.logger.warning(f"{logtime} | {self.serviceName} | {type} | {message}")

            if ("dev" not in secrets["Environment"].lower()):
                try:
                    requests.post(
                        f'http://{self._localIp}:8080/sendMessage',
                        json={"message": {"message": message, "logType": type}, "type": "logMessage"}
                    )
                except Exception:
                    pass

        except Exception as e:
            print(f"Error sending log message: {e}, MESSAGE: {message}")
        
    def newline(self, withDivider=True, baronly=False):
        
        """withdivider : defaults to true, if true, adds a divider ('+')."""
        
        if baronly:
            print("\t\t    |")
            
            return
        
        if withDivider:
            print("-" * 20 + "+" + "-" * 90)
        
        else:
            print("-" * 111)
            
    def colourText(self, text : str, colour : str):
        """
        Returns a formatted string with the given colour depending on the mode.
        
        Mode Options:
        - 0 = CMD Text Colours
        - 1 = HTML Text Colours
        
        Colour Options:   
        - Red   
        - Green
        - Yellow
        - Blue
        - Magenta
        - Cyan 
        - Black
        """
        
        return f"{colours.get(colour.title(), '\033[94m')}{text}{reset}"

    def sendEmail(self, content, type):
        try:   
            if "dev" in secrets["Environment"] and True:
                return
            
            url = "https://benmercer.pythonanywhere.com/play2day/api/sendLogMessage"
            data = {
                "type": type.title(),
                "messegeContent": content + f"<br>Sent by Environment: {secrets["Environment"]}",
                "secretKey": secrets["EmailSecretKey"],
            }
            
            response = requests.post(url, data=data)
                    
        except Exception as e:
            self.message(f"Failed to send log message to server: {e}", type="warning")