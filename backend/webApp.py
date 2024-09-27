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
        self.DMXConnected = False

        self.init_logging()
        self.socketio.init_app(self.app, cors_allowed_origins="*") 
        self.open_files()
        
        self.setup_routes()
        
        self.setUpDMX()
        
        with self.app.app_context():
            db.create_all()
            self.seedDBData() 

    def init_logging(self):
        self.app.logger.disabled = True
        logging.getLogger('werkzeug').disabled = True
        return
    
    def setUpDMX(self):
        try:
            format.message("Setting up DMX Connection")
        
            from PyDMXControl.controllers import OpenDMXController as Controller
            from PyDMXControl.profiles.Generic import Dimmer

            # This holds all the fixture information and outputs it.
            # This will start outputting data immediately.
            self._dmx = Controller(dynamic_frame=True, suppress_ticker_behind_warnings=True)

            # Add a new Dimmer fixture to our controller
        
            try:
                format.message("Registering Red Bulk-Head Lights", type="info")
                self._RedBulkHeadLights = self._dmx.add_fixture(Dimmer, name="RedBulkHeadLights")

                # This is done over 5000 milliseconds, or 5 seconds.
                self._RedBulkHeadLights.dim(255, 5000)
            
                self._RedBulkHeadLights.dim(0, 5000)
            except Exception as e:
                format.message(f"Error registering Red Bulk-Head Lights: {e}", type="error")
        
            self.DMXConnected = True
            
            format.message("DMX Connection set up successfully", type="success")
        except Exception as e:
            format.message(f"Error occured while setting up DMX connection! ({e})", type="error")
            
    def setBulkheadsTo50Brightness(self):
        self._RedBulkHeadLights.dim((255/2), 5000)
        
    def turnBulkHeadLightsOff(self):
        self._RedBulkHeadLights.dim(0, 5000)
        
    def seedDBData(self):
        if not Gun.query.first() and not Player.query.first():
            format.message("Empty DB Found! Seeding Data....", type="error")
 
            gunAlpha = Gun(name="Alpha", defaultColor="Red")
            gunApollo = Gun(name="Apollo", defaultColor="Red")
            gunChaos = Gun(name="Chaos", defaultColor="Red")
            gunCipher = Gun(name="Cipher", defaultColor="Red")
            gunCobra = Gun(name="Cobra", defaultColor="Red")
            gunComet = Gun(name="Comet", defaultColor="Red")
            gunCommander = Gun(name="Commander", defaultColor="Red")
            gunCyborg = Gun(name="Cyborg", defaultColor="Red")
            gunCyclone = Gun(name="Cyclone", defaultColor="Red")
            gunDelta = Gun(name="Delta", defaultColor="Red")
            gunDodger = Gun(name="Dodger", defaultColor="Green")
            gunDragon = Gun(name="Dragon", defaultColor="Green")
            gunEagle = Gun(name="Eagle", defaultColor="Green")
            gunEliminator = Gun(name="Eliminator", defaultColor="Green")
            gunElite = Gun(name="Elite", defaultColor="Green")
            gunFalcon = Gun(name="Falcon", defaultColor="Green")
            gunGhost = Gun(name="Ghost", defaultColor="Green")
            gunGladiator = Gun(name="Gladiator", defaultColor="Green")
            gunHawk = Gun(name="Hawk", defaultColor="Green")
            gunHyper = Gun(name="Hyper", defaultColor="Green")
            gunInferno = Gun(name="Inferno", defaultColor="Green")
            
            db.session.add(gunAlpha)
            db.session.add(gunApollo)
            db.session.add(gunChaos)
            db.session.add(gunCipher)
            db.session.add(gunCobra)
            db.session.add(gunComet)
            db.session.add(gunCommander)
            db.session.add(gunCyborg)
            db.session.add(gunCyclone)
            db.session.add(gunDelta)
            db.session.add(gunDodger)
            db.session.add(gunDragon)
            db.session.add(gunEagle)
            db.session.add(gunEliminator)
            db.session.add(gunElite)
            db.session.add(gunFalcon)
            db.session.add(gunGhost)
            db.session.add(gunGladiator)
            db.session.add(gunHawk)
            db.session.add(gunHyper)
            db.session.add(gunInferno)
            
            db.session.commit()
            format.message("Data seeded successfully", type="success")
        else:
            format.message("Data already exists, skipping seeding.", type="info")

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
            self.DMXADAPTOR = str(f.readline().strip())
            self._RedLightDimmer = str(f.readline().strip())
            
            format.message("Files opened successfully", type="success")
            
            self.filesOpened = True

    def hexToASCII(self, hexString):
 
        # initialize the ASCII code string as empty.
        ascii = ""
     
        for i in range(0, len(hexString), 2):
     
            # extract two characters from hex string
            part = hexString[i : i + 2]
     
            # change it into base 16 and
            # typecast as the character 
            ch = chr(int(part, 16))
     
            # add this char to final ASCII string
            ascii += ch
         
        return ascii

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html', OBSConnected=self.OBSConnected)

        @self.app.route('/scoreboard')
        def scoreboard():
            return render_template('scoreboard.html')

        @self.app.route('/toggle')
        def togglePlayback():
            self.toggle_playback()
            return jsonify({"message": "Playback toggled"})

        @self.app.route('/end')
        def terminateServer():
            logging.shutdown()
            os.kill(os.getpid(), signal.SIGTERM)
            
        @self.socketio.on('connect')
        def handleConnect():
            format.message("Sniffer Client connected")
            emit('response', {'message': 'Connected to the server!'})

        @self.socketio.on('client_event')
        def handleClientEvent(json):
            format.message(f"Received event: {json}")
        
        @self.socketio.on('SpotifyControl')
        def handleSpotifyControl(json):
            format.message(f"Spotify control = {json["data"]}")
            
            self.spotifyControl = json["data"]
            
        @self.socketio.on('spotifyControlStatus')
        def handleSpotifyControlVariable(json):
            self.spotifyControl = json["data"]
            format.message(f"Spotify control = {self.spotifyControl}")
            
        @self.app.route('/sendMessage', methods=['POST'])
        def sendMessage():
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
            
    def startSniffing(self):
        print("Starting packet sniffer...")
        try:
            sniff(prn=self.packetCallback, store=False, iface=self.ETHERNET_INTERFACE if self.devMode != "true" else None)
        except Exception as e:
            try:
                sniff(prn=self.packetCallback, store=False, iface=r"\Device\NPF_{65FB39AF-8813-4541-AC82-849B6D301CAF}" if self.devMode != "true" else None)
                format.message(f"Error while trying to sniff, falling back to default adaptor", type="error")
            except Exception as e:
                format.message(f"Error while sniffing: {e}", type="error")

    def packetCallback(self, packet):
        try:
            if packet.haslayer(IP) and (packet[IP].src == self.IP1 or packet[IP].src == self.IP2) and packet[IP].dst == "192.168.0.255":
                format.message(f"Packet 1: {packet}")
                
                packet_data = bytes(packet['Raw']).hex()  # Get the raw data in hex format
                format.message(f"Packet Data (hex): {packet_data}, {type(packet_data)}")
                
                # Corrected call to hexToASCII with the right argument
                decodedData = (self.hexToASCII(hexString=packet_data[0])).split(',')
                format.message(f"Decoded Data: {decodedData}")
                
                if "34" in packet_data.lower():
                    # Either a game has started or ended as 34 (Hex) = 4 (Denary) which signifies a Game Start / End event.
                    self.gameStatusPacket(decodedData)
                    
                elif "33" in packet_data.lower():
                    # The game has ended and the final scores packets are arriving, becuase 33 (Hex) = 3 (Denary)
                    self.finalScorePacket(decodedData)
                
                elif "31" in packet_data.lower():
                    # A timing packet is being transmitted as the Event Type = 31 (Hex) = 1
                    self.timingPacket(decodedData)    
                
                elif "35" in packet_data.lower():
                    # A shot has been confirmed as the transmitted Event Type = 35 (Hex) = 5
                    self.shotConfirmedPacket(decodedData)
                    
                # elif "342c403031352c30" in packet_bytes.lower():
                #     format.message(f"Game start packet detected at {datetime.datetime.now()}", type="success")
                #     self.handleMusic()
                #     self.gameStarted()
                #     response = requests.post('http://localhost:8080/sendMessage', data={'message': f"Game Started @ {str(datetime.datetime.now())}", 'type': "start"})
                #     format.message(f"Response: {response.text}")
                # elif "342c403031342c30" in packet_bytes.lower():
                #     format.message(f"Game Ended at {datetime.datetime.now()}", type="success") 
                #     self.handleMusic()
                #     response = requests.post('http://localhost:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
                #     format.message(f"Response: {response.text}")
                # elif "312c373634312c2240303034222c33302c31" in packet_bytes.lower():
                #     format.message(f"30 seconds remain!", type="success") 
                #     response = requests.post('http://localhost:8080/sendMessage', data={'message': f"30", 'type': "timeleft"})
                
                
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

        self.sniffing_thread = threading.Thread(target=self.startSniffing)
        self.sniffing_thread.daemon = True
        self.sniffing_thread.start()

        self.socketio.run(self.app, host='0.0.0.0', port=8080)

    
    def sendTestPacket(self, type="server"):
        format.message(f"Sending {type} packet")
        match type.lower():
            case "server":
                response = requests.post('http://localhost:8080/sendMessage', data={'message': "Test Packet", 'type': "server"})
                format.message(f"Response: {response.text}")
            case "start":
                response = requests.post('http://localhost:8080/sendMessage', data={'message': f"Game Start Test Packet sent @ {datetime.datetime.now()}", 'type': "start"})
                format.message(f"Response: {response.text}")
            case "end":
                response = requests.post('http://localhost:8080/sendMessage', data={'message': f"Game End Test Packet sent @ {datetime.datetime.now()}", 'type': "end"})
                format.message(f"Response: {response.text}")

    def gameStarted(self):
        format.message("Game started")
        
        self.handleMusic()
        self._dmx.dimDeviceToValue(self._RedLightDimmer, 255)
        
    def GameEnded(self):
        format.message("Game ended")
        
        self.handleMusic()
        self._dmx.dimDeviceToValue(self._RedLightDimmer, 0)
        
    def gameStatusPacket(self, packetData):
        # 4,@015,0 = start
        # 4,@014,0 = end
        
        if packetData[2] == "@015":
            format.message(f"Game start packet detected at {datetime.datetime.now()}", type="success")
            self.gameStarted()
            response = requests.post('http://localhost:8080/sendMessage', data={'message': f"Game Started @ {str(datetime.datetime.now())}", 'type': "start"})
            format.message(f"Response: {response.text}")
        
        elif packetData[2] == "@014":
            format.message(f"Game Ended at {datetime.datetime.now()}", type="success") 
            self.handleMusic()
            response = requests.post('http://localhost:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
            format.message(f"Response: {response.text}")
    
    def timingPacket(self, packetData):
        timeLeft = packetData[3]
        if int(timeLeft) % 30 == 0:
            format.message(f"{timeLeft} seconds remain!", type="success") 
            response = requests.post('http://localhost:8080/sendMessage', data={'message': f"{timeLeft} seconds remain!", 'type': "server"})
    
    def finalScorePacket(self, packetData):
        gunId = packetData[2]
        finalScore = packetData[4]
        accuracy = packetData[7]
        
        try:
            gunName = Gun.query.filter_by(id=gunId).first().name
        
        except Exception as e:
            format.message(f"Error getting gun name: {e}", type="error")
        
        if gunName == None:
            gunName = gunId
        
        response = requests.post('http://localhost:8080/sendMessage', data={'message': f"Gun Name {gunName} has a final score of {finalScore} and an overall accuracy of {accuracy}", 'type': "server"})
        
    def shotConfirmedPacket(self, packetData):
        pass
            
class Gun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    defaultColor = db.Column(db.String(60), unique=False, nullable=False)
    
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    kills = db.Column(db.Integer, nullable=False)
    deaths = db.Column(db.Integer, nullable=False)
    gamesWon = db.Column(db.Integer, nullable=False)
    gamesLost = db.Column(db.Integer, nullable=False)
    
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
    gamePlayers = db.relationship("GamePlayers", backref="team_ref", lazy=True)


class GamePlayers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gameID = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    gunID = db.Column(db.Integer, db.ForeignKey("gun.id"), nullable=False)
    playerID = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    playerWon = db.Column(db.Boolean, nullable=False)
    team = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
