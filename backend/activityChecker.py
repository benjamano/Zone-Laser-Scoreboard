# This file is run at startup of the PC.
# It pings the running flask server, if there is no response, it will restart / start the server.
# This is a background activity

try:
    import requests
    import time
    import os
    import subprocess
    import socket
    import ctypes
    
except Exception as e:
    print(f"Failed to import required modules, {e}")
    input("Press enter to exit")
    
print("Web App Status Checker Started, hiding console")
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

tries = 0
    
while True:
    try:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception as e:
            print(f"Error finding local IP: {e}")
        
        dir = os.path.dirname(os.path.realpath(__file__))
        
        print(f"Checking server status at {ip} with directory {dir}")
        
        try:
            response = requests.get(fr"http://{ip}:8080/ping").status_code
        except Exception as e:
            print(f"Failed to ping server: {e}")
            response = 500
        
        if response != 500:
            tries = 0
            pass
        else:
            tries += 1
            if tries == 7:
                subprocess.Popen(["python", fr"{dir}\ScoreBoard.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            elif tries > 12:
                os.system("shutdown /r /t 1")
                tries = 0

        time.sleep(60)
    except Exception as e:
        print(f"Failed to check server status: {e}")
        time.sleep(60)