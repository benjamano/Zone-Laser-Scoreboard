from flask import Flask, render_template, redirect, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from scapy.all import sniff, conf, IP
import threading
import sys
import requests
import ctypes
from ctypes import wintypes
import pywin32

db = SQLAlchemy()
socketio = SocketIO()

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Scoreboard.db'
app.secret_key = 'SJ8SU0D2987G887vf76g87whgd87qwgs87G78GF987EWGF87GF897GH8'

db.init_app(app)
socketio.init_app(app)

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
SCOPE = 'user-modify-playback-state'

WM_APPCOMMAND = 0x0319
APPCOMMAND_PLAY_PAUSE = 0x0000
APPCOMMAND_NEXT = 0x000B
APPCOMMAND_PREV = 0x000C

try:
    with open("data/keys.txt", "r") as f:
        ClientId = f.readline().strip()
        ClientSecret = f.readline().strip()
        REDIRECT_URI = str(f.readline().strip())
        IP1 = str(f.readline().strip())
        IP2 = str(f.readline().strip())
        ETHERNET_INTERFACE = str(f.readline().strip())        
        ACCESS_TOKEN = str(f.readline().strip())
        
except Exception as e:
    print(f"An error occured while reading the file: {e}")
    sys.exit()
    
# -------------------------------------------------| ROUTES |------------------------------------------------- #



@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/login')
# def login():
#     auth_url = f"{AUTH_URL}?response_type=code&client_id={ClientId}&scope={SCOPE}&redirect_uri={REDIRECT_URI}"
#     return redirect(auth_url)

# @app.route('/callback')
# def callback():
#     code = request.args.get('code')
#     if not code:
#         return 'Authorization failed', 400

#     token_data = {
#         'grant_type': 'authorization_code',
#         'code': code,
#         'redirect_uri': REDIRECT_URI,
#         'client_id': ClientId,
#         'client_secret': ClientSecret
#     }
    
#     token_response = requests.post(TOKEN_URL, data=token_data)
#     if token_response.status_code != 200:
#         return 'Failed to retrieve access token', 400

#     token_info = token_response.json()
#     session['access_token'] = token_info['access_token']
    
#     print(token_info)

#     return 'Access token retrieved! You can now control playback.'

@app.route('/play')
def resume_playback():
    play_pause()

# -------------------------------------------------| SNIFFER |------------------------------------------------ #

def packet_callback(packet):
    if packet.haslayer(IP) and (packet[IP].src == IP1 or packet[IP].src == IP2):
        
        packet_info = packet.original.show(dump=True)
        packet_bytes = bytes(packet).hex()
        
        with open("packet.txt", "a") as f:
            f.write(str(packet_info))
            f.write("\n")
            f.write(str(packet_bytes))
            f.write("\n")
        
        
        socketio.emit('packet_data', {'data': packet_info + '\n' + packet_bytes})
    
    
    # if packet.haslayer(IP) and (packet[IP].dst == "192.168.1.126"):
    #     packet_info = packet.show(dump=True)
    #     packet_bytes = bytes(packet).hex()
    #     socketio.emit('packet_data', {'data': packet_info + '\n' + packet_bytes})
        
    
    #packet_info = packet.show(dump=True)
    #packet_bytes = bytes(packet).hex()
    
    #print(packet)
    #socketio.emit('packet_data', {'data': packet_info + '\n' + packet_bytes})
        

def start_sniffing():
    conf.L3socket = conf.L3socket
    print("Starting packet sniffer...")
    sniff(prn=packet_callback, store=False, iface=ETHERNET_INTERFACE)
    #sniff(prn=packet_callback, store=False)


# ---------------------------------------------| SOCKET HANDLING |------------------------------------------- #



@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('server_response', {'message': 'Connected to the server!'})

@socketio.on('client_event')
def handle_client_event(json):
    print(f"Received event: {json}")
    emit('server_response', {'message': 'Received your event!'})
    
    
# ----------------------------------------------------------------------------------------------------------- #

def send_media_key(app_command):
    ctypes.windll.user32.SendMessageW(
        pywin32.GetForegroundWindow(),
        WM_APPCOMMAND,
        0,
        app_command << 16
    )

def play_pause():
    send_media_key(APPCOMMAND_PLAY_PAUSE)

def next_track():
    send_media_key(APPCOMMAND_NEXT)

def previous_track():
    send_media_key(APPCOMMAND_PREV)

sniffing_thread = threading.Thread(target=start_sniffing)
sniffing_thread.daemon = True 
sniffing_thread.start()