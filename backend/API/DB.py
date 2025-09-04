from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_migrate import Migrate
import os, datetime

from data.models import *
from API.format import Format
from API.Supervisor import Supervisor

f = Format("DBContext")
class context:
    def __init__(self, app: Flask, db: SQLAlchemy):
        self.app = app
        self._supervisor = None
        self.db = db
        
        self.Gun = Gun
        self.Player = Player
        self.Game = Game
        self.Team = Team
        self.GamePlayer = GamePlayer
        self.DMXScene = DMXScene
        self.DMXSceneEvent = DMXSceneEvent
        self.DMXSceneEventChannel = DMXSceneEventChannel
        self.Fixture = Fixture
        self.FixtureChannel = FixtureChannel
        self.FixtureChannelValue = FixtureChannelValue
        self.PatchedFixtures = PatchedFixture
        self.InternalServerError = InternalServerError
        self.SystemControls = SystemControls
        self.Permission = Permission
        self.User = User

        self.fixtureProfiles = {
                "dimmer": {
                    "Dimmer": list(range(0, 255)),
                },
                "colorspot575xt": {
                    "Pan": list(range(0, 255)),
                    "Tilt": list(range(0, 255)),
                    "Pan_Fine": list(range(0, 255)),
                    "Tilt_Fine": list(range(0, 255)),
                    "PanTilt_Speed": {},
                    "FanLamp_Control": {},
                    "Colour_1": {
                    "White": 0,
                    "Light_blue": 13,
                    "Red": 26,
                    "Blue": 38,
                    "Light_green": 51,
                    "Yellow": 64,
                    "Magenta": 77,
                    "Cyan": 90,
                    "Green": 102,
                    "Orange": 115,
                    "Rainbow": list(range(128, 255)),
                    },
                    "Colour_2": {
                    "White": 0,
                    "Deep_Red": 12,
                    "Deep_Blue": 24,
                    "Pink": 36,
                    "Cyan": 48,
                    "Magenta": 60,
                    "Yellow": 72,
                    "5600K_Filter": 84,
                    "3200K_Filter": 96,
                    "UV": 108
                    },
                    "Prism": {
                    "Open": 0,
                    "Rotation": list(range(1, 127)),
                    },
                    "Macros": {},
                    "Gobos": {
                    "Open": list(range(0, 7)),
                    "1": list(range(8, 15)), 
                    "2": list(range(16, 23)), 
                    "3": list(range(24, 31)), 
                    "4": list(range(32, 39)), 
                    "5": list(range(40, 47)), 
                    "6": list(range(48, 55)), 
                    "7": list(range(56, 63)), 
                    "8": list(range(64, 71)), 
                    "9": list(range(72, 79)), 
                    "1_Shaking": list(range(80, 95)), 
                    "2_Shaking": list(range(96, 111)), 
                    "3_Shaking": list(range(112, 127)), 
                    "4_Shaking": list(range(128, 143)), 
                    "5_Shaking": list(range(144, 159)), 
                    "6_Shaking": list(range(160, 175)), 
                    "7_Shaking": list(range(176, 191)), 
                    "8_Shaking": list(range(192, 207)), 
                    "9_Shaking": list(range(208, 223)), 
                    "Rotation_Slow_Fast": list(range(224, 255)), 
                    },
                    "Rotating_Gobos": {    
                    "Open": list(range(0, 31)),
                    "1": list(range(32, 63)), 
                    "2": list(range(64, 95)), 
                    "3": list(range(96, 127)), 
                    "4": list(range(128, 159)), 
                    "5": list(range(160, 191)), 
                    "6": list(range(192, 223)), 
                    "Rotation_Slow_Fast": list(range(224, 255)), 
                    },
                    "Rotation_Speed": {
                    "Indexing": list(range(0, 127)),    
                    "Rotation": list(range(128, 255)),    
                    },
                    "Iris": {
                    "Open": 0,
                    "MaxToMin": list(range(1, 179)),   
                    "Closed": list(range(180, 191)),   
                    "Pulse_Close_Slow_Fast": list(range(192, 223)),   
                    "Pulse_Open_Fast_Slow": list(range(224, 225)),   
                    },
                    "Focus": list(range(0, 255)),
                    "Strobe_Shutter": {
                    "Closed": list(range(0, 32)),   
                    "Open": list(range(32, 63)),   
                    "Strobe_Slow_Fast": list(range(64, 95)),   
                    "Pulse_Slow_Fast": list(range(128, 159)),   
                    "Random_Slow_Fast": list(range(192, 223)),   
                    },
                    "Dimmer": list(range(0, 255)),
                },
                "colorspot250at": {
                    "Pan": list(range(0, 255)),
                    "Pan_Fine": list(range(0, 255)),
                    "Tilt": list(range(0, 255)),
                    "Tilt_Fine": list(range(0, 255)),
                    "Pan_Tilt_Speed": {
                    "Max": 0,
                    "Speed": list(range(1, 255)),
                    },
                    "Special_Functions": {},
                    "Pan_Tilt_Macros": {},
                    "Pan_Tilt_Macros_Speed": {},
                    "Colour_1": {
                    "White": 0,
                    "Dark_Green": 11,
                    "Red": 23,
                    "Light_Azure": 34,
                    "Magenta": 46,
                    "UV filter": 58,
                    "Yellow": 70,
                    "Green": 81,
                    "Pink": 93,
                    "Blue": 105,
                    "Deep red": 117,
                    "Rotation": list(range(190, 243)),
                    "Audio": list(range(224, 249)),
                    "Random_Fast_Slow": list(range(250, 255)),
                    },
                    "Colour_Fine_Position": list(range(0, 255)),
                    "Gobos": {
                    "Open": list(range(0, 3)),
                    "1": list(range(4, 7)),   
                    "2": list(range(8, 11)),   
                    "3": list(range(12, 15)),   
                    "4": list(range(16, 19)),   
                    "5": list(range(20, 23)),   
                    "6": list(range(24, 27)),   
                    "7": list(range(28, 31)),   
                    "1_Rotating": list(range(32, 35)),
                    "2_Rotating": list(range(36, 39)),
                    "3_Rotating": list(range(40, 43)),
                    "4_Rotating": list(range(44, 47)),
                    "5_Rotating": list(range(48, 51)),
                    "6_Rotating": list(range(52, 55)),
                    "7_Rotating": list(range(56, 59)),
                    "1_Shaking_Slow_Fast": list(range(60, 69)),
                    "2_Shaking_Slow_Fast": list(range(70, 79)),
                    "3_Shaking_Slow_Fast": list(range(80, 89)),
                    "4_Shaking_Slow_Fast": list(range(90, 99)),
                    "5_Shaking_Slow_Fast": list(range(100, 109)),
                    "6_Shaking_Slow_Fast": list(range(110, 119)),
                    "7_Shaking_Slow_Fast": list(range(120, 139)),
                    "1_Shaking_Fast_Slow": list(range(130, 139)),
                    "2_Shaking_Fast_Slow": list(range(140, 149)),
                    "3_Shaking_Fast_Slow": list(range(150, 159)),
                    "4_Shaking_Fast_Slow": list(range(160, 169)),
                    "5_Shaking_Fast_Slow": list(range(170, 179)),
                    "6_Shaking_Fast_Slow": list(range(180, 189)),
                    "7_Shaking_Fast_Slow": list(range(190, 199)),
                    "Rotation": list(range(202, 243)),
                    "Audio": list(range(244, 249)),
                    "Random_Fast_Slow": list(range(250, 255)),
                    },
                    "Gobo_Rotation_Speed": {
                    "No_Rotation": 0,
                    "Rotation": list(range(1, 255)),  
                    },
                    "Gobo_Fine_Position": list(range(0, 255)),
                    "Prism": {
                    "Open_Position_Hole": list(range(0, 19)),
                    "3_Facet": list(range(20, 159)),
                    "Macro_1": list(range(160, 167)),
                    "Macro_2": list(range(168, 175)),
                    "Macro_3": list(range(176, 183)),
                    "Macro_4": list(range(184, 191)),
                    "Macro_5": list(range(192, 199)),
                    "Macro_6": list(range(200, 207)),
                    "Macro_7": list(range(208, 215)),
                    "Macro_8": list(range(216, 223)),
                    "Macro_9": list(range(224, 231)),
                    "Macro_10": list(range(232, 239)),
                    "Macro_11": list(range(240, 247)),
                    "Macro_12": list(range(248, 255)),
                    },
                    "Prism_Rotation": {
                    "No_Rotation": 0,
                    "Rotation": list(range(1, 255)), 
                    },
                    "Focus": list(range(1, 255)),
                    "Focus_Fine": list(range(1, 255)),
                    "Shutter": {
                    "Closed": list(range(0, 31)),
                    "Open": list(range(32, 63)),
                    "Strobe_Slow_Fast": list(range(64, 95)),
                    "Pulse_Slow_Fast": list(range(128, 143)),
                    "Pulse_Fast_Slow": list(range(144, 159)),
                    "Random_Slow_Fast": list(range(192, 223)),
                    },
                    "Dimmer": list(range(0, 255)),
                    "Dimmer_Fine": list(range(0, 255)),
                },
                "colorwash250at": {
                    "Pan": list(range(0, 255)),
                    "Pan_Fine": list(range(0, 255)),
                    "Tilt": list(range(0, 255)),
                    "Tilt_Fine": list(range(0, 255)),
                    "Pan_Tilt_Speed": {
                    "Max": 0,
                    "Speed": list(range(1, 255)),
                    },
                    "Special_Functions": {},
                    "Pan_Tilt_Macros": {},
                    "Pan_Tilt_Macros_Speed": {},
                    "Colour_1": {
                    "White": 0,
                    "Red": 18,
                    "Blue": 36,
                    "Green": 54,
                    "3200K_Filter": 72,
                    "6000K_Filter": 90,
                    "UV": list(range(190, 243)),
                    "Audio": list(range(244, 249)),
                    "Random_Fast_Slow": list(range(250, 255)),
                    },
                    "Colour_Fine_Position": list(range(0, 255)),
                    "Cyan": list(range(0, 255)),
                    "Magenta": list(range(0, 255)),
                    "Yellow": list(range(0, 255)),
                    "CMY_Dimmer_Speed": list(range(0, 255)),
                    "CMY_Macros": {
                    "Open": list(range(0, 7)),
                    "Rainbow_Fast_Slow": list(range(240, 243)),
                    "Audio": list(range(244, 249)),
                    "Random_Fast_Slow": list(range(250, 255)),
                    },
                    "Effect_Wheel": {
                    "Open": list(range(0, 70)),  
                    "Beam_Shaper": list(range(71, 179)),  
                    "Swivelling_Slow_Fast": list(range(180, 199)),  
                    "Frost": list(range(200, 255)),  
                    },
                    "Zoom": list(range(0, 255)),
                    "Shutter": {
                    "Closed": list(range(0, 31)),
                    "Open": list(range(32, 63)),
                    "Strobe_Slow_Fast": list(range(64, 95)),
                    "Opening_Pulse_Slow_Fast": list(range(128, 143)),
                    "Closing_Pulse_Fast_Slow": list(range(144, 159)),
                    "Random": list(range(192, 223)),
                    },
                    "Dimmer": list(range(0, 255)),
                    "Dimmer_Fine": list(range(0, 255)),
                }
            }

        self.__createDatabase()

    def getFixtureProfiles(self):
        return self.fixtureProfiles
    
    def getAllGames(self) -> list[Game]:
        with self.app.app_context():
            return self.Game.query.all()
    
    def __createDatabase(self):
        self.__createModels()
        self.__seedDBData()
        
    def setSupervisor(self, supervisor : Supervisor):
        self._supervisor = supervisor
        
    def __createModels(self):
        return
        #migrate = Migrate(self.app, self.db)
        
        # self.db.Model.metadata.create_all(bind=self.db.engine)
        
        # self.db.create_all()

    def __seedDBData(self):
        try:
            with self.app.app_context():
                if not self.Permission.query.first():
                    self.Insert(self.Permission(name="Admin", isActive=True))
                    self.SaveChanges()

                if not self.User.query.first():
                    self.Insert(self.User(username="Admin", password="1234", createDate=datetime.now(), isActive=True))
                    self.SaveChanges()

                if not self.Gun.query.first() and not self.Player.query.first():
                    f.message("Empty DB Found! Seeding Data....", type="warning")
                    
                    self.Insert(self.Gun(name="Alpha", defaultColor="Red"))
                    self.Insert(self.Gun(name="Apollo", defaultColor="Red"))
                    self.Insert(self.Gun(name="Chaos", defaultColor="Red"))
                    self.Insert(self.Gun(name="Cipher", defaultColor="Red"))
                    self.Insert(self.Gun(name="Cobra", defaultColor="Red"))
                    self.Insert(self.Gun(name="Comet", defaultColor="Red"))
                    self.Insert(self.Gun(name="Commander", defaultColor="Red"))
                    self.Insert(self.Gun(name="Cyborg", defaultColor="Red"))
                    self.Insert(self.Gun(name="Cyclone", defaultColor="Red"))
                    self.Insert(self.Gun(name="Delta", defaultColor="Red"))
                    self.Insert(self.Gun(name="Dodger", defaultColor="Green"))
                    self.Insert(self.Gun(name="Dragon", defaultColor="Green"))
                    self.Insert(self.Gun(name="Eagle", defaultColor="Green"))
                    self.Insert(self.Gun(name="Eliminator", defaultColor="Green"))
                    self.Insert(self.Gun(name="Elite", defaultColor="Green"))
                    self.Insert(self.Gun(name="Falcon", defaultColor="Green"))
                    self.Insert(self.Gun(name="Ghost", defaultColor="Green"))
                    self.Insert(self.Gun(name="Gladiator", defaultColor="Green"))
                    self.Insert(self.Gun(name="Hawk", defaultColor="Green"))
                    self.Insert(self.Gun(name="Hyper", defaultColor="Green"))
                    self.Insert(self.Gun(name="Inferno", defaultColor="Green"))
                    
                    self.Insert(self.SystemControls(name="isInitialised", value=0))
                    
                    with self.app.app_context():
                        for fixture_name, channels in self.fixtureProfiles.items():
                            fixture = self.Fixture(name=fixture_name, noOfchannels=len(channels))
                            self.db.session.add(fixture)
                            self.db.session.flush()  

                            for index, (channelName, values) in enumerate(channels.items()):
                                channel = self.FixtureChannel(fixtureID=fixture.id, channelNo=index + 1, name=channelName)
                                self.db.session.add(channel)
                                self.db.session.flush() 

                                if isinstance(values, dict):
                                    for valueName, valueRange in values.items():
                                        if isinstance(valueRange, list):
                                            for val in valueRange:
                                                value_entry = self.FixtureChannelValue(channelID=channel.id, value=val, name=valueName)
                                                self.db.session.add(value_entry)
                                        else:
                                            value_entry = self.FixtureChannelValue(channelID=channel.id, value=valueRange, name=valueName)
                                            self.db.session.add(value_entry)
                                elif isinstance(values, list):
                                    for val in values:
                                        value_entry = self.FixtureChannelValue(channelID=channel.id, value=val, name=str(val))
                                        self.db.session.add(value_entry)
                            self.db.session.commit()  

                    self.SaveChanges()
                    
                    f.message("Data seeded successfully", type="success")
        except Exception as e:
            f.message(f"Error occurred when seeding data: {str(e)}", type="error")
            pass
    
    def Insert(self, object):
        with self.app.app_context():
            self.db.session.add(object)
            self.db.session.commit()
        
    def InsertMany(self, objects):
        with self.app.app_context():
            self.db.session.add_all(objects) 
            self.SaveChanges()

    def SaveChanges(self):
        with self.app.app_context():
            try:
                self.db.session.commit()
                # f.message("Changes committed.", type="success")
            except Exception as e:
                self.db.session.rollback()
                
    def createNewGame(self):
        try:
            with self.app.app_context():
                newGame = self.Game(
                    name=f"Game_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
                    startTime=datetime.now(),
                )
                self.db.session.add(newGame)
                self.db.session.commit()
                
                #f.message(f"Created new game with ID: {newGame.id}", type="success")
                return newGame.id
                
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            ise.service = "db"
            ise.exception_message = str(e)
            ise.process = "Create New Game"
            ise.severity = 2
            
            self._supervisor.logInternalServerError(ise)
            return None  
        
    def addGamePlayer(self, player : GamePlayer):
        try:
            with self.app.app_context():
                self.db.session.add(player)
                self.db.session.commit()
                
                #f.message(f"Created new game with ID: {newGame.id}", type="success")
                return player.id
                
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            ise.service = "db"
            ise.exception_message.message = str(e)
            ise.process = "Add Game Player"
            ise.severity = 2
            
            self._supervisor.logInternalServerError(ise)
            return None  
    
    def updateGame(self, gameId, **kwargs):
        try:
            with self.app.app_context():
                game = self.Game.query.get(gameId)
                
                if game:
                    for key, value in kwargs.items():
                        setattr(game, key, value)
                    self.db.session.commit()
                    
                    return game
                else:
                    f.message(f"Game with ID {gameId} not found", type="error")
                    return None
        
        except Exception as e:
            ise : InternalServerError = InternalServerError()
            ise.service = "db"
            ise.exception_message = str(e)
            ise.process = "Update Game"
            ise.severity = 2
            
            self._supervisor.logInternalServerError(ise)
            return None
            
    class DMXSceneDTO:
        def __init__(self, id, name, duration, updateDate, createDate, repeat, flash, keyboard_keybind, song_keybind, game_event_keybind, events):
            self.id = id
            self.name = name
            self.duration = duration
            self.updateDate = updateDate    
            self.createDate = createDate
            self.repeat = repeat
            self.flash = flash
            self.keyboard_keybind = keyboard_keybind
            self.song_keybind = song_keybind
            self.game_event_keybind = game_event_keybind
            self.events = events
        
        def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "duration": self.duration,
                "updateDate": self.updateDate.isoformat() if self.updateDate else None,
                "createDate": self.createDate.isoformat() if self.createDate else None,
                "repeat": self.repeat,
                "flash": self.flash,
                "keyboard_keybind": self.keyboard_keybind,
                "song_keybind": self.song_keybind,
                "game_event_keybind": self.game_event_keybind,
                "events": [event.to_dict() for event in self.events]
            }
            
    class DMXSceneEventDTO:
        def __init__(self, id, name, duration, updateDate, channels):
            self.id = id
            self.name = name
            self.duration = duration
            self.updateDate = updateDate
            self.channels = channels
        
        def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "duration": self.duration,
                "updateDate": self.updateDate.isoformat() if self.updateDate else None,
                "channels": self.channels
            }
    
    class FixtureDTO:
        def __init__(self, id, name, noOfchannels, mode, notes, icon, channels):
            self.id = id
            self.name = name
            self.noOfchannels = noOfchannels
            self.mode = mode
            self.notes = notes
            self.icon = icon
            self.channels = channels
        
        def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "noOfchannels": self.noOfchannels,
                "mode": self.mode,
                "notes": self.notes,
                "icon": self.icon,
                "channels": [channel.to_dict() for channel in self.channels]
            }
    
    class FixtureChannelDTO:
        def __init__(self, id, fixtureID, channelNo, name, description, icon, channelValues):
            self.id = id
            self.fixtureID = fixtureID
            self.channelNo = channelNo
            self.name = name
            self.description = description
            self.icon = icon
            self.channelValues = channelValues
        
        def to_dict(self):
            return {
                "id": self.id,
                "fixtureID": self.fixtureID,
                "channelNo": self.channelNo,
                "name": self.name,
                "description": self.description,
                "icon": self.icon,
                "channelValues": self.channelValues #[channelValue.to_dict() for channelValue in self.channelValues]
            }