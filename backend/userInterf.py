import time
import threading
import tkinter as tk
from tkinter import ttk
import __init__ as init
import ctypes

def startUI():
    global root, progress, startApp, revealUI

    def startApp():
        progress.start()
        progress["value"] = 0
        for i in range(5, 0, -1):
            countdownLbl.config(text=f"Web App Starting in {i} seconds...")
            root.update()
            time.sleep(1)
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
        try:
            from webApp import sendTestPacket
        
            sendTestPacket()
        except Exception as e:
            format.message(f"Error sending test packet: {e}", type="error")
            
    def showOutputWindow():
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)
       
    def hideOutputWindow():
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    testButton = tk.Button(interfaceWindow, text="Send Test Message", command=sendTestMessage)
    testButton.pack(pady=10)

    showWindowButton = tk.Button(interfaceWindow, text="Show Python Output", command=showOutputWindow)
    showWindowButton.pack(pady=10)
    
    hideWindowButton = tk.Button(interfaceWindow, text="Hide Python Output", command=hideOutputWindow)
    hideWindowButton.pack(pady=10)


    interfaceWindow.geometry("300x200")
    interfaceWindow.mainloop()

def startWebApp():
    try:
        print("\n|----------------------------------| STARTING WEB APP |----------------------------------------|\n")
        root.destroy()
        import webApp as webApp
    except Exception as e:
        print(f"An error occurred: {e}")
        input("...")

showInterface()