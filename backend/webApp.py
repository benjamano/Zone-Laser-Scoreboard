from flask import Flask, render_template, redirect, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from scapy.all import sniff, conf, IP
import threading
import sys
import pyautogui

try:
    from func import format
except:
    sys.exit("Failed to import format tools")

db = SQLAlchemy()
socketio = SocketIO()

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Scoreboard.db'
app.secret_key = 'SJ8SU0D2987G887vf76g87whgd87qwgs87G78GF987EWGF87GF897GH8'

db.init_app(app)
socketio.init_app(app)

WM_APPCOMMAND = 0x0319
APPCOMMAND_PLAY_PAUSE = 0x0000
APPCOMMAND_NEXT = 0x000B
APPCOMMAND_PREV = 0x000C

try:
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
    with open(r"data/keys.txt", "r") as f:
        IP1 = str(f.readline().strip())
        IP2 = str(f.readline().strip())
        ETHERNET_INTERFACE = str(f.readline().strip())        

except Exception as e:
    format.message(f"An error occured while reading the file: {e}", type="error")
    format.message("Falling back to dev location", type="info")

    try:
        with open(r"backend\data\keys.txt", "r") as f:
            IP1 = str(f.readline().strip())
            IP2 = str(f.readline().strip())
            ETHERNET_INTERFACE = str(f.readline().strip())   
            
        format.message("Dev location found", type="success")
        
            
    except Exception as e:
        format.message(f"An error occured while reading the file: {e}", type="error")
        sys.exit("An error occured while reading the file.")
    
    
    
# -------------------------------------------------| ROUTES |------------------------------------------------- #



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/toggle')
def togglePlaybackRoute():
    
    togglePlayback()
    
    return "Playback toggled"

# -------------------------------------------------| SNIFFER |------------------------------------------------ #


def packet_callback(packet):
    try:
        
        if packet.haslayer(IP) and (packet[IP].src == IP1 or packet[IP].src == IP2):
            # Use packet.show() directly instead of packet.original.show()
            packet_info = packet.show(dump=True)
            packet_bytes = bytes(packet).hex()

            with open(r"packet.txt", "a") as f:
                f.write(str(packet_info))
                f.write("\n")
                f.write(str(packet_bytes))
                f.write("\n")
                
            format.message(f"Packet info: {packet_info}\nPacket bytes: {packet_bytes}")

            socketio.emit('packet_data', {'data': packet_info + '\n' + packet_bytes})
            
        elif devMode == "true":
            packet_info = packet.show(dump=True)
            packet_bytes = bytes(packet).hex()

            with open(r"packet.txt", "a") as f:
                try:
                    f.write(str(packet_info))
                except:
                    f.write("Failed to write packet info")
                f.write("\n")
                try:
                    f.write(str(packet_bytes))
                except:
                    f.write("Failed to write packet bytes")
                f.write("\n")
                
            format.message(f"Packet info: {packet_info}")

            socketio.emit('packet_data', {'data': packet_info + '\n' + packet_bytes})
        
    except Exception as e:
        format.message(f"An error occurred while handling the packet: {e}", type="error")
        sys.exit("An error occurred while handling the packet.")

def start_sniffing():
    print("Starting packet sniffer...")
    
    if devMode == "true":
        try:
            sniff(prn=packet_callback, store=False)
        
        except Exception as e:
            format.message(f"An error occurred while sniffing: {e}", type="error")
            sys.exit("An error occurred while sniffing.")
    
    else:
        try:
            sniff(prn=packet_callback, store=False, iface=ETHERNET_INTERFACE)
        except Exception as e:
            format.message(f"An error occurred while sniffing: {e}", type="error")
            format.message(f"Starting without Ethernet", type="info")
        
        
        

# ---------------------------------------------| SOCKET HANDLING |------------------------------------------- #



@socketio.on('connect')
def handle_connect():
    format.message("Sniffer Client connected", type="success")
    emit('server_response', {'message': 'Connected to the server!'})

@socketio.on('client_event')
def handle_client_event(json):
    format.message(f"Received event: {json}")
    emit('server_response', {'message': 'Received your event!'})
    
    
# ----------------------------------------------------------------------------------------------------------- #


def togglePlayback():
    #Assuming spotify is always paused when first run
    pyautogui.press('playpause')


sniffing_thread = threading.Thread(target=start_sniffing)
sniffing_thread.daemon = True 
sniffing_thread.start()