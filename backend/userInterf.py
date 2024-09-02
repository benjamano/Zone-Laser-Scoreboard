import time
import threading
import tkinter as tk

def startWebApp():
    import ScoreBoard as main
    main.mainProgram()

def countdown_and_start():
    for i in range(30, 0, -1):
        countdown_label.config(text=f"Starting in {i} seconds...")
        root.update()
        time.sleep(1)
    startWebApp()

def startButtonClick():
    threading.Thread(target=countdown_and_start).start()

root = tk.Tk()
root.title("Arena Scoreboard")

start_button = tk.Button(root, text="Start Web App", command=startButtonClick)
start_button.pack(pady=20)

countdown_label = tk.Label(root, text="")
countdown_label.pack(pady=20)

root.mainloop()