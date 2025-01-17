from flask_sqlalchemy import SQLAlchemy
import os

from func.format import message

class context:
    def __init__(self, app):
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath('Scoreboard.db')}"
        
        self.db = SQLAlchemy(app)
        self.app = app
        
        self.Gun = None
        self.Player = None
        self.Game = None
        self.Team = None
        self.GamePlayers = None
        self.DMXScene = None
        self.DMXSceneEvent = None
        self.DMXSceneEventChannel = None
        
        self.fixtureProfiles = {
                "Dimmer": {
                    "Dimmer": list(range(0, 255)),
                },
                "Colorspot575XT": {
                    "Pan": list(range(0, 255)),
                    "Tilt": list(range(0, 255)),
                    "Pan Fine": list(range(0, 255)),
                    "Tilt Fine": list(range(0, 255)),
                    "PanTilt Speed": {},
                    "FanLamp Control": {},
                    "Colour 1": {
                    "White": 0,
                    "Light blue": 13,
                    "Red": 26,
                    "Blue": 38,
                    "Light green": 51,
                    "Yellow": 64,
                    "Magenta": 77,
                    "Cyan": 90,
                    "Green": 102,
                    "Orange": 115,
                    "Rainbow": list(range(128, 255)),
                    },
                    "Colour 2": {
                    "White": 0,
                    "Deep Red": 12,
                    "Deep Blue": 24,
                    "Pink": 36,
                    "Cyan": 48,
                    "Magenta": 60,
                    "Yellow": 72,
                    "5600K Filter": 84,
                    "3200K Filter": 96,
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
                    "1 Shaking": list(range(80, 95)), 
                    "2 Shaking": list(range(96, 111)), 
                    "3 Shaking": list(range(112, 127)), 
                    "4 Shaking": list(range(128, 143)), 
                    "5 Shaking": list(range(144, 159)), 
                    "6 Shaking": list(range(160, 175)), 
                    "7 Shaking": list(range(176, 191)), 
                    "8 Shaking": list(range(192, 207)), 
                    "9 Shaking": list(range(208, 223)), 
                    "Rotation Slow Fast": list(range(224, 255)), 
                    },
                    "Rotating Gobos": {    
                    "Open": list(range(0, 31)),
                    "1": list(range(32, 63)), 
                    "2": list(range(64, 95)), 
                    "3": list(range(96, 127)), 
                    "4": list(range(128, 159)), 
                    "5": list(range(160, 191)), 
                    "6": list(range(192, 223)), 
                    "Rotation Slow Fast": list(range(224, 255)), 
                    },
                    "Rotation Speed": {
                    "Indexing": list(range(0, 127)),    
                    "Rotation": list(range(128, 255)),    
                    },
                    "Iris": {
                    "Open": 0,
                    "MaxToMin": list(range(1, 179)),   
                    "Closed": list(range(180, 191)),   
                    "Pulse Close Slow Fast": list(range(192, 223)),   
                    "Pulse Open Fast Slow": list(range(224, 225)),   
                    },
                    "Focus": list(range(0, 255)),
                    "Strobe / Shutter": {
                    "Closed": list(range(0, 32)),   
                    "Open": list(range(32, 63)),   
                    "Strobe Slow Fast": list(range(64, 95)),   
                    "Pulse Slow Fast": list(range(128, 159)),   
                    "Random Slow Fast": list(range(192, 223)),   
                    },
                    "Dimmer": list(range(0, 255)),
                },
                "Colorspot250AT": {
                    "Pan": list(range(0, 255)),
                    "Pan Fine": list(range(0, 255)),
                    "Tilt": list(range(0, 255)),
                    "Tilt Fine": list(range(0, 255)),
                    "Pan Tilt Speed": {
                    "Max": 0,
                    "Speed": list(range(1, 255)),
                    },
                    "Special Functions": {},
                    "Pan Tilt Macros": {},
                    "Pan Tilt Macros Speed": {},
                    "Colour 1": {
                    "White": 0,
                    "Dark green": 11,
                    "Red": 23,
                    "Light azure": 34,
                    "Magenta": 46,
                    "UV filter": 58,
                    "Yellow": 70,
                    "Green": 81,
                    "Pink": 93,
                    "Blue": 105,
                    "Deep red": 117,
                    "Rotation": list(range(190, 243)),
                    "Audio": list(range(224, 249)),
                    "Random Fast Slow": list(range(250, 255)),
                    },
                    "Colour Fine Position": list(range(0, 255)),
                    "Gobos": {
                    "Open": list(range(0, 3)),
                    "1": list(range(4, 7)),   
                    "2": list(range(8, 11)),   
                    "3": list(range(12, 15)),   
                    "4": list(range(16, 19)),   
                    "5": list(range(20, 23)),   
                    "6": list(range(24, 27)),   
                    "7": list(range(28, 31)),   
                    "1 Rotating": list(range(32, 35)),
                    "2 Rotating": list(range(36, 39)),
                    "3 Rotating": list(range(40, 43)),
                    "4 Rotating": list(range(44, 47)),
                    "5 Rotating": list(range(48, 51)),
                    "6 Rotating": list(range(52, 55)),
                    "7 Rotating": list(range(56, 59)),
                    "1 Shaking Slow Fast": list(range(60, 69)),
                    "2 Shaking Slow Fast": list(range(70, 79)),
                    "3 Shaking Slow Fast": list(range(80, 89)),
                    "4 Shaking Slow Fast": list(range(90, 99)),
                    "5 Shaking Slow Fast": list(range(100, 109)),
                    "6 Shaking Slow Fast": list(range(110, 119)),
                    "7 Shaking Slow Fast": list(range(120, 139)),
                    "1 Shaking Fast Slow": list(range(130, 139)),
                    "2 Shaking Fast Slow": list(range(140, 149)),
                    "3 Shaking Fast Slow": list(range(150, 159)),
                    "4 Shaking Fast Slow": list(range(160, 169)),
                    "5 Shaking Fast Slow": list(range(170, 179)),
                    "6 Shaking Fast Slow": list(range(180, 189)),
                    "7 Shaking Fast Slow": list(range(190, 199)),
                    "Rotation": list(range(202, 243)),
                    "Audio": list(range(244, 249)),
                    "Random Fast Slow": list(range(250, 255)),
                    },
                    "Gobo Rotation Speed": {
                    "No Rotation": 0,
                    "Rotation": list(range(1, 255)),  
                    },
                    "Gobo Fine Position": list(range(0, 255)),
                    "Prism": {
                    "Open position (hole)": list(range(0, 19)),
                    "3-facet": list(range(20, 159)),
                    "Macro 1": list(range(160, 167)),
                    "Macro 2": list(range(168, 175)),
                    "Macro 3": list(range(176, 183)),
                    "Macro 4": list(range(184, 191)),
                    "Macro 5": list(range(192, 199)),
                    "Macro 6": list(range(200, 207)),
                    "Macro 7": list(range(208, 215)),
                    "Macro 8": list(range(216, 223)),
                    "Macro 9": list(range(224, 231)),
                    "Macro 10": list(range(232, 239)),
                    "Macro 11": list(range(240, 247)),
                    "Macro 12": list(range(248, 255)),
                    },
                    "Prism Rotation": {
                    "No Rotation": 0,
                    "Rotation": list(range(1, 255)), 
                    },
                    "Focus": list(range(1, 255)),
                    "Focus Fine": list(range(1, 255)),
                    "Shutter": {
                    "Closed": list(range(0, 31)),
                    "Open": list(range(32, 63)),
                    "Strobe Slow Fast": list(range(64, 95)),
                    "Pulse Slow Fast": list(range(128, 143)),
                    "Pulse Fast Slow": list(range(144, 159)),
                    "Random Slow Fast": list(range(192, 223)),
                    },
                    "Dimmer": list(range(0, 255)),
                    "Dimmer Fine": list(range(0, 255)),
                },
                "Colorwash250AT": {
                    "Pan": list(range(0, 255)),
                    "Pan Fine": list(range(0, 255)),
                    "Tilt": list(range(0, 255)),
                    "Tilt Fine": list(range(0, 255)),
                    "Pan Tilt Speed": {
                    "Max": 0,
                    "Speed": list(range(1, 255)),
                    },
                    "Special Functions": {},
                    "Pan Tilt Macros": {},
                    "Pan Tilt Macros Speed": {},
                    "Colour 1": {
                    "White": 0,
                    "Red": 18,
                    "Blue": 36,
                    "Green": 54,
                    "3200K Filter": 72,
                    "6000K Filter": 90,
                    "UV": list(range(190, 243)),
                    "Audio": list(range(244, 249)),
                    "Random Fast Slow": list(range(250, 255)),
                    },
                    "Colour Fine Position": list(range(0, 255)),
                    "Cyan": list(range(0, 255)),
                    "Magenta": list(range(0, 255)),
                    "Yellow": list(range(0, 255)),
                    "CMY Dimmer Speed": list(range(0, 255)),
                    "CMY Macros": {
                    "Open": list(range(0, 7)),
                    "Rainbow Fast Slow": list(range(240, 243)),
                    "Audio": list(range(244, 249)),
                    "Random Fast Slow": list(range(250, 255)),
                    },
                    "Effect Wheel": {
                    "Open": list(range(0, 70)),  
                    "Beam Shaper": list(range(71, 179)),  
                    "Swivelling Slow Fast": list(range(180, 199)),  
                    "Frost": list(range(200, 255)),  
                    },
                    "Zoom": list(range(0, 255)),
                    "Shutter": {
                    "Closed": list(range(0, 31)),
                    "Open": list(range(32, 63)),
                    "Strobe Slow Fast": list(range(64, 95)),
                    "Opening Pulse Slow Fast": list(range(128, 143)),
                    "Closing Pulse Fast Slow": list(range(144, 159)),
                    "Random": list(range(192, 223)),
                    },
                    "Dimmer": list(range(0, 255)),
                    "Dimmer Fine": list(range(0, 255)),
                }
            }

        self.__createDatabase(app)
    
    def __createDatabase(self, app):
        self.__createModels()
        self.__seedDBData()
        
    def __createModels(self):
        col = self.db.Column
        
        class Gun(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            name = self.db.Column(self.db.String(100), unique=True, nullable=False)
            defaultColor = self.db.Column(self.db.String(100), unique=False, nullable=False)
            
        class Player(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            name = self.db.Column(self.db.String(60), unique=True, nullable=False)
            kills = self.db.Column(self.db.Integer, nullable=False)
            deaths = self.db.Column(self.db.Integer, nullable=False)
            gamesWon = self.db.Column(self.db.Integer, nullable=False)
            gamesLost = self.db.Column(self.db.Integer, nullable=False)
            
        class Game(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            name = self.db.Column(self.db.String(60), unique=True, nullable=False)
            startTime = self.db.Column(self.db.DateTime, nullable=False)
            endTime = self.db.Column(self.db.DateTime, nullable=False)
            winningPlayer = self.db.Column(self.db.Integer, self.db.ForeignKey("player.id"), nullable=True)
            winningTeam = self.db.Column(self.db.Integer, self.db.ForeignKey("team.id"), nullable=True)
            loser = self.db.Column(self.db.String(60), nullable=True)
            
        class Team(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            name = self.db.Column(self.db.String(60), unique=True, nullable=False)
            teamColour = self.db.Column(self.db.String(10), nullable=False)
            gamePlayers = self.db.relationship("GamePlayers", backref="team_ref", lazy=True)

        class GamePlayers(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            gameID = self.db.Column(self.db.Integer, self.db.ForeignKey("game.id"), nullable=False)
            gunID = self.db.Column(self.db.Integer, self.db.ForeignKey("gun.id"), nullable=False)
            playerID = self.db.Column(self.db.Integer, self.db.ForeignKey("player.id"), nullable=False)
            playerWon = self.db.Column(self.db.Boolean, nullable=False)
            team = self.db.Column(self.db.Integer, self.db.ForeignKey("team.id"), nullable=True)
            
        class DMXScene(self.db.Model):
            __tablename__ = 'dmxscene'
            id = self.db.Column(self.db.Integer, primary_key=True)
            name = self.db.Column(self.db.String(60), nullable=False)
            duration = self.db.Column(self.db.Integer, nullable=False)
            updateDate = self.db.Column(self.db.DateTime, nullable=True)
            createDate = self.db.Column(self.db.DateTime, nullable=False)
            repeat = self.db.Column(self.db.Boolean, nullable=False)
            flash = self.db.Column(self.db.Boolean, nullable=False)
            keybind = self.db.Column(self.db.String(15), nullable=True)

            events = self.db.relationship("DMXSceneEvent", back_populates="scene", lazy=True)

        class DMXSceneEvent(self.db.Model):
            __tablename__ = 'dmxsceneevent'
            id = self.db.Column(self.db.Integer, primary_key=True)
            sceneID = self.db.Column(self.db.Integer, self.db.ForeignKey("dmxscene.id"), nullable=False)
            name = self.db.Column(self.db.String(60), nullable=False)
            duration = self.db.Column(self.db.Integer, nullable=False)
            updateDate = self.db.Column(self.db.DateTime, nullable=True)

            scene = self.db.relationship("DMXScene", back_populates="events")

        class DMXSceneEventChannel(self.db.Model):
            id = col(self.db.Integer, primary_key=True)
            eventID = col(self.db.Integer, self.db.ForeignKey("dmxsceneevent.id"), nullable=False)
            fixture = col(self.db.String(100), nullable=False)
            channel = col(self.db.String(100), nullable=False)
            value = col(self.db.Integer, nullable=False)
            
        class Fixture(self.db.Model):
            id = col(self.db.Integer, primary_key=True)
            name = col(self.db.String(100), nullable=False)
            noOfchannels = col(self.db.Integer, nullable=False)
            mode = col(self.db.String(100), nullable=True)
            notes = col(self.db.String(100), nullable=True)
            icon = col(self.db.String(100), nullable=True)
            #fixtureType = col(self.db.String(100), nullable=True)
            
        class FixtureChannel(self.db.Model):
            __tablename__ = 'fixturechannel'
            id = col(self.db.Integer, primary_key=True)
            fixtureID = col(self.db.Integer, self.db.ForeignKey("fixture.id"), nullable=False)
            channelNo = col(self.db.Integer, nullable=False)
            name = col(self.db.String(100), nullable=False)
            description = col(self.db.String(100), nullable=True)
            icon = col(self.db.String(100), nullable=True)
            
        class FixtureChannelValue(self.db.Model):
            __tablename__ = 'fixturechannelvalue'
            id = col(self.db.Integer, primary_key=True)
            channelID = col(self.db.Integer, self.db.ForeignKey("fixturechannel.id"), nullable=False)
            value = col(self.db.Integer, nullable=False)
            name = col(self.db.String(100), nullable=False)
            icon = col(self.db.String(100), nullable=True)
            
        self.Gun = Gun
        self.Player = Player
        self.Game = Game
        self.Team = Team
        self.GamePlayers = GamePlayers
        self.DMXScene = DMXScene
        self.DMXSceneEvent = DMXSceneEvent
        self.DMXSceneEventChannel = DMXSceneEventChannel
        self.Fixture = Fixture
        self.FixtureChannel = FixtureChannel
        self.FixtureChannelValue = FixtureChannelValue
        
        self.db.Model.metadata.create_all(bind=self.db.engine)
        
        self.db.create_all()

    def __seedDBData(self):
        if not self.Gun.query.first() and not self.Player.query.first():
            message("Empty DB Found! Seeding Data....", type="warning")
            
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
            
            message("Data seeded successfully", type="success")
        else:
            message("Data already exists, skipping seeding.", type="info")
    
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
                message("Changes committed.", type="success")
            except Exception as e:
                message(f"Error committing changes: {e}", type="error")
                self.db.session.rollback()
                print(f"Error: {e}")
    
    class DMXSceneDTO:
        def __init__(self, id, name, duration, updateDate, createDate, repeat, flash, keybind, events):
            self.id = id
            self.name = name
            self.duration = duration
            self.updateDate = updateDate    
            self.createDate = createDate
            self.repeat = repeat
            self.flash = flash
            self.keybind = keybind  
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
                "keybind": self.keybind,
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