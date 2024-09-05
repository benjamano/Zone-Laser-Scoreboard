import time
import threading
import tkinter as tk


def StartUI():
    
    global root
    
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
    
    root.geometry("300x100")
    
    StartApp()

    root.mainloop()
        

def StartWebApp():
    try:

        print("\n|----------------------------------| STARTING WEB APP |----------------------------------------|\n")
        
        root.destroy()
        
        import webApp as webApp
        
        webApp.app.run(host="0.0.0.0", port=8080)
        
    except Exception as e:
        print(f"An error occured: {e}")
        close = str(input("..."))
    