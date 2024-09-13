import threading
import time
import eventlet
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, send
import os
import signal
import ctypes
import datetime
import pyautogui
from obswebsocket import obsws, requests
from scapy.all import sniff, conf, IP
from flask_cors import CORS
import requests

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
import logging

class WebApp:
    def __init__(self):
        self.db = SQLAlchemy()
        self.socketio = SocketIO()

        self.app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Scoreboard.db'
        self.app.secret_key = 'SJ8SU0D2987G887vf76g87whgd87qwgs87G78GF987EWGF87GF897GH8'

        self.WM_APPCOMMAND = 0x0319
        self.APPCOMMAND_PLAY_PAUSE = 0x0000
        self.APPCOMMAND_NEXT = 0x000B
        self.APPCOMMAND_PREV = 0x000C

        self.OBSConnected = False
        self.devMode = "False"
        self.filesOpened = False

        self.init_logging()
        self.db.init_app(self.app)
        self.socketio.init_app(self.app, cors_allowed_origins="*") 
        self.open_files()

        self.setup_routes()

    def init_logging(self):
        self.app.logger.disabled = True
        logging.getLogger('werkzeug').disabled = True

    def open_files(self):
        try:
            with open(r"backend\data\keys.txt", "r") as f:
                self.IP1 = str(f.readline().strip())
                self.IP2 = str(f.readline().strip())
                self.ETHERNET_INTERFACE = str(f.readline().strip())
                self.OBSSERVERIP = str(f.readline().strip())
                self.OBSSERVERPORT = int(f.readline().strip())
                self.OBSSERVERPASSWORD = str(f.readline().strip())
            format.message("Files opened successfully", type="success")
            self.filesOpened = True
        except Exception as e:
            format.message(f"Failed to open files: {e}", type="error")

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html', OBSConnected=self.OBSConnected)

        @self.app.route('/scoreboard')
        def scoreboard():
            return render_template('scoreboard.html')

        @self.app.route('/toggle')
        def toggle_playback_route():
            self.toggle_playback()
            return jsonify({"message": "Playback toggled"})

        @self.app.route('/end')
        def terminate_server():
            logging.shutdown()
            os.kill(os.getpid(), signal.SIGTERM)
            
        @self.socketio.on('connect')
        def handle_connect():
            format.message("Sniffer Client connected")
            emit('response', {'message': 'Connected to the server!'})

        @self.socketio.on('client_event')
        def handle_client_event(json):
            format.message(f"Received event: {json}")
            
        @self.app.route('/send_message', methods=['POST'])
        def send_message():
            message = request.form.get('response')
            type = request.form.get('type')
            if message:
                match type:
                    case "start":
                        self.socketio.emit('start', {'server': message})
                    case "end":
                        self.socketio.emit('end', {'server': message})
                    case _:
                        self.socketio.emit('server', {'message': message})
                        
            return 'Message sent!'
            
    def start_sniffing(self):
        print("Starting packet sniffer...")
        try:
            sniff(prn=self.packet_callback, store=False, iface=self.ETHERNET_INTERFACE if self.devMode != "true" else None)
        except Exception as e:
            format.message(f"Error while sniffing: {e}", type="error")

    def packet_callback(self, packet):
        try:
            if packet.haslayer(IP) and (packet[IP].src == self.IP1 or packet[IP].src == self.IP2) and packet[IP].dst == "192.168.0.255":
                packet_bytes = bytes(packet).hex()

                if "342c403031352c30" in packet_bytes.lower():
                    format.message(f"Game start packet detected at {datetime.datetime.now()}", type="success")
                    self.socketio.emit('game_start', {'message': "Game Started @ " + str(datetime.datetime.now())})
                elif "342c403031342c30" in packet_bytes.lower():
                    format.message(f"Game Ended at {datetime.datetime.now()}", type="success")
                    self.socketio.emit('game_end', {'message': "Game Ended @ " + str(datetime.datetime.now())})
        except Exception as e:
            format.message(f"Error handling packet: {e}", type="error")

    def toggle_playback(self):
        pyautogui.press('playpause')

    def obs_connect(self):
        try:
            format.message("Connecting to OBS")
            ws = obsws(self.OBSSERVERIP, self.OBSSERVERPORT, self.OBSSERVERPASSWORD)
            ws.connect()
            self.OBSConnected = True
            format.message("Connected to OBS", type="success")
        except Exception as e:
            format.message(f"Failed to connect to OBS: {e}", type="error")

    def start(self):
        self.obs_thread = threading.Thread(target=self.obs_connect)
        self.obs_thread.start()

        print("Web App Started, hiding console")
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

        self.sniffing_thread = threading.Thread(target=self.start_sniffing)
        self.sniffing_thread.daemon = True
        self.sniffing_thread.start()

        eventlet.wsgi.server(eventlet.listen(('', 8080)), self.app)

    
    def send_test_packet(self):
        format.message("Sending test packet")
        response = requests.post('http://localhost:8080/send_message', data={'response': "Test Packet", 'type': "server"})
        format.message(f"Response: {response.text}")

