import string
from flask import Flask, render_template, request, jsonify, redirect, g, session, url_for, Blueprint
from flask_socketio import SocketIO, emit
import os, signal, ctypes, datetime, socket, requests, psutil, webbrowser, asyncio, pyautogui, random, logging, json, threading, time, sys
from scapy.all import sniff, IP
from dotenv import dotenv_values
from datetime import timedelta
from werkzeug.exceptions import HTTPException
import subprocess

try:
    import winrt.windows.media.control as wmc
except Exception as e:
    print("Failed to import winrt.windows.media.control ", e)
    input("Press any key to exit...")

from API.format import Format
from API.BPM import MediaBPMFetcher
from API.DMXControl import dmx
from API.DB import *
from API.OBS import OBS
from API.Supervisor import Supervisor
from API.Emails import EmailsAPIController
from API.Feedback.feedback import RequestAndFeedbackAPIController
from API.Music.MusicAPIController import MusicAPIController
from data.models import *
from API.createApp import createApp

# MainBlueprint = Blueprint("Main", __name__)

f = Format("Web App")

class WebApp:
    def __init__(self):
        global secrets
        
        self._dir = os.path.dirname(os.path.realpath(__file__))
        
        secrets = dotenv_values(self._dir.replace(r"\backend", "") + r"\.env")
        
        f.message(f.colourText("Loading Environment Variables", "Cyan"), type="info")
        
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
        self.VersionNumber = "1.3"
        # END LOAD
        
        # INIT ALL OTHER VARIABLES
        self.OBSConnected = False
        self.devMode = self.ENVIRONMENT == "Development"
        self._localIp = ""
        self.RestartRequested = False
        self.gameStatus = "stopped" # Either running or stopped
        self.endOfDay = False
        self.currentGameId = 0
        self.GunScores = {}
        self.TeamScores = {}    
        self.DevToolsOTP = ""
        self.DevToolsRefreshCount = 5
        # END INIT
           
        # INIT DEPENDANCIES
        self._supervisor : Supervisor = None
        self._obs : OBS = None
        self._dmx : dmx = None
        self._context : context = None
        self.app : Flask = None
        self._eAPI : EmailsAPIController = None
        self._fAPI : RequestAndFeedbackAPIController = None
        self._mAPI : MusicAPIController = None
        # END INIT
                
        pyautogui.FAILSAFE = False

    # -----------------| Starting Tasks |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
    
    def startFlask(self):
        f.message(f.colourText("Attempting to start Flask Server", "green"))
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((self._localIp, 8080)) == 0:
                    f.message(f"Port 8080 is already in use on {self._localIp}", type="error")
                    raise RuntimeError("Port in use. Exiting application.")
                
                log = logging.getLogger('werkzeug')
                log.disabled = True
                cli = sys.modules['flask.cli']
                cli.show_server_banner = lambda *x: None

                self.socketio.run(self.app, host=self._localIp, port=8080, debug=self.devMode, use_reloader=False)
                
                if self.devMode == True:
                    self.app.debug = True
                
        except Exception as e:
            f.message(f"Fatal! {e}")
            raise
        
        f.message(f"Web App hosted on IP" + f.colourText(f"http://{self._localIp}:8080", "blue"), type="success")
            
    def _getLocalIp(self) -> str:
        try:
            # Create a dummy socket connection to find the local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self._localIp = s.getsockname()[0]
            s.close()
        except Exception as e:
            f.message(f"Error finding local IP: {e}")
        
    def start(self):
        f.message("Running on Commit: " + f.colourText(f"{self.getCurrentCommit()}", "green"), type="info")
        f.message(f"Starting Web App at {str(datetime.now())}", type="warning")
        
        ctypes.windll.kernel32.SetConsoleTitleW("Zone Laser Scoreboard")
        
        self.app, self.socketio, self._context = createApp() 

        self._getLocalIp()
        self.setupRoutes()
        
        self._supervisor = Supervisor()
        
        while self._supervisor == None:
            time.sleep(1)
        
        self._fetcher = MediaBPMFetcher()
        self._fAPI = RequestAndFeedbackAPIController(self._context.db)
        self._mAPI = MusicAPIController(self._supervisor, self._context.db, secrets, self.app, self._dir)
        
        self.flaskThread = threading.Thread(target=self.startFlask, daemon=True).start()
        self.mediaStatusCheckerThread = threading.Thread(target=self.mediaStatusChecker, daemon=True).start()
        self.obsThread = threading.Thread(target=self.connectToOBS, daemon=True).start()
        self.dmxThread = threading.Thread(target=self.setUpDMX, daemon=True).start()
        self.sniffingThread = threading.Thread(target=self.startSniffing, daemon=True).start()

        self._eAPI = EmailsAPIController.EmailsAPIController(secrets["GmailAppPassword"] if secrets["GmailAppPassword"] is not None else "", secrets["GmailSenderEmail"] if secrets["GmailSenderEmail"] is not None else "", secrets["GmailSenderDisplayName"] if secrets["GmailSenderDisplayName"] is not None else "")
        
        self._supervisor.setDependencies(obs=self._obs, dmx=self._dmx, db=self._context, webApp=self)
        
        f.sendEmail(f"Web App started at {str(datetime.now())}", "APP STARTED")
        f.message(f"Serving Web App at IP: http://{str(self._localIp)}:8080", type="warning")
        
    def getCurrentCommit(self) -> str:
        try:
            commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
            return commit
        except Exception as e:
            f.message(f"Error getting current commit: {e}", type="error")
            return ""
    
    def setUpDMX(self):
        #Requires USB to DMX with driver version of "libusb-win32"
        
        f.message(f.colourText("Setting up DMX Connection", "green"), type="info")
        
        try:
            self._dmx = dmx(self._context, self._supervisor, self.socketio, self.app, self.devMode)
            
        except Exception as e:
            f.message(f"Error starting DMX Connection: {e}", type="error")
            return
        
        if self._dmx.isConnected() == True:
            try:
                f.message("Registering Red Bulk-Head Lights", type="info")
                
                self.BulkHeadLights = self._dmx.registerDimmerFixture("Bulk-Head Lights")
                
            except Exception as e:
                f.message(f"Error registering Red Bulk-Head Lights: {e}", type="error")
                
            try:
                f.message("Registering ColorWash 250 AT", type="info")
                
                patchedFixture = self._dmx.registerFixtureUsingType("ColorWash 250 AT", "colorwash250at", 43)
                self._dmx.addFixtureToGroup(patchedFixture, "Moving Heads")
                
            except Exception as e:
                f.message(f"Error registering ColorWash 250 AT: {e}", type="error")
                
            try:
                f.message("Registering ColorSpot 250 AT ", type="info")
                
                patchedFixture = self._dmx.registerFixtureUsingType("ColorSpot 250 AT", "colorspot250at", 10)
                self._dmx.addFixtureToGroup(patchedFixture, "Moving Heads")
                
            except Exception as e:
                f.message(f"Error registering ColorSpot 250 AT: {e}", type="error")
        
            self.DMXConnected = True
            
            self.socketio.emit("dmxStatus", {"message": "CONNECTED"})
            
            f.message("DMX Connection set up successfully", type="success")
        
    def connectToOBS(self):
        try:
            self._obs = OBS(self.OBSSERVERIP, self.OBSSERVERPORT, self.OBSSERVERPASSWORD, self._dir, self._supervisor, secrets)
        except Exception as e:
            f.message(f"Error setting up OBS connection: {e}", type="error")

    def setupRoutes(self):     
        f.message(f.colourText("Setting up routes..." ,"Blue"))
        
        # @self.app.errorhandler(404)
        # def not_found():
        #     return render_template("error.html", message="Page not found")
        
        @self.app.context_processor
        def inject_global_vars():
            return dict(
                SysName=self.SysName,
                VersionNo=self.VersionNumber,
                PageTitle=getattr(g, 'PageTitle', ""),
                Environment=secrets["Environment"]
        )

        @self.app.errorhandler(HTTPException)
        def handle_exception(e):
            """Return JSON instead of HTML for HTTP errors."""
            if hasattr(e, "original_exception") and e.original_exception:
                # f.message(f"HTTP Exception: {e.original_exception}", type="error")
                # Try to serialize the original exception, fallback to str if not serializable
                try:
                    return jsonify({"error": str(e.original_exception)}), 500
                except Exception:
                    return jsonify({"error": "Unserializable exception"}), 500
            else:
                # f.message(f"HTTP Exception: {e}", type="error")
                
                response = e.get_response()
                response.data = json.dumps({
                    "code": e.code,
                    "name": e.name,
                    "description": e.description,
                })
                response.content_type = "application/json"
                return response, e.code if e.code != None else 500 
            
        @self.app.route('/')
        def index():
            try:    
                self.DevToolsOTP = ""
                            
                g.PageTitle = "Home"
                
                return render_template('index.html')
        
            except Exception as e:
                f.message(f"Error loading index.html: {e}", type="error")
                return render_template("error.html", message=f"Error loading index: {e}\nThis is a bug, a report has been automatically submitted.")
            
        @self.app.route("/api/getReleaseNotes")
        def getReleaseNotes():
            try:
                url = "https://api.github.com/repos/benjamano/Zone-Laser-Scoreboard/commits"
                headers = {"Authorization": f"token {secrets["GithubAuthToken"]}"}
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    commits = response.json()
                    return commits[:100] 
                
                except Exception as e:
                    return {"error": str(e)}
                
            except Exception as e:
                f.message(f"Error getting release notes: {e}", type="error")
                return jsonify({"error": str(e)}), 500
            
        @self.app.route("/api/getCurrentCommit")
        def api_getCurrentCommit():
            try:
                return self.getCurrentCommit()
            except Exception as e:
                f.message(f"Error getting current commit: {e}", type="error")
                return jsonify({"error": str(e)}), 500
    
        @self.app.route("/schedule")
        def scehdule():
            self.DevToolsOTP = ""
            
            g.PageTitle = "Schedule"
            
            return render_template("schedule.html")
        
        @self.app.route("/settings")
        def settings():
            self.DevToolsOTP = ""
            
            g.PageTitle = "Settings"
            
            return render_template("settings/settings.html")
        
        @self.app.route("/settings/devtools/")
        def settings_devtools():
            otp = request.args.get("code")
            
            if ((otp == None or otp == "" or otp != self.DevToolsOTP or self.DevToolsRefreshCount <= 0) and self.devMode == False):
                self.DevToolsOTP = ""
                return render_template("error.html", message="Access Denied")
            
            self.DevToolsRefreshCount -= 1
            
            g.PageTitle = "Dev Tools"
            
            variables = {}
            
            for k,v in vars(self).items():
                if not k.startswith('__'):
                    variables[k] = v
                    
                    if hasattr(v, '__dict__'):
                        try:
                            obj_vars = vars(v)
                            for ok, ov in obj_vars.items():
                                if not ok.startswith('__'):
                                    variables[f"{k}.{ok}"] = ov
                        except:
                            pass
            
            return render_template("settings/devtools.html", variables=variables)
        
        @self.app.route("/editScene")
        def editScene():
            #Accessed by /EditScene?Id=[sceneId]
            self.DevToolsOTP = ""
            
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
                f.message(f"Error fetching scene with Id '{sceneId}' for Advanced Scene view: {e}", type="error")
                return render_template("error.html", message=f"Error fetching scene: {e}<br>This is a bug, a report has been automatically submitted.")
        
        @self.app.route("/text")
        def neonText():
            self.DevToolsOTP = ""
            
            return render_template("neonFlicker.html")
        
        @self.app.route("/status")
        def status():
            self.DevToolsOTP = ""
            
            g.PageTitle = "Status"
            
            return render_template("status.html")
        
        @self.app.route("/experimental")
        def experimental():
            self.DevToolsOTP = ""
            
            return redirect("/")
            
            return render_template("experimental/newIndex.html", SysName=self.SysName, PageTitle="Experiments")
        
        @self.app.route("/feedback")
        def feedback():
            self.DevToolsOTP = ""
            
            g.PageTitle = "Leave Feedback"
            
            return render_template("feedback/leaveFeedback.html")
        
        @self.app.route("/api/feedback/getFeatureRequests", methods=["GET"])
        def feedback_getFeatureRequests():
            try:
                featureRequests = self._fAPI.getFeatureRequests()
                
                featureRequestList : list[dict] = []
                
                for featureRequest in featureRequests:
                    featureRequestList.append(featureRequest.to_dict())
                    
                return jsonify(featureRequestList)
            
            except Exception as e:
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Error getting feature requests: {e}, Traceback: {e.__traceback__}")
                ise.process = "API: Get Feature Requests"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
                
                return jsonify({"error": f"Error getting feature requests: {e}"}), 500
            
        @self.app.route("/api/feedback/getBugReports", methods=["GET"])#
        def feedback_getBugReports():
            try:
                bugReports = self._fAPI.getBugReports()
                
                bugReportList : list[dict] = []
                
                for bugReport in bugReports:
                    bugReportList.append(bugReport.to_dict())
                    
                return jsonify(bugReportList)
            
            except Exception as e:
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Error getting bug reports: {e}, Traceback: {e.__traceback__}")
                ise.process = "API: Get Bug Reports"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
                
                return jsonify({"error": f"Error getting bug reports: {e}"}), 500
            
        @self.app.route("/api/feedback/getSongRequests", methods=["GET"])
        def feedback_getSongRequests():
            try:
                songRequests = self._fAPI.getSongRequests()
                
                songRequestList : list[dict] = []
                
                for songRequest in songRequests:
                    songRequestList.append(songRequest.to_dict())
                    
                return jsonify(songRequestList)
            
            except Exception as e:
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Error getting song requests: {e}, Traceback: {e.__traceback__}")
                ise.process = "API: Get song requests"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
                
                return jsonify({"error": f"Error getting song requests: {e}"}), 500
        
        @self.app.route("/api/feedback/submitForm", methods=["POST"])
        def feedback_submitForm():
            try:
                data = request.get_json()

                requestId = ""

                type = data.get("Type", "")
                submitter = data.get("SubmitterName", "")
                
                if type == "NewFeature":
                    featureDescription = data.get("FeatureDescription", "")
                    featureUseCase = data.get("FeatureUseCase", "")
                    featureExpected = data.get("FeatureExpected", "")
                    featureDetails = data.get("FeatureDetails", "")
                    
                    requestId = self._fAPI.processNewFeatureRequest(featureDescription, featureUseCase, featureExpected, featureDetails, submitter)
                elif type == "Bug":
                    bugDescription = data.get("BugDescription", "")
                    whenItOccurs = data.get("WhenItOccurs", "")
                    expectedBehavior = data.get("ExpectedBehavior", "")
                    stepsToReproduce = data.get("StepsToReproduce", "")
                    
                    requestId = self._fAPI.processBugReport(bugDescription, whenItOccurs, expectedBehavior, stepsToReproduce, submitter)
                elif type == "SongAddition":
                    songName = data.get("SongName", "")
                    naughtyWords = data.get("NaughtyWords", "")
                    
                    requestId = self._fAPI.processSongRequest(songName, naughtyWords, submitter)
                else:
                    return {"error": "Unknown Type"}, 400
                
                f.messagesendEmail(f"{type} Feedback submitted by {submitter} with request ID {requestId}", f"{type} Feedback Submitted")

                return {"id": requestId}, 200
            
            except Exception as e:
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Error submitting feedback: {e}, Traceback: {e.__traceback__}")
                ise.process = "API: Submit Feedback"
                ise.severity = "2"
                
                self._supervisor.logInternalServerError(ise)
                
                return jsonify({"error": f"Error submitting feedback: {e}"}), 500
        
        @self.app.route("/statistics")
        def statistics():
            self.DevToolsOTP = ""
            
            g.PageTitle = "Statistics"
            
            return render_template("statistics.html")

        @self.app.route("/managerTools")
        def managerTools():
            self.DevToolsOTP = ""
            
            g.PageTitle = "Manager Tools"
            
            return render_template("ManagerTools/managerTools.html")
        
        def managerTools_VerifyAuthCookie(cookie: str) -> bool:
            try:
                if cookie is None or cookie == "":
                    return False
                
                cookieDate = datetime.fromisoformat(cookie)
                if cookieDate > datetime.now():
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
                newCookie : datetime = datetime.now() + timedelta(days=7)
                
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
                    self._eAPI.sendEmail(recipient, subject, body)
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
            
        @self.app.route("/api/settings/devtools/requestAccess", methods=["POST"])
        def settings_devtools_requestAccess():
            try:
                password = request.form.get("password")
                
                if (str(password) != str(secrets["DevToolsPassword"]) and self.devMode == False):
                    return jsonify({"error": "Invalid password"}), 401
                
                self.DevToolsOTP = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                self.DevToolsRefreshCount = 5
                return jsonify(self.DevToolsOTP)
                    
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/ping")
        def ping():   
            #f.message("|--- I'm still alive! ---|")
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
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503
            
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
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                fixtures = self._dmx.getFixtures()
                
                channelValues = []

                for fixture in fixtures:
                    fixtureId = fixture["id"]
                    fixtureName = fixture["name"]
                    fixtureType = fixture["fixture"]["id"]
                    fixtureChannels = (self._dmx.getFixtureTypeChannels(fixtureType))

                    channels = {}

                    for channel in fixtureChannels:
                        DMXFixture = self._dmx.getFixtureById(fixtureId)
                        
                        if (DMXFixture == None):
                            channels[channel.name] = {
                                    "DMXValue": -1,
                                    "channel": channel.name
                            }
                            continue
                        
                        channelValue = DMXFixture.get_channel_value((str(channel.name)).lower())
                        
                        if DMXFixture.json_data["type"] == "Generic.Dimmer":
                            channels = {"DMXValue": DMXFixture.channels[1]["value"][0], "channel": DMXFixture.channels[1]["name"]}
                        else:
                            try:
                                fixtureChannelTemp = 0

                                for keyId, dmxChannel in DMXFixture.channels.items():
                                    if str(channel.name).lower() == str(dmxChannel["name"]).lower():
                                        fixtureChannelTemp = dmxChannel["value"][0]

                                channels[channel.name] = {
                                    "DMXValue": fixtureChannelTemp,
                                    "channel": channel.name
                                }
                            except Exception as e:
                                f.message(f"Error getting fixture channel: {e}, {dmxChannel["name"]}, {channelValue}", type="error")

                    channelValues.append({
                        "name": fixtureName,
                        "id": fixtureId,
                        "attributes": channels
                    })
                    
                return jsonify(channelValues), 200
            
            except Exception as e:
                ise : InternalServerError = InternalServerError()
                
                ise.service = "api"
                ise.exception_message = str(f"Error getting DMX channel values: {e}")
                ise.process = "API: Get DMX Values"
                ise.severity = "3"
                
                self._supervisor.logInternalServerError(ise)
                
                return jsonify({"error": f"Error getting DMX Channel Values: {e}"}), 500
            
        @self.app.route("/api/dmx/scenes", methods=["GET"])
        def getDMXScenes():
            if self._dmx == None or self._dmx.isConnected() == False:
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
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503

            sceneId = request.args.get("sceneId") 

            if not sceneId:
                return jsonify({"error": "Scene Id is required"}), 400

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
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503

            sceneId = request.form.get("sceneId") 

            if not sceneId:
                return jsonify({"error": "Scene id is required"}), 500

            try:
                self._dmx.startScene(sceneId)

                return jsonify(self._dmx.getDMXSceneById(sceneId).to_dict()), 200
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
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503

            sceneId = request.form.get("sceneId") 

            if not sceneId:
                return jsonify({"error": "Scene id is required"}), 500

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
                return jsonify({"error": f"Failed to end scene: {e}"}), 500
        
        @self.app.route("/api/dmx/createScene", methods=["POST"])
        def createDMXScene():
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                newDMXScene = self._context.DMXScene(
                    name="New Scene",
                    createDate=datetime.now(),
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
            if self._dmx == None or self._dmx.isConnected() == False:
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
            if self._dmx == None or self._dmx.isConnected() == False:
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
            if self._dmx == None or self._dmx.isConnected() == False:
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

        @self.app.route("/api/dmx/createSceneEvent", methods=["POST"])
        def createSceneEvent():
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503
            
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
            
        @self.app.route("/api/dmx/updateSceneEventDuration", methods=["POST"])
        def updateSceneEventDuration():
            if self._dmx is None or not self._dmx.isConnected():
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                sceneEventId = request.form.get("sceneEventId", type=int)
                duration = request.form.get("duration", type=int)

                if sceneEventId is None:
                    return jsonify({"error": "sceneEventId is required"}), 400

                if duration is None or duration < 0:
                    return jsonify({"error": "Invalid duration"}), 400

                with self.app.app_context():
                    sceneEvent = self._context.DMXSceneEvent.query.filter_by(id=sceneEventId).first()
                    if not sceneEvent:
                        return jsonify({"error": "Scene event not found"}), 404

                    sceneEvent.duration = duration

                    scene = self._context.DMXScene.query.filter_by(id=sceneEvent.sceneID).first()
                    if scene:
                        totalDuration = sum(event.duration for event in self._context.DMXSceneEvent.query.filter_by(sceneID=scene.id).all())
                        scene.duration = totalDuration

                    self._context.db.session.commit()

                    return jsonify(sceneEvent.to_dict()), 200

            except Exception as e:
                ise = InternalServerError()
                ise.service = "api"
                ise.exception_message = f"Failed to update scene event duration: {e}"
                ise.process = "API: Update Scene Event Duration"
                ise.severity = "3"

                self._supervisor.logInternalServerError(ise)
                return jsonify({"error": ise.exception_message}), 500

        @self.app.route("/api/dmx/toggleSceneLoop", methods=["POST"])
        def toggleSceneLoop():
            if self._dmx is None or not self._dmx.isConnected():
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                sceneId = request.form.get("sceneId")
                
                if not sceneId:
                    return jsonify({"error": "sceneId is required"}), 500
                
                with self.app.app_context():
                    scene : DMXScene = self._context.DMXScene.query.filter_by(id=sceneId).first()
                    if not scene:
                        return jsonify({"error": "Scene not found"}), 404
                    
                    scene.repeat = not scene.repeat
                    
                    self._context.db.session.commit()
                    
                    return jsonify(scene.repeat), 200

            except Exception as e:
                ise = InternalServerError()
                ise.service = "api"
                ise.exception_message = f"Failed to update scene repeat mode: {e}"
                ise.process = "API: Update Scene Repeat Mode"
                ise.severity = "3"

                self._supervisor.logInternalServerError(ise)
                return jsonify({"error": ise.exception_message}), 500
            
        @self.app.route("/api/dmx/toggleSceneFlash", methods=["POST"])
        def toggleSceneFlash():
            if self._dmx is None or not self._dmx.isConnected():
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                sceneId = request.form.get("sceneId")
                
                if not sceneId:
                    return jsonify({"error": "sceneId is required"}), 500
                
                with self.app.app_context():
                    scene : DMXScene = self._context.DMXScene.query.filter_by(id=sceneId).first()
                    if not scene:
                        return jsonify({"error": "Scene not found"}), 404
                    
                    scene.flash = not scene.flash
                    
                    self._context.db.session.commit()
                    
                    return jsonify(scene.flash), 200

            except Exception as e:
                ise = InternalServerError()
                ise.service = "api"
                ise.exception_message = f"Failed to update scene event duration: {e}"
                ise.process = "API: Update Scene Flash Mode"
                ise.severity = "3"

                self._supervisor.logInternalServerError(ise)
                return jsonify({"error": ise.exception_message}), 500

        @self.app.route("/api/dmx/setSceneSongTrigger", methods=["POST"])
        def setSceneSongTrigger():
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503
            
            try:
            
                sceneId = request.form.get("sceneId")
                songName = request.form.get("songName")

                if not sceneId or not songName:
                    return jsonify({"error": "sceneId and songName are required"}), 400
                
                with self.app.app_context():
                    scene : DMXScene = self._context.DMXScene.query.filter_by(id=sceneId).first()
                    if not scene:
                        return jsonify({"error": "Scene not found"}), 404
                    
                    scene.song_keybind = songName
                    
                    self._context.db.session.commit()

                return jsonify({"success": "Scene song trigger set"})
            
            except Exception as e:
                ise = InternalServerError()
                ise.service = "api"
                ise.exception_message = f"Failed to update scene song trigger: {e}"
                ise.process = "API: Update Scene Song Trigger"
                ise.severity = "3"

                self._supervisor.logInternalServerError(ise)
                return jsonify({"error": ise.exception_message}), 500

        @self.app.route("/api/dmx/setSceneKeybind", methods=["POST"])
        def setSceneKeybind():
            if self._dmx is None or not self._dmx.isConnected():
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                sceneId = request.form.get("sceneId")
                keybind = request.form.get("keybind")
                
                if not sceneId or not keybind:
                    return jsonify({"error": "sceneId and keybind are required"}), 400
                
                with self.app.app_context():
                    scene : DMXScene = self._context.DMXScene.query.filter_by(id=sceneId).first()
                    if not scene:
                        return jsonify({"error": "Scene not found"}), 404
                    
                    scene.keyboard_keybind = keybind
                    
                    self._context.db.session.commit()
                
                return jsonify({"success": "Scene keybind set"}), 200

            except Exception as e:
                ise = InternalServerError()
                ise.service = "api"
                ise.exception_message = f"Failed to update scene key bind: {e}"
                ise.process = "API: Update Scene Keybind"
                ise.severity = "3"

                self._supervisor.logInternalServerError(ise)
                return jsonify({"error": ise.exception_message}), 500
            
        @self.app.route("/api/dmx/getScenesWithKeyboardTriggers", methods=["GET"])
        def getScenesWithKeyboardTriggers():
            if self._dmx is None or not self._dmx.isConnected():
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                with self.app.app_context():
                    Scenes : list[DMXScene] = self._context.DMXScene.query.filter(self._context.DMXScene.keyboard_keybind.isnot(None).isnot("")).all()

                    scenesWithTriggers = [scene.to_dict() for scene in Scenes if scene.keyboard_keybind]
                    
                return jsonify(scenesWithTriggers), 200
            except Exception as e:
                ise = InternalServerError()
                ise.service = "api"
                ise.exception_message = f"Failed to get scenes with keyboard triggers: {e}"
                ise.process = "API: Get Scenes With Keyboard Triggers"
                ise.severity = "3"

                self._supervisor.logInternalServerError(ise)
                return jsonify({"error": ise.exception_message}), 500

        @self.app.route('/end')
        def terminateServer():
            logging.shutdown()
            os.kill(os.getpid(), signal.SIGTERM)
            
        @self.socketio.on('connect')
        def handleConnect():            
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
            
        @self.socketio.on('UpdateDMXValue')
        def UpdateDMXValue(json):
            if self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503
            
            fixture = json["fixtureName"]
            channelName = json["attributeName"]
            value = json["value"]
            
            try:
                self._dmx.setFixtureChannel(fixture, channelName, value)
                
                return jsonify({"newValue": value}), 200
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
                    f.message("Playing briefing")
                    
                    self._obs.switchScene("Video")
                    
                    return jsonify({"status": "success"}), 200
                except Exception as e:
                    ise : InternalServerError = InternalServerError()
                
                    ise.service = "api"
                    ise.exception_message = str(f"Failed to start OBS Briefing: {e}")
                    ise.process = "API: Start OBS Briefing"
                    ise.severity = "1"
                    
                    self._supervisor.logInternalServerError(ise)

            else:
                #f.message("OBS not connected, cannot play breifing!", type="warning")
                return jsonify({"status": "error", "message": "OBS not connected, cannot play briefing!"}), 500
            
        @self.socketio.on("setVolume")
        def setVolume(msg):
            self._mAPI.setVolume(msg.get("volume", 0))
    
        @self.app.route('/sendMessage', methods=['POST'])
        def sendMessage():
            try:
                data = request.get_json(silent=True) or {}
                message = data.get("message") or request.form.get("message")
                type_ = data.get("type") or request.form.get("type")

                if type_:
                    if isinstance(message, dict):
                        self.socketio.emit(f"{type_}", {"message": message})
                    else:
                        self.socketio.emit(f"{type_}", {"message": message})
                                    
                return jsonify({"status": "success"}), 200
            
            except Exception as e:
                ise : InternalServerError = InternalServerError()
                
                ise.service = "socket"
                ise.exception_message = str(f"Failed To Send Socket Message: {e}")
                ise.process = "Socket: Send Message"
                ise.severity = "1"
                
                self._supervisor.logInternalServerError(ise)
    
    # -----------------| Background Tasks |-------------------------------------------------------------------------------------------------------------------------------------------------------- # 
            
    def startSniffing(self):
        f.message("Starting packet sniffer...")
        try:
            sniff(prn=self.packetCallback, store=False, iface=self.ETHERNET_INTERFACE if self.devMode != "true" else None)
        except Exception as e:
            f.message(f"Error while sniffing: {e}", type="error")
            return
            
    # async def getPlayingStatus(self):
    #     try:
    #         sessions = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
    #     except Exception as e:
    #         f.message(f"Error getting session manager: {e}", type="error")
    #         raise
        
    #     try:
    #         current_session = sessions.get_current_session()
    #     except Exception as e:
    #         f.message(f"Error getting current session: {e}", type="error")
    #         raise
        
    #     if not current_session:
    #         return "paused", 0, 0

    #     try:
    #         playback_info = current_session.get_playback_info()
    #     except Exception as e:
    #         f.message(f"Error getting playback info: {e}", type="error")
    #         raise
        
    #     try:
    #         timeline_properties = current_session.get_timeline_properties()
    #     except Exception as e:
    #         f.message(f"Error getting timeline properties: {e}", type="error")
    #         raise

    #     try:
    #         status = "playing" if playback_info.playback_status == wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING else "paused"
    #     except Exception as e:
    #         f.message(f"Error getting playback status: {e}", type="error")
    #         raise

    #     try:
    #         currentPosition = timeline_properties.position.total_seconds()
    #         totalDuration = timeline_properties.end_time.total_seconds()
    #     except Exception as e:
    #         f.message(f"Error getting timeline properties: {e}", type="error")
    #         raise

    #     return status, currentPosition, totalDuration
    
    def handleMusic(self, mode):
        match mode.lower():
            case "toggle":
                self._mAPI.togglePauseMusic()
            case "next":
                self._mAPI.next()
            case "previous":
                self._mAPI.previous()
            case "restart":
                self._mAPI.restart()
            case "pause":
                self._mAPI.pause()
            case "play":
                self._mAPI.play()
        return True
            
    def restartApp(self, reason="unknown"):
        if self.devMode == True:
            f.message("Development mode, skipping restart", type="warning")
            return
        
        f.message(f"Restarting App due to {reason}", type="error")
        
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': "Restarting Web App Now!", 'type': "createWarning"})
        
        # Make sure all the end of game processing completes
        time.sleep(5)
        
        f.message("Restarting App", type="warning")

        os._exit(1)
            
    # def handleBPM(self, song, album, bpm=0):
    #     #f.message(f"Get Here with {song}, {bpm}, {album}")
    #     try:
    #         if (self.rateLimit == True and ((random.randint(1, 50)) == 10)) or self.rateLimit == False:
                
    #             if song == None or bpm == None or bpm == "Song not found":
    #                 match song:
    #                     #This makes me want to die
    #                     #Implemented because these are local songs used specifically in the Arena, and aren't on spotify.
    #                     case "Main Theme":
    #                         bpm = "69"
    #                     case "Loon Skirmish":
    #                         bpm = "80"
    #                     case "Crainy Yum (Medium)":
    #                         bpm = "80"
    #                     case "Crainy Yum":
    #                         bpm = "80"
    #                     case "Thing Of It Is":
    #                         bpm = "87"
    #                     case "Bug Zap":
    #                         bpm = "87"
    #                     case "Bug Zap (Medium)":
    #                         bpm = "87"
    #                     case "Only Partially Blown Up (Medium)":
    #                         bpm = "87"
    #                     case "Only Partially Blown Up":
    #                         bpm = "87"
    #                     case "Baron von Bats":
    #                         bpm = "87"
    #                     case "Treasure Yeti":
    #                         bpm = "86"
    #                     case "Normal Wave (A) (Medium)":
    #                         bpm = "86"
    #                     case "Normal Wave A":
    #                         bpm = "86"
    #                     case "Normal Wave B":
    #                         bpm = "87"
    #                     case "Normal Wave (C) (High)":
    #                         bpm = "87"
    #                     case "Special Wave A":
    #                         bpm = "87"
    #                     case "Special Wave B":
    #                         bpm = "101"
    #                     case "Challenge Wave B":
    #                         bpm = "101"
    #                     case "Challenge Wave C":
    #                         bpm = "101"
    #                     case "Boss Wave (A)":
    #                         bpm = "93"
    #                     case "Boss Wave (B)":
    #                         bpm = "98"
    #                     case "The Gnomes Cometh (B)":
    #                         bpm = "90"
    #                     case "The Gnomes Cometh (C)":
    #                         bpm = "86"
    #                     case "Gnome King":
    #                         bpm = "95"
    #                     case "D Boss Is Here":
    #                         bpm = "90"
    #                     case "Excessively Bossy":
    #                         bpm = "93"
    #                     case "One Bad Boss":
    #                         bpm = "84"
    #                     case "Zombie Horde":
    #                         bpm = "84"
    #                     case "Marching Madness":
    #                         bpm = "58"
    #                     case "March Of The Brain Munchers":
    #                         bpm = "58"
    #                     case "SUBURBINATION!!!":
    #                         bpm = "86"
    #                     case "Splattack!":
    #                         bpm = "88"
    #                     case "Science Blaster":
    #                         bpm = "92"
    #                     case "Undertow":
    #                         bpm = "88"
    #                     case _:
    #                         bpm = "60"
            
    #             #f.message(f"Current song: {song}, BPM: {bpm}")
            
    #             response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{str(round(int(bpm)))}", 'type': "songBPM"})
                
    #             self.rateLimit = False
                
    #     except Exception as e:
    #         if "max retries, reason: too many 429 error responses" in e.lower():
    #             self.rateLimit = True
    #             return
    #         else:
    #             f.message(f"Error occured while handling BPM: {e}", type="warning")
        
    # def findBPM(self):
    #     try:
    #         try:
    #             self._fetcher.fetch()
    #             song, bpm, album = self._fetcher.get_current_song_and_bpm()
                
    #             if type(bpm) == str:
    #                 bpm = 0
                
    #             self.handleBPM(song, album, bpm)
    #         except Exception as e:
    #             f.message(f"Error fetching BPM: {e}", type="error")
            
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
    #                 f.message(f"Error sending Spotify status: {e}", type="error")

    #     except Exception as e:
    #         f.message(f"Failed to find BPM: {e}", type="error")
   
    def runAsyncioInSta(self, coro):
        result_container = {}
        exc_container = {}

        def runner():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()

            try:
                result_container['result'] = loop.run_until_complete(coro)
            except Exception as e:
                exc_container['exception'] = e
            finally:
                loop.close()

        thread = threading.Thread(target=runner)
        thread.daemon = True
        thread.start()
        thread.join()

        if 'exception' in exc_container:
            raise exc_container['exception']

        return result_container['result']

    def sendSongDetails(self, song, album, bpm, duration, timeleft, isPlaying, currentVolume):
        self.socketio.emit('songAlbum', {'message': album})
        self.socketio.emit('songName', {'message': song})
        self.socketio.emit('musicVolume', {'message': currentVolume})
        self.socketio.emit('musicStatusV2', {'message': {"playbackStatus": isPlaying, "musicPosition": (duration-timeleft), "duration": duration}})
        queue = self._mAPI.getQueue()
        queue_dicts = [song.to_dict() for song in queue]
        self.socketio.emit('musicQueue', {'queue': queue_dicts})
   
    def mediaStatusChecker(self):
        f.message(f.colourText("Attempting to start Media status checker", "blue"))
        
        while True:
            time.sleep(1)
            
            try:
                songDetails : SongDetailsDTO = self._mAPI.currentSongDetails()
                
                self.sendSongDetails(songDetails.name, songDetails.album, 0, songDetails.duration, songDetails.timeleft, songDetails.isPlaying, songDetails.currentVolume)
            except Exception as e:
                f.message(f"Error fetching current song details: {e}", type="error")
            
            # try:
            #     song, album, bpm = self._fetcher.get_current_song_and_bpm()
                
            #     if (previousSong != song):
            #         previousSong = song
                    
            #         
                    
            #         self._dmx.checkForSongTriggers(song)
    
            #     # self.handleBPM(song)
            
            # except Exception as e:
            #     pass
            
            # try:
            #     temp_spotifyStatus, currentPosition, totalDuration = self.runAsyncioInSta(self.getPlayingStatus())
                
            #     if temp_spotifyStatus != self.spotifyStatus:
            #         self.spotifyStatus = temp_spotifyStatus
                    
            #     try:
            #         # response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{self.spotifyStatus}", 'type': "musicStatus"})
                    
            #         
                    
            #         # response = requests.post(
            #         #     f"http://{self._localIp}:8080/sendMessage",
            #         #     json={
            #         #         "message": {
            #         #             "playbackStatus": self.spotifyStatus,
            #         #             "musicPosition": currentPosition,
            #         #             "duration": totalDuration
            #         #         },
            #         #         "type": "musicStatusV2"
            #         #     }
            #         # )
            #     except Exception as e:
            #         f.message(f"Error sending music status message: {e}.", type="error")
                    
            #     # if currentPosition and totalDuration:
            #     #     try:
            #     #         response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{currentPosition}", 'type': "musicPosition"})
            #     #         response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{totalDuration}", 'type': "musicDuration"})
            #     #     except Exception as e:
            #     #         f.message(f"Error sending music status message, app probably hasn't started. {e}.", type="error")
                
            # except Exception as e:
            #     f.message(f"Error occured while checking media status: {e}", type="error")
                
            #     if str(e) != "an integer is required":
        
            #         f.message("Requesting app restart", type="warning")
                        
            #         # response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"WARNING: A critical error has occured! Background service will restart at the end of this game.", 'type': "createWarning"})
                    
            #         self.RestartRequested = True
                    
            #         with self.app.app_context():
            #             self._context.db.session.add(RestartRequest(
            #                 created_by_service_name = "WebApp - Media Status Checker",
            #                 reason = f"RESTART PC - RESTART PC - Failed to check for media status: {str(e)}",,
            #             ))
                    
            #             self._context.db.session.commit()
                    
            #         # Just makes sure to pause this process, so it doesn't keep logging the same error
            #         time.sleep(1800)
                    
            #     else:
            #         f.message("Error not fatal, don't care", type="warning")
                
            #         time.sleep(3)                 
        
    # -----------------| Packet Handling |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
        
    def packetCallback(self, packet):
        try:
            if packet.haslayer(IP) and (packet[IP].src == self.IP1 or packet[IP].src == self.IP2) and packet[IP].dst == "192.168.0.255":
                
                #f.message(f"Packet 1: {packet}")
                
                packet_data = bytes(packet['Raw']).hex()
                #f.message(f"Packet Data (hex): {packet_data}, {type(packet_data)}")
                
                decodedData = (self.hexToASCII(hexString=packet_data)).split(',')
                #f.message(f"Decoded Data: {decodedData}")
                
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
            f.message(f"Error handling packet: {e}, Packet: {packet}", type="error")
        
    def gameStatusPacket(self, packetData):
        # 4,@015,0 = start
        # 4,@014,0 = end
        
        f.message(f"Game Status Packet: {packetData}, Mode: {packetData[1]}")

        if packetData[1] == "@015":
            self.gameStarted()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Started @ {str(datetime.now())}", 'type': "start"})
            #f.message(f"Response: {response.text}")
        
        elif packetData[1] == "@014":
            self.gameEnded()
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"Game Ended @ {str(datetime.now())}", 'type': "end"})
            #f.message(f"Response: {response.text}")
            
        elif "@004" in packetData[1]:
            # This is a game mode / time change packet, e.g. 4,@004,0 = game mode changed to 0
            newTime = ""
            newSoundMode = ""
            newGameMode = ""
            
            values = str(packetData).split("@")
            for value in values:
                if "016" in value:
                    newTime = value.strip("016")
                elif "017" in value:
                    newSoundMode = value.strip("017")
                elif "00" in value:
                    newGameMode = value.strip("00")
            
            f.message(f"Game Mode Changed to {newGameMode} with time {newTime} and sound mode {newSoundMode}")
            
        response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{packetData[0]}", 'type': "gameMode"})
        
    def teamScorePacket(self, packetData):
        #0 = red, 2 = green
        #f.message(f"Team Score Packet: {packetData}")
        
        teamId = str(packetData[1])
        teamScore = str(packetData[2])
        
        if teamId == "0":
            teamId = "Red"
        else:
            teamId = "Green"

        try:
            self.TeamScores[teamId] = teamScore
        except Exception as e:
            f.message(f"Error updating Team Scores: {e}", type="error")

    def timingPacket(self, packetData):
        timeLeft = packetData[3]
        
        #f.message(f"Time Left: {timeLeft}")

        if int(timeLeft) <= 0:
            #f.message(f"Game Ended at {datetime.now()}", type="success") 
            self.gameEnded()
        else:
            self.gameStarted()
            self.endOfDay = False
            if self._obs != None:
                self._obs.switchScene("Laser Scores")
            response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"{timeLeft}", 'type': "timeRemaining"})
    
    def finalScorePacket(self, packetData):
        gunId = packetData[1]
        finalScore = packetData[3]
        accuracy = packetData[7]
        
        self.socketio.emit('gunScores', {'message': f"{gunId},{finalScore},{accuracy}"})

        gunName = ""
        
        try:
            with self.app.app_context():
                gunName : str = self._context.Gun.query.filter_by(id=gunId).first().name
        
        except Exception as e:
            f.message(f"Error getting gun name: {e}", type="error")
            
        if gunName == "":
            gunName = "id: "+gunId
            
        try:
            self.GunScores[gunId] = finalScore
        except Exception as e:
            f.message(f"Error updating Gun Scores: {e}", type="error")
            
        #f.message(f"Gun {gunName} has a score of {finalScore} and an accuracy of {accuracy}", type="success")

    def shotConfirmedPacket(self, packetData):
        # f.message(f"Shot Confirmed Packet: {packetData}")
        
        shooterGunId = packetData[1]
        shotGunId = packetData[2]
        pointForRedTeam = packetData[3]
        pointForGreenTeam = packetData[4]
        
        shotGunName = ""
        shooterGunName = ""
        
        try:
            with self.app.app_context():
                shotGunName : str = self._context.Gun.query.filter_by(id=shotGunId).first().name
                shooterGunName : str = self._context.Gun.query.filter_by(id=shooterGunId).first().name
        
        except Exception as e:
            f.message(f"Error getting gun names: {e}", type="error")
        
        f.message(f"{shotGunName} just shot {shooterGunName}")
        
        self.socketio.emit("shotConfirmed", {"ShotGun": shotGunId, "ShooterGun": shooterGunId})
        
        # if pointForRedTeam > 0:
        #     self.TeamScores["Red"] += pointForRedTeam
        # elif pointForGreenTeam > 0:
        #     self.TeamScores["Green"] += pointForGreenTeam
        
        # 2025-06-07 17:08:25 | Info : Shot Confirmed Packet: ['5', '6', '1', '0', '0', '0', '0', '0\x00']

        # 2025-06-07 17:08:25 | Info : Shot Confirmed Packet: ['5', '6', '1', '0', '0', '0', '0', '0\x00']

        # 2025-06-07 17:08:25 | Info : Shot Confirmed Packet: ['5', '10', '9', '0', '0', '0', '0', '0\x00']

        # 2025-06-07 17:08:25 | Info : Shot Confirmed Packet: ['5', '10', '9', '0', '0', '0', '0', '0\x00']

        # 2025-06-07 17:08:25 | Info : Shot Confirmed Packet: ['5', '13', '1', '2', '0', '0', '0', '0\x00']

        # 2025-06-07 17:08:25 | Info : Shot Confirmed Packet: ['5', '13', '1', '2', '0', '0', '0', '0\x00']
        
        pass
    
    # -----------------| Game Handling |-------------------------------------------------------------------------------------------------------------------------------------------------------- #            
    
    def gameStarted(self):
        if self.gameStatus == "running":
            return
        
        f.newline()
        
        try:
            self.socketio.emit('start', {'message': f"Game Started @ {str(datetime.now())}"})
        except Exception as e:
            pass
                    
        f.message(f"Game started at {datetime.now():%d/%m/%Y %H:%M:%S}", type="success")

        self.handleMusic(mode="play")

        self.gameStatus = "running"
        self.GunScores = {}
        self.TeamScores = {}
        self.endOfDay = False

        self.currentGameId = self._context.createNewGame()
        
        f.message(f"Created new game with Id {self.currentGameId}")
            
        if self._obs != None:
            self._obs.switchScene("Laser Scores")
        
    def gameEnded(self):
        if self.gameStatus == "stopped":
            return
        
        self.gameStatus = "stopped"
        
        self.handleMusic(mode="pause")
        
        try:
            self.socketio.emit('end', {'message': f"Game Ended @ {str(datetime.now())}"})
        except Exception as e:
            pass
        
        f.message(f"Game ended at {datetime.now():%d/%m/%Y %H:%M:%S}", type="success")
            
        try:
            if self.currentGameId != 0:
                winningPlayer = ""
                winningTeam = ""
                
                try:
                    winningPlayer = max(self.GunScores.items(), key=lambda x: x[1])[0]
                except Exception as e:
                    f.message(f"Error getting winning player: {e}", type="error")
                    
                try:
                    winningTeam = max(self.TeamScores.items(), key=lambda x: x[1])[0]
                except Exception as e:
                    f.message(f"Error getting winning team: {e}", type="error")
                    
                if winningPlayer != "" and winningTeam != "" and self._obs != None:
                    #self._obs.showWinners(str(winningPlayer), str(winningTeam))
                    pass
                
                self._context.updateGame(self.currentGameId, endTime=datetime.now(), winningPlayer=winningPlayer, winningTeam=winningTeam)
                
                #f.message(f"Set Current Game's End Time to {datetime.now()}, ID: {self.currentGameId}")
            
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
                        
                    else:
                        gamePlayer : GamePlayer = GamePlayer(gameId=self.currentGameId, gunId=gunId, score=score, accuracy=0)
                        self._context.addGamePlayer(gamePlayer)
                        
                    f.message(f"Adding gun id: {gunId}'s score: {score} into game id of {self.currentGameId}")
                    
                self._context.SaveChanges()
                    
                self.currentGameId = 0
                    
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "zone"
            ise.exception_message = str(f"Failed to update player scores in DB: {e}")
            ise.process = "Zone: Update Gun Scores in DB"
            ise.severity = "3"
            
            self._supervisor.logInternalServerError(ise)
            
        # try:
        #     self._supervisor.executePendingRestarts()
            
        # except Exception as e:
        #     ise : InternalServerError = InternalServerError()
                
        #     ise.service = "webapp"
        #     ise.exception_message = str(f"Failed to check for requested restart: {e}")
        #     ise.process = "WebApp: Check for requested restarts"
        #     ise.severity = "1"
            
        #     self._supervisor.logInternalServerError(ise)

    # -------------------------------------------------------------------------| Testing |----------------------------------------------------------------------------------------------------------------------------------- #    
    
    def sendTestPacket(self, type="server"):
        f.message(f"Sending {type} packet")
        match type.lower():
            case "server":
                with self.app.app_context():
                    self._context.db.session.add(RestartRequest(
                            created_by_service_name = "WebApp - Test Packet",
                            reason = f"Test packet generated by server at {str(datetime.now())}."
                    ))
                    
                    self._context.db.session.commit()
                
                self.RestartRequested = True
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': f"WARNING: A critical error has occured! Background service will restart at the end of this game.", 'type': "createWarning"})
                
                response = requests.post(f'http://{self._localIp}:8080/sendMessage', data={'message': "Test Packet", 'type': "server"})
                f.message(f"Response: {response.text}")
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
            case "play":
                self._mAPI.loadSong("05 Bug Zap")
                self._mAPI.play()
                            
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