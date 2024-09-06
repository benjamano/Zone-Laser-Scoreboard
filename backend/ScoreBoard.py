try:
    import __init__ as init
    import os
    import signal
    
except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")

def load_custom_image(file_path):
    return Image.open(file_path)

def stop():
    print("Stopping...")
    os.kill(os.getpid(), signal.SIGTERM)

def startIcon():
    def onQuit(icon, item):
        stop()

    menu = pystray.Menu(pystray.MenuItem("Stop Server", onQuit))
    try:
        icon_image = load_custom_image("backend/images/SmallLogo.png")
    except:
        icon_image = load_custom_image("C:\Users\Ben Mercer\Documents\GitHub\Play2Day-Laser-Scoreboard\backend\images\SmallLogo.png")
    
    icon = pystray.Icon('Laser Tag Scoreboard', icon=icon_image, menu=menu)
    icon.run()

try:
    init.start()
    print("\n|----------------------------------------------------------------------------------------------------|\n")
    
    from PIL import Image, ImageDraw
    from pystray import Icon as icon, Menu as menu, MenuItem as item
    import pystray
    import threading
    
    threading.Thread(target=startIcon).start()
        
    print("""
██╗░░░░░░█████╗░░██████╗███████╗██████╗░░░░░░░████████╗░█████╗░░██████╗░
██║░░░░░██╔══██╗██╔════╝██╔════╝██╔══██╗░░░░░░╚══██╔══╝██╔══██╗██╔════╝░
██║░░░░░███████║╚█████╗░█████╗░░██████╔╝█████╗░░░██║░░░███████║██║░░██╗░
██║░░░░░██╔══██║░╚═══██╗██╔══╝░░██╔══██╗╚════╝░░░██║░░░██╔══██║██║░░╚██╗
███████╗██║░░██║██████╔╝███████╗██║░░██║░░░░░░░░░██║░░░██║░░██║╚██████╔╝
╚══════╝╚═╝░░╚═╝╚═════╝░╚══════╝╚═╝░░╚═╝░░░░░░░░░╚═╝░░░╚═╝░░╚═╝░╚═════╝░

░██████╗░█████╗░░█████╗░██████╗░███████╗██████╗░░█████╗░░█████╗░██████╗░██████╗░
██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗
╚█████╗░██║░░╚═╝██║░░██║██████╔╝█████╗░░██████╦╝██║░░██║███████║██████╔╝██║░░██║
░╚═══██╗██║░░██╗██║░░██║██╔══██╗██╔══╝░░██╔══██╗██║░░██║██╔══██║██╔══██╗██║░░██║
██████╔╝╚█████╔╝╚█████╔╝██║░░██║███████╗██████╦╝╚█████╔╝██║░░██║██║░░██║██████╔╝
╚═════╝░░╚════╝░░╚════╝░╚═╝░░╚═╝╚══════╝╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░

██████╗░██╗░░░██╗  ██████╗░███████╗███╗░░██╗  ███╗░░░███╗███████╗██████╗░░█████╗░███████╗██████╗░
██╔══██╗╚██╗░██╔╝  ██╔══██╗██╔════╝████╗░██║  ████╗░████║██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗
██████╦╝░╚████╔╝░  ██████╦╝█████╗░░██╔██╗██║  ██╔████╔██║█████╗░░██████╔╝██║░░╚═╝█████╗░░██████╔╝
██╔══██╗░░╚██╔╝░░  ██╔══██╗██╔══╝░░██║╚████║  ██║╚██╔╝██║██╔══╝░░██╔══██╗██║░░██╗██╔══╝░░██╔══██╗
██████╦╝░░░██║░░░  ██████╦╝███████╗██║░╚███║  ██║░╚═╝░██║███████╗██║░░██║╚█████╔╝███████╗██║░░██║
╚═════╝░░░░╚═╝░░░  ╚═════╝░╚══════╝╚═╝░░╚══╝  ╚═╝░░░░░╚═╝╚══════╝╚═╝░░╚═╝░╚════╝░╚══════╝╚═╝░░╚═╝""")
    

    print("User Interface starting")

    import userInterf as ui
    
    ui.StartUI()

        
except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")
    #sys.exit(f"An error occurred: {e}")
    