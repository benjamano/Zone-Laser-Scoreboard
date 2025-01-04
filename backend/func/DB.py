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
        self.Notification = None

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
            
        class Notification(self.db.Model):
            id = col(self.db.Integer, primary_key=True)
            title = col(self.db.String(100), nullable=False)
            message = col(self.db.String(100), nullable=False)
            date = col(self.db.DateTime, nullable=False)
            dismissed = col(self.db.Boolean, nullable=False)
            
        self.Gun = Gun
        self.Player = Player
        self.Game = Game
        self.Team = Team
        self.GamePlayers = GamePlayers
        self.DMXScene = DMXScene
        self.DMXSceneEvent = DMXSceneEvent
        self.DMXSceneEventChannel = DMXSceneEventChannel
        self.Notification = Notification
        
        self.db.Model.metadata.create_all(bind=self.db.engine)
        
        self.db.create_all()

    def __seedDBData(self):
        if not self.Gun.query.first() and not self.Player.query.first():
            message("Empty DB Found! Seeding Data....", type="warning")
            
            print(self.db.inspect(self.Gun).columns)
            
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
    
    