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
        print(f"An error occurred: {e}")
        input("Press any key to exit...")
        
import logging

db = SQLAlchemy()

class WebApp:
    def __init__(self):
        self.app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Scoreboard.db'
        self.app.secret_key = 'SJ8SU0D2987G887vf76g87whgd87qwgs87G78GF987EWGF87GF897GH8'
            
        db.init_app(self.app)
        
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self._dir = os.path.dirname(os.path.realpath(__file__))

        self.OBSConnected = False
        self.devMode = "False"
        self.filesOpened = False
        self.spotifyControl = False

        self.init_logging()
        self.socketio.init_app(self.app, cors_allowed_origins="*") 
        self.open_files()
        
        self.setup_routes()
        
        with self.app.app_context():
            db.create_all()

    def init_logging(self):
        self.app.logger.disabled = True
        logging.getLogger('werkzeug').disabled = True

    def open_files(self):
        try:
            f = open(fr"{self._dir}\data\keys.txt", "r")
        except:
            try:
                f = open(r"C:\Users\benme\Documents\GitHub\Play2Day-Laser-Scoreboard\backend\data\keys.txt", "r")
            except Exception as e:
                format.message(f"Failed to open files: {e}", type="error")
        finally:
            self.IP1 = str(f.readline().strip())
            self.IP2 = str(f.readline().strip())
            self.ETHERNET_INTERFACE = str(f.readline().strip())
            self.OBSSERVERIP = str(f.readline().strip())
            self.OBSSERVERPORT = int(f.readline().strip())
            self.OBSSERVERPASSWORD = str(f.readline().strip())
            
            format.message("Files opened successfully", type="success")
            
            self.filesOpened = True

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
        
        @self.socketio.on('SpotifyControl')
        def handle_spotify_control(json):
            format.message(f"Spotify control = {json["data"]}")
            
            self.spotifyControl = json["data"]
            
            
        @self.app.route('/send_message', methods=['POST'])
        def send_message():
            message = request.form.get('message')
            type = request.form.get('type')
            format.message(f"Sending message: {message} with type: {type}")
            if message:
                match type.lower():
                    case "start":
                        format.message("Sending start message")
                        self.socketio.emit('start', {'message': message})
                    case "end":
                        format.message("Sending end message")
                        self.socketio.emit('end', {'message': message})
                    case "server":
                        format.message("Sending server message")
                        self.socketio.emit('server', {'message': message})
                    case "timeleft":
                        format.message(f"Sending timeleft message, {message} seconds left")
                        self.socketio.emit('timeleft', {'message': f"{message} seconds remaining"})
                        
            return 'Message sent!'
            
    def start_sniffing(self):
        print("Starting packet sniffer...")
        try:
            sniff(prn=self.packet_callback, store=False, iface=self.ETHERNET_INTERFACE if self.devMode != "true" else None)
        except Exception as e:
            try:
                sniff(prn=self.packet_callback, store=False, iface=r"\Device\NPF_{65FB39AF-8813-4541-AC82-849B6D301CAF}" if self.devMode != "true" else None)
                format.message(f"Error while trying to sniff, falling back to default adaptor", type="error")
            except Exception as e:
                format.message(f"Error while sniffing: {e}", type="error")

    def packet_callback(self, packet):
        try:
            if packet.haslayer(IP) and (packet[IP].src == self.IP1 or packet[IP].src == self.IP2) and packet[IP].dst == "192.168.0.255":
                packet_bytes = bytes(packet).hex()

                if "342c403031352c30" in packet_bytes.lower():
                    format.message(f"Game start packet detected at {datetime.datetime.now()}", type="success")
                    self.handleMusic()
                    self.gameStarted()
                    response = requests.post('http://localhost:8080/send_message', data={'message': f"Game Started @ {str(datetime.datetime.now())}", 'type': "start"})
                    format.message(f"Response: {response.text}")
                elif "342c403031342c30" in packet_bytes.lower():
                    format.message(f"Game Ended at {datetime.datetime.now()}", type="success") 
                    self.handleMusic()
                    response = requests.post('http://localhost:8080/send_message', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
                    format.message(f"Response: {response.text}")
                elif "312c373634312c2240303034222c33302c31" in packet_bytes.lower():
                    format.message(f"30 seconds remain!", type="success") 
                    response = requests.post('http://localhost:8080/send_message', data={'message': f"30", 'type': "timeleft"})
                    
        except Exception as e:
            format.message(f"Error handling packet: {e}", type="error")
    
    def handleMusic(self):
        if self.spotifyControl == True:
            format.message("Toggling playback")
            pyautogui.press('playpause')
        else:
            format.message("Spotify control is disabled")
            pass

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
        response = requests.post('http://localhost:8080/send_message', data={'message': "Test Packet", 'type': "server"})
        format.message(f"Response: {response.text}")

    def gameStarted(self):
        format.message("Game started")
        
        
        
class Gun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    defaultColor = db.Column(db.String(60), unique=False, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    kills = db.Column(db.Integer, nullable=False)
    deaths = db.Column(db.Integer, nullable=False)
    gamesWon = db.Column(db.Integer, nullable=False)
    gamesLost = db.Column(db.Integer, nullable=False)
    
class GamePlayers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gameID = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    gunID = db.Column(db.Integer, db.ForeignKey("gun.id"),  nullable=False)
    playerID = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    playerWon = db.Column(db.Boolean, nullable=False)
    team = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    startTime = db.Column(db.DateTime, nullable=False)
    endTime = db.Column(db.DateTime, nullable=False)
    winningPlayer = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    winningTeam = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    loser = db.Column(db.String(60), nullable=True)
    
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    teamColour = db.Column(db.String(10), nullable=False)
    gamePlayers = db.relationship("gameplayers", backref="team", lazy=True)