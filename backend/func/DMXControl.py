import os, json
from os import walk
from PyDMXControl.controllers import OpenDMXController
from PyDMXControl.profiles.Generic import Custom, Dimmer
            
from func import format
import threading
import time
import requests
import socket
import datetime
            
class dmx:
    def __init__(self, context, app, devmode):
        try:
            self._dmx = OpenDMXController()       
        except Exception as e:
            self._dmx = None
            
            format.message(f"Error starting DMX controller: {e}", "error")
            if devmode != True:
                AttributeError(f"DMX controller not started, {e}")
                
                return
            else:
                format.message("Continuing DMX connection in devmode", "warning")
                
        self._context = context
        self.app = app
        
        self._localIp = self.__getLocalIp()
        self.devMode = devmode

        self.runningScenes = {}
        self.fixtures = {}
        self.scenes = {}
        self.fixtureGroups = {}
        self.fixtureProfiles = self._context.getFixtureProfiles()
        
        try:
            self.scenes = self.getDMXScenes()
        except Exception as e:
            format.message(f"Error processing DMX scenes: {e}", "error")
            
    # Setters
    
    def __appendToFixtures(self, fixture, fixtureType):
        self.fixtures[fixture.name] = {"type": fixtureType, "id": fixture.id}

    def addFixtureToGroup(self, groupName, fixture):
        if groupName not in self.fixtureGroups:
            self.fixtureGroups[groupName] = []
            
        self.fixtureGroups[groupName].append(fixture)
        
        return self.fixtureGroups[groupName]
        
    def registerDimmerFixture(self, fixtureName):
        try:
            fixture = self._dmx.add_fixture(Dimmer, name=fixtureName)
            setattr(self, fixtureName, fixture)
            
            self.__appendToFixtures(fixture, "dimmer")
            
            return fixture
        except Exception as e:
            format.message(f"Error registering Dimmer fixture: {e}", "error")
            return None
    
    def registerCustomFixture(self, fixtureName, fixtureType, channels, startChannel):
        try:
            fixture = self._dmx.add_fixture(Custom(channels=channels, name=fixtureName, start_channel=startChannel))
            
            setattr(self, fixtureName, fixture)
        
            self.__appendToFixtures(fixture, fixtureType)
            
            return fixture
        except Exception as e:
            format.message(f"Error registering Custom fixture: {e}", "error")
            return None
        
    def registerFixtureUsingType(self, fixtureName, fixtureType, startChannel):
        try:
            if str(fixtureType).lower() in self.fixtureProfiles:
                fixture = self._dmx.add_fixture(Custom(channels=0, start_channel=startChannel, name=fixtureName))
                
                setattr(self, fixtureName, fixture)
                
                self.__appendToFixtures(fixture, fixtureType)
                
                for channel in self.fixtureProfiles[fixtureType.lower()]:
                    fixture._register_channel(channel)
                
                return fixture
            
            raise LookupError(f"Fixture type {fixtureType} not found")
        
        except Exception as e:
            format.message(f"Error registering fixture: {e}", "error")
            return
        
    def registerChannel(self, fixtureName, channelName):
        try:
            fixture = self._dmx.get_fixtures_by_name(fixtureName)[0]
            
            if fixture != None:
                fixture._register_channel(channelName)
            else:
                return LookupError(f"Fixture {fixtureName} not found")
            
        except Exception as e:
            format.message(f"Error registering channel: {e}", "error")
        
    def setFixtureChannel(self, fixtureName, channelName, value):
        try:
            try:
                fixture = self._dmx.get_fixture(int(fixtureName))
            except Exception as e:
                fixture = self._dmx.get_fixtures_by_name(fixtureName)[0]
            
            if fixture != None:
                fixture.set_channel(channelName.lower(), int(value))
            else:
                return LookupError(f"Fixture {fixtureName} not found")
            
        except Exception as e:
            format.message(f"Error setting channel: {e}", "error")
            
    def startScene(self, sceneId):
        scene = self.getDMXSceneById(sceneId)
        
        for thread in threading.enumerate():
            if thread.name == f"DMXScene Running - {sceneId}":
                thread, stopEvent = self.runningScenes[sceneId]
                stopEvent.set() 
                thread.join()   
                del self.runningScenes[sceneId]
                format.message(f"Scene {sceneId} stopped", "info")
        
        if scene != None:
            stopEvent = threading.Event()
            thread = threading.Thread(target=self.__startScene, args=(scene,stopEvent))
            thread.name = f"DMXScene Running - {sceneId}"
            self.runningScenes[sceneId] = (thread, stopEvent)
            thread.start()
        else:
            format.message(f"Scene {sceneId} not found", "error")
            
    def stopScene(self, sceneId):
        for thread in threading.enumerate():
            if thread.name == f"DMXScene Running - {sceneId}":
                thread, stopEvent = self.runningScenes[sceneId]
                stopEvent.set() 
                thread.join()   
                del self.runningScenes[sceneId]
                self.turnOffAllChannels()
                format.message(f"Scene {sceneId} stopped", "info")
                return
            
        format.message(f"Scene {sceneId} not found", "error")
    
    def createNewScene(self, DMXScene):
        try:
            with self.app.app_context():
                self._context.db.session.add(DMXScene)
                self._context.db.session.commit()

                self._context.db.session.refresh(DMXScene)
                return DMXScene
        except Exception as e:
            format.message(f"Error creating new scene: {e}", "error")
            return
        
    def updateFixtureChannelEvent(self, sceneEventID, fixture, channel, value):
        try:
            with self.app.app_context():
                event = self._context.DMXSceneEventChannel.query.filter_by(
                    eventID=sceneEventID,
                    fixture=fixture,
                    channel=channel
                ).first()

                if event:
                    event.value = value
                else:
                    event = self._context.DMXSceneEventChannel(
                        eventID=sceneEventID,
                        fixture=fixture,
                        channel=channel,
                        value=value
                    )
                    self._context.db.session.add(event)
                
                try:
                    self._context.db.session.commit()
                    return event
                except Exception as e:
                    self._context.db.session.rollback()
                    format.message(f"Error saving event to database: {e}", "error")
                    return None

        except Exception as e:
            format.message(f"Error accessing database context: {e}", "error")
            return None
        
    def turnOffAllChannels(self):
        fixtures = self.getRegisteredFixtures()
        
        for fixture in fixtures.items():
            fixtureName = fixture[0]
            fixtureType = fixture[1]["type"]
            fixtureProfile = (self.getFixtureProfiles()).get(fixtureType)
            
            for channel in fixtureProfile.items():
                self.setFixtureChannel(fixtureName, channel[0], 0)
                
        return
    
    def setSceneSongTrigger(self, sceneId, songName):
        scene = self.getDMXSceneById(sceneId)
        scene.songKeybind = songName
        self._context.db.session.commit()
        
        return scene
    
    def createNewSceneEvent(self, sceneId):
        newSceneEvent = self._context.DMXSceneEvent(
            name="New Event", 
            duration=0, 
            updateDate=datetime.datetime.now(), 
            sceneID=sceneId)
        
        self._context.db.session.add(newSceneEvent)
        self._context.db.session.commit()
        
        return newSceneEvent

    # Getters
        
    def getFixtureProfiles(self):
        return self.fixtureProfiles
    def getFixtures(self):
        Fixtures = []
        try:
            with self.app.app_context():
                registeredFixtures = self.fixtures
                
                for registeredFixture in registeredFixtures.items():
                
                    fixtures = self._context.Fixture.query.filter_by(name=str(registeredFixture[1]["type"])).all()

                    for fixture in fixtures:
                        DMXFixture = self.getFixturesByName(registeredFixture[0])[0]
                        
                        fixtureDTO = self.__mapToFixtureDTO(fixture, registeredFixture[1]["id"])
                        fixtureDict = fixtureDTO[0].to_dict()
                        Fixtures.append({"fixture": fixtureDict, "name": registeredFixture[0], "id": registeredFixture[1]["id"], "channels": DMXFixture.channel_usage})
        except Exception as e:
            format.message(f"Error getting fixtures: {e}", "error")
            return []
        
        return Fixtures
    def getRegisteredFixtures(self):
        return self.fixtures
    def getFixtureTypes(self):
        return list(self.fixtureProfiles.keys())
    def getFixtureGroups(self):
        return self.fixtureGroups
    def getFixturesByName(self, fixtureName):
        fixtures = self._dmx.get_fixtures_by_name(fixtureName)
        return fixtures
    def getDMXScenes(self):
        self.__processJSONDMXScenes()
        DMXScenes = []
        try:
            with self.app.app_context():
                scenes = self._context.DMXScene.query.all()

                for scene in scenes:
                    DMXScenes += self.__mapToDMXSceneDTO(scene)
        except Exception as e:
            format.message(f"Error getting DMX scenes: {e}", "error")
            return []
        
        return DMXScenes
        
    def getDMXSceneByName(self, sceneName):
        return self.__findScene(sceneName)
    def getDMXSceneById(self, sceneID, return_dto=True):
        return self.__findSceneWithId(sceneID, return_dto=return_dto)
    def getValueForSettingInChannel(self, fixtureType, channelName, settingName):
        return self.__getValueForChannelSetting(fixtureType, channelName, settingName)
    def __getLocalIp(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            format.message(f"Error getting local IP: {e}", "error")
            return ""
    def getSceneEventById(self, eventId):
        event = self._context.DMXSceneEvent.query.get(eventId)
        return self._context.DMXSceneEventDTO(
            id=event.id,
            name=event.name, 
            duration=event.duration,
            updateDate=event.updateDate,
            channels=[
                {
                    "fixture": channel.fixture,
                    "channel": channel.channel,
                    "value": channel.value
                }
                for channel in self._context.DMXSceneEventChannel.query.filter_by(eventID=event.id).all()
            ]
        )
    # Processing
    
    def __mapToDMXSceneDTO(self, scene):
        DMXScene = [
            self._context.DMXSceneDTO(
                id=scene.id,
                name=scene.name,
                duration=scene.duration,
                updateDate=scene.updateDate,
                createDate=scene.createDate,
                flash=scene.flash,
                repeat=scene.repeat,
                keyboard_keybind=scene.keyboard_keybind,
                song_keybind=scene.song_keybind,
                game_event_keybind=scene.game_event_keybind,
                events=[
                    self._context.DMXSceneEventDTO(
                        id=event.id,
                        name=event.name,
                        duration=event.duration,
                        updateDate=event.updateDate,
                        channels=[
                            {
                                "fixture": channel.fixture,
                                "channel": channel.channel,
                                "value": channel.value
                            }
                            for channel in self._context.DMXSceneEventChannel.query.filter_by(eventID=event.id).all()
                        ]
                    )
                    for event in self._context.DMXSceneEvent.query.filter_by(sceneID=scene.id).all()
                ]
            )
        ]
        
        return DMXScene
    
    def __mapToFixtureDTO(self, fixture, fixtureId = None):
        return [
            self._context.FixtureDTO(
                id=fixtureId,
                name=fixture.name,
                mode=fixture.mode,
                notes=fixture.notes,
                icon=fixture.icon,
                noOfchannels=fixture.noOfchannels,
                channels=[
                    self._context.FixtureChannelDTO(
                        id=channel.id,
                        fixtureID=channel.fixtureID,
                        channelNo=channel.channelNo,
                        name=channel.name,
                        description=channel.description,
                        icon=channel.icon,
                        channelValues = [
                            {
                                "value": value.value,
                                "name": value.name,
                                "icon": value.icon
                            }
                            for value in self._context.FixtureChannelValue.query.filter_by(channelID=channel.id).all()
                        ]
                    )
                    for channel in self._context.FixtureChannel.query.filter_by(fixtureID=fixture.id).all()
                ]
            )
        ]
    
    def __findScene(self, sceneName):
        with self.app.app_context():
            scene = self._context.DMXScene.query.filter_by(name=sceneName).first()
            
            # Map the results to DMXSceneDTO objects
            DMXScene = self._context.DMXSceneDTO(
                id=scene.id,
                name=scene.name,
                duration=scene.duration,
                updateDate=scene.updateDate,
                createDate=scene.createDate,
                repeat = scene.repeat,
                flash = scene.flash,
                keybind = scene.keybind,
                events=[
                    self._context.DMXSceneEventDTO(
                        id=event.id,
                        name=event.name,
                        duration=event.duration,
                        updateDate=event.updateDate,
                        channels=[
                            {
                                "fixture": channel.fixture,
                                "channel": channel.channel,
                                "value": channel.value
                            }
                            for channel in self._context.DMXSceneEventChannel.query.filter_by(eventID=event.id).all()
                        ]
                    )
                    for event in self._context.DMXSceneEvent.query.filter_by(sceneID=scene.id).all()
                ]
            )
            

        return DMXScene
    
    
    def __findSceneWithId(self, sceneId, return_dto=True):
        with self.app.app_context():
            scene = self._context.db.session.query(self._context.DMXScene).filter_by(id=sceneId).first()

            if not scene:
                return None

            if return_dto:
                return self._context.DMXSceneDTO(
                    id=scene.id,
                    name=scene.name,
                    duration=scene.duration,
                    updateDate=scene.updateDate,
                    createDate=scene.createDate,
                    repeat=scene.repeat,
                    flash=scene.flash,
                    keyboard_keybind = scene.keyboard_keybind,
                    song_keybind = scene.song_keybind,
                    game_event_keybind = scene.game_event_keybind,
                    events=[
                        self._context.DMXSceneEventDTO(
                            id=event.id,
                            name=event.name,
                            duration=event.duration,
                            updateDate=event.updateDate,
                            channels=[
                                {
                                    "fixture": channel.fixture,
                                    "channel": channel.channel,
                                    "value": channel.value
                                }
                                for channel in self._context.DMXSceneEventChannel.query.filter_by(eventID=event.id).all()
                            ]
                        )
                        for event in self._context.DMXSceneEvent.query.filter_by(sceneID=scene.id).all()
                    ]
                )

            return scene
    
    def __getValueForChannelSetting(self, fixtureType, channelName, settingName):
        try:
            return self.fixtureProfiles[fixtureType][channelName][settingName]
        except Exception as e:
            format.message(f"Error getting value: {e}", "error")
            return None
    
    def __processJSONDMXScenes(self):
        scenes = []
        
        if self.devMode == True:
            folder = os.getcwd() + "\\backend\\data\\DMXScenes\\"
        else:
            folder = os.getcwd() + "\\data\\DMXScenes\\"
        
        format.message(f"Searching for DMX scenes in {folder}", "info")

        with self.app.app_context():
            for (dirpath, dirnames, filenames) in walk(folder):
                format.message(f"Processing {len(filenames)} DMX scenes", "info")
                
                for filename in filenames:
                    if filename.endswith(".json") and "_processed" not in filename:
                        try:
                            with open(folder + filename) as json_file:
                                try:
                                    for scene in json.load(json_file):
                                        newDMXScene = self._context.DMXScene(
                                            name=str(filename).strip(".json"),
                                            createDate=datetime.datetime.now(),
                                            duration=scene["duration"],
                                            repeat=scene["repeat"],
                                            flash=scene["flash"],
                                            keyboard_keybind=scene["keyboardKeybind"],
                                            song_keybind=scene["songKeybind"],
                                            game_event_keybind=scene["gameEventKeybind"]
                                        )
                                        self._context.db.session.add(newDMXScene) 
                                        self._context.db.session.commit()
                                        
                                        for event in scene["events"]:
                                            duration = event["duration"]

                                            newDMXSceneEvent = self._context.DMXSceneEvent(
                                                sceneID=newDMXScene.id, 
                                                name=scene["name"], 
                                                updateDate=datetime.datetime.now(), 
                                                duration=duration
                                            )
                                            self._context.db.session.add(newDMXSceneEvent)
                                            self._context.db.session.commit()

                                            for channel in event["channels"]:
                                                for channel, value in channel.items():
                                                    if channel.lower() == "fixture":
                                                        fixture = value
                                                        continue

                                                    newDMXSceneEventChannel = self._context.DMXSceneEventChannel(
                                                        eventID=newDMXSceneEvent.id, 
                                                        fixture=fixture, 
                                                        channel=channel, 
                                                        value=value
                                                    )
                                                    self._context.db.session.add(newDMXSceneEventChannel)

                                        self._context.db.session.commit()

                                except Exception as e:
                                    format.message(f"Error processing DMX scene {filename}: {e}", "error")
                            
                            os.rename(folder + "\\" + filename, f"{folder}\\{filename.strip('.json')}_processed.json")
                            
                        except Exception as e:
                            format.message(f"Error opening DMX scene {filename}: {e}", "error")
                
            return scenes

    def __startScene(self, scene, stopEvent):   
        while not stopEvent.is_set():
            for event in scene.events:
                if stopEvent.is_set():
                    return 200
                for channel in event.channels:
                    try:
                        fixture_id = int(channel["fixture"])
                        fixture = self._dmx.get_fixture(fixture_id)
                    except ValueError:
                        fixture = self.getFixturesByName(channel["fixture"])[0]

                    fixture.set_channel(channel["channel"].lower(), int(channel["value"]))
                    
                    requests.post(
                        f'http://{self._localIp}:8080/sendMessage',
                        json={"message": {"channel": str(channel["channel"]).title(), "fixture": fixture.id, "value": int(channel["value"])}, "type": "UpdateDMXValue"}
                    )

                        
                if event.duration > 0:
                    time.sleep(event.duration / 1000)
            
            if scene.repeat == True:
                self.__startScene(scene, stopEvent)
                
        return 200
            
    # Config
    
    def enableWebInterface(self):
        try:
            self._dmx.web_control()
        except Exception as e:
            format.message(f"Error enabling web interface: {e}", "error")
        