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
    
while True:
    try:
        try:
            #print("Finding local IP")
            # Create a dummy socket connection to find the local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception as e:
            print(f"Error finding local IP: {e}")
        
        dir = os.path.dirname(os.path.realpath(__file__))
        
        print(f"Checking server status at {ip} with directory {dir}")
        
        try:
            #print("Pinging server")
            response = requests.get(fr"http://{ip}:8080/ping").status_code
        except Exception as e:
            print(f"Failed to ping server: {e}")
            response = 500
            
        print(f"Server response: {response}")

        if response == 200:
            #print("Server is running, no action needed")
            pass
        else:
            #ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)
            
            # print("\n\n\n\n\n")
            # print("\033[91mWARNING: SERVER IS NOT RUNNING\033[0m")
            # print("\n\n")
            # print("\033[91mSTARTING SERVER\033[0m")
            
            subprocess.Popen(["python", fr"{dir}\ScoreBoard.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # time.sleep(10)
            
            # ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

        time.sleep(60)
    except Exception as e:
        print(f"Failed to check server status: {e}")
        time.sleep(60)