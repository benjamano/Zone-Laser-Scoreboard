from flask import Flask, render_template, request, jsonify, redirect, g, session, url_for
from flask_socketio import SocketIO, emit
import os, signal, ctypes, datetime, socket, requests, psutil, webbrowser, asyncio, pyautogui, random, logging, json, threading, time
from scapy.all import sniff, IP
from dotenv import dotenv_values

try:
    import winrt.windows.media.control as wmc
except Exception as e:
    print("Failed to import winrt.windows.media.control ", e)
    input("Press any key to exit...")

from API import format
from API.BPM import MediaBPMFetcher
from API.DMXControl import dmx
from API.DB import *
from API.OBS import OBS
from API.Supervisor import Supervisor
from API.Emails import EmailsAPIController


from data.models import *

from API.createApp import *

class WebApp:
    def __init__(self):
        global secrets
        
        self._dir = os.path.dirname(os.path.realpath(__file__))
        
        secrets = dotenv_values(self._dir.replace(r"\backend", "") + r"\.env")
        
        # print(secrets)
        
        format.message(format.colourText("Loading Environment Variables", "Cyan"), type="info")
        
        # LOAD ENVIRONMENT VARIABLES
        self.ENVIRONMENT = secrets["Environment"]
        self.IP1 = secrets["IP1"]
        self.IP2 = secrets["IP2"]
        self.ETHERNET_INTERFACE = secrets["EthernetInterface"]
        self.OBSSERVERIP = secrets["ObsServerIp"]
        self.OBSSERVERPORT = secrets["ObsServerPort"]
        self.OBSSERVERPASSWORD = secrets["ObsServerPassword"]
        # END LOAD
        
        # LOAD SYSTEM VARIABLES
        self.SysName = "TBS"
        self.VersionNumber = "1.1.3"
        # END LOAD
        
        # INIT ALL OTHER VARIABLES
        self.OBSConnected = False
        self.devMode = self.ENVIRONMENT == "Development"
        self.spotifyControl = True
        self.spotifyStatus = "paused"
        self._localIp = ""
        self.RestartRequested = False
        self.gameStatus = "stopped" # Either running or stopped
        self.endOfDay = False
        self.currentGameId = 0
        self.GunScores = {}
        self.TeamScores = {}    
        # END INIT
           
        # INIT DEPENDANCIES
        self._supervisor : Supervisor = None
        self._obs : OBS = None
        self._dmx : dmx = None
        self._context : context = None
        self.app : Flask = None
        self._emailsApi : EmailsAPIController = None
        # END INIT
                
        pyautogui.FAILSAFE = False

        format.message(f"Starting Web App at {str(datetime.datetime.now())}", type="warning")
        
        self.initLogging()
        
        self.app, self.socketio, self._context = create_app(self._supervisor) 
        
        format.message(format.colourText("Setting up routes..." ,"Blue"))
        
        self.setupRoutes()

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
            format.message(f"Fatal! {e}")
            os._exit(1)
        
    def start(self):
        format.newline() 
        
        try:
            format.message("Starting Supervisor", type="info")
            self.SupervisorThread = threading.Thread(target=self.startSupervisor, daemon=True).start()
            
        except Exception as e:
            format.message(f"Error starting Supervisor: {e}", type="error")
            raise Exception("Error starting Supervisor: ", e)
        
        try:
            # Create a dummy socket connection to find the local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self._localIp = s.getsockname()[0]
            s.close()
        except Exception as e:
            format.message(f"Error finding local IP: {e}")
        
        format.message("Attempting to start Flask Server")
        
        try:
            self.flaskThread = threading.Thread(target=self.startFlask)
            self.flaskThread.daemon = True
            self.flaskThread.start()
            
            format.message("Waiting for app to start", type="warning")
            time.sleep(2)
            
        except Exception as e:
            format.message(f"Error starting Flask Server: {e}", type="error")
            return SystemExit

        format.message(f"Web App hosted on IP {self._localIp}", type="success")
        
        while self.app == None:
            format.message("Waiting for app to start", type="warning")
            time.sleep(2)
        
        # with self.app.app_context():
        #     self._context = context(self.app, self._supervisor, self.db)
        
        # def bpmLoop():
        #     while True:
        #         try:
        #             self.findBPM()
        #             time.sleep(10)
        #         except Exception as e:
        #             format.message(f"Error in BPM loop: {e}", type="error")
        #             break

        # self.bpm_thread = threading.Thread(target=bpmLoop, daemon=True)
        # self.bpm_thread.start()  
            
        format.message("Attempting to start Media status checker")
        
        try:
            self.mediaStatusCheckerThread = threading.Thread(target=self.mediaStatusChecker)
            self.mediaStatusCheckerThread.daemon = True
            self.mediaStatusCheckerThread.start()
            
        except Exception as e:
            format.message(f"Error starting Media Status Checker: {e}", type="error")
        
        # if self.devMode == False:
        #     webbrowser.open(f"http://{self._localIp}:8080")
            
        try:
            self.obs_thread = threading.Thread(target=self.connectToOBS)
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

        # format.message("Web App Started, hiding console", type="success")
        
        # try:
        #     ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        # except Exception as e:
        #     format.message(f"Hiding console: {e}", type="error")
        
        try:
            self.sniffing_thread = threading.Thread(target=self.startSniffing)
            self.sniffing_thread.daemon = True
            self.sniffing_thread.start()
            
        except Exception as e:
            format.message(f"Error starting packet sniffer: {e}", type="error")
            
        try:
            self.fetcher = MediaBPMFetcher()
        except Exception as e:
            format.message(f"Error starting music info fetcher: {e}", type="error")
            
        try:
            self._emailsApi = EmailsAPIController.EmailsAPIController(secrets["GmailAppPassword"], secrets["GmailSenderEmail"], secrets["GmailSenderDisplayName"])
        except Exception as e:
            format.message(f"Error starting email api: {e}", type="error")
            
        while self._supervisor == None:
            time.sleep(1)
        
        self._supervisor.setDependencies(obs=self._obs, dmx=self._dmx, db=self._context, webApp=self)
        
        format.sendEmail(f"Web App started at {str(datetime.datetime.now())}", "APP STARTED")
        
        format.newline()    
        
        self.flaskThread.join()

    def initLogging(self):
        #self.app.logger.disabled = True
        #logging.getLogger('werkzeug').disabled = True
        return
    
    def startSupervisor(self):
        self._supervisor = Supervisor()
        
        return
    
    def setUpDMX(self):
        #Requires USB to DMX with driver version of "libusb-win32"
        
        try:
            self._dmx = dmx(self._context, self._supervisor, self.app, self.devMode)
            
        except Exception as e:
            format.message(f"Error starting DMX Connection: {e}", type="error")
            return
        
        if self._dmx.isConnected() == True:
            
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
        
    def connectToOBS(self):
        try:
            self._obs = OBS(self.OBSSERVERIP, self.OBSSERVERPORT, self.OBSSERVERPASSWORD, self._dir, self._supervisor)
        except Exception as e:
            format.message(f"Error setting up OBS connection: {e}", type="error")

    def setupRoutes(self):     
        # @self.app.errorhandler(404)
        # def not_found():
        #     return render_template("error.html", message="Page not found")
        
        @self.app.context_processor
        def inject_global_vars():
            return dict(
                SysName=self.SysName,
                VersionNo=self.VersionNumber,
                PageTitle=getattr(g, 'PageTitle', "")
            )
            
        @self.app.route('/')
        def index():
            try:                
                g.PageTitle = "Home"
                
                return render_template('index.html')
        
            except Exception as e:
                format.message(f"Error loading index.html: {e}", type="error")
                return render_template("error.html", message=f"Error loading index: {e}\nThis is a bug, a report has been automatically submitted.")
    
        @self.app.route("/schedule")
        def scehdule():
            g.PageTitle = "Schedule"
            
            return render_template("schedule.html")
        
        @self.app.route("/settings")
        def settings():
            g.PageTitle = "Settings"
            
            return render_template("settings.html")
        
        @self.app.route("/editScene")
        def editScene():
            #Accessed by /EditScene?Id=[sceneId]
            g.PageTitle = "Lighting Control"
            
            sceneId = request.args.get('Id') 
            
            try:
            
                if sceneId != None or sceneId == "":
                    dmxScene = self._dmx.getDMXSceneById(sceneId)
                    
                    if dmxScene:
                        return render_template("scene.html", sceneId=sceneId, scene=dmxScene.to_dict())
                    else:
                        return render_template("error.html", message=f"Scene with Id '{sceneId}' not found")
                else:
                    return render_template("scene.html")
                
            except Exception as e:
                format.message(f"Error fetching scene with Id '{sceneId}' for Advanced Scene view: {e}", type="error")
                return render_template("error.html", message=f"Error fetching scene: {e}<br>This is a bug, a report has been automatically submitted.")
        
        @self.app.route("/text")
        def neonText():
            return render_template("neonFlicker.html")
        
        @self.app.route("/status")
        def status():
            g.PageTitle = "Status"
            
            return render_template("status.html")
        
        @self.app.route("/experimental")
        def experimental():
            return redirect("/")
            
            return render_template("experimental/newIndex.html", SysName=self.SysName, PageTitle="Experiments")
        
        @self.app.route("/feedback")
        def feedback():
            g.PageTitle = "Leave Feedback"
            
            return render_template("feedback.html")
        
        @self.app.route("/statistics")
        def statistics():
            g.PageTitle = "Statistics"
            
            return render_template("statistics.html")

        @self.app.route("/managerTools")
        def managerTools():
            g.PageTitle = "Manager Tools"
            
            return render_template("ManagerTools/managerTools.html")
        
        def managerTools_VerifyAuthCookie(cookie: str) -> bool:
            try:
                if cookie is None or cookie == "":
                    return False
                
                cookieDate = datetime.datetime.fromisoformat(cookie)
                if cookieDate < datetime.datetime.now():
                    return True
                else:
                    return False
                
            except Exception:
                return False
        
        @self.app.route("/api/managerTools/requestAuthorisation", methods=["POST"])
        def managerTools_RequestAuth():
            try:
                # if (request.remote_addr):
                    
                
                password : str = request.form.get("password", "")
            except Exception as e:
                return jsonify({
                    "error": f"Error parsing request data: {str(e)}"
                }), 400
                
            if (password == secrets["ManagerLoginCredentials"]):
                # AUTHORISE THIS USER FOR 7 DAYS
                newCookie : datetime.datetime = datetime.datetime.now() + datetime.timedelta(days=7)
                
                return jsonify({
                    "cookie": newCookie.isoformat()
                }), 200
            else:
                return jsonify({
                    "error": f"Incorrect password!"
                }), 401
        
        @self.app.route("/api/managerTools/amIAuthorised")
        def managerTools_amIAuthorised():
            cookie: str = request.args.get("cookie")
            
            try:
                if managerTools_VerifyAuthCookie(cookie) == False:
                    return jsonify({"response": False}), 200
                    
                return jsonify({"response": True}), 200
                
            except Exception:
                return jsonify({"response": False}), 200
        
        @self.app.route("/api/managerTools/sendEmail", methods=["POST"])
        def sendEmail():
            try:
                cookie: str = request.form.get("authCookie", None)
                if managerTools_VerifyAuthCookie(cookie) == False:
                    return jsonify({
                    "error": f"Your authorisation cookie has expired. Please re-enter your authorisation credentials."
                }), 401
                
                recipients = request.form.get("recipients", [])
                if isinstance(recipients, str):
                    recipients = [recipients]
                    
                body = request.form.get("emailBody", "")
                
                subject = request.form.get("emailSubject", "")
                
            except Exception as e:
                return jsonify({
                    "error": f"Error parsing request data: {str(e)}"
                }), 400
            
            if not subject or len(subject) < 5:
                return jsonify({
                    "error": "The subject must be at least 5 characters long"
                }), 400
                
            if not body:
                return jsonify({
                    "error": "The email body cannot be empty"
                }), 400
            
            errorList : list = []
            
            if secrets["Environment"] == "Development":
                recipients = [secrets["DevelopmentEmailAddress"]]
            
            for recipient in recipients:
                try:
                    self._emailsApi.sendEmail(recipient, subject, body)
                except Exception as e:
                    errorList.append(f"Error sending to {recipient}: {e}")
            
            return jsonify({
                "message": "Emails Sent!",
                "errorList": errorList
            }), 200
        
        @self.app.route("/api/managerTools/ProcessEmailAddresses", methods=["POST"])
        def processEmailAddresses():
            try:
                csvContent = request.form.get("EmailAddresses")
                
                if csvContent:
                    emailAddresses = csvContent.strip().split(",")
                    processedAddresses = []
                    
                    for email in emailAddresses:
                        cleanedEmail = email.strip().strip('"').strip("'")
                        if cleanedEmail:
                            processedAddresses.append(cleanedEmail)
                    
                    return jsonify({
                        "processed": len(processedAddresses),
                        "emails": processedAddresses
                    })
                    
                return jsonify({"error": "No content provided"}), 400
                    
            except Exception as e:
                return jsonify({"error": str(e)}), 500
            
        @self.app.route("/api/settings/sendMessage", methods=["POST"])
        def settings_sendMessage():
            try:
                message = request.form.get("message")
                
                with open(self._dir + "/data/messages.txt", "a") as f:
                    f.write(message + "\n")
                    
                return jsonify({
                    "message": "Message Sent"
                })
                    
            except Exception as e:
                return jsonify({"error": str(e)}), 500
            
        @self.app.route("/api/settings/getMessages", methods=["GET"])
        def settings_getMessages():
            try:
                with open(self._dir + "/data/messages.txt", "r") as f:
                    messages = f.read()
                    
                return jsonify(messages)
                    
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/ping")
        def ping():   
            #format.message("|--- I'm still alive! ---|")
            return 'OK'
        
        @self.app.route("/api/getAllGames", methods=["GET"])
        def getAllGames():
            try:
                games : list[Game] = self._context.getAllGames()
                
                gameList : list[dict] = []
                
                for game in games:
                    gameList.append(game.to_dict())
                    
                return jsonify(gameList)
            
            except Exception as e:
                return
                # ise : InternalServerError = InternalServerError()
                
                # ise.service = "api"
                # ise.exception_message = str(f"Error getting service status: {e}, Traceback: {e.__traceback__}")
                # ise.process = "API: Get Service Status"
                # ise.severity = "1"
                
                # self._supervisor.logInternalServerError(ise)
                
                # return jsonify({"error": f"Error getting service status: {e}"}), 500
        
        @self.app.route("/api/serviceStatus", methods=["GET"])
        def serviceStatus():
            try:
                services : list[str] = self._supervisor.getServices()
                
                serviceHealthList : list[dict] = []
                
                for service in services:
                    serviceHealth : ServiceHealthDTO = self._supervisor.getServiceHealth(service)
                    
                    if (serviceHealth != None):
                        serviceHealthList.append(serviceHealth.to_dict())
                
                return jsonify(serviceHealthList)
            
            except Exception as e:
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Error getting service status: {e}, Traceback: {e.__traceback__}")
                ise.process = "API: Get Service Status"
                ise.severity = "1"
                
                self._supervisor.logInternalServerError(ise)
                
                return jsonify({"error": f"Error getting service status: {e}"}), 500
        
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Error Getting available fixtures: {e}")
                ise.process = "API: Get Available Fixtures"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
                
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Error DMX channel values: {e}")
                ise.process = "API: Get DMX Values"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Failed to fetch scenes: {e}")
                ise.process = "API: Get DMX Scenes"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Failed to fetch scene: {e}")
                ise.process = "API: DMX Scene"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Failed to start scene: {e}")
                ise.process = "API: Start DMX Scene"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Failed to stop scene: {e}")
                ise.process = "API: Stop DMX Scene"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Failed to create scene: {e}")
                ise.process = "API: Create DMX Scene"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Failed to edit scene name: {e}")
                ise.process = "API: Edit DMX Scene Name"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Failed to get scene event: {e}")
                ise.process = "API: Get DMX Scene Event"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Failed to save scene event: {e}")
                ise.process = "API: Save DMX Scene Event"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
                return jsonify({"error": f"Failed to save scene event: {e}"}), 500
            
        @self.app.route("/api/dmx/setSceneSongTrigger", methods=["POST"])
        def setSceneSongTrigger():
            sceneId = request.form.get("sceneId")
            songName = request.form.get("songName")

            self._dmx.setSceneSongTrigger(sceneId, songName)

            return jsonify({"success": "Scene song trigger set"})

        @self.app.route("/api/dmx/createSceneEvent", methods=["POST"])
        def createSceneEvent():
            sceneId = request.form.get("sceneId")

            try:
                self._dmx.createNewSceneEvent(sceneId)
                
                return jsonify({"success": "Scene event created"})
            except Exception as e:
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Failed to create scene event: {e}")
                ise.process = "API: Create New DMX Scene Event"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
                return jsonify({"error": f"Failed to create scene event: {e}"}), 500

        @self.app.route('/end')
        def terminateServer():
            logging.shutdown()
            os.kill(os.getpid(), signal.SIGTERM)
            
        @self.socketio.on('connect')
        def handleConnect():
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
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Failed to update DMX Value: {e}")
                ise.process = "API: Update DMX Value"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
            
        @self.socketio.on('playBriefing')
        def playBriefing():
            if self._obs != None and self._obs.isConnected() == True:
                try:
                    #format.message("Playing briefing")
                    self._obs.switchScene("Video")
                    
                    return 200
                except Exception as e:
                    ise : InternalServerError = InternalServerError()
                
                    ise.service = "api"
                    ise.exception_message = str(f"Failed to start OBS Briefing: {e}")
                    ise.process = "API: Start OBS Briefing"
                    ise.severity = "1"
                    
                    self._supervisor.logInternalServerError(ise)

            else:
                #format.message("OBS not connected, cannot play breifing!", type="warning")
                return 500
    
        @self.app.route('/sendMessage', methods=['POST'])
        def sendMessage():
            try:
                data = request.get_json(silent=True) or {}
                message = data.get("message") or request.form.get("message")
                type_ = data.get("type") or request.form.get("type")

                if type_:
                    self.socketio.emit(f"{type_}", {"message": message}) 
                                    
                return jsonify({"status": "success"}), 200
            
            except Exception as e:
                ise : InternalServerError = InternalServerError()
                
                ise.service = "socket"
                ise.exception_message = str(f"Failed To Send Socket Message: {e}")
                ise.process = "Socket: Send Message"
                ise.severity = "1"
                
                self._supervisor.logInternalServerError(ise)
                    
            # ise : InternalServerError = InternalServerError()
            
            # ise.service = "api"
            # ise.exception_message = str(f"Failed to start server: {e}")
            # ise.process = "API: Start Server"
            # ise.severity = "1"
            
            # self._supervisor.logInternalServerError(ise)
    
    # -----------------| Background Tasks |-------------------------------------------------------------------------------------------------------------------------------------------------------- # 
            
    def startSniffing(self):
        format.message("Starting packet sniffer...")
        try:
            sniff(prn=self.packetCallback, store=False, iface=self.ETHERNET_INTERFACE if self.devMode != "true" else None)
        except Exception as e:
            format.message(f"Error while sniffing: {e}", type="error")
            return
            
    async def getPlayingStatus(self):
        sessions = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
        current_session = sessions.get_current_session()
        
        if not current_session:
            return "paused", 0, 0

        playback_info = current_session.get_playback_info()
        timeline_properties = current_session.get_timeline_properties()

        status = "playing" if playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING else "paused"

        currentPosition = timeline_properties.position.total_seconds()
        totalDuration = timeline_properties.end_time.total_seconds()

        return status, currentPosition, totalDuration
    
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
                
            # try:
            #     self.bpm_thread = threading.Thread(target=self.findBPM)
            #     self.bpm_thread.daemon = True
            #     self.bpm_thread.start()
            # except Exception as e:
            #     format.message(f"Error running BPM thread: {e}", type="error")
                
            return result
                    
        else:
            format.message("Spotify control is disabled", type="warning")
            
    def restartApp(self, reason="unknown"):
        if self.devMode == True:
            format.message("Development mode, skipping restart", type="warning")
            return
        
        format.message(f"Restarting App due to {reason}", type="error")
        
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': "Restarting Web App Now!", 'type': "createWarning"})
        
        # Make sure all the end of game processing completes
        time.sleep(5)
        
        format.message("Restarting App", type="warning")

        os._exit(1)
            
    def handleBPM(self, song, album, bpm=0):
        #format.message(f"Get Here with {song}, {bpm}, {album}")
        try:
            if (self.rateLimit == True and ((random.randint(1, 50)) == 10)) or self.rateLimit == False:
                
                if song == None or bpm == None or bpm == "Song not found":
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
            
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{str(round(int(bpm)))}", 'type': "songBPM"})
                
                self.rateLimit = False
                
        except Exception as e:
            if "max retries, reason: too many 429 error responses" in e.lower():
                self.rateLimit = True
                return
            else:
                format.message(f"Error occured while handling BPM: {e}", type="warning")
        
    # def findBPM(self):
    #     try:
    #         try:
    #             self.fetcher.fetch()
    #             song, bpm, album = self.fetcher.get_current_song_and_bpm()
                
    #             if type(bpm) == str:
    #                 bpm = 0
                
    #             self.handleBPM(song, album, bpm)
    #         except Exception as e:
    #             format.message(f"Error fetching BPM: {e}", type="error")
            
    #         temp_spotifyStatus, currentPosition, totalDuration = asyncio.run(self.getPlayingStatus())

    #         if temp_spotifyStatus != self.spotifyStatus:
    #             self.spotifyStatus = temp_spotifyStatus

    #             try:
    #                 response = requests.post(
    #                     f'http://{self._localIp}:8080/sendMessage',
    #                     data={'message': self.spotifyStatus, 'type': "musicStatus"}
    #                 )
    #                 if response.status_code != 200:
    #                     raise Exception(f"Failed to send status: {response.text}")
    #             except Exception as e:
    #                 format.message(f"Error sending Spotify status: {e}", type="error")

    #     except Exception as e:
    #         format.message(f"Failed to find BPM: {e}", type="error")
   
    def mediaStatusChecker(self):
        while True:
            time.sleep(5)
            
            try:
                song, album, bpm = self.fetcher.get_current_song_and_bpm()
                
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{album}", 'type': "songAlbum"})
                
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{song}", 'type': "songName"})
                
                # self.handleBPM(song)
            
            except Exception as e:
                pass
            
            try:
                temp_spotifyStatus, currentPosition, totalDuration = asyncio.run(self.getPlayingStatus())
                
                if temp_spotifyStatus != self.spotifyStatus:
                    self.spotifyStatus = temp_spotifyStatus
                    
                try:
                    # response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{self.spotifyStatus}", 'type': "musicStatus"})
                    
                    response = requests.post(
                        f"http://{self._localIp}:8080/sendMessage",
                        json={
                            "message": {
                                "playbackStatus": self.spotifyStatus,
                                "musicPosition": currentPosition,
                                "duration": totalDuration
                            },
                            "type": "musicStatusV2"
                        }
                    )
                except Exception as e:
                    format.message(f"Error sending music status message: {e}.", type="error")
                    
                # if currentPosition and totalDuration:
                #     try:
                #         response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{currentPosition}", 'type': "musicPosition"})
                #         response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{totalDuration}", 'type': "musicDuration"})
                #     except Exception as e:
                #         format.message(f"Error sending music status message, app probably hasn't started. {e}.", type="error")
                
            except Exception as e:
                format.message(f"Error occured while checking media status: {e}", type="error")
                
                if self.devMode == True:
                    format.message("Development Mode, ignoring error handling because its dumb", type="warning")
                    return
                
                if str(e) != "an integer is required":
        
                    format.message("Requesting app restart", type="warning")
                        
                    response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"WARNING: A critical error has occured! Background service will restart at the end of this game.", 'type': "createWarning"})
                    
                    self.RestartRequested = True
                    
                    # Just makes sure to pause this process, so it doesn't keep logging the same error
                    time.sleep(600)
                    
                else:
                    format.message("Error not fatal, don't care", type="warning")
                
                    time.sleep(3)                 
        
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
                    
                elif decodedData[0] == "2":
                    # Team Score packet is being transmitted as the Event Type = 32 (Hex) = 2
                    threading.Thread(target=self.teamScorePacket, args=(decodedData,)).start()
                
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
        
        format.message(f"Game Status Packet: {packetData}, Mode: {packetData[1]}")
        
        if packetData[1] == "@015":
            self.gameStarted()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Started @ {str(datetime.datetime.now())}", 'type': "start"})
            #format.message(f"Response: {response.text}")
        
        elif packetData[1] == "@014":
            self.gameEnded()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
            #format.message(f"Response: {response.text}")
            
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{packetData[0]}", 'type': "gameMode"})
        
    def teamScorePacket(self, packetData):
        #0 = red, 2 = green
        #format.message(f"Team Score Packet: {packetData}")
        
        teamId = str(packetData[1])
        teamScore = str(packetData[2])
        
        if teamId == "0":
            teamId = "Red"
        else:
            teamId = "Green"

        try:
            self.TeamScores[teamId] = teamScore
        except Exception as e:
            format.message(f"Error updating Team Scores: {e}", type="error")

    def timingPacket(self, packetData):
        timeLeft = packetData[3]
        
        #format.message(f"Time Left: {timeLeft}")

        if int(timeLeft) <= 0:
            #format.message(f"Game Ended at {datetime.datetime.now()}", type="success") 
            self.gameEnded()
        else:
            self.gameStarted()
            self.endOfDay = False
            if self._obs != None:
                self._obs.switchScene("Laser Scores")
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{timeLeft}", 'type': "timeRemaining"})
        
        #format.newline()
    
    def finalScorePacket(self, packetData):
        gunId = packetData[1]
        finalScore = packetData[3]
        accuracy = packetData[7]

        gunName = ""
        
        try:
            with self.app.app_context():
                gunName : str = self._context.Gun.query.filter_by(id=gunId).first().name
        
        except Exception as e:
            format.message(f"Error getting gun name: {e}", type="error")
            
        if gunName == "":
            gunName = "id: "+gunId
            
        try:
            self.GunScores[gunId] = finalScore
        except Exception as e:
            format.message(f"Error updating Gun Scores: {e}", type="error")
            
        #format.message(f"Gun {gunName} has a score of {finalScore} and an accuracy of {accuracy}", type="success")
        
        data = f"{gunId},{finalScore},{accuracy}"
        
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': data, 'type': "gunScores"})
        
    def shotConfirmedPacket(self, packetData):
        #format.message(f"Shot Confirmed Packet: {packetData}")
        pass
    
    # -----------------| Game Handling |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
    
    def gameStarted(self):
        if self.gameStatus == "running":
            return
        
        format.newline()
        
        try:
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Started @ {str(datetime.datetime.now())}", 'type': "start"})
        except Exception as e:
            pass
                    
        format.message(f"Game started at {datetime.datetime.now():%d/%m/%Y %H:%M:%S}", type="success")

        self.handleMusic(mode="play")

        self.gameStatus = "running"
        self.GunScores = {}
        self.TeamScores = {}
        self.endOfDay = False

        self.currentGameId = self._context.createNewGame()
        
        format.message(f"Created new game with Id {self.currentGameId}")
            
        if self._obs != None:
            self._obs.switchScene("Laser Scores")
        
    def gameEnded(self):
        if self.gameStatus == "stopped":
            return
        
        try:
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.datetime.now())}", 'type': "end"})
        except Exception as e:
            pass
        
        format.message(f"Game ended at {datetime.datetime.now():%d/%m/%Y %H:%M:%S}", type="success")

        self.gameStatus = "stopped"
        
        self.handleMusic(mode="pause")
            
        try:
            if self.currentGameId != 0:
                winningPlayer = ""
                winningTeam = ""
                
                try:
                    winningPlayer = max(self.GunScores.items(), key=lambda x: x[1])[0]
                except Exception as e:
                    format.message(f"Error getting winning player: {e}", type="error")
                    
                try:
                    winningTeam = max(self.TeamScores.items(), key=lambda x: x[1])[0]
                except Exception as e:
                    format.message(f"Error getting winning team: {e}", type="error")
                    
                if winningPlayer != "" and winningTeam != "" and self._obs != None:
                    #self._obs.showWinners(str(winningPlayer), str(winningTeam))
                    pass
                
                self._context.updateGame(self.currentGameId, endTime=datetime.datetime.now(), winningPlayer=winningPlayer, winningTeam=winningTeam)
                
                #format.message(f"Set Current Game's End Time to {datetime.datetime.now()}, ID: {self.currentGameId}")
            
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "webapp"
            ise.exception_message = str(f"Failed To Switch To Winners Screen: {e}")
            ise.process = "WebApp: Switch To Winners Screen"
            ise.severity = "2"
            
            self._supervisor.logInternalServerError(ise)
            
        try:
            with self.app.app_context():
                for gunId, score in self.GunScores.items():
                    gamePlayer : GamePlayer = self._context.GamePlayer.query.filter_by(gameId=self.currentGameId).filter_by(gunId=gunId).first()
                        
                    if gamePlayer != None:
                        gamePlayer.score = score
                        gamePlayer.accuracy = 0
                        self._context.SaveChanges()
                        
                    else:
                        gamePlayer : GamePlayer = GamePlayer(gameId=self.currentGameId, gunId=gunId, score=score, accuracy=0)
                        self._context.addGamePlayer(gamePlayer)
                        
                    format.message(f"Adding gun id: {gunId}'s score: {score} into game id of {self.currentGameId}")
                    
                self.currentGameId = 0
                    
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "zone"
            ise.exception_message = str(f"Failed to update player scores in DB: {e}")
            ise.process = "Zone: Update Gun Scores in DB"
            ise.severity = "3"
            
            self._supervisor.logInternalServerError(ise)
            
        try:
            if self.RestartRequested == True:
                self.AppRestartThread = threading.Thread(target=self.restartApp(f"Restart Requested"))
                self.AppRestartThread.daemon = True
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "webapp"
            ise.exception_message = str(f"Failed to check for requested restart: {e}")
            ise.process = "WebApp: Check for requested restarts"
            ise.severity = "2"
            
            self._supervisor.logInternalServerError(ise)

    # -------------------------------------------------------------------------| Testing |----------------------------------------------------------------------------------------------------------------------------------- #    
    
    def sendTestPacket(self, type="server"):
        format.message(f"Sending {type} packet")
        match type.lower():
            case "server":
                self.RestartRequested = True
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"WARNING: A critical error has occured! Background service will restart at the end of this game.", 'type': "createWarning"})
                
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': "Test Packet", 'type': "server"})
                format.message(f"Response: {response.text}")
            case "start":
                self.gameStarted()
            case "end":
                self.gameEnded()
            case "gunscore":
                for i in range(120, 110, -2):
                    self.timingPacket([0, 0, 0, i])
                    self.finalScorePacket([0, 1, 0, random.randint(1, 200), 0, 0, 0, random.randint(1, 100)])
                    self.finalScorePacket([0, 3, 0, random.randint(1, 200), 0, 0, 0, random.randint(1, 100)])
                    self.finalScorePacket([0, 7, 0, random.randint(1, 200), 0, 0, 0, random.randint(1, 100)])
                    time.sleep(2)
        
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