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
import psutil
import socket
import webbrowser


try:
    from func import format
    print("Imported functions") 
except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")
        
from func.BPM import MediaBPMFetcher
    
import logging

db = SQLAlchemy()

class WebApp:
    def __init__(self):
        self.app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Scoreboard.db'
        self.app.secret_key = 'SJ8SU0D2987G887vf76g87whgd87qwgs87G78GF987EWGF87GF897GH8'
        
        self.expecteProcesses = ["Spotify.exe", "obs64"]
        
        self.goboModes = ["SpinningAll", "Static", "Stacked"]
        self.colourModes  = ["BPM", "Static", "Rainbow"]
        self.panTiltModes  = ["Crazy", "Normal", "Slow"]
            
        db.init_app(self.app)
        
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self._dir = os.path.dirname(os.path.realpath(__file__))

        self.OBSConnected = False
        self.devMode = "False"
        self.filesOpened = False
        self.spotifyControl = False
        self.DMXConnected = False
        self.spotifyStatus = "paused"
        self._localIp = ""
        self.fixtures = []

        self.initLogging()
        self.socketio.init_app(self.app, cors_allowed_origins="*") 
        self.openFiles()
        
        self.setupRoutes()
        
        with self.app.app_context():
            db.create_all()
            self.seedDBData() 

    def initLogging(self):
        #self.app.logger.disabled = True
        #logging.getLogger('werkzeug').disabled = True
        return
    
    def setUpDMX(self):
        try:
            format.message("Setting up DMX Connection")
        
            from PyDMXControl.controllers import OpenDMXController
            # from PyDMXControl.controllers import uDMXController

            # Import the fixture profile we will use,
            #  the simple Dimmer in this example.
            from PyDMXControl.profiles.Generic import Dimmer

            # Create an instance of the uDMX controller, 
            #  this holds all the fixture information and outputs it.
            # This will start outputting data immediately.
            self._dmx = OpenDMXController()

            # Add a new Dimmer fixture to our controller
        
            try:
                format.message("Registering Red Bulk-Head Lights", type="info")
                self._RedBulkHeadLights = self._dmx.add_fixture(Dimmer, name="RedBulkHeadLights")

                # This is done over 5000 milliseconds, or 5 seconds.
                self._RedBulkHeadLights.dim(255, 5000)
            
                self._RedBulkHeadLights.dim(0, 5000)
                
                self.fixtures.append(self._RedBulkHeadLights)
                
            except Exception as e:
                format.message(f"Error registering Red Bulk-Head Lights: {e}", type="error")
        
            self.DMXConnected = True
            
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"CONNECTED", 'type': "dmxStatus"})
            
            format.message("DMX Connection set up successfully", type="success")
            
        except Exception as e:
            format.message(f"Error occured while setting up DMX connection! ({e})", type="error")
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"DISCONNECTED", 'type': "dmxStatus"})
            
        
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

    def openFiles(self):
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
            self.SPOTIPY_CLIENT_ID = str(f.readline().strip())
            self.SPOTIPY_CLIENT_SECRET = str(f.readline().strip())
                        
            format.message("Files opened successfully", type="success")
            
            self.filesOpened = True

    def hexToASCII(self, hexString):
        ascii = ""
     
        for i in range(0, len(hexString), 2):
     
            part = hexString[i : i + 2]
     
            ch = chr(int(part, 16))
     
            ascii += ch
            
            if ch == "\x00":
                break
         
        return ascii

    def setupRoutes(self):
        @self.app.route('/')
        def index():
            if not self.OBSConnected:
                OBSConnection = "DISCONNECTED"
            else:
                OBSConnection = "CONNECTED"
            
            if not self.DMXConnected:
                DMXConnection = "DISCONNECTED"
            else:
                DMXConnection = "CONNECTED"
            
            return render_template('index.html', OBSConnected=OBSConnection, DMXConnected=DMXConnection)
        
        @self.app.route("/lights")
        def lights():   
            
            return render_template('lights.html')
        
        # API --------------------------------------------------------------------------------------------------------------------
        
        @self.app.route("/api/availableFixtures", methods=["GET"])
        def availableFixtures():
            
            self.fixtures = [{"fixture_id": idx, "fixture": fixture.name} for idx, fixture in enumerate(self.fixtures)]
            
            format.message(f"{self.fixtures}")
        
            return jsonify(self.fixtures)
        
        

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
            #format.message(f"Sending message: {message} with type: {type}")
            if message:
                
                self.socketio.emit(f"type", {f"{message}": message})

                # match type.lower():
                #     case "start":
                #         #format.message("Sending start message")
                #         self.socketio.emit('start', {'message': message})
                #     case "end":
                #         #format.message("Sending end message")
                #         self.socketio.emit('end', {'message': message})
                #     case "server":
                #         #format.message("Sending server message")
                #         self.socketio.emit('server', {'message': message})
                #     case "timeleft":
                #         #format.message(f"Sending timeleft message, {message} seconds left")
                #         self.socketio.emit('timeleft', {'message': f"{message} seconds remaining"})
                #     case "gunscores":
                #         #format.message(f"Sending gunScore message, {message}")
                #         self.socketio.emit('gunScores', {'message': message})
                #     case "timeremaining":
                #         #format.message(f"Sending time left message, {message}")
                #         self.socketio.emit('timeRemaining', {'message': message})
                #     case "songname":
                #         #format.message(f"Sending Music Name, {message}")
                #         self.socketio.emit('songName', {'message': message})
                #     case "songbpm":
                #         #format.message(f"Sending Music BPM, {message}")
                #         self.socketio.emit('songBPM', {'message': message})       
                #     case "songalbum":
                #         #format.message(f"Sending Music Album, {message}")
                #         self.socketio.emit('songAlbum', {'message': message})
                        
            #format.newline()
                        
            return 'Message sent!'
            
    def startSniffing(self):
        print("Starting packet sniffer...")
        try:
            sniff(prn=self.packetCallback, store=False, iface=self.ETHERNET_INTERFACE if self.devMode != "true" else None)
        except Exception as e:
            try:
                format.message(f"Error while trying to sniff, falling back to default adaptor", type="error")
                sniff(prn=self.packetCallback, store=False, iface=r"\Device\NPF_{65FB39AF-8813-4541-AC82-849B6D301CAF}" if self.devMode != "true" else None)
            except Exception as e:
                format.message(f"Error while sniffing: {e}", type="error")

    def packetCallback(self, packet):
        try:
            if packet.haslayer(IP) and (packet[IP].src == self.IP1 or packet[IP].src == self.IP2) and packet[IP].dst == "192.168.0.255":
                #format.message(f"Packet 1: {packet}")
                
                packet_data = bytes(packet['Raw']).hex()
                #format.message(f"Packet Data (hex): {packet_data}, {type(packet_data)}")
                
                decodedData = (self.hexToASCII(hexString=packet_data)).split(',')
                #format.message(f"Decoded Data: {decodedData}")
                
                if decodedData[0] == "1":
                    # A timing packet is being transmitted as the Event Type = 31 (Hex) = 1
                    threading.Thread(target=self.timingPacket, args=(decodedData,)).start()
                
                elif decodedData[0] == "3":
                    # The game has ended and the final scores packets are arriving, because 33 (Hex) = 3 (Denary)
                    threading.Thread(target=self.finalScorePacket, args=(decodedData,)).start()
                
                elif decodedData[0] == "4":
                    # Either a game has started or ended as 34 (Hex) = 4 (Denary) which signifies a Game Start / End event.
                    threading.Thread(target=self.gameStatusPacket, args=(decodedData,)).start()
                
                elif decodedData[0] == "5":
                    # A shot has been confirmed as the transmitted Event Type = 35 (Hex) = 5
                    threading.Thread(target=self.shotConfirmedPacket, args=(decodedData,)).start()
                
        except Exception as e:
            format.message(f"Error handling packet: {e}", type="error")
    
    def handleMusic(self, mode):
        if self.spotifyControl == True:
            
            if mode.lower() == "pause":
                if self.spotifyStatus == "paused":
                    return
                else:
                    format.message("Pausing music", type="warning")
                    self.spotifyStatus = "paused"
                    pyautogui.press('playpause')
            
            if mode.lower() == "play":
                if self.spotifyStatus == "playing":
                    return
                else:
                    format.message("Playing music", type="warning")
                    self.spotifyStatus = "playing"
                    pyautogui.press('playpause')
        else:
            format.message("Spotify control is disabled", type="warning")

    def obs_connect(self):
        try:
            format.message("Attempting to connect to OBS")
            ws = obsws(self.OBSSERVERIP, self.OBSSERVERPORT, self.OBSSERVERPASSWORD)
            ws.connect()
            self.OBSConnected = True
            format.message("Successfully Connected to OBS", type="success")
            
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"CONNECTED", 'type': "obsStatus"})

        except Exception as e:
            format.message(f"Failed to connect to OBS: {e}", type="error")
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"DISCONNECTED", 'type': "obsStatus"})
            
    def checkIfProcessRunning(self, processName):
        for proc in psutil.process_iter():
            try:
                if processName.lower() in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    def runProcessChecker(self):
        while True:
            for processName in self.expecteProcesses:
                processFound = self.checkIfProcessRunning(processName)
                #format.message(f"Process {processName} running: {processFound}")
                
                if not processFound:
                    try:
                        format.message(f"Process {processName} not found, starting it..", type="warning")
                        if processName.lower() == "spotify":
                            os.startfile(f"{self._dir}\\appShortcuts\\Spotify.lnk")
                        elif processName.lower() == "obs64":
                            os.startfile(f"{self._dir}\\appShortcuts\\OBS.lnk")
                        else:
                            format.message(f"Process {processName} not recognized for auto-start", type="error")
                        if self.DMXConnected == False:
                            format.message(f"DMX Connection lost, restarting DMX Network")
                            self.setUpDMX()
                        if self.OBSConnected == False:
                            format.message(f"OBS Connection lost, restarting OBS")
                            self.obs_connect()
                            
                    except Exception as e:
                        format.message(f"Error starting process {processName}: {e}", type="error")
                
            time.sleep(600)
            
    def handleBPM(self, song, bpm, album):
        try:
            if song == None or bpm  == None or bpm == "Song not found":
                match song:
                    #This makes me want to die
                    #Implemented because these are local songs used specifically in the Arena, and aren't on spotify.
                    case "Main Theme":
                        bpm = "69"
                    case "Loon Skirmish":
                        bpm = "80"
                    case "Crainy Yum (Medium)":
                        bpm = "80"
                    case "Crainy Yum":
                        bpm = "80"
                    case "Thing Of It Is":
                        bpm = "87"
                    case "Bug Zap":
                        bpm = "87"
                    case "Bug Zap (Medium)":
                        bpm = "87"
                    case "Only Partially Blown Up (Medium)":
                        bpm = "87"
                    case "Only Partially Blown Up":
                        bpm = "87"
                    case "Baron von Bats":
                        bpm = "87"
                    case "Treasure Yeti":
                        bpm = "86"
                    case "Normal Wave (A) (Medium)":
                        bpm = "86"
                    case "Normal Wave A":
                        bpm = "86"
                    case "Normal Wave B":
                        bpm = "87"
                    case "Normal Wave (C) (High)":
                        bpm = "87"
                    case "Special Wave A":
                        bpm = "87"
                    case "Special Wave B":
                        bpm = "101"
                    case "Challenge Wave B":
                        bpm = "101"
                    case "Challenge Wave C":
                        bpm = "101"
                    case "Boss Wave (A)":
                        bpm = "93"
                    case "Boss Wave (B)":
                        bpm = "98"
                    case "The Gnomes Cometh (B)":
                        bpm = "90"
                    case "The Gnomes Cometh (C)":
                        bpm = "86"
                    case "Gnome King":
                        bpm = "95"
                    case "D Boss Is Here":
                        bpm = "90"
                    case "Excessively Bossy":
                        bpm = "93"
                    case "One Bad Boss":
                        bpm = "84"
                    case "Zombie Horde":
                        bpm = "84"
                    case "Marching Madness":
                        bpm = "58"
                    case "March Of The Brain Munchers":
                        bpm = "58"
                    case "SUBURBINATION!!!":
                        bpm = "86"
                    case "Splattack!":
                        bpm = "88"
                    case "Science Blasteer":
                        bpm = "92"
                    case "Undertow":
                        bpm = "88"
                    case _:
                        bpm = "60"
        
            #format.message(f"Current song: {song}, BPM: {bpm}")
        
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{song}", 'type': "songName"})
        
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{str(round(int(bpm)))}", 'type': "songBPM"})
        
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{album}", 'type': "songAlbum"})
            
        except Exception as e:
            format.message(f"Error occured while handling BPM: {e}", type="warning")
        
            
    def findBPM(self):
        format.message("Attempting to start BPM finder")
        try:
            self.media_bpm_fetcher = MediaBPMFetcher(self.SPOTIPY_CLIENT_ID, self.SPOTIPY_CLIENT_SECRET)
            self.media_bpm_fetcher.start()
            
            format.message("BPM Finder Active", type="success")

            while True:
                # Get the current song and BPM
                song, bpm, album = self.media_bpm_fetcher.get_current_song_and_bpm()
            
                self.handleBPM(song, bpm, album)
                
                time.sleep(5)
                
        except Exception as e:
            format.message("Failed to start BPM finder: {e}", type="error")

    def startFlask(self):
        format.message("Attempting to start Flask Server")
        try:
            self.socketio.run(self.app, host=self._localIp, port=8080)
        except Exception as e:
            format.message(f"An error occured while trying to start Flask Server: {e}", type="error")
   

    def start(self):
        format.newline()    
        
        self.flaskThread = threading.Thread(target=self.startFlask)
        self.flaskThread.daemon = True
        self.flaskThread.start()
        format.message("Flask Server Started!", type="success")

        try:
            # Create a dummy socket connection to find the local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self._localIp = s.getsockname()[0]
            s.close()
        except Exception as e:
            format.message(f"Error finding local IP: {e}")

        format.message(f"Web App hosted on IP {self._localIp}", type="success")
        
        if self.devMode == "false":
            webbrowser.open(f"http://{self._localIp}:8080")

        self.obs_thread = threading.Thread(target=self.obs_connect)
        self.obs_thread.daemon = True
        self.obs_thread.start()
        
        self.DMXThread = threading.Thread(target=self.setUpDMX)
        self.DMXThread.daemon = True
        self.DMXThread.start()

        print("Web App Started, hiding console")
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

        self.sniffing_thread = threading.Thread(target=self.startSniffing)
        self.sniffing_thread.daemon = True
        self.sniffing_thread.start()
        
        self.process_checker_thread = threading.Thread(target=self.runProcessChecker)
        self.process_checker_thread.daemon = True
        self.process_checker_thread.start()
        
        self.bpm_thread = threading.Thread(target=self.findBPM)
        self.bpm_thread.daemon = True
        self.bpm_thread.start()
        
        format.newline()    

    
    def sendTestPacket(self, type="server"):
        format.message(f"Sending {type} packet")
        match type.lower():
            case "server":
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': "Test Packet", 'type': "server"})
                format.message(f"Response: {response.text}")
            case "start":
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Start Test Packet sent @ {datetime.datetime.now()}", 'type': "start"})
                format.message(f"Response: {response.text}")
            case "end":
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game End Test Packet sent @ {datetime.datetime.now()}", 'type': "end"})
                format.message(f"Response: {response.text}")

    def gameStarted(self):
        format.message("Game started")
        
        try:
            self.handleMusic(mode="play")
        except Exception as e:
            format.message(f"Error handling music: {e}", type="error")
            
        try:
            self._RedBulkHeadLights.dim(255, 5000)
        except Exception as e:
            format.message(f"Error dimming red lights: {e}", type="error")
            format.message(f"Restarting DMX Network: {e}", type="warning")
            self.setUpDMX()
        
    def gameEnded(self):
        format.message("Game ended")
        
        try:
            self.handleMusic(mode="pause")
        except Exception as e:
            format.message(f"Error handling music: {e}", type="error")
            
        try:
            self._RedBulkHeadLights.dim(0, 5000)
        except Exception as e:
            format.message(f"Error dimming red lights: {e}", type="error")
            format.message(f"Restarting DMX Network: {e}", type="warning")
            self.setUpDMX()
        
    def gameStatusPacket(self, packetData):
        # 4,@015,0 = start
        # 4,@014,0 = end
        
        format.message(f"Game Status Packet: {packetData}, Mode: {packetData[1]}")
        
        if packetData[1] == "@015":
            format.message(f"Game start packet detected at {datetime.datetime.now()}", type="success")
            self.gameStarted()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Started @ {str(datetime.datetime.now())}", 'type': "start"})
            format.message(f"Response: {response.text}")
        
        elif packetData[1] == "@014":
            format.message(f"Game Ended at {datetime.datetime.now()}", type="success") 
            self.gameEnded()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
            format.message(f"Response: {response.text}")
            
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{packetData[0]}", 'type': "gameMode"})

    
    def timingPacket(self, packetData):
        timeLeft = packetData[3]
        
        format.message(f"Time Left: {timeLeft}")

        if int(timeLeft) <= 0:
            format.message(f"Game Ended at {datetime.datetime.now()}", type="success") 
            self.gameEnded()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
            format.message(f"Response: {response.text}")
        else:
            format.message(f"{timeLeft} seconds remain!", type="success") 
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{timeLeft}", 'type': "timeRemaining"})
        
        format.newline()
    
    def finalScorePacket(self, packetData):
        gunId = packetData[1]
        finalScore = packetData[3]
        accuracy = packetData[7]

        gunName = None
        
        try:
            with self.app.app_context():
                gunName = "name: "+ Gun.query.filter_by(id=gunId).first().name
        
        except Exception as e:
            format.message(f"Error getting gun name: {e}", type="error")
        
        if gunName == None:
            gunName = "id: "+gunId
            
        format.message(f"Gun {gunName} has a score of {finalScore} and an accuracy of {accuracy}", type="success")
        
        data = f"{gunId},{finalScore},{accuracy}"
        
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': data, 'type': "gunScores"})
        
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
