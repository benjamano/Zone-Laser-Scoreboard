try:

    from flask import Flask, render_template, redirect, request, session, jsonify
    from flask_sqlalchemy import SQLAlchemy
    from flask_socketio import SocketIO, emit
    from scapy.all import sniff, conf, IP
    import threading
    import sys
    import pyautogui
    import logging
    import ctypes as ctypes
    import datetime
    import os
    import signal
    import time
    import obswebsocket
    from obswebsocket import obsws, requests
    import eventlet
    
except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")

try:
    from func.format import format
except Exception as e:
    print(f"An error occurred attempting to import format tools: {e}")
    try:
        from func import format
        
        print("Imported functions")
        
    except Exception as e:

        try:
            import func.format as format
            
        except:

            print(f"An error occurred: {e}")
            input("Press any key to exit...")
    
try:
    
    global db, socketio, app, WM_APPCOMMAND, APPCOMMAND_PLAY_PAUSE, APPCOMMAND_NEXT, APPCOMMAND_PREV
    
    db = SQLAlchemy()
    socketio = SocketIO()

    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Scoreboard.db'
    app.secret_key = 'SJ8SU0D2987G887vf76g87whgd87qwgs87G78GF987EWGF87GF897GH8'

    app.logger.disabled = True
    log = logging.getLogger('werkzeug')
    log.disabled = True

    logging.getLogger('werkzeug').disabled = True

    db.init_app(app)
    socketio.init_app(app)

    WM_APPCOMMAND = 0x0319
    APPCOMMAND_PLAY_PAUSE = 0x0000
    APPCOMMAND_NEXT = 0x000B
    APPCOMMAND_PREV = 0x000C
    
except Exception as e:
    format.message(f"Failed to init variables: {e}", type="error")

def openFiles():
    format.message("Opening Files")
    
    try:
        global IP1, IP2, ETHERNET_INTERFACE, devMode, ENDGAMEBYTES, STARTGAMEBYTES, OBSSERVERIP, OBSSERVERPORT, NOTNEEDED_OBSSERVERPASSWORD
        
        with open(r"data/dev.txt") as f:
            devMode = str(f.readline().strip())
    except:
        try:
            with open(r"backend\data\dev.txt") as f:
                devMode = str(f.readline().strip())
        
            format.message(f"Developer mode is {devMode}")
        except:
            devMode = "False"
            pass

    try:
        f = open(r"C:\Users\Ben Mercer\Documents\GitHub\Play2Day-Laser-Scoreboard\backend\data\keys.txt", "r")
    except Exception as e:
        try:
            format.message(f"An error occured while reading the file: {e}", type="error")
            format.message("Falling back to dev location", type="info")
        
            f = open(r"backend\data\keys.txt", "r")
        
        except Exception as e:
            format.message(f"An error occured while reading the file: {e}", type="error")#
            format.message("Falling back to other location", type="info")
            
            f = open(r"C:\Users\benme\Documents\GitHub\Play2Day-Laser-Scoreboard\backend\data\keys.txt", "r")
        
        format.message("Dev location found", type="success")
        
    finally:
        IP1 = str(f.readline().strip())
        IP2 = str(f.readline().strip())
        ETHERNET_INTERFACE = str(f.readline().strip())      
        OBSSERVERIP = str(f.readline().strip())
        OBSSERVERPORT = int(f.readline().strip())
        NOTNEEDED_OBSSERVERPASSWORD = str(f.readline().strip())
        
        format.message("Files opened", type="success")
        
        f.close()
    
    
# try:
    
#     app.run(host="0.0.0.0", port=8080, debug=True)

# except Exception as e:
#     format.message(f"Failed to start web server: {e}", type="error")

# -------------------------------------------------| ROUTES |------------------------------------------------- #



@app.route('/')
def index():
    return render_template('index.html', OBSConnected=OBSConnected)

@app.route('/scoreboard')
def scoreboard():
    return render_template('scoreboard.html')


@app.route('/toggle')
def togglePlaybackRoute():
    
    togglePlayback()
    
    return jsonify({"message" : "Playback toggled"})

@app.route('/end')
def terminateServer():

    logging.shutdown()
    
    os.kill(os.getpid(), signal.SIGTERM)
    

# -------------------------------------------------| SNIFFER |------------------------------------------------ #


def packet_callback(packet):
    try:
        
        if packet.haslayer(IP) and (packet[IP].src == IP1 or packet[IP].src == IP2) and packet[IP].dst == "192.168.0.255":
            packet_info = packet.show(dump=True)
            packet_bytes = bytes(packet).hex()
            

            try:
                with open(r"packet.txt", "a") as f:
                    f.write(str(packet_bytes))
                    f.write("\n")
            except:
                pass
                
            #format.message(f"Packet info: {packet_info}\nPacket bytes: {packet_bytes}")
            #format.message(f"Packet bytes: {packet_bytes}")
            
            if "342c403031352c30" in str(packet_bytes) or "342c403031342c30" in str(packet_bytes) or "342c403031352c30" in str(packet_bytes):
                format.message(f"Game started at {datetime.datetime.now()}", type="success")
                socketio.emit('game_start', {'data': str(datetime.date.today()) + '---->  ' + packet_info + '\n >>>>  ' + packet_bytes})
                                
            elif "342c202c30" in str(packet_bytes):
                format.message(f"Game ended at {datetime.datetime.now()}", type="success")
                socketio.emit('game_end', {'data': str(datetime.date.today()) + '---->  ' + packet_info + '\n >>>>  ' + packet_bytes})
                
            

            # socketio.emit('packet_data', {'data': str(datetime.date.today()) + '---->  ' + packet_info + '\n >>>>  ' + packet_bytes})
            
        # elif devMode == "true":
        #     packet_info = packet.show(dump=True)
        #     packet_bytes = bytes(packet).hex()

            # with open(r"packet.txt", "a") as f:
            #     try:
            #         f.write(str(packet_info))
            #     except:
            #         f.write("Failed to write packet info")
            #     f.write("\n")
            #     try:
            #         f.write(str(packet_bytes))
            #     except:
            #         f.write("Failed to write packet bytes")
            #     f.write("\n")
                
            # format.message(f"Packet info: {packet_info}")

            # socketio.emit('packet_data', {'data': str(datetime.date.today()) + '---->  ' + packet_info + '\n >>>>  ' + packet_bytes})
        
    except Exception as e:
        format.message(f"An error occurred while handling the packet: {e}", type="error")

def start_sniffing():
    print("Starting packet sniffer...")
    
    if devMode == "true":
        try:
            sniff(prn=packet_callback, store=False)
        
        except Exception as e:
            format.message(f"An error occurred while sniffing: {e}", type="error")
            input("...")
    
    else:
        try:
            sniff(prn=packet_callback, store=False, iface=ETHERNET_INTERFACE)
        except Exception as e:
            format.message(f"An error occurred while sniffing: {e}", type="error")
            format.message(f"Starting without Ethernet", type="info")
        
        
        

# ---------------------------------------------| SOCKET HANDLING |------------------------------------------- #



@socketio.on('connect')
def handle_connect():
    format.message("Sniffer Client connected")
    emit('server_response', {'message': 'Connected to the server!'})

@socketio.on('client_event')
def handle_client_event(json):
    format.message(f"Received event: {json}")
    emit('server_response', {'message': 'Received your event!'})
    
    
# ----------------------------------------------- | PLAYBACK |------------------------------------------------------------ #


def togglePlayback():
    #Assuming spotify is always paused when first run
    pyautogui.press('playpause')
    
    
# ---------------------------------------------- | OBS CONTROL |----------------------------------------------------------- #

def obsConnect():
    
    try:
        
        global OBSConnected
        
        format.message("Connecting to OBS")
        
        ws = obsws(OBSSERVERIP, OBSSERVERPORT, NOTNEEDED_OBSSERVERPASSWORD)
        
        ws.connect()
        
        format.message("Connected to OBS", type="success")
        
        OBSConnected = True
        
        #ws.call(requests.SetCurrentProgramScene(scene_name))
        
    except Exception as e:
        
        format.message(f"Failed to connect to OBS: {e}", type="error")
    

openFiles()

def startServer():
    
    eventlet.wsgi.server(eventlet.listen(('', 8080)), app)

try:
    
    time.sleep(2)
    
    OBSConnected = False
    
    #socketio.run(app)
    
    #app.run(host="0.0.0.0", port=8080, debug=True)
    
    obsConnect()
    
    print("Web App Started, hiding console")

    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    sniffing_thread = threading.Thread(target=start_sniffing)
    sniffing_thread.daemon = True 
    sniffing_thread.start()
    
    threading.Thread(target=startServer).start()

except Exception as e:
    format.message(f"Failed to start threading: {e}", type="error")