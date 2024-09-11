try:
    import __init__ as init
    import os
    import signal
    from PIL import Image, ImageDraw
    import pystray
    import threading
    
except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")

def loadCustomImage(filePath):
    return Image.open(filePath)

def stop():
    print("Stopping...")
    os.kill(os.getpid(), signal.SIGTERM)

def showInterface():
    ui.showInterface()

def startIcon():
    def onQuit(icon, item):
        stop()

    def onShowUI(icon, item):
        showInterface()

    menu = pystray.Menu(
        pystray.MenuItem("Stop Server", onQuit),
        pystray.MenuItem("Show Interface", onShowUI)
    )

    try:
        iconImage = loadCustomImage("backend/images/SmallLogo.png")
    except:
        iconImage = loadCustomImage(r"C:\Users\Ben Mercer\Documents\GitHub\Play2Day-Laser-Scoreboard\backend\images\SmallLogo.png")
    
    icon = pystray.Icon('Laser Tag Scoreboard', icon=iconImage, menu=menu)
    icon.run()

try:
    init.start()
    print("\n|----------------------------------------------------------------------------------------------------|\n")
    
    global ui
    import userInterf as ui
    
 
    threading.Thread(target=startIcon, daemon=True).start()
        
    print("User Interface starting")
    
    UI = threading.Thread(target=ui.startUI, daemon=True)
    UI.start()

    UI.join()
    
except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")
