import datetime
import logging
import ctypes
import os

try:
    with open(r"data/dev.txt") as f:
        devMode = str(f.readline().strip())
except:
    try:
        with open(r"backend\data\dev.txt") as f:
            devMode = str(f.readline().strip())
        
        format.message(f"Developer mode is {devMode}")
    except:
        devMode = "False"
        pass

try:
    
    logger = logging.getLogger("webAppLogger")

    if devMode == "true":
        logFilePath = os.path.join(r"C:\Users\benme\Documents\GitHub\Play2Day-Laser-Scoreboard\backend\app.log")
    else:
        logFilePath = os.path.join(r"C:\Users\Ben Mercer\Documents\GitHub\Play2Day-Laser-Scoreboard\backend\app.log")

    logging.basicConfig(filename=r'\app.log', level=logging.DEBUG)

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

        color = colors.get(type, "\033[94m")
        
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
        else:
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