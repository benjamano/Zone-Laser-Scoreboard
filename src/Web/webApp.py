import asyncio
import json
import logging
import random
import signal
import socket
import string
import subprocess
import sys
import json
import logging
import os
import random
import signal
import string
import sys
import threading
import time
from datetime import datetime, timedelta

import pyautogui
import requests
from flask import Flask, render_template, request, jsonify, redirect, g, session
from flask_socketio import SocketIO, emit
from scapy.all import sniff
from scapy.layers.inet import IP
from werkzeug.exceptions import HTTPException

from Web.API.BPM import MediaBPMFetcher
from Web.API.DB import *
from Web.API.DMXControl import dmx
from Web.API.Emails import EmailsAPIController
from Web.API.Feedback.feedback import RequestAndFeedbackAPIController
from Web.API.Initialisation.InitialisationAPIController import InitialisationAPIController
from Web.API.Music.MusicAPIController import MusicAPIController
from Utilities.format import Format
from Data.models import *
from Utilities.networkUtils import *
from VRS.VRS import *
from Utilities.Git import *
from Utilities.InternalServerErrors import logInternalServerError

# MainBlueprint = Blueprint("Main", __name__)

f = Format("Web App")

class WebApp:
    def __init__(self, app: Flask, socketio: SocketIO, context, dmx: dmx, mAPI: MusicAPIController,
                 eAPI: EmailsAPIController.EmailsAPIController,
                 fAPI: RequestAndFeedbackAPIController,
                 iAPI: InitialisationAPIController,
                 bpm_fetcher: MediaBPMFetcher,
                 secrets: dict,
                 VRSProjector: VRSProjector):
        
        self.app = app
        self.socketio = socketio
        self._context = context
        self._dmx = dmx
        self._mAPI = mAPI
        self._eAPI = eAPI
        self._fAPI = fAPI
        self._iAPI = iAPI
        self._fetcher = bpm_fetcher
        self.secrets = secrets
        self.__VRSProjector = VRSProjector

        # LOAD ENVIRONMENT VARIABLES
        self.ENVIRONMENT = secrets["ENVIRONMENT"]
        self.IP1 = secrets["IP1"]
        self.IP2 = secrets["IP2"]
        self.ETHERNET_INTERFACE = secrets["ETHERNETINTERFACE"]
        self.OBSSERVERIP = secrets["OBSSERVERIP"]
        self.OBSSERVERPORT = secrets["OBSSERVERPORT"]
        self.OBSSERVERPASSWORD = secrets["OBSSERVERPASSWORD"]
        # END LOAD

        # LOAD SYSTEM VARIABLES
        self.SysName = "TBS"
        self.VersionNumber = "1.5"
        # END LOAD

        # INIT ALL OTHER VARIABLES
        self.OBSConnected = False
        self.devMode = self.ENVIRONMENT == "Development"
        self.RestartRequested = False
        self.gameStatus = "stopped"  # Either running or stopped
        self.endOfDay = False
        self.currentGameId = 0
        self.GunScores = {}
        self.TeamScores = {}
        # END INIT

        pyautogui.FAILSAFE = False

    # -----------------| Starting Tasks |-------------------------------------------------------------------------------------------------------------------------------------------------------- #

    def startFlask(self, ready_event: threading.Event):
        f.message(f.colourText("Attempting to start Flask Server", "green"))

        log = logging.getLogger('werkzeug')
        log.disabled = True
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None

        ready_event.set()

        self.socketio.run(
            self.app,
            host=get_local_ip(),
            port=8080,
            debug=self.devMode,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )

    async def start(self):
        if is_app_already_running():
            raise RuntimeError("Port in use, app is probably already running. Exiting application.")
        
        f.message("Running on Commit: " + f.colourText(f"{getCurrentCommit()}", "green"), type="info")
        f.message(f"Starting Web App at {str(datetime.now())}", type="warning")

        f.message(f.colourText("Running Database Migrations", "green"), type="info")
        try:
            with self.app.app_context():
                from Utilities.getApp import runMigrations
                runMigrations()
        except Exception as e:
            f.message(f"Error running migrations: {e}", type="error")

        self.setupRoutes()

        flaskIsReady = threading.Event()
        self.flaskThread = threading.Thread(target=self.startFlask, args=(flaskIsReady,), daemon=True)
        self.flaskThread.start()
        flaskIsReady.wait()
        
        mediaCheckerIsReady = threading.Event()
        threading.Thread(target=self.mediaStatusChecker, args=(mediaCheckerIsReady,), daemon=True).start()
        mediaCheckerIsReady.wait()

        f.message(f"{f.colourText('Flask Web Server has Started!', 'green')}", type="success")
        f.message(f"Web App hosted on IP " + f.colourText(f"http://{get_local_ip()}:8080", "blue"), type="success")
        
        self.flaskThread.join()
        
    def setupRoutes(self):
        # @self.app.errorhandler(404)
        # def not_found():
        #     return render_template("error.html", message="Page not found")

        @self.app.context_processor
        def injectGlobalVariables():
            return dict(
                SysName=self.SysName,
                VersionNo=self.VersionNumber,
                PageDescription=getattr(g, 'PageDescription', ""),
                PageTitle=getattr(g, 'PageTitle', ""),
                Environment=self.secrets["ENVIRONMENT"],
                IsLoggedIn=checkLoginStatus()
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
                g.PageTitle = "Home"

                return render_template('index.html')

            except Exception as e:
                f.message(f"Error loading index.html: {e}", type="error")
                return render_template("error.html",
                    message=f"Error loading index: {e}\nThis is a bug, a report has been automatically submitted.")

        @self.app.route("/api/getReleaseNotes")
        def getReleaseNotes():
            try:
                url = "https://api.github.com/repos/benjamano/Zone-Laser-Scoreboard/commits"
                headers = {"Authorization": f"token {self.secrets['GITHUBAUTHTOKEN']}"}
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
                return getCurrentCommit()
            except Exception as e:
                f.message(f"Error getting current commit: {e}", type="error")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/schedule")
        def schedule():
            g.PageTitle = "Schedule"

            return render_template("schedule.html")

        @self.app.route("/settings")
        def settings():
            g.PageTitle = "Settings"

            return render_template("Settings/settings.html")

        @self.app.route("/devtools/")
        def devtools():
            g.PageTitle = "Dev Tools"

            variables = {}

            for k, v in vars(self).items():
                try:
                    if not k.startswith('__') and not "__" in k:
                        variables[k] = v

                        if hasattr(v, '__dict__'):
                            try:
                                obj_vars = vars(v)
                                for ok, ov in obj_vars.items():
                                    if not ok.startswith('__'):
                                        variables[f"{k}.{ok}"] = ov
                            except:
                                pass
                except:
                    pass

            return render_template("Settings/devtools.html", variables=variables)
        
        @self.app.route("/VideoRenderingSystem")
        def VideoRenderingSystem():
            g.PageTitle = "Video Rendering System"

            return render_template("vrs/vrs.html", current_scene=self.__VRSProjector.get_current_view(), view_options = self.__VRSProjector.get_views())

        @self.app.route("/editScene")
        def editScene():
            # Accessed by /EditScene?Id=[sceneId]
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
                return render_template("error.html",
                    message=f"Error fetching scene: {e}<br>This is a bug, a report has been automatically submitted.")

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

        @self.app.route("/feedback")
        def feedback():
            g.PageTitle = "Leave Feedback"

            return render_template("Feedback/leaveFeedback.html")
        
        @self.app.route("/dynamicRendering/gameResults")
        def dynamicRendering_gameResults():
            g.PageTitle = "Game Results"

            return render_template("DynamicRendering/gameResults.html")

        @self.app.route("/api/feedback/getFeatureRequests", methods=["GET"])
        def feedback_getFeatureRequests():
            try:
                featureRequests = self._fAPI.getFeatureRequests()

                featureRequestList: list[dict] = []

                for featureRequest in featureRequests:
                    featureRequestList.append(featureRequest.to_dict())

                return jsonify(featureRequestList)

            except Exception as e:
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Error getting feature requests: {e}, Traceback: {e.__traceback__}")
                ise.process = "API: Get Feature Requests"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)

                return jsonify({"error": f"Error getting feature requests: {e}"}), 500

        @self.app.route("/api/feedback/getBugReports", methods=["GET"])  #
        def feedback_getBugReports():
            try:
                bugReports = self._fAPI.getBugReports()

                bugReportList: list[dict] = []

                for bugReport in bugReports:
                    bugReportList.append(bugReport.to_dict())

                return jsonify(bugReportList)

            except Exception as e:
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Error getting bug reports: {e}, Traceback: {e.__traceback__}")
                ise.process = "API: Get Bug Reports"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)

                return jsonify({"error": f"Error getting bug reports: {e}"}), 500

        @self.app.route("/api/feedback/getSongRequests", methods=["GET"])
        def feedback_getSongRequests():
            try:
                songRequests = self._fAPI.getSongRequests()

                songRequestList: list[dict] = []

                for songRequest in songRequests:
                    songRequestList.append(songRequest.to_dict())

                return jsonify(songRequestList)

            except Exception as e:
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Error getting song requests: {e}, Traceback: {e.__traceback__}")
                ise.process = "API: Get song requests"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)

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

                    requestId = self._fAPI.processNewFeatureRequest(featureDescription, featureUseCase, featureExpected,
                        featureDetails, submitter)
                elif type == "Bug":
                    bugDescription = data.get("BugDescription", "")
                    whenItOccurs = data.get("WhenItOccurs", "")
                    expectedBehavior = data.get("ExpectedBehavior", "")
                    stepsToReproduce = data.get("StepsToReproduce", "")

                    requestId = self._fAPI.processBugReport(bugDescription, whenItOccurs, expectedBehavior,
                        stepsToReproduce, submitter)
                elif type == "SongAddition":
                    songName = data.get("SongName", "")
                    naughtyWords = data.get("NaughtyWords", "")

                    requestId = self._fAPI.processSongRequest(songName, naughtyWords, submitter)
                else:
                    return {"error": "Unknown Type"}, 400

                f.sendEmail(f"{type} Feedback submitted by {submitter} with request ID {requestId}",
                    f"{type} Feedback Submitted")

                return {"id": requestId}, 200

            except Exception as e:
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Error submitting Feedback: {e}, Traceback: {e.__traceback__}")
                ise.process = "API: Submit Feedback"
                ise.severity = "2"

                logInternalServerError(self.app, self._context, ise)

                return jsonify({"error": f"Error submitting Feedback: {e}"}), 500

        @self.app.route("/statistics")
        def statistics():
            g.PageTitle = "Statistics"

            return render_template("statistics.html")

        @self.app.route("/managerTools")
        def managerTools():
            g.PageTitle = "Manager Tools"

            return render_template("ManagerTools/managerTools.html")

        def checkLoginStatus() -> bool:
            currentToken: str = session.get("System_AccountAuthToken") or ""

            if currentToken:
                FoundUserAuthToken: UserAuthToken = self._context.db.session.query(UserAuthToken).filter_by(token=currentToken).first()

                if FoundUserAuthToken is not None and FoundUserAuthToken.expiryDate > datetime.now():
                    return True

            session["System_AccountAuthToken"] = None

            return False

        @self.app.route("/music")
        def music():
            g.PageTitle = "Benify"

            return render_template("/Music/musicControls.html")

        @self.app.route("/api/accounts/login", methods=["POST"])
        def accounts_login():
            currentToken: str = session.get("System_AccountAuthToken") or ""

            if currentToken:
                return jsonify({}), 200

            username: str = request.form.get("username", "")
            password: str = request.form.get("password", "")

            FoundUser: User = self._context.db.session.query(User).filter_by(username=username).first()

            if FoundUser is None:
                return jsonify({
                    "error": "Couldn't find an account with those details!"
                }), 403

            if FoundUser.password == password:
                AuthToken: str = ''.join(
                    random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(100))

                NewUserAuthToken: UserAuthToken = UserAuthToken(
                    userId=FoundUser.id,
                    token=AuthToken,
                    expiryDate=datetime.now() + timedelta(days=7),
                    createDate=datetime.now(),
                    isActive=True
                )

                self._context.db.session.add(NewUserAuthToken)

                self._context.db.session.commit()

                session["System_AccountAuthToken"] = AuthToken

                return jsonify({
                    "Token": AuthToken,
                })

            else:
                return jsonify({
                    "error": "Incorrect password"
                }), 403

        @self.app.route("/api/accounts/logout", methods=["POST"])
        def accounts_logout():
            currentToken: str = session.get("System_AccountAuthToken") or ""

            FoundUserAuthToken: UserAuthToken = self._context.db.session.query(UserAuthToken).filter_by(
                token=currentToken).first()

            if FoundUserAuthToken is not None:
                FoundUserAuthToken.expiryDate = datetime.now()

            session["System_AccountAuthToken"] = None

            return jsonify({}), 200

        @self.app.route("/api/accounts/getMyPermissions", methods=["GET"])
        def accounts_getMyPermissions():
            currentToken: str = session.get("System_AccountAuthToken") or ""

            FoundUserAuthToken: UserAuthToken = self._context.db.session.query(UserAuthToken).filter_by(
                token=currentToken).first()

            if FoundUserAuthToken is None:
                return jsonify({}), 200

            UserId: int = FoundUserAuthToken.userId

            Permissions = self._context.db.session.query(UserPermission).filter_by(userId=UserId).all()

            return jsonify([up.to_dict() for up in Permissions]), 200

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

                password: str = request.form.get("password", "")
            except Exception as e:
                return jsonify({
                    "error": f"Error parsing request data: {str(e)}"
                }), 400

            if (password == self.secrets["MANAGERLOGINCREDENTIALS"]):
                # AUTHORISE THIS USER FOR 7 DAYS
                newCookie: datetime = datetime.now() + timedelta(days=7)

                return jsonify({
                    "cookie": newCookie.isoformat()
                }), 200
            else:
                return jsonify({
                    "error": f"Incorrect password!"
                }), 401

        @self.app.route("/api/managerTools/amIAuthorised")
        def managerTools_amIAuthorised():
            cookie: str = request.args.get("cookie") or ""

            try:
                if managerTools_VerifyAuthCookie(cookie) == False:
                    return jsonify({"response": False}), 200

                return jsonify({"response": True}), 200

            except Exception:
                return jsonify({"response": False}), 200

        @self.app.route("/api/managerTools/sendEmail", methods=["POST"])
        def sendEmail():
            try:
                cookie: str = request.form.get("authCookie", "")
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

            errorList: list = []

            if os.environ["ENVIRONMENT"] == "Development":
                recipients = [os.environ["DEVELOPEREMAILADDRESS"]]

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
                
                if message:
                    with open("Data/messages.txt", "a") as f:
                        f.write(message + "\n")

                return jsonify({
                    "message": "Message Sent"
                })

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/settings/getMessages", methods=["GET"])
        def settings_getMessages():
            try:
                with open("Data/messages.txt", "r") as f:
                    messages = f.read()

                return jsonify(messages)

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/settings/devtools/requestAccess", methods=["POST"])
        def settings_devtools_requestAccess():
            try:
                password = request.form.get("password")

                if (str(password) != str(os.environ["DEVTOOLSPASSWORD"]) and self.devMode == False):
                    return jsonify({"error": "Invalid password"}), 401

                self.DevToolsOTP = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                self.DevToolsRefreshCount = 5
                return jsonify(self.DevToolsOTP)

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/ping")
        def ping():
            # f.message("|--- I'm still alive! ---|")
            return 'OK'

        @self.app.route("/api/getAllGames", methods=["GET"])
        def getAllGames():
            try:
                games: list[Game] = self._context.getAllGames()

                gameList: list[dict] = []

                for game in games:
                    gameList.append(game.to_dict())

                return jsonify(gameList)

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # @self.app.route("/api/serviceStatus", methods=["GET"])
        # def serviceStatus():
        #     try:
        #         services: list[str] = self._supervisor.getServices()

        #         serviceHealthList: list[dict] = []

        #         for service in services:
        #             serviceHealth: ServiceHealthDTO = self._supervisor.getServiceHealth(service)

        #             if (serviceHealth != None):
        #                 serviceHealthList.append(serviceHealth.to_dict())

        #         return jsonify(serviceHealthList)

        #     except Exception as e:
        #         ise: InternalServerError = InternalServerError()

        #         ise.service = "api"
        #         ise.exception_message = str(f"Error getting service status: {e}, Traceback: {e.__traceback__}")
        #         ise.process = "API: Get Service Status"
        #         ise.severity = "1"

        #         logInternalServerError(self.app, self._context, ise)

        #         return jsonify({"error": f"Error getting service status: {e}"}), 500

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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Error Getting available fixtures: {e}")
                ise.process = "API: Get Available Fixtures"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)

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

                    if not isinstance(fixtureChannels, (list, tuple)):
                        fixtureChannels = []
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
                            channels = {"DMXValue": DMXFixture.channels[1]["value"][0],
                                        "channel": DMXFixture.channels[1]["name"]}
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
                                f.message(f"Error getting fixture channel: {e}, {dmxChannel["name"]}, {channelValue}",
                                    type="error")

                    channelValues.append({
                        "name": fixtureName,
                        "id": fixtureId,
                        "attributes": channels
                    })

                return jsonify(channelValues), 200

            except Exception as e:
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Error getting DMX channel values: {e}")
                ise.process = "API: Get DMX Values"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)

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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to fetch scenes: {e}")
                ise.process = "API: Get DMX Scenes"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to fetch scene: {e}")
                ise.process = "API: DMX Scene"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to start scene: {e}")
                ise.process = "API: Start DMX Scene"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to stop scene: {e}")
                ise.process = "API: Stop DMX Scene"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
                return jsonify({"error": f"Failed to end scene: {e}"}), 500

        @self.app.route("/api/dmx/updatePatchedFixtureName", methods=["POST"])
        def updatePatchedFixtureName():
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                fixtureId = request.form.get("fixtureId")
                newName = request.form.get("name")

                if not fixtureId or not newName:
                    return jsonify({"error": "Invalid input"}), 400

                patchedFixture : PatchedFixture = self._context.PatchedFixtures.query.filter_by(id=fixtureId).first()

                if not patchedFixture:
                    return jsonify({"error": "Patched fixture not found"}), 404

                patchedFixture.fixtureName = newName
                
                self._context.db.session.commit()

                return jsonify({"newName": newName})
            except Exception as e:
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to update fixture name: {e}")
                ise.process = "API: Update DMX Fixture Name"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
                return jsonify({"error": f"Failed to update fixture name: {e}"}), 500
            
        @self.app.post("/api/dmx/updatePatchedFixtureAddress")
        def dmx_updatePatchedFixtureAddress():
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                fixtureId = request.form.get("fixtureId")
                newAddress = request.form.get("startAddress", type=int)

                if not fixtureId or not newAddress:
                    return jsonify({"error": "Invalid input"}), 400

                patchedFixture : PatchedFixture = self._context.PatchedFixtures.query.filter_by(id=fixtureId).first()

                if not patchedFixture:
                    return jsonify({"error": "Patched fixture not found"}), 404
                
                patchedFixture.dmxStartAddress = newAddress
                fixture_channels = self._dmx.getFixtureTypeChannels(patchedFixture.fixtureId)
                if not isinstance(fixture_channels, list):
                    fixture_channels = []
                patchedFixture.dmxEndAddress = len(fixture_channels) + newAddress - 1

                self._context.db.session.commit()
                
                self._dmx.unPatchFixture(patchedFixture.id)
                self._dmx.registerFixtureUsingTypeId(patchedFixture.fixtureName, patchedFixture.fixtureId, patchedFixture.dmxStartAddress)

                return jsonify({"newAddress": newAddress})
            except Exception as e:
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to update fixture address: {e}")
                ise.process = "API: Update DMX Fixture Address"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
                return jsonify({"error": f"Failed to update fixture address: {e}"}), 500
            
        @self.app.route("/api/dmx/unPatchFixture", methods=["POST"])
        def dmx_unPatchFixture():
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                fixtureId = request.form.get("fixtureId")

                if not fixtureId:
                    return jsonify({"error": "Invalid input"}), 400

                patchedFixture : PatchedFixture = self._context.PatchedFixtures.query.filter_by(id=fixtureId).first()

                if not patchedFixture:
                    return jsonify({"error": "Patched fixture not found"}), 404
                
                self._dmx.unPatchFixture(patchedFixture.id)
                
                self._context.db.session.delete(patchedFixture)
                self._context.db.session.commit()

                return jsonify({"message": "Fixture unpatched successfully"})
            except Exception as e:
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to unpatch fixture: {e}")
                ise.process = "API: Unpatch DMX Fixture"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
                return jsonify({"error": f"Failed to unpatch fixture: {e}"}), 500
            
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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to create scene: {e}")
                ise.process = "API: Create DMX Scene"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to edit scene name: {e}")
                ise.process = "API: Edit DMX Scene Name"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to get scene event: {e}")
                ise.process = "API: Get DMX Scene Event"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
                return jsonify({"error": f"Failed to fetch scene event: {e}"}), 500

        @self.app.route("/api/dmx/saveSceneEvent", methods=["POST"])
        def saveSceneEvent():
            if self._dmx == None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                sceneEventId = int(request.form.get("sceneEventId", 0))
                DMXValues = request.form.get("DMXValues")
                if DMXValues is None:
                    return jsonify({"error": "DMXValues cannot be None"}), 400
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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to save scene event: {e}")
                ise.process = "API: Save DMX Scene Event"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to create scene event: {e}")
                ise.process = "API: Create New DMX Scene Event"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
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
                        totalDuration = sum(event.duration for event in
                                            self._context.DMXSceneEvent.query.filter_by(sceneID=scene.id).all())
                        scene.duration = totalDuration

                    self._context.db.session.commit()

                    return jsonify(sceneEvent.to_dict()), 200

            except Exception as e:
                ise = InternalServerError()
                ise.service = "api"
                ise.exception_message = f"Failed to update scene event duration: {e}"
                ise.process = "API: Update Scene Event Duration"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
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
                    scene: DMXScene = self._context.DMXScene.query.filter_by(id=sceneId).first()
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

                logInternalServerError(self.app, self._context, ise)
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
                    scene: DMXScene = self._context.DMXScene.query.filter_by(id=sceneId).first()
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

                logInternalServerError(self.app, self._context, ise)
                return jsonify({"error": ise.exception_message}), 500

        @self.app.route("/api/dmx/setSceneSongTrigger", methods=["POST"])
        def dmx_setSceneSongTrigger():
            if self._dmx is None or self._dmx.isConnected() == False:
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                sceneId = request.form.get("sceneId")
                songId = request.form.get("songId")

                if not sceneId or not songId:
                    return jsonify({"error": "sceneId and songId are required"}), 400

                with self.app.app_context():
                    scene: DMXScene = self._context.db.session.query(DMXScene).filter_by(id=sceneId).first()
                    if not scene:
                        return jsonify({"error": "Scene not found"}), 404

                    scene.song_id = songId

                    self._context.db.session.commit()

                return jsonify({"success": "Scene song trigger set"})

            except Exception as e:
                ise = InternalServerError()
                ise.service = "api"
                ise.exception_message = f"Failed to update scene song trigger: {e}"
                ise.process = "API: Update Scene Song Trigger"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
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
                    scene: DMXScene = self._context.DMXScene.query.filter_by(id=sceneId).first()
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

                logInternalServerError(self.app, self._context, ise)
                return jsonify({"error": ise.exception_message}), 500

        @self.app.route("/api/dmx/getScenesWithKeyboardTriggers", methods=["GET"])
        def getScenesWithKeyboardTriggers():
            if self._dmx is None or not self._dmx.isConnected():
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                with self.app.app_context():
                    Scenes: list[DMXScene] = self._context.DMXScene.query.filter(
                        self._context.DMXScene.keyboard_keybind.isnot(None).isnot("")).all()

                    scenesWithTriggers = [scene.to_dict() for scene in Scenes if scene.keyboard_keybind]

                return jsonify(scenesWithTriggers), 200
            except Exception as e:
                ise = InternalServerError()
                ise.service = "api"
                ise.exception_message = f"Failed to get scenes with keyboard triggers: {e}"
                ise.process = "API: Get Scenes With Keyboard Triggers"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
                return jsonify({"error": ise.exception_message}), 500
            
        @self.app.route("/api/dmx/patchFixture", methods=["POST"])
        def dmx_patchFixture():
            if self._dmx is None or not self._dmx.isConnected():
                return jsonify({"error": "DMX Connection not available"}), 503

            try:
                fixtureId = request.form.get("id")
                name = request.form.get("name")
                fixtureTypeId = request.form.get("fixtureTypeId")
                startChannel = request.form.get("startChannel")
                channelCount = request.form.get("channelCount")
                
                dmxControllerId = 0
                dmxControllerId = self._dmx.registerFixtureUsingTypeId(name, fixtureTypeId, startChannel)

                with self.app.app_context():
                    fixture: PatchedFixture = self._context.db.session.query(PatchedFixture).filter_by(id=fixtureId).first()
                    if not fixture:
                        fixture = PatchedFixture(
                            fixtureName=name,
                            dmxStartAddress=int(startChannel or 0),
                            dmxEndAddress=int(startChannel or 0) + int(channelCount or 0) - 1,
                            fixtureId=fixtureTypeId,
                            dmxControllerFixtureId=dmxControllerId
                        )

                        self._context.db.session.add(fixture)
                        self._context.db.session.commit()
                        return jsonify({"success": "Fixture created successfully"}), 201

                    fixture.fixtureName = name
                    fixture.fixtureId = fixtureTypeId
                    fixture.dmxStartAddress = int(startChannel or 0)
                    fixture.dmxEndAddress = int(startChannel or 0) + int(channelCount or 0) - 1
                    fixture.dmxControllerFixtureId = dmxControllerId

                    self._context.db.session.commit()

                return jsonify({"success": "Fixture patched successfully"}), 200

            except Exception as e:
                ise = InternalServerError()
                ise.service = "api"
                ise.exception_message = f"Failed to patch fixture: {e}"
                ise.process = "API: Patch Fixture"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)
                return jsonify({"error": ise.exception_message}), 500

        @self.app.route('/end')
        def terminateServer():
            logging.shutdown()
            os.kill(os.getpid(), signal.SIGTERM)

        @self.app.route('/api/email/sendTestEmail', methods=["POST"])
        def sendTestEmail():
            try:
                email = request.form["EmailAddress"]
                password = request.form["AppPassword"]

                self._eAPI.SendTestEmail(email, password)

                return jsonify({"message": "Test Email Sent Sucessfully!"}), 200
            except Exception as e:
                return jsonify({"message": "FAILED to send Test Email:<br>" + str(e)}), 200

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
                ise: InternalServerError = InternalServerError()

                ise.service = "api"
                ise.exception_message = str(f"Failed to update DMX Value: {e}")
                ise.process = "API: Update DMX Value"
                ise.severity = "3"

                logInternalServerError(self.app, self._context, ise)

        @self.socketio.on('playBriefing')
        def playBriefing():
            self.__VRSProjector.play_video("src/VRS/media/Briefing.mp4")
            
        @self.socketio.on('stopBriefing')
        def stopBriefing():
            self.__VRSProjector.show_idle()
            
        @self.socketio.on('test_startGame')
        def test_startGame():
            self.gameStarted()
            
            for i in range(120, 110, -2):
                self.timingPacket(["0", "0", "0", f"{str(i)}"])
                self.finalScorePacket(["0", "1", "0", str(random.randint(1, 200)), "0", "0", "0", str(random.randint(1, 100))])
                self.teamScorePacket(["0", "0", str(random.randint(1, 100))])
                self.teamScorePacket(["0", "2", str(random.randint(1, 100))])
                self.finalScorePacket(["0", "3", "0", str(random.randint(1, 200)), "0", "0", "0", str(random.randint(1, 100))])
                self.finalScorePacket(["0", "7", "0", str(random.randint(1, 200)), "0", "0", "0", str(random.randint(1, 100))])
                time.sleep(2)
                
        @self.socketio.on('test_endGame')
        def test_endGame():
            self.gameEnded()
            
        @self.socketio.on('vrs_switchView')
        def vrs_switchView(data):
            if self.__VRSProjector is not None:
                self.__VRSProjector.switch_view_to_index(int(data.get("view", 0)))
            
        @self.socketio.on('vrs_getView')
        def vrs_getView():
            if self.__VRSProjector is not None:
                return self.__VRSProjector.get_current_view()

        @self.socketio.on("setVolume")
        def setVolume(msg):
            self._mAPI.setVolume(msg.get("volume", 0))

        @self.socketio.on("seekSong")
        def seekSong(msg):
            self._mAPI.seek(msg["location"])

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
                ise: InternalServerError = InternalServerError()

                ise.service = "socket"
                ise.exception_message = str(f"Failed To Send Socket Message: {e}")
                ise.process = "Socket: Send Message"
                ise.severity = "1"

                logInternalServerError(self.app, self._context, ise)
                
                return jsonify({"error": f"Failed to send socket message: {e}"}), 500

    # -----------------| Background Tasks |-------------------------------------------------------------------------------------------------------------------------------------------------------- #

    def startSniffing(self, ready_event: threading.Event):
        try:
            ready_event.set()
            sniff(prn=self.packetCallback, store=False,
                iface=self.ETHERNET_INTERFACE if self.devMode != "true" else None)
        except Exception as e:
            f.message(f"Error while sniffing: {e}", type="error")
            return

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

        response = requests.post(f'http://{get_local_ip()}:8080/sendMessage',
            data={'message': "Restarting Web App Now!", 'type': "createWarning"})

        # Make sure all the end of game processing completes
        time.sleep(5)

        f.message("Restarting App", type="warning")

        os._exit(1)

    def sendSongDetails(self, songDetails):
        self.socketio.emit('songAlbum', {'message': songDetails.album})
        self.socketio.emit('songName', {'message': {"name": songDetails.name, "id": songDetails.songId}})
        self.socketio.emit('musicVolume', {'message': songDetails.currentVolume})
        self.socketio.emit('musicStatusV2', {
            'message': {"playbackStatus": songDetails.isPlaying, "musicPosition": (songDetails.duration - songDetails.timeleft), "duration": songDetails.duration}})
        queue = self._mAPI.getQueue()
        queue_dicts = [song.to_dict() for song in queue]
        self.socketio.emit('musicQueue', {'queue': queue_dicts})
        self.socketio.emit('songBpm', {"message": songDetails.bpm})
        self.socketio.emit('songArtist', {"message": songDetails.artist})
        self.socketio.emit('playlist', {"playlist": songDetails.playlist.to_dict() if songDetails.playlist else ""})

    def mediaStatusChecker(self, ready_event: threading.Event):
        f.message(f.colourText("Starting Media status checker", "blue"))
        
        ready_event.set()

        while True:
            if self._mAPI is None:
                time.sleep(10)

            time.sleep(0.1)

            try:
                if self._mAPI is not None:
                    songDetails: SongDetailsDTO = self._mAPI.currentSongDetails()

                    self.sendSongDetails(songDetails)
            except Exception as e:
                f.message(f"Error fetching current song details: {e}", type="error")

    # -----------------| Packet Handling |-------------------------------------------------------------------------------------------------------------------------------------------------------- #

    def packetCallback(self, packet):
        try:
            if packet.haslayer(IP) and (packet[IP].src == self.IP1 or packet[IP].src == self.IP2) and packet[
                IP].dst == "192.168.0.255":

                # f.message(f"Packet 1: {packet}")

                packet_data = bytes(packet['Raw']).hex()
                # f.message(f"Packet Data (hex): {packet_data}, {type(packet_data)}")

                decodedData = (hexToASCII(hexString=packet_data)).split(',')
                # f.message(f"Decoded Data: {decodedData}")

                with self.app.app_context():
                    self.socketio.emit("zonePacket", {"data": decodedData})

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
            response = requests.post(f'http://{get_local_ip()}:8080/sendMessage',
                data={'message': f"Game Started @ {str(datetime.now())}", 'type': "start"})
        # f.message(f"Response: {response.text}")

        elif packetData[1] == "@014":
            self.gameEnded()
            response = requests.post(f'http://{get_local_ip()}:8080/sendMessage',
                data={'message': f"Game Ended @ {str(datetime.now())}", 'type': "end"})
        # f.message(f"Response: {response.text}")

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

        response = requests.post(f'http://{get_local_ip()}:8080/sendMessage',
            data={'message': f"{packetData[0]}", 'type': "gameMode"})


    def teamScorePacket(self, packetData):
        # 0 = red, 2 = green
        # f.message(f"Team Score Packet: {packetData}")

        teamId = str(packetData[1])
        teamScore = int(packetData[2])

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

        # f.message(f"Time Left: {timeLeft}")

        if int(timeLeft) <= 0:
            # f.message(f"Game Ended at {datetime.now()}", type="success")
            self.gameEnded()
        else:
            self.gameStarted()
            self.endOfDay = False
            response = requests.post(f'http://{get_local_ip()}:8080/sendMessage',
                data={'message': f"{timeLeft}", 'type': "timeRemaining"})


    def finalScorePacket(self, packetData):
        gunId = packetData[1]
        finalScore = packetData[3]
        accuracy = packetData[7]

        self.socketio.emit('gunScores', {'message': f"{gunId},{finalScore},{accuracy}"})

        gunName = ""

        try:
            with self.app.app_context():
                gunName: str = self._context.db.session.query(Gun).filter_by(id=gunId).first().name

        except Exception as e:
            f.message(f"Error getting gun name: {e}", type="error")

        if gunName == "":
            gunName = "id: " + gunId

        try:
            self.GunScores[gunId] = finalScore
        except Exception as e:
            f.message(f"Error updating Gun Scores: {e}", type="error")

    # f.message(f"Gun {gunName} has a score of {finalScore} and an accuracy of {accuracy}", type="success")

    def shotConfirmedPacket(self, packetData):
        # f.message(f"Shot Confirmed Packet: {packetData}")

        shooterGunId = packetData[1]
        shotGunId = packetData[2]
        pointForRedTeam = int(packetData[3])
        pointForGreenTeam = int(packetData[4])

        shotGunName = ""
        shooterGunName = ""

        try:
            with self.app.app_context():
                shotGunName: str = self._context.Gun.query.filter_by(id=shotGunId).first().name
                shooterGunName: str = self._context.Gun.query.filter_by(id=shooterGunId).first().name

        except Exception as e:
            f.message(f"Error getting gun names: {e}", type="error")

        f.message(f"{shotGunName} just shot {shooterGunName}")

        self.socketio.emit("shotConfirmed", {"ShotGun": shotGunId, "ShooterGun": shooterGunId})

        if pointForRedTeam > 0:
            self.TeamScores["Red"] = int(self.TeamScores["Red"]) + pointForRedTeam
        elif pointForGreenTeam > 0:
            self.TeamScores["Green"] = int(self.TeamScores["Green"]) + pointForGreenTeam

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
        
        self.currentGameId = self._context.createNewGame()

        f.message(f"Created new game with Id {self.currentGameId}")

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

        self.__VRSProjector.play_video(int(os.getenv("PREFERRED_SCOREBOARD_CAPTURE_DEVICE_INDEX", 0)))

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
            winningPlayer = ""
            winningTeam = ""
            
            if self.GunScores != {}:
                winningPlayer = max(self.GunScores.items(), key=lambda x: x[1])
            if self.TeamScores != {}:
                winningTeam = max(self.TeamScores.items(), key=lambda x: x[1])

            if winningPlayer != "" and winningTeam != "" and self.currentGameId != 0:
                self._context.updateGame(self.currentGameId, endTime=datetime.now(), winningPlayer=winningPlayer[0], winningTeam=winningTeam[0])
                
                with self.app.app_context():
                    for gunId, score in self.GunScores.items():
                        gamePlayer: GamePlayer = self._context.db.session.query(GamePlayer).filter_by(
                            gameId=self.currentGameId).filter_by(gunId=gunId).first()

                        if gamePlayer != None:
                            gamePlayer.score = score
                            gamePlayer.accuracy = 0

                        else:
                            gamePlayer: GamePlayer = GamePlayer(gameId=self.currentGameId, gunId=gunId, score=score,
                                accuracy=0)
                            self._context.addGamePlayer(gamePlayer)

                        f.message(f"Adding gun id: {gunId}'s score: {score} into game id of {self.currentGameId}")

                    self._context.SaveChanges()

                self.currentGameId = 0

        except Exception as e:
            ise: InternalServerError = InternalServerError()

            ise.service = "zone"
            ise.exception_message = str(f"Failed to update player scores in DB: {e}")
            ise.process = "Zone: Update Gun Scores in DB"
            ise.severity = "3"

            logInternalServerError(self.app, self._context, ise)
            
        try:
            self.showWinners()
        except Exception as e:
            ise: InternalServerError = InternalServerError()

            ise.service = "webapp"
            ise.exception_message = str(f"Failed To Switch To Winners Screen: {e}")
            ise.process = "WebApp: Switch To Winners Screen"
            ise.severity = "2"

            logInternalServerError(self.app, self._context, ise)
            
    def showWinners(self):
        winningTeam = ""
        winningPlayer = ""
    
        if self.GunScores != {}:
            winningPlayer = max(self.GunScores.items(), key=lambda x: x[1])
        if self.TeamScores != {}:
            winningTeam = max(self.TeamScores.items(), key=lambda x: x[1])

        with self.app.app_context():
            winningGun: Gun = self._context.db.session.query(Gun).filter_by(id=winningPlayer[0]).first()
            
            winningGunName = winningGun.name
            gunScore = winningPlayer[1]
            teamName = winningTeam[0]
            teamScore = winningTeam[1]
            
            try:
                self.__VRSProjector.show_page(f"http://{get_local_ip()}:8080/dynamicRendering/gameResults?mainText=Game%20Over!")

                time.sleep(7)

                self.__VRSProjector.show_page(f"http://{get_local_ip()}:8080/dynamicRendering/gameResults?mode=team&teamName={teamName}%20Team&teamColor={teamName.lower()}&score={teamScore}")

                time.sleep(7)
                
                self.__VRSProjector.show_page(f"http://{get_local_ip()}:8080/dynamicRendering/gameResults?mode=player&playerName={winningGunName}&score={gunScore}")

                time.sleep(7)
                
                self.__VRSProjector.show_page(f"http://{get_local_ip()}:8080/dynamicRendering/gameResults?mainText=Please%20Return%20to%20the%20Starting%20Area")
                
                time.sleep(20)

                self.__VRSProjector.play_video(int(os.getenv("PREFERRED_SCOREBOARD_CAPTURE_DEVICE_INDEX", 0)))

                return True
            except Exception as e:
                ise : InternalServerError = InternalServerError()
                
                ise.service = "vrs"
                ise.exception_message = str(f"Error showing winners screen: {e}")
                ise.process = "VRS: Show Winners Screen"
                ise.severity = "3"
                    
                logInternalServerError(self.app, self._context, ise)
                
                return False