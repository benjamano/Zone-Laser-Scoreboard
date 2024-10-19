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
    
except:
    print("Failed to import required modules")
    input("Press enter to exit")
    
print("Web App Status Checker Started, hiding console")
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
while True:
    try:
        ip = socket.gethostbyname(socket.gethostname())
        
        dir = os.path.dirname(os.path.realpath(__file__))
        
        try:
            response = requests.get(fr"http://{ip}:8080/ping").status_code
        except Exception as e:
            print(f"Failed to ping server: {e}")
            response = 500

        if response == 200:
            pass
        else:
            print("Server is not running, starting server")
            subprocess.Popen(["python", fr"{dir}\ScoreBoard.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)

        time.sleep(60)
    except Exception as e:
        print(f"Failed to check server status: {e}")
        time.sleep(60)