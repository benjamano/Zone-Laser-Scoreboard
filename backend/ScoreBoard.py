try:
    import __init__ as init
    import os
    import signal
    import threading
    from func import format
    
except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")

def loadCustomImage(filePath):
    from PIL import Image, ImageDraw
    return Image.open(filePath)

def stop():
    print("Stopping...")
    os.kill(os.getpid(), signal.SIGTERM)

def showInterface():
    ui.showInterface()

def startIcon():
    from PIL import Image, ImageDraw
    import pystray
    
    def onQuit(icon, item):
        stop()

    def onShowUI(icon, item):
        showInterface()

    menu = pystray.Menu(
        pystray.MenuItem("Stop Server", onQuit),
        pystray.MenuItem("Show Interface", onShowUI)
    )

    try:
        dir = os.path.dirname(os.path.realpath(__file__))
        iconImage = loadCustomImage(fr"{dir}\images\SmallLogo.png")
        
        icon = pystray.Icon('Laser Tag Scoreboard', icon=iconImage, menu=menu)
        threading.Thread(target=icon.run).start()
        
    except:
        print("Failed to load custom image for icon. Not Running Icon.")
    
try:
    init.start()
    format.newline()
    
    global ui
    import userInterf as ui
    
    startIcon()
    format.message("User Interface starting")
    
    threading.Thread(target=ui.startUI).run()

except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")
