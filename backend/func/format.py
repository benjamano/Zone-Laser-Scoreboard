import datetime
import logging
import ctypes
import os
import sys
import requests

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

colors = {
        "Info": "\033[94m",    
        "Warning": "\033[93m", 
        "Error": "\033[91m",  
        "Success": "\033[92m"  
}

def message(message, type="Info", date=True, newline=False):
    """Possible types: Info, Warning, Error, Success.
    \ndate : defaults to true, this should be kept true as it will break the look of the log if false.
    \nnewline : defaults to false, if true, will add a new line before the message."""
    
    try:
        type = type.title()
    
        logtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        messagetosend = ""
        
        reset = "\033[0m"

        color = colors.get((type.title()), "\033[94m")
        
        if newline:
            messagetosend += "\n"
        
        if not date:
            messagetosend += f"| {color}{type.title()}{reset} : {message}"
            
        else:
            messagetosend += f"{logtime} | {color}{type.title()}{reset} : {message}"

        if type.title() == "Error":
            logger.error(f"{logtime} | {message}")
        elif type.title() == "Warning":
            logger.warning(f"{logtime} | {message}")
            
        try:            
            if type.title() == "Error":
                
                with open(fr"{dir}\..\data\keys.txt") as f:
                    secretKey = f.readline().strip()  
                    environment = f.readline().strip()
                    
                if "dev" in environment.lower():
                    pass
                else:
                    url = "https://benmercer.pythonanywhere.com/play2day/api/sendLogMessage"
                    data = {
                        "type": type.title(),
                        "messegeContent": message + f"<br>Sent by Environment: {environment}",
                        "secretKey": secretKey
                    }
                    try:
                        response = requests.post(url, data=data)
                        response.raise_for_status()
                    except Exception as e:
                        pass
                        #print(f"Failed to send log message to server: {e}")
                    
        except Exception as e:
            pass
            #print(f"Failed to send log message to server: {e}")

        print(messagetosend)
        
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