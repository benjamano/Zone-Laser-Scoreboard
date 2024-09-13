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
        try:
            iconImage = loadCustomImage(r"C:\Users\Ben Mercer\Documents\GitHub\Play2Day-Laser-Scoreboard\backend\images\SmallLogo.png")
        except:
            try:
                iconImage = loadCustomImage(r"\Users\benme\Documents\GitHub\Play2Day-Laser-Scoreboard\backend\images\SmallLogo.png")
            except:
                print("Failed to load custom image for icon. Using default.")
                iconImage = pystray.Icon.DEFAULT_IMAGE6
    icon = pystray.Icon('Laser Tag Scoreboard', icon=iconImage, menu=menu)
    threading.Thread(target=icon.run).start()
try:
    init.start()
    print("\n|----------------------------------------------------------------------------------------------------|\n")
    
    global ui
    import userInterf as ui
    
    startIcon()
    print("User Interface starting")
    
    threading.Thread(target=ui.startUI).run()

except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")
