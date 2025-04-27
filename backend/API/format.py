import datetime
import logging
import ctypes
import os
import sys
import requests
import socket

try:
    dir = os.path.dirname(os.path.realpath(__file__))
    with open(fr"{dir}\data\dev.txt") as f:
        devMode = str(f.readline().strip())
except:
    try:
        with open(fr"{dir}\data\dev.txt") as f:
            devMode = str(f.readline().strip())
        
        format.message(f"Developer mode is {devMode}")
    except:
        devMode = "False"
        pass

try:
    
    logger = logging.getLogger("webAppLogger")

    logFilePath = fr"{dir}\app.log"
        
    logging.basicConfig(filename=logFilePath, level=logging.DEBUG, filemode="a")

except Exception as e:
    print(f"An error occured: {e}")
    input("Press any key to exit...")

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

reset = "\033[0m"

try:
    # Create a dummy socket connection to find the local IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    _localIp = s.getsockname()[0]
    s.close()
except Exception as e:
    format.message(f"Error finding local IP: {e}")

def message(message, type="Info", date=True, newline=False):
    """Possible types: Info, Warning, Error, Success.
    \ndate : defaults to true, this should be kept true as it will break the look of the log if false.
    \nnewline : defaults to false, if true, will add a new line before the message."""
    
    try:
        type = type.title()
    
        logtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        messagetosend = ""

        color = colours.get((type.title()), "\033[94m")
        
        if newline:
            messagetosend += "\n"
        
        if not date:
            messagetosend += f"| {color}{type.title()}{reset} : {message}"
            
        else:
            messagetosend += f"{logtime} | {color}{type.title()}{reset} : {message}"
            
        print(messagetosend)

        if type.title() == "Error":
            logger.error(f"{logtime} | {message}")
            sendEmail(message, type)
        elif type.title() == "Warning":
            logger.warning(f"{logtime} | {message}")
        
        try:
            response = requests.post(
                f'http://{_localIp}:8080/sendMessage',
                json={"message": {"message": message, "logType": type}, "type": "logMessage"}
            )
        except:
            pass
        
    except Exception as e:
        print(f"Error sending log message: {e}, MESSAGE: {message}")
    
    
def newline(withDivider=True, baronly=False):
    
    """withdivider : defaults to true, if true, adds a divider ('+')."""
    
    if baronly:
        print("\t\t    |")
        
        return
    
    if withDivider:
        print("-" * 20 + "+" + "-" * 90)
    
    else:
        print("-" * 111)
        
def colourText(text : str, colour : str):
    """
    Returns a formatted string with the given colour depdending on the mode.
    
    Mode Options:
    - 0 = CMD Text Colours
    - 1 = HTML Text Colours
    
    Colour Options:
`    - Red
`    - Green
    - Yellow
    - Blue
    - Magenta
    - Cyan 
    - Black
    """
    
    return f"{colours.get(colour.title(), '\033[94m')}{text}{reset}"

def sendEmail(content, type):
    try:   
        with open(fr"{dir}\..\data\keys.txt") as f:
            secretKey = f.readline().strip()  
            environment = f.readline().strip()

        if "dev" in environment.lower() and True:
            return
        
        url = "https://benmercer.pythonanywhere.com/play2day/api/sendLogMessage"
        data = {
            "type": type.title(),
            "messegeContent": content + f"<br>Sent by Environment: {environment}",
            "secretKey": secretKey
        }
        
        response = requests.post(url, data=data)
                
    except Exception as e:
            message(f"Failed to send log message to server: {e}", type="error")