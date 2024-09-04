import time
import threading
import tkinter as tk


def StartUI():
    
    global root
    
    def StartApp():
        for i in range(5, 0, -1):
            countdown_label.config(text=f"Starting in {i} seconds...")
            root.update()
            time.sleep(1)
        
        StartWebApp()
    
    root = tk.Tk()
    root.title("Arena Scoreboard")

    countdown_label = tk.Label(root, text="")
    countdown_label.pack(pady=20)
    
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
    

