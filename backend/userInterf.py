import time
import threading
import tkinter as tk
from tkinter import ttk
import ctypes
from webApp import WebApp
import subprocess
import os

web_app = WebApp()

def startUI():
    global root, progress, startApp, revealUI

    def startApp():
        progress.start()
        progress["value"] = 0
        for i in range(5, 0, -1):
            countdownLbl.config(text=f"Web App Starting in {i} seconds...")
            root.update()
            time.sleep(1)
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
    interfaceWindow = tk.Tk()
    interfaceWindow.title("Control Panel")
    

    def sendTestMessage():
        threading.Thread(target=web_app.sendTestPacket()).start()
        
    def sendGameStartMessage():
        threading.Thread(target=web_app.sendTestPacket(type="start")).start()
    
    def sendGameEndMessage():
        threading.Thread(target=web_app.sendTestPacket(type="end")).start()

    def showOutputWindow():
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)

    def hideOutputWindow():
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
    def openFileDir():
        filedir = os.path.dirname(os.path.realpath(__file__))
        print(f"Opening file directory: {filedir}")
        subprocess.Popen(rf'explorer /select, "{filedir}"')
        
    def restartDMX():
        threading.Thread(target=web_app.setUpDMX).start()
        
    def BrightnessSet50BulkHeads():
        threading.Thread(target=web_app.setBulkheadsTo50Brightness).start()
        
    def TurnOffBulkHeadLights():
        threading.Thread(target=web_app.turnBulkHeadLightsOff).start()

    creditsLbl = tk.Label(interfaceWindow, text="Test Panel")
    creditsLbl.pack(pady=10)

    testButton = tk.Button(interfaceWindow, text="Send Test Message", command=sendTestMessage)
    testButton.pack(pady=10)
    
    startTestButton = tk.Button(interfaceWindow, text="Send Game Start Test Message", command=sendGameStartMessage)
    startTestButton.pack(pady=10)
    
    EndTestButton = tk.Button(interfaceWindow, text="Send Game End Test Message", command=sendGameEndMessage)
    EndTestButton.pack(pady=10)
    
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

    TurnOffBulkHeadLightsButton = tk.Button(interfaceWindow, text="Set Bulkhead Lights to 50%", command=TurnOffBulkHeadLights)
    TurnOffBulkHeadLightsButton.pack(pady=10)

    interfaceWindow.geometry("500x400")
    interfaceWindow.mainloop()

def startWebApp():
    web_app.start()
