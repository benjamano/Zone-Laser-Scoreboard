from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from scapy.all import sniff, IP
import threading

db = SQLAlchemy()
socketio = SocketIO()

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Scoreboard.db'

db.init_app(app)
socketio.init_app(app)

IP1 = "127.0.0.1"
IP2 = "192.168.1.20"

ETHERNET_INTERFACE = "Ethernet"

# -------------------------------------------------| ROUTES |------------------------------------------------- #



@app.route('/')
def index():
    return render_template('index.html')



# -------------------------------------------------| SNIFFER |------------------------------------------------ #



def packet_callback(packet):
    if packet.haslayer(IP):
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        
        if (src_ip == IP1 and dst_ip == IP2) or (src_ip == IP2 and dst_ip == IP1):
            packet_info = f"{src_ip} -> {dst_ip}: {packet.summary()}"
            socketio.emit('packet_data', {'data': packet_info})

def start_sniffing():
    sniff(filter="ip", prn=packet_callback, store=0, iface=ETHERNET_INTERFACE)



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
    
    
    
if __name__ == '__main__':
    sniffing_thread = threading.Thread(target=start_sniffing)
    sniffing_thread.daemon = True
    sniffing_thread.start()