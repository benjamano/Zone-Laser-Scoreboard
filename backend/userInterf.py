import time
import threading
import tkinter as tk


def StartUI():
    
    def countdown_and_start():
        for i in range(10, 0, -1):
            countdown_label.config(text=f"Starting in {i} seconds...")
            root.update()
            time.sleep(1)
        
        StartWebApp()
    
    def startButtonClick():
        threading.Thread(target=countdown_and_start).start()
    
    root = tk.Tk()
    root.title("Arena Scoreboard")

    start_button = tk.Button(root, text="Start Web App", command=startButtonClick)
    start_button.pack(pady=20)

    countdown_label = tk.Label(root, text="")
    countdown_label.pack(pady=20)

    root.mainloop()
        

def StartWebApp():
    try:

        print("\n|----------------------------------| STARTING WEB APP |----------------------------------------|\n")
        
        import sys
        import subprocess
        import os
        
        pythonExecutable = sys.executable

        flaskPath = os.path.abspath('webApp.py')

        subprocess.Popen([pythonExecutable, flaskPath],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        
    except Exception as e:
        print(f"An error occured: {e}")
        close = str(input("..."))
    

