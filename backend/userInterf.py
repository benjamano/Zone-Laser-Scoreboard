import time
import threading
import tkinter as tk
from tkinter import ttk
import __init__ as init

def StartUI():
    
    global root, progress, StartApp
    
    def StartApp():
        for i in range(5, 0, -1):
            countdownlbl.config(text=f"Web App Starting in {i} seconds...")
            root.update()
            time.sleep(1)
        
        StartWebApp()
    
    root = tk.Tk()
    root.title("Arena Scoreboard Starting...")
    
    creditslbl = tk.Label(root, text="""Laser Tag Arena Scoreboard
Programmed by Ben Mercer""")
    creditslbl.pack(pady=10)

    countdownlbl = tk.Label(root, text="")
    countdownlbl.pack(pady=5)
    
    progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", maximum=6)
    progress.pack(pady=20)
    progress.start()
    
    root.geometry("300x200")

    StartApp()

    root.mainloop()
    

def StartWebApp():
    try:

        print("\n|----------------------------------| STARTING WEB APP |----------------------------------------|\n")
        
        root.destroy()
        
        import webApp as webApp
        
        webApp.startWebApp()
        
    except Exception as e:
        print(f"An error occured: {e}")
        close = str(input("..."))

StartUI()