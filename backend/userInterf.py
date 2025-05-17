import threading
import tkinter as tk
from tkinter import ttk
import ctypes
import subprocess
import os
import requests
import socket

def startUI():
    global root, progress, startApp, revealUI

    def startApp():
        # progress.start()
        # progress["value"] = 0
        # for i in range(5, 0, -1):
        #     countdownLbl.config(text=f"Web App Starting in {i} seconds...")
        #     root.update()
        #     time.sleep(1)
        root.destroy()
        startWebApp()

    def revealUI():
        root.deiconify()

    root = tk.Tk()
    root.title("Arena Scoreboard Starting...")

    creditsLbl = tk.Label(root, text="Laser Tag Arena Scoreboard\nProgrammed by Ben Mercer")
    creditsLbl.pack(pady=10)

    countdownLbl = tk.Label(root, text="")
    countdownLbl.pack(pady=5)

    progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", maximum=6, value=0)
    progress.pack(pady=20)

    root.geometry("300x200")
    
    startApp()
    
    root.mainloop()

def showInterface():
    try:
        # Create a dummy socket connection to find the local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        _localIp = s.getsockname()[0]
        s.close()
    except Exception as e:
        format.message(f"Error finding local IP: {e}")
    
    interfaceWindow = tk.Tk()
    interfaceWindow.title("Control Panel")
    
    def sendTestMessage():
        threading.Thread(target=webApp.sendTestPacket()).start()
    
    def restartPC():
        restartPCThread = threading.Thread(target=webApp.restartApp("UI Request"))
        restartPCThread.daemon = True
        restartPCThread.start()
        
    def sendGameStartMessage():
        threading.Thread(target=lambda: webApp.sendTestPacket(type="start")).start()
    
    def sendGameEndMessage():
        threading.Thread(target=webApp.sendTestPacket(type="end")).start()

    def showOutputWindow():
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)

    def hideOutputWindow():
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
    def openFileDir():
        filedir = os.path.dirname(os.path.realpath(__file__))
        print(f"Opening file directory: {filedir}")
        subprocess.Popen(rf'explorer /select, "{filedir}"')
        
    def restartDMX():
        threading.Thread(target=webApp.setUpDMX).start()
        
    def BrightnessSet50BulkHeads():
        threading.Thread(target=webApp.setBulkheadsTo50Brightness).start()
        
    def TurnOffBulkHeadLights():
        threading.Thread(target=webApp.turnBulkHeadLightsOff).start()

    def RefreshPages():
        threading.Thread(target=refreshAllPages).start()
        
    def refreshAllPages():
        response = requests.post(f'http://{_localIp}:8080/sendMessage', data={"message": "", "type": "refreshPage"})
        
    def sendGunScoreTestMessage():
        threading.Thread(target=webApp.sendTestPacket(type="gunscore")).start()
        
    creditsLbl = tk.Label(interfaceWindow, text="Test Panel")
    creditsLbl.pack(pady=10)

    testButton = tk.Button(interfaceWindow, text="Send Test Message", command=sendTestMessage)
    testButton.pack(pady=10)
    
    startTestButton = tk.Button(interfaceWindow, text="Send Game Start Test Message", command=sendGameStartMessage)
    startTestButton.pack(pady=10)
    
    EndTestButton = tk.Button(interfaceWindow, text="Send Game End Test Message", command=sendGameEndMessage)
    EndTestButton.pack(pady=10)
    
    GunScoreTestButton = tk.Button(interfaceWindow, text="Send Gun Score Test Message", command=sendGunScoreTestMessage)
    GunScoreTestButton.pack(pady=10)
    
    fileDirButton = tk.Button(interfaceWindow, text="Open file directory", command=openFileDir)
    fileDirButton.pack(pady=10)

    showWindowButton = tk.Button(interfaceWindow, text="Show Python Output", command=showOutputWindow)
    showWindowButton.pack(pady=10)
    
    hideWindowButton = tk.Button(interfaceWindow, text="Hide Python Output", command=hideOutputWindow)
    hideWindowButton.pack(pady=10)

    restartDMXButton = tk.Button(interfaceWindow, text="Re-Start DMX Service", command=restartDMX)
    restartDMXButton.pack(pady=10)
    
    BrightnessSet50BulkHeadsButton = tk.Button(interfaceWindow, text="Set Bulkhead Lights to 50%", command=BrightnessSet50BulkHeads)
    BrightnessSet50BulkHeadsButton.pack(pady=10)

    TurnOffBulkHeadLightsButton = tk.Button(interfaceWindow, text="Turn off Bulkhead lights", command=TurnOffBulkHeadLights)
    TurnOffBulkHeadLightsButton.pack(pady=10)
    
    RestartPCButton = tk.Button(interfaceWindow, text="Restart PC", command=restartPC)
    RestartPCButton.pack(pady=10)
    
    RefreshPagesButton = tk.Button(interfaceWindow, text="Refresh connected Pages", command=RefreshPages)
    RefreshPagesButton.pack(pady=10)
    
    interfaceWindow.geometry("600x700")
    interfaceWindow.mainloop()

def startWebApp():
    from webApp import WebApp
    
    global webApp
    
    webApp = WebApp()
    
    webApp.start()
