import threading
import time
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os
import signal
import ctypes
import datetime
import pyautogui
import obsws_python as obs
from scapy.all import sniff, IP
import requests
import psutil
import socket
import webbrowser
import asyncio
import random
import logging
import json

try:
    import winrt.windows.media.control as wmc
except ImportError:
    print("Failed to import winrt.windows.media.control")

try:
    from func import format
    print("Imported functions") 
except Exception as e:
    print(f"An error occurred: {e}")
    input("Press any key to exit...")
        
from func.BPM import MediaBPMFetcher

from func.DMXControl import dmx

from func.DB import context

class WebApp:
    def __init__(self):
        self.app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
        # self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Scoreboard.db'
        self.app.secret_key = 'SJ8SU0D2987G887vf76g87whgd87qwgs87G78GF987EWGF87GF897GH8'
        
        self.expecteProcesses = ["Spotify.exe", "obs64"]
        
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self._dir = os.path.dirname(os.path.realpath(__file__))

        self.OBSConnected = False
        self.devMode = False
        self.filesOpened = False
        self.spotifyControl = True
        self.DMXConnected = False
        self.spotifyStatus = "paused"
        self._localIp = ""
        self.rateLimit = False
        self.RestartRequested = False
        self.gameStatus = "stopped" #Either running or stopped
        self.endOfDay = False
        self.SysName = "TBS"
        
        pyautogui.FAILSAFE = False

        format.message(f"Starting Web App at {str(datetime.datetime.now())}", type="warning")
        
        with self.app.app_context():
            self._context = context(self.app)
        
        self.initLogging()
        self.socketio.init_app(self.app, cors_allowed_origins="*") 
        self.openFiles()
        
        self.setupRoutes()
        
        self.fetcher = MediaBPMFetcher(self.SPOTIPY_CLIENT_ID, self.SPOTIPY_CLIENT_SECRET)

    # -----------------| Starting Tasks |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
    
    def startFlask(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((self._localIp, 8080)) == 0:
                    format.message(f"Port 8080 is already in use on {self._localIp}", type="error")
                    raise RuntimeError("Port in use. Exiting application.")

                self.socketio.run(self.app, host=self._localIp, port=8080)
                
                if self.devMode == True:
                    self.app.debug = True
                
        except Exception as e:
            format.message("Fatal! ", e)
            os._exit(1)
        
    def start(self):
        format.newline()  
        
        def bpmLoop():
            while True:
                try:
                    self.findBPM()
                    time.sleep(10)
                except Exception as e:
                    format.message(f"Error in BPM loop: {e}", type="error")
                    break

        self.bpm_thread = threading.Thread(target=bpmLoop, daemon=True)
        self.bpm_thread.start()  
        
        try:
            # Create a dummy socket connection to find the local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self._localIp = s.getsockname()[0]
            s.close()
        except Exception as e:
            format.message(f"Error finding local IP: {e}")
            
        format.message("Attempting to start Media status checker")
        
        try:
            self.mediaStatusCheckerThread = threading.Thread(target=self.mediaStatusChecker)
            self.mediaStatusCheckerThread.daemon = True
            self.mediaStatusCheckerThread.start()
            
        except Exception as e:
            format.message(f"Error starting Media Status Checker: {e}", type="error")
            
        format.message("Attempting to start Flask Server")
        
        try:
            self.flaskThread = threading.Thread(target=self.startFlask)
            self.flaskThread.daemon = True
            self.flaskThread.start()
            
        except Exception as e:
            format.message(f"Error starting Flask Server: {e}", type="error")
            return SystemExit

        format.message(f"Web App hosted on IP {self._localIp}", type="success")
        
        if self.devMode == False:
            webbrowser.open(f"http://{self._localIp}:8080")
            
        try:
            if self.OBSSERVERIP == "" or self.OBSSERVERPASSWORD == "" or self.OBSSERVERPORT == "" or self.devMode == True:
                format.message(f"Development Mode or Missing Values, skipping OBS Connection ('{self.OBSSERVERIP}', '{self.OBSSERVERPASSWORD}', '{self.OBSSERVERPORT}')", type="warning")
            else:
                self.obs_thread = threading.Thread(target=self.obs_connect)
                self.obs_thread.daemon = True
                self.obs_thread.start()
                
        except Exception as e:
            format.message(f"Error starting OBS Connection: {e}", type="error")
            
        try:
            format.message("Setting up DMX Connection")
            self.DMXThread = threading.Thread(target=self.setUpDMX)
            self.DMXThread.daemon = True
            self.DMXThread.start()
            
        except Exception as e:
            format.message(f"Error starting DMX Connection: {e}", type="error")

        format.message("Web App Started, hiding console", type="success")
        
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except Exception as e:
            format.message(f"Hiding console: {e}", type="error")
        
        try:
            self.sniffing_thread = threading.Thread(target=self.startSniffing)
            self.sniffing_thread.daemon = True
            self.sniffing_thread.start()
            
        except Exception as e:
            format.message(f"Error starting packet sniffer: {e}", type="error")
        
        if self.devMode != True:
            self.process_checker_thread = threading.Thread(target=self.runProcessChecker)
            self.process_checker_thread.daemon = True
            self.process_checker_thread.start()
        
        format.message("Attempting to start BPM finder")
        
        self.flaskThread.join()
        
        format.newline()    

    def initLogging(self):
        #self.app.logger.disabled = True
        #logging.getLogger('werkzeug').disabled = True
        return
    
    def setUpDMX(self):
        #Requires USB to DMX with driver version of "libusb-win32"
        
        try:
            self._dmx = dmx(self._context, self.app, self.devMode)
            
        except Exception as e:
            format.message(f"Error starting DMX Connection: {e}", type="error")
            return
        
        try:
            #try:
                #self._dmx.web_control()
                
            #except Exception as e:
                #format.message(f"Error starting DMX web control: {e}", type="error")
        
            try:
                format.message("Registering Red Bulk-Head Lights", type="info")
                
                self.BulkHeadLights = self._dmx.registerDimmerFixture("Bulk-Head Lights")
                
            except Exception as e:
                format.message(f"Error registering Red Bulk-Head Lights: {e}", type="error")
                
            try:
                format.message("Registering ColorWash 250 AT", type="info")
                
                self.ColorWash250 = self._dmx.registerFixtureUsingType("ColorWash 250 AT", "colorwash250at", 43)
                self._dmx.addFixtureToGroup(self.ColorWash250, "Moving Heads")
                
            except Exception as e:
                format.message(f"Error registering ColorWash 250 AT: {e}", type="error")
                
            try:
                format.message("Registering ColorSpot 250 AT ", type="info")
                
                self.ColorSpot250 = self._dmx.registerFixtureUsingType("ColorSpot 250 AT", "colorspot250at", 10)
                self._dmx.addFixtureToGroup(self.ColorSpot250, "Moving Heads")
                
            except Exception as e:
                format.message(f"Error registering ColorSpot 250 AT: {e}", type="error")
        
            self.DMXConnected = True
            
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"CONNECTED", 'type': "dmxStatus"})
            
            format.message("DMX Connection set up successfully", type="success")
            
        except Exception as e:
            format.message(f"Error occured while setting up DMX connection! ({e})", type="error")
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"DISCONNECTED", 'type': "dmxStatus"})

    def openFiles(self):
        try:
            f = open(fr"{self._dir}\data\keys.txt", "r")
            
            blank = f.readline()
            blank = f.readline()
            self.IP1 = str(f.readline().strip())
            self.IP2 = str(f.readline().strip())
            self.ETHERNET_INTERFACE = str(f.readline().strip())
            self.OBSSERVERIP = str(f.readline().strip())
            self.OBSSERVERPORT = int(f.readline().strip() or 0)
            self.OBSSERVERPASSWORD = str(f.readline().strip())
            self.DMXADAPTOR = str(f.readline().strip())
            self.SPOTIPY_CLIENT_ID = str(f.readline().strip() or "null")
            self.SPOTIPY_CLIENT_SECRET = str(f.readline().strip() or "null")
            
        except Exception as e:
            format.message(f"Error opening keys.txt: {e}", type="error")
            
        try:
            f = open(fr"{self._dir}\data\dev.txt", "r")
        except Exception as e:
            format.message(f"Error opening dev.txt: {e}", type="error")
        finally:
            devMode = f.readline().strip()
            
            if devMode.lower() == "true":
                self.devMode = True
                
                format.message("Development Mode Enabled", type="warning")
            else:
                self.devMode = False
            
        format.message("Files opened successfully", type="success")
            
        self.filesOpened = True

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
        
        @self.app.route("/schedule")
        def scehdule():
            return render_template("schedule.html")
        
        @self.app.route("/settings")
        def settings():
            return render_template("settings.html")
        
        @self.app.route("/editScene")
        def editScene():
            #Accessed by /EditScene?Id=[sceneId]
            
            sceneId = request.args.get('Id') 
            
            try:
            
                if sceneId != None or sceneId == "":
                    dmxScene = self._dmx.getDMXSceneById(sceneId)
                    
                    if dmxScene:
                        return render_template("scene.html", sceneId=sceneId, scene=dmxScene.to_dict())
                    else:
                        return render_template("error.html", message=f"Scene with Id '{sceneId}' not found")
                else:
                    return render_template("scene.html", SysName=self.SysName, PageTitle="Advanced DMX Control")
                
            except Exception as e:
                format.message(f"Error fetching scene with Id for Advanced Scene view: {e}", type="error")
                return render_template("error.html", message=f"Error fetching scene: {e}<br>This is a bug, a report has been automatically submitted.")
        
        @self.app.route("/text")
        def neonText():
            return render_template('neonFlicker.html')

        @self.app.route("/ping")
        def ping():   
            #format.message("|--- I'm still alive! ---|")
            return 'OK'
        
        @self.app.route("/api/availableFixtures", methods=["GET"])
        def availableFixtures():
            if self.DMXConnected == False:
                return jsonify({"error": "DMX Connection not available"})
            
            temp_fixtures = []
            
            try:
                
                temp_fixtures = self._dmx.getFixtures()
                
                serialized_fixtures = temp_fixtures
                
                return jsonify(serialized_fixtures)
                    
            except Exception as e:
                format.message(f"Error getting available fixtures: {e}", type="error")
                
                return jsonify({"error": f"Error getting available fixtures: {e}"}), 500
            
        @self.app.route("/api/dmx/dmxChannelValues", methods=["GET"])
        def getDMXChannelValues():
            if not self.DMXConnected:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:

                fixtures = self._dmx.getRegisteredFixtures()
                
                fixtureChannels = []

                for fixture in fixtures.items():
                    fixtureId = fixture[1]["id"]
                    fixtureName = fixture[0]
                    fixtureType = fixture[1]["type"]
                    fixtureProfile = (self._dmx.getFixtureProfiles()).get(fixtureType)

                    # Add an index to each attribute
                    indexed_fixture_profile = {}
                    for index, (key, value) in enumerate(fixtureProfile.items()):
                        fixture_temp = self._dmx.getFixturesByName(fixtureName)[0]
                        
                        if fixture_temp.json_data["type"] == "Generic.Dimmer":
                            indexed_fixture_profile = {"index": index, "value": fixture_temp.get_channel_value(key), "DMXValue": fixture_temp.channels[1]["value"][0], "channel": fixture_temp.channels[1]["name"]}
                        else:
                            try:
                                fixtureChannel_temp = 0

                                for key_id, channel in fixture_temp.channels.items():
                                    if channel["name"] == key.lower():
                                        fixtureChannel_temp = channel["value"][0]

                                indexed_fixture_profile[key] = {
                                    "DMXValue": fixtureChannel_temp,
                                    "channel": key
                                }
                            except Exception as e:
                                format.message(f"Error getting fixture channel: {e}, {key}, {value}", type="error")

                    fixtureChannels.append({
                        "name": fixtureName,
                        "id": fixtureId,
                        "attributes": indexed_fixture_profile
                    })
                    
                return jsonify(fixtureChannels)
            
            except Exception as e:
                format.message(f"Error getting DMX Channel Values: {e}", type="error")
                return jsonify({"error": f"Error getting DMX Channel Values: {e}"}), 500
            
        @self.app.route("/api/dmx/scenes", methods=["GET"])
        def getDMXScenes():
            if not self.DMXConnected:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                scenes = self._dmx.getDMXScenes() 

                serialized_scenes = [scene.to_dict() for scene in scenes]
                
                return jsonify(serialized_scenes)
            except Exception as e:
                format.message(f"Failed to fetch scenes: {str(e)}", type="error")
                return jsonify({"error": f"Failed to fetch scenes: {str(e)}"}), 500
                
        @self.app.route("/api/dmx/getScene", methods=["GET"])
        def getDMXScene():
            if not self.DMXConnected:
                return jsonify({"error": "DMX Connection not available"}), 503

            sceneId = request.args.get("sceneId") 

            if not sceneId:
                return jsonify({"error": "Scene name is required"}), 400

            try:
                scene = self._dmx.getDMXSceneById(sceneId)

                return jsonify(scene.to_dict())
            except Exception as e:
                format.message(f"Failed to fetch scene: {e}", type="error")
                return jsonify({"error": f"Failed to fetch scene: {e}"}), 500
            
        @self.app.route("/api/dmx/startScene", methods=["POST"])
        def startDMXScene():
            if not self.DMXConnected:
                return jsonify({"error": "DMX Connection not available"}), 503

            sceneId = request.form.get("sceneId") 

            if not sceneId:
                return jsonify({"error": "Scene name is required"}), 400

            try:
                self._dmx.startScene(sceneId)

                return jsonify(200)
            except Exception as e:
                format.message(f"Failed to start scene: {e}", type="error")
                return jsonify({"error": f"Failed to start scene: {e}"}), 500

        @self.app.route("/api/dmx/stopScene", methods=["POST"])
        def stopDMXScene():
            if not self.DMXConnected:
                return jsonify({"error": "DMX Connection not available"}), 503

            sceneId = request.form.get("sceneId") 

            if not sceneId:
                return jsonify({"error": "Scene name is required"}), 400

            try:
                self._dmx.stopScene(sceneId)

                return jsonify(200)
            except Exception as e:
                format.message(f"Failed to start scene: {e}", type="error")
                return jsonify({"error": f"Failed to start scene: {e}"}), 500
        
        @self.app.route("/api/dmx/createScene", methods=["POST"])
        def createDMXScene():
            if not self.DMXConnected:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                newDMXScene = self._context.DMXScene(
                    name="New Scene",
                    createDate=datetime.datetime.now(),
                    duration=0,
                    repeat=False,
                    flash=False
                )
                
                createdScene = self._dmx.createNewScene(newDMXScene)

                return jsonify(createdScene.id)
            except Exception as e:
                format.message(f"Failed to create scene: {e}", type="error")
                return jsonify({"error": f"Failed to create scene: {e}"}), 500
            
        @self.app.route("/api/dmx/editSceneName", methods=["POST"])
        def editDMXSceneName():
            if not self.DMXConnected:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                sceneId = request.form.get("sceneId")
                newName = request.form.get("newName")

                if not sceneId or not newName:
                    return jsonify({"error": "Invalid input"}), 400

                with self._context.db.session.begin():
                    scene = self._context.db.session.query(self._context.DMXScene).filter_by(id=sceneId).first()

                    if not scene:
                        return jsonify({"error": "Scene not found"}), 404

                    scene.name = newName

                return jsonify({"newName": newName})
            except Exception as e:
                format.message(f"Failed to edit scene name: {e}", type="error")
                return jsonify({"error": f"Failed to edit scene name: {e}"}), 500

        @self.app.route("/api/dmx/getSceneEvent", methods=["GET"])
        def getSceneEvent():
            if not self.DMXConnected:
                return jsonify({"error": "DMX Connection not available"}), 503
            
            eventId = request.args.get("eventId")
            
            try:
                event = self._dmx.getSceneEventById(eventId)
                
                return jsonify(event.to_dict())
            except Exception as e:
                format.message(f"Failed to fetch scene event: {e}", type="error")
                return jsonify({"error": f"Failed to fetch scene event: {e}"}), 500

        @self.app.route("/api/dmx/saveSceneEvent", methods=["POST"])
        def saveSceneEvent():
            if not self.DMXConnected:
                return jsonify({"error": "DMX Connection not available"}), 503
            
            try:
                sceneEventId = int(request.form.get("sceneEventId"))
                DMXValues = request.form.get("DMXValues")
                DMXValues = json.loads(DMXValues)
                
                if not sceneEventId or not DMXValues:
                    return jsonify({"error": "Invalid input"}), 400

                for value in DMXValues:
                    fixture = value["fixture"]
                    channel = value["channel"]
                    value = int(value["value"])
                    self._dmx.updateFixtureChannelEvent(sceneEventId, fixture, channel, value)
                    
                return jsonify({"success": "Scene event saved"}), 200
                
            except Exception as e:
                format.message(f"Failed to save scene event: {e}", type="error")
                return jsonify({"error": f"Failed to save scene event: {e}"}), 500
            
        @self.app.route("/api/dmx/setSceneSongTrigger", methods=["POST"])
        def setSceneSongTrigger():
            sceneId = request.form.get("sceneId")
            songName = request.form.get("songName")

            self._dmx.setSceneSongTrigger(sceneId, songName)

            return jsonify({"success": "Scene song trigger set"})

        @self.app.route('/end')
        def terminateServer():
            logging.shutdown()
            os.kill(os.getpid(), signal.SIGTERM)
            
        @self.socketio.on('connect')
        def handleConnect():
            format.message("Sniffer Client connected")
            
            emit('musicStatus', {'message': f"{self.spotifyStatus}"} )
            
            emit('response', {'message': 'Connected to server'})
            
        @self.socketio.on('toggleMusic')
        def togglePlayback():
            response = self.handleMusic("toggle")
            
            emit('musicStatus', {'message': f"{response}"})
            
        @self.socketio.on('restartSong')
        def restartSong():
            response = self.handleMusic("restart")
            
            emit('musicStatus', {'message': f"{response}"})
            
        @self.socketio.on('nextSong')
        def nextSong():
            response = self.handleMusic("next")
            
            emit('musicStatus', {'message': f"{response}"})
        
        @self.socketio.on('SpotifyControl')
        def handleSpotifyControl(json):
            #format.message(f"Spotify control = {json["data"]}")
            
            self.spotifyControl = json["data"]
            
        @self.socketio.on('UpdateDMXValue')
        def UpdateDMXValue(json):
            fixture = json["fixtureName"]
            channelName = json["attributeName"]
            value = json["value"]
            
            try:
                self._dmx.setFixtureChannel(fixture, channelName, value)
            except Exception as e:
                format.message(f"Error updating DMX Value: {e}", type="error")
            
        @self.socketio.on('playBriefing')
        def playBriefing():
            try:
                format.message("Playing briefing")
                if self.OBSConnected == True:
                    self.obs.set_current_program_scene("Video")
            except Exception as e:
                format.message(f"Error playing briefing: {e}", type="error")
    
        @self.app.route('/sendMessage', methods=['POST'])
        def sendMessage():
            try:
                data = request.json 
                message = data.get("message")
                type_ = data.get("type") 
            except:
                message = request.form.get("message")
                type_ = request.form.get("type")
            
            if type_:
                self.socketio.emit(f"{type_}", {"message": message}) 
                                
            return 'Message sent!'

    def obs_connect(self):
        if self.devMode == False:
            try:
                format.message("Attempting to connect to OBS")
                
                self.obs = obs.ReqClient(host=self.OBSSERVERIP, port=self.OBSSERVERPORT, password=self.OBSSERVERPASSWORD, timeout=3)
                
                self.OBSConnected = True
                format.message("Successfully Connected to OBS", type="success")
                
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"CONNECTED", 'type': "obsStatus"})

            except Exception as e:
                format.message(f"Failed to connect to OBS: {e}", type="error")
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"DISCONNECTED", 'type': "obsStatus"})
        else:
            format.message("Development Mode, skipping OBS Connection", type="warning")
    
    # -----------------| Background Tasks |-------------------------------------------------------------------------------------------------------------------------------------------------------- # 
            
    def startSniffing(self):
        format.message("Starting packet sniffer...")
        try:
            sniff(prn=self.packetCallback, store=False, iface=self.ETHERNET_INTERFACE if self.devMode != "true" else None)
        except Exception as e:
            try:
                format.message(f"Error while trying to sniff, falling back to default adaptor", type="error")
                sniff(prn=self.packetCallback, store=False, iface=r"\Device\NPF_{65FB39AF-8813-4541-AC82-849B6D301CAF}" if self.devMode != "true" else None)
            except Exception as e:
                format.message(f"Error while sniffing: {e}", type="error")
                return
            
    async def getPlayingStatus(self):
        sessions = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
        current_session = sessions.get_current_session()

        if current_session:
            info = await current_session.try_get_media_properties_async()
            playback_info = current_session.get_playback_info()
            timeline_properties = current_session.get_timeline_properties()

            # Get media playback status
            if playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                status = "playing"
            elif playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED:
                status = "paused"
            elif playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.STOPPED:
                status = "paused"
            else:
                status = "paused"
            
            currentPosition = timeline_properties.position.total_seconds()
            totalDuration = timeline_properties.end_time.total_seconds()

            return status, currentPosition, totalDuration
            
        else:
            return "paused", 0, 0
    
    def handleMusic(self, mode):
        if self.spotifyControl == True:
            if mode.lower() == "toggle":
                if self.spotifyStatus == "paused":
                    #format.message("Playing music", type="warning")
                    self.spotifyStatus = "playing"
                    pyautogui.press('playpause')
                    
                    result = self.spotifyStatus
                else:
                    #format.message("Pausing music", type="warning")
                    self.spotifyStatus = "paused"
                    pyautogui.press('playpause')
                    result = self.spotifyStatus
                
            elif mode.lower() == "next":
                pyautogui.hotkey('nexttrack')
                self.spotifyStatus = "playing"
                result = self.spotifyStatus
            
            elif mode.lower() == "previous":
                pyautogui.hotkey('prevtrack')
                pyautogui.hotkey('prevtrack')
                self.spotifyStatus = "playing"
                result = self.spotifyStatus
            
            elif mode.lower() == "restart":
                pyautogui.hotkey('prevtrack')
                result = self.spotifyStatus
                
            elif mode.lower() == "pause":
                if self.spotifyStatus == "paused":
                    return
                else:
                    #format.message("Pausing music", type="warning")
                    self.spotifyStatus = "paused"
                    pyautogui.press('playpause')
                    result = "playing"
            
            elif mode.lower() == "play":
                if self.spotifyStatus == "playing":
                    return
                else:
                    #format.message("Playing music", type="warning")
                    self.spotifyStatus = "playing"
                    pyautogui.press('playpause')
                    result = "paused"
                    
            time.sleep(2)
                
            try:
                self.bpm_thread = threading.Thread(target=self.findBPM)
                self.bpm_thread.daemon = True
                self.bpm_thread.start()
            except Exception as e:
                format.message(f"Error running BPM thread: {e}", type="error")
                
            return result
                    
        else:
            format.message("Spotify control is disabled", type="warning")
            
    def checkIfProcessRunning(self, processName):
        for proc in psutil.process_iter():
            try:
                if processName.lower() in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    def runProcessChecker(self):
        try:
            while True:
                time.sleep(600)
                for processName in self.expecteProcesses:
                    processFound = self.checkIfProcessRunning(processName)
                    #format.message(f"Process {processName} running: {processFound}")
                    
                    if not processFound:
                        try:
                            format.message(f"Process {processName} not found, starting it..", type="warning")
                            if processName.lower() == "spotify":
                                os.startfile(f"{self._dir}\\appShortcuts\\Spotify.lnk")
                            elif processName.lower() == "obs64":
                                os.startfile(f"{self._dir}\\appShortcuts\\OBS.lnk", arguments='--disable-shutdown-check')
                                time.sleep(15)
                                self.obs_connect()
                            else:
                                format.message(f"Process {processName} not recognized for auto-start", type="error")
                            # if self.DMXConnected == False:
                            #     format.message(f"DMX Connection lost, restarting DMX Network")
                            #     self.setUpDMX()
                            if self.OBSConnected == False:
                                format.message(f"OBS Connection lost, restarting OBS")
                                self.obs_connect()
                                
                        except Exception as e:
                            format.message(f"Error starting process {processName}: {e}", type="error")
                            
                # if self.RestartRequested == True and self.gameStatus == "stopped":
                #     format.message(f"Restart requested, restarting PC in 1 minute")
                #     self.AppRestartThread = threading.Thread(target=self.restartApp("Restart Requested"))
                #     self.AppRestartThread.daemon = True
                #     self.AppRestartThread.start()
                    
                if self.gameStatus == "stopped" and self.OBSConnected == True:
                    if self.endOfDay == True:
                        format.message(f"EOD, setting OBS output to Test Mode")
                        
                        try:
                            with open(fr"{self._dir}\data\OBSText.txt", "w") as f:
                                f.write("EndOfDay: Waiting for next game ")
                                
                        except Exception as e:
                            format.message(f"Error opening OBSText.txt: {e}", type="error")
                        
                        self.obs.set_current_program_scene("Test Mode")
                    else:
                        self.endOfDay = True
                
                elif self.gameStatus == "running":
                    self.endOfDay = False
                
        except Exception as e:
            format.message(f"Error occured while checking processes: {e}", type="error")
            
    def restartApp(self, reason="unknown"):
        if self.devMode == True:
            format.message("Development mode, skipping restart", type="warning")
            return
        
        format.message(f"Restarting App in 1 minute due to {reason}", type="warning")
        
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Restart", 'type': "createWarning"})
        
        time.sleep(60)
        
        format.message("Restarting App", type="warning")

        os._exit(1)
            
    def handleBPM(self, song, album, bpm=0):
        #format.message(f"Get Here with {song}, {bpm}, {album}")
        try:
            if (self.rateLimit == True and ((random.randint(1, 50)) == 10)) or self.rateLimit == False:
                
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
                        case "Science Blaster":
                            bpm = "92"
                        case "Undertow":
                            bpm = "88"
                        case _:
                            bpm = "60"
            
                #format.message(f"Current song: {song}, BPM: {bpm}")
            
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{song}", 'type': "songName"})
            
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{str(round(int(bpm)))}", 'type': "songBPM"})
            
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{album}", 'type': "songAlbum"})
                
                self.rateLimit = False
                
        except Exception as e:
            if "Max Retries, reason: too many 429 error responses" in bpm:
                self.rateLimit = True
                return
            else:
                format.message(f"Error occured while handling BPM: {e}", type="warning")
        
    def findBPM(self):
        try:
            try:
                self.fetcher.fetch()
                song, bpm, album = self.fetcher.get_current_song_and_bpm()
                
                if type(bpm) == str:
                    bpm = 0
                
                self.handleBPM(song, album, bpm)
            except Exception as e:
                format.message(f"Error fetching BPM: {e}", type="error")
            
            temp_spotifyStatus, currentPosition, totalDuration = asyncio.run(self.getPlayingStatus())

            if temp_spotifyStatus != self.spotifyStatus:
                self.spotifyStatus = temp_spotifyStatus

                try:
                    response = requests.post(
                        f'http://{self._localIp}:8080/sendMessage',
                        data={'message': f"{self.spotifyStatus}", 'type': "musicStatus"}
                    )
                    if response.status_code != 200:
                        raise Exception(f"Failed to send status: {response.text}")
                except Exception as e:
                    format.message(f"Error sending Spotify status: {e}", type="error")

        except Exception as e:
            format.message(f"Failed to find BPM: {e}", type="error")

   
    def mediaStatusChecker(self):
        while True:
            try:
                temp_spotifyStatus, currentPosition, totalDuration = asyncio.run(self.getPlayingStatus())
                
                if temp_spotifyStatus != self.spotifyStatus:
                    self.spotifyStatus = temp_spotifyStatus
                    
                    try:
                        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{self.spotifyStatus}", 'type': "musicStatus"})
                    except Exception as e:
                        format.message(f"Error sending music status message, app probably hasn't started. {e}.", type="error")
                    
                if currentPosition and totalDuration:
                    try:
                        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{currentPosition}", 'type': "musicPosition"})
                        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{totalDuration}", 'type': "musicDuration"})
                    except Exception as e:
                        format.message(f"Error sending music status message, app probably hasn't started. {e}.", type="error")
                    
                time.sleep(5)
                
            except Exception as e:
                format.message(f"Error occured while checking media status: {e}", type="error")
                
                if self.devMode == True:
                    format.message("Development Mode, ignoring error handling because its dumb", type="warning")
                    return
                
                if str(e) != "an integer is required":
        
                    format.message("Requesting app restart", type="warning")
                    if self.gameStatus != "stopped":
                        pyautogui.press("playpause")
                    
                    self.RestartRequested = True
                    
                    self.AppRestartThread = threading.Thread(target=self.restartApp(f"Restart Requested - BPM Issue: {e}"))
                    self.AppRestartThread.daemon = True
                    
                    # Just makes sure to pause this process, so it doesn't keep logging the same error
                    time.sleep(600)
                    
                else:
                    format.message("Error not fatal, don't care", type="warning")
                
                    time.sleep(5)                 
        
    # -----------------| Packet Handling |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
        
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
        
    def gameStatusPacket(self, packetData):
        # 4,@015,0 = start
        # 4,@014,0 = end
        
        if self.OBSConnected == True:
            self.endOfDay = False
            self.obs.set_current_program_scene("Laser Scores")
        
        format.message(f"Game Status Packet: {packetData}, Mode: {packetData[0]}")
        
        if packetData[1] == "@015":
            self.gameStatus = "running"
            format.message(f"Game start packet detected at {datetime.datetime.now()}", type="success")
            self.gameStarted()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Started @ {str(datetime.datetime.now())}", 'type': "start"})
            #format.message(f"Response: {response.text}")
        
        elif packetData[1] == "@014":
            self.gameStatus = "stopped"
            format.message(f"Game Ended at {datetime.datetime.now()}", type="success") 
            self.gameEnded()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
            #format.message(f"Response: {response.text}")
            
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{packetData[0]}", 'type': "gameMode"})

    def timingPacket(self, packetData):
        timeLeft = packetData[3]
        
        format.message(f"Time Left: {timeLeft}")

        if int(timeLeft) <= 0:
            self.gameStatus = "stopped"
            format.message(f"Game Ended at {datetime.datetime.now()}", type="success") 
            self.gameEnded()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
            #format.message(f"Response: {response.text}")
        else:
            self.gameStatus = "running"
            if self.OBSConnected == True:
                self.endOfDay = False
                self.obs.set_current_program_scene("Laser Scores")
            format.message(f"{timeLeft} seconds remain!", type="success") 
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Started @ {str(datetime.datetime.now())}", 'type': "start"})
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{timeLeft}", 'type': "timeRemaining"})
        
        format.newline()
    
    def finalScorePacket(self, packetData):
        gunId = packetData[1]
        finalScore = packetData[3]
        accuracy = packetData[7]

        gunName = None
        
        try:
            with self.app.app_context():
                gunName = "name: "+ self._context.Gun.query.filter_by(id=gunId).first().name
        
        except Exception as e:
            format.message(f"Error getting gun name: {e}", type="error")
        
        if gunName == None:
            gunName = "id: "+gunId
            
        format.message(f"Gun {gunName} has a score of {finalScore} and an accuracy of {accuracy}", type="success")
        
        data = f"{gunId},{finalScore},{accuracy}"
        
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': data, 'type': "gunScores"})
        
    def shotConfirmedPacket(self, packetData):
        pass
    
    # -----------------| Game Handling |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
    
    def gameStarted(self):
        format.message("Game started")
        
        if self.gameStatus == "running":
            return
        
        try:
            self.gameStatus = "running"
            
            self.handleMusic(mode="play")
        except Exception as e:
            format.message(f"Error handling music: {e}", type="error")
            
        try:
            #self.setFixtureBrightness(255)
            
            #self._RedBulkHeadLights.dim(255, 5000)
            
            pass
        except Exception as e:
            format.message(f"Error dimming red lights: {e}", type="error")
        
    def gameEnded(self):
        format.message("Game ended")
        
        if self.gameStatus == "stopped":
            return
        
        try:
            self.gameStatus = "stopped"
            
            self.handleMusic(mode="pause")
        except Exception as e:
            format.message(f"Error handling music: {e}", type="error")
            
        try:
            #self.setFixtureBrightness(0)
            
            pass
            
        except Exception as e:
            format.message(f"Error dimming red lights: {e}", type="error")

    # -----------------| Testing |-------------------------------------------------------------------------------------------------------------------------------------------------------- #    
    
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
        
    # -----------------| Utlities |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
        
    def hexToASCII(self, hexString):
        ascii = ""
     
        for i in range(0, len(hexString), 2):
     
            part = hexString[i : i + 2]
     
            ch = chr(int(part, 16))
     
            ascii += ch
            
            if ch == "\x00":
                break
         
        return ascii