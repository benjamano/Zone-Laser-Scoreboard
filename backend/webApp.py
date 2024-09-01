from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from scapy.all import sniff, conf, IP
import threading

db = SQLAlchemy()
socketio = SocketIO()

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Scoreboard.db'

db.init_app(app)
socketio.init_app(app)

IP1 = "192.168.2.60"
IP2 = "192.168.2.42"

ETHERNET_INTERFACE = r"\Device\NPF_{65FB39AF-8813-4541-AC82-849B6D301CAF}"

# -------------------------------------------------| ROUTES |------------------------------------------------- #



@app.route('/')
def index():
    threading.Thread(target=start_sniffing).start()
    return render_template('index.html')



# -------------------------------------------------| SNIFFER |------------------------------------------------ #

def packet_callback(packet):
    if packet.haslayer(IP):
        if packet[IP].src == IP1 or packet[IP].src == IP2:
            print(packet.show())
            print(bytes(packet))

def start_sniffing():
    conf.L3socket = conf.L3socket
    
    print("Starting packet sniffer...")
    sniff(prn=packet_callback, store=False)



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