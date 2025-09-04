import datetime
import json
import os
import socket
import threading
import time
from os import walk

import requests
from API.DB import context as dbContext
from API.Supervisor import Supervisor
from API.format import Format
from PyDMXControl.controllers import OpenDMXController
from PyDMXControl.profiles.Generic import Custom, Dimmer
from data.models import *
from flask import Flask
from flask_socketio import SocketIO

format = Format("DMX")
            
class dmx:
    def __init__(self, context : dbContext, supervisor : Supervisor, socket : SocketIO, app, devmode):
        self._dmx = None

        try:
            self._dmx : OpenDMXController = OpenDMXController()
        except Exception as e:            
            format.message(f"DMX controller not started, {e}", "error")
                
        self._context : dbContext = context
        self._supervisor : Supervisor = supervisor
        self.app : Flask = app
        self.socket : SocketIO = socket
        
        self._localIp = self.__getLocalIp()
        self.devMode = devmode

        self.runningScenes = {}
        # self.fixtures = {}
        self.scenes = {}
        self.fixtureGroups = {}
        self.fixtureProfiles = self._context.getFixtureProfiles()
        
        try:
            self.scenes = self.getDMXScenes()
        except Exception as e:
            format.message(f"Error processing DMX scenes: {e}", "error")
            
        self._supervisor.setDependencies(dmx=self)

    # Setters
    
    def checkForSongTriggers(self, songName):
        try:
            with self.app.app_context():
                scenes : list[DMXScene] = self._context.DMXScene.query.filter_by(song_keybind=songName).all()
                if len(scenes) > 0:
                    for scene in scenes:
                        self.startScene(scene.id)
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error checking for song triggers: {e}")
            ise.process = "DMX: Check For Song Triggers"
            ise.severity = "1"
            
            self._supervisor.logInternalServerError(ise)
    
    def __appendToFixtures(self, fixture, fixtureType):
        return
        # self.fixtures[fixture.name] = {"type": fixtureType, "id": fixture.id}

    def addFixtureToGroup(self, groupName, fixture):
        if groupName not in self.fixtureGroups:
            self.fixtureGroups[groupName] = []
            
        self.fixtureGroups[groupName].append(fixture)
        
        return self.fixtureGroups[groupName]
        
    def registerDimmerFixture(self, displayName):
        try:
            fixture = None
            try:
                fixture = self._dmx.add_fixture(Dimmer, name=displayName)
                setattr(self, displayName, fixture)
            except Exception as e:
                pass
            
            fixtureTypeId = self.getFixtureTypeIdFromName("dimmer")
            
            with self.app.app_context():
                patchedFixture : PatchedFixture = self._context.PatchedFixtures.query.filter_by(fixtureId=fixtureTypeId, dmxControllerFixtureId=(fixture.id if fixture != None else 0)).first()
                
                if patchedFixture == None:
                    self._context.db.session.add(PatchedFixture(
                        fixtureName = displayName,
                        fixtureId = fixtureTypeId,
                        dmxControllerFixtureId = fixture.id if fixture != None else 0,
                        dmxStartAddress = fixture.start_channel if fixture != None else 0,
                        dmxEndAddress= len(self.getFixtureTypeChannels(fixtureTypeId)) + (fixture.start_channel if fixture != None else 0) - 1,
                    ))

                    self._context.db.session.commit()
            
            return fixture
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error registering dimmer: {e}")
            ise.process = "DMX: Register Dimmer Fixture"
            ise.severity = "1"
            
            self._supervisor.logInternalServerError(ise)
            
            return None
    
    def registerCustomFixture(self, fixtureName, fixtureType, channels, startChannel):
        try:
            fixture = self._dmx.add_fixture(Custom(channels=channels, name=fixtureName, start_channel=startChannel))
            
            setattr(self, fixtureName, fixture)
        
            self.__appendToFixtures(fixture, fixtureType)
            
            return fixture
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error registering custom fixture: {e}")
            ise.process = "DMX: Register custom fixture"
            ise.severity = "1"
            
            self._supervisor.logInternalServerError(ise)
            return None
        
    def registerFixtureUsingType(self, displayName, fixtureType, startChannel):
        try:
            if str(fixtureType).lower() in self.fixtureProfiles:
                fixture = None
                try:
                    fixture = self._dmx.add_fixture(Custom(channels=0, start_channel=startChannel, name=displayName))
                    setattr(self, displayName, fixture)
                except Exception as e:
                    pass
                
                fixtureTypeId = self.getFixtureTypeIdFromName(fixtureType)
                
                with self.app.app_context():
                    patchedFixture : PatchedFixture = self._context.PatchedFixtures.query.filter_by(fixtureId=fixtureTypeId, dmxControllerFixtureId=(fixture.id if fixture != None else 0)).first()
                    
                    if patchedFixture == None:
                        self._context.db.session.add(PatchedFixture(
                            fixtureName = displayName,
                            fixtureId = fixtureTypeId,
                            dmxControllerFixtureId = fixture.id if fixture != None else 0,
                            dmxStartAddress = startChannel,
                            dmxEndAddress= len(self.getFixtureTypeChannels(fixtureTypeId)) + startChannel - 1,
                        ))

                        self._context.db.session.commit()
                
                try:
                    for channel in self.fixtureProfiles[fixtureType.lower()]:
                        fixture._register_channel(channel)
                except Exception as e:
                    pass
                
                return fixture
            
            return None
        
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error registering fixture using type '{fixtureType}': {e}")
            ise.process = "DMX: Register Fixture Using Type"
            ise.severity = "1"
            
            self._supervisor.logInternalServerError(ise)
            
            return
        
    def registerChannel(self, fixtureName, channelName):
        try:
            fixture = self._dmx.get_fixtures_by_name(fixtureName)[0]
            
            if fixture != None:
                fixture._register_channel(channelName)
            else:
                return LookupError(f"Fixture {fixtureName} not found")
            
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error registering channel '{channelName}': {e}")
            ise.process = "DMX: Register Channel"
            ise.severity = "1"
            
        self._supervisor.logInternalServerError(ise)
        
    def getFixtureTypeChannels(self, fixtureTypeId):
        try:
            fixture = None
            
            with self.app.app_context():
                fixture = self._context.Fixture.query.filter_by(id=fixtureTypeId).first()
                
                if not fixture:
                    return []
                
                fixtureChannels = self._context.FixtureChannel.query.filter_by(fixtureID=fixture.id).all()
                return fixtureChannels
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error getting fixture type addresses from id '{fixtureTypeId}': {e}")
            ise.process = "DMX: Get Fixture Type Addresses"
            ise.severity = "2"
            
            self._supervisor.logInternalServerError(ise)
            
            return 0
        
    def getFixtureTypeIdFromName(self, fixtureTypeName) -> int:
        try:
            fixture = None
            
            with self.app.app_context():
                fixture = self._context.Fixture.query.filter_by(name=fixtureTypeName).first()
                
                if fixture != None:
                    return fixture.id
                else:
                    return 0
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error getting fixture type id from name '{fixtureTypeName}': {e}")
            ise.process = "DMX: Get Fixture Type Id From Name"
            ise.severity = "2"
            
            self._supervisor.logInternalServerError(ise)
            
            return 0
        
    def setFixtureChannel(self, fixtureName, channelName, value) -> int:
        try:
            if (self._dmx == None or self.isConnected() == False):
                return -1
            
            try:
                fixture = self._dmx.get_fixture(int(fixtureName))
            except Exception as e:
                fixture = self._dmx.get_fixtures_by_name(fixtureName)[0]
            
            if fixture != None:
                fixture.set_channel(channelName.lower(), int(value))
                
                return int(value)
            else:
                return LookupError(f"Fixture {fixtureName} not found")
            
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error setting channel '{fixtureName}-{channelName}' to value '{value}': {e}")
            ise.process = "DMX: Set Channel Value"
            ise.severity = "2"
            
            self._supervisor.logInternalServerError(ise)
            
    def startScene(self, sceneId):
        scene = self.getDMXSceneById(sceneId)
        
        for thread in threading.enumerate():
            if thread.name == f"DMXScene Running - {sceneId}":
                try:
                    thread, stopEvent = self.runningScenes[sceneId]
                except KeyError:
                    continue
                stopEvent.set() 
                del self.runningScenes[sceneId]
                format.message(f"Scene {sceneId} started", "info")
        
        if scene != None:
            stopEvent = threading.Event()
            thread = threading.Thread(target=self.__startScene, args=(scene,stopEvent))
            thread.name = f"DMXScene Running - {sceneId}"
            self.runningScenes[sceneId] = (thread, stopEvent)
            thread.start()
            
            return
        else:
            return
            
    def stopScene(self, sceneId):
        for thread in threading.enumerate():
            if thread.name == f"DMXScene Running - {sceneId}":
                try:
                    thread, stopEvent = self.runningScenes[sceneId]
                except KeyError:
                    thread.join()
                    return
                
                stopEvent.set() 
                format.message(f"Scene {sceneId} stopped", "info")
                
                response = requests.post(
                    f'http://{self._localIp}:8080/sendMessage',
                    json={
                        'message': {"sceneId": sceneId},
                        'type': "dmxSceneStopped"
                    }
                )
                
                return
            
        return
    
    def createNewScene(self, DMXScene):
        try:
            with self.app.app_context():
                self._context.db.session.add(DMXScene)
                self._context.db.session.commit()

                self._context.db.session.refresh(DMXScene)
                return DMXScene
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error Creating New Scene '{DMXScene}': {e}")
            ise.process = "DMX: Create New Scene"
            ise.severity = "2"
            
            self._supervisor.logInternalServerError(ise)
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
                
                self._context.db.session.commit()
                return event

        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error updating fixture channel event Id: '{sceneEventID}' Channel: '{fixture}-{channel}' to value '{value}': {e}")
            ise.process = "DMX: Register Dimmer Fixture"
            ise.severity = "2"
            
            self._supervisor.logInternalServerError(ise)
            return None
        
    def turnOffAllChannels(self):
        try:
            if (self._dmx == None or self.isConnected() == False):
                return
            
            fixtures = self.getRegisteredFixtures()
            
            for fixture in fixtures.items():
                fixtureName = fixture[0]
                fixtureType = fixture[1]["type"]
                fixtureProfile = (self.getFixtureProfiles()).get(fixtureType)
                
                for channel in fixtureProfile.items():
                    self.setFixtureChannel(fixtureName, channel[0], 0)
                    
            return
        
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error turning off all channels: {e}")
            ise.process = "DMX: Turn Off All Channels"
            ise.severity = "2"
            
            self._supervisor.logInternalServerError(ise)
            
            return
    
    def createNewSceneEvent(self, sceneId):
        try:
            newSceneEvent = self._context.DMXSceneEvent(
                name="New Event", 
                duration=0, 
                updateDate=datetime.now(), 
                sceneID=sceneId)
            
            self._context.db.session.add(newSceneEvent)
            self._context.db.session.commit()
            
            return newSceneEvent
        
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error creating new scene event for scene Id: '{sceneId}': {e}")
            ise.process = "DMX: Create New Scene Event"
            ise.severity = "2"
            
            self._supervisor.logInternalServerError(ise)
            
            return None
        
    def resetConnection(self) -> bool:
        if self._dmx != None:
            self._dmx.close()
        self._dmx = None
        try:
            self._dmx : OpenDMXController = OpenDMXController()       
        except Exception as e:            
            raise
        
        self._supervisor.setDependencies(dmx=self)
        
        return True
    
    # Getters
    
    def isConnected(self) -> bool:
        try:
            return (not self._dmx == None) or self.devMode == True
        except:
            return False
        
    def getFixtureProfiles(self):
        return self.fixtureProfiles
    def getFixtures(self):
        Fixtures = []
        try:
            with self.app.app_context():
                registeredFixtures : list[PatchedFixture] = self._context.PatchedFixtures.query.order_by(PatchedFixture.dmxStartAddress).all()
                
                for registeredFixture in registeredFixtures:            
                    fixture : Fixture = self._context.Fixture.query.filter_by(id = registeredFixture.fixtureId).first()
                    
                    if (registeredFixture.dmxControllerFixtureId == 0):
                        fixtureDTO = self.__mapToFixtureDTO(fixture, registeredFixture.id)
                        fixtureDict = fixtureDTO[0].to_dict()
                        Fixtures.append({"fixture": fixtureDict, "name": registeredFixture.fixtureName, "id": registeredFixture.id, "channels": str(registeredFixture.dmxStartAddress) + "->" + str(registeredFixture.dmxEndAddress) + f" ({str(registeredFixture.dmxEndAddress - registeredFixture.dmxStartAddress)})"})
                    else:
                        DMXFixture = self.getFixtureById(registeredFixture.dmxControllerFixtureId)
                        
                        fixtureDTO = self.__mapToFixtureDTO(fixture, registeredFixture.id)
                        fixtureDict = fixtureDTO[0].to_dict()
                        Fixtures.append({"fixture": fixtureDict, "name": registeredFixture.fixtureName, "id": registeredFixture.id, "channels": DMXFixture.channel_usage})
                        
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error getting fixtures: {e}")
            ise.process = "DMX: Get All Fixtures"
            ise.severity = "1"
            
            self._supervisor.logInternalServerError(ise)
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
    def getFixtureById(self, fixtureId):
        try:
            fixture = self._dmx.get_fixture(fixtureId)
            return fixture
        except Exception as e:
            return None
    def getDMXScenes(self):
        try:
            self.__processJSONDMXScenes()
            DMXScenes = []
            
            with self.app.app_context():
                scenes = self._context.DMXScene.query.all()

                for scene in scenes:
                    DMXScenes += self.__mapToDMXSceneDTO(scene)
            
            return DMXScenes
        except Exception as e:
            ise : InternalServerError = InternalServerError()
                
            ise.service = "dmx"
            ise.exception_message = str(f"Error getting DMX scenes: {e}")
            ise.process = "DMX: Get All DMX Scenes"
            ise.severity = "1"
            
            self._supervisor.logInternalServerError(ise)
            
            return []
        
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
                id=fixture.id,
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
        
        #format.message(f"Searching for DMX scenes in {folder}", "info")

        with self.app.app_context():
            for (dirpath, dirnames, filenames) in walk(folder):
                #format.message(f"Processing {len(filenames)} DMX scenes", "info")
                
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
                                            keyboard_keybind=scene["keyboard_Keybind"],
                                            song_keybind=scene["song_Keybind"],
                                            game_event_keybind=scene["game_Event_Keybind"]
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
                                    ise : InternalServerError = InternalServerError()
                
                                    ise.service = "dmx"
                                    ise.exception_message = str(f"Error processing DMX JSON scene '{filename}': {e}")
                                    ise.process = "DMX: Process JSON DMX Scenes"
                                    ise.severity = "2"
                                    
                                    self._supervisor.logInternalServerError(ise)
                            
                            os.rename(folder + "\\" + filename, f"{folder}\\{filename.strip('.json')}_processed.json")
                            
                        except Exception as e:
                            ise : InternalServerError = InternalServerError()
                
                            ise.service = "dmx"
                            ise.exception_message = str(f"Error opening JSON DMX Scene: {e}")
                            ise.process = "DMX: Process JSON DMX Scenes"
                            ise.severity = "3"
                            
                            self._supervisor.logInternalServerError(ise)
                
            return scenes

    def __startScene(self, scene : DMXScene, stopEvent):  
        try:
            if not self.isConnected():
                return 200
            
            if len(scene.events) == 0:
                return 200
            
            self.socket.emit(
                'dmxSceneStarted',
                {"message": f"Scene '{scene.name}' started", "scene": self.getDMXSceneById(scene.id).to_dict()} #,
            )
            
            while not stopEvent.is_set():
                for event in scene.events:
                    if stopEvent.is_set():
                        del self.runningScenes[str(scene.id)]
                        self.turnOffAllChannels()
                        
                        self.socket.emit(
                            'dmxSceneStopped',
                            {"message": {'sceneId': scene.id}},
                        )
                        
                        return 200
                    if scene.duration == 0:
                        self.socket.emit(
                            'dmxSceneStopped',
                            {'sceneId': scene.id},
                        )
                        
                        return
                    for channel in event.channels:
                        if self._dmx != None:
                            try:
                                fixture_id = int(channel["fixture"])
                                fixture = self._dmx.get_fixture(fixture_id)
                            except ValueError:
                                fixture = self.getFixturesByName(channel["fixture"])[0]
                            except Exception as e:
                                format.message(f"Error getting fixture: {e}", "error")
                                continue
                            
                            fixture.set_channel(channel["channel"].lower(), int(channel["value"]))
                            
                            self.socket.emit(
                                'UpdateDMXValue',
                                {"message": {"channel": str(channel["channel"]).title(), "fixture": fixture.id, "value": int(channel["value"])}},
                            )
                    if event.duration > 0:
                        time.sleep(event.duration / 1000)
                
                if scene.repeat == True:
                    with self.app.app_context():
                        foundScene : DMXScene = self.getDMXSceneById(scene.id)
                        if foundScene.repeat == False:
                            self.socket.emit(
                                'dmxSceneStopped',
                                {"message": {'sceneId': scene.id}},
                            )
            
                            return 200
                
                if scene.repeat == True:
                    self.__startScene(scene, stopEvent)
                else:
                    self.socket.emit(
                        'dmxSceneStopped',
                        {"message": {'sceneId': scene.id}},
                    )

                    return 200
                    
            return 200
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            
            ise.service = "dmx"
            ise.exception_message = str(f"Error starting scene: {e}")
            ise.process = "DMX: Running Scene"
            ise.severity = "1"
            
            self._supervisor.logInternalServerError(ise)
            
    # Config
    
    def enableWebInterface(self):
        try:
            self._dmx.web_control()
        except Exception as e:
            format.message(f"Error enabling web interface: {e}", "error")
        