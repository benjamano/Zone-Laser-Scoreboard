import datetime
import logging
import ctypes
import os
import sys

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

    try:
        logFilePath = fr"{dir}\app.log"
        
    except:
        sys.exit("Failed to open log file.")
        
    logging.basicConfig(filename=logFilePath, level=logging.DEBUG)

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

        if type == "Error":
            logger.error(f"{logtime} | {message}")
        elif type == "Warning":
            logger.warning(f"{logtime} | {message}")
        elif type == "Success":
            logger.info(f"{logtime} | {message}")
        
        print(messagetosend)
        
    except Exception as e:
        print(f"Error sending log message: {e}")
    
    
def newline(withDivider=True, baronly=False):
    
    """withdivider : defaults to true, if true, adds a divider ('+')."""
    
    if baronly:
        print("\t\t    |")
        
        return
    
    if withDivider:
        print("-" * 20 + "+" + "-" * 90)
    
    else:
        print("-" * 111)