from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass, asdict

db = SQLAlchemy()

class InternalServerError(db.Model):
    __tablename__ = 'internal_server_error'
    id = db.Column(db.Integer, primary_key=True)
    exception_message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    process = db.Column(db.String(255), nullable=True)
    service = db.Column(db.String(255), nullable=True)
    severity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "exception_message": self.exception_message,
            "timestamp": self.timestamp.isoformat(),
            "process": self.process,
            "service": self.service,
            "severity": self.severity,
        }

@dataclass
class ServiceHealthDTO:
    serviceName: str
    status: str
    numberOfRecentErrors: int
    recentErrorList: list

    def to_dict(self):
        return asdict(self)

class Gun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    defaultColor = db.Column(db.String(100), unique=False, nullable=False)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    kills = db.Column(db.Integer, nullable=False)
    deaths = db.Column(db.Integer, nullable=False)
    gamesWon = db.Column(db.Integer, nullable=False)
    gamesLost = db.Column(db.Integer, nullable=False)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=True)
    startTime = db.Column(db.DateTime, nullable=False)
    endTime = db.Column(db.DateTime, nullable=True)
    winningPlayerRed = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    winningPlayerGreen = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    winningPlayer = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    winningTeam = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "startTime": self.startTime,
            "endTime": self.endTime,
            "winningPlayer": self.winningPlayer,
            "winningTeam": self.winningTeam,
        }

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    teamColour = db.Column(db.String(10), nullable=False)
    gamePlayers = db.relationship("GamePlayer", backref="team_ref", lazy=True)

class GamePlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gameId = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    gunId = db.Column(db.Integer, db.ForeignKey("gun.id"), nullable=False)
    playerId = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=True)
    playerWon = db.Column(db.Boolean, nullable=True)
    score = db.Column(db.Integer, nullable=True)
    accuracy = db.Column(db.Integer, nullable=True)
    team = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)

class DMXScene(db.Model):
    __tablename__ = 'dmxscene'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    updateDate = db.Column(db.DateTime, nullable=True)
    createDate = db.Column(db.DateTime, nullable=False)
    repeat = db.Column(db.Boolean, nullable=False)
    flash = db.Column(db.Boolean, nullable=False)
    keyboard_keybind = db.Column(db.String(15), nullable=True)
    song_keybind = db.Column(db.String(15), nullable=True)
    game_event_keybind = db.Column(db.String(15), nullable=True)
    events = db.relationship("DMXSceneEvent", back_populates="scene", lazy=True)

class DMXSceneEvent(db.Model):
    __tablename__ = 'dmxsceneevent'
    id = db.Column(db.Integer, primary_key=True)
    sceneID = db.Column(db.Integer, db.ForeignKey("dmxscene.id"), nullable=False)
    name = db.Column(db.String(60), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    updateDate = db.Column(db.DateTime, nullable=True)
    scene = db.relationship("DMXScene", back_populates="events")

class DMXSceneEventChannel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventID = db.Column(db.Integer, db.ForeignKey("dmxsceneevent.id"), nullable=False)
    fixture = db.Column(db.String(100), nullable=False)
    channel = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Integer, nullable=False)

class Fixture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    noOfchannels = db.Column(db.Integer, nullable=False)
    mode = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.String(100), nullable=True)
    icon = db.Column(db.String(100), nullable=True)

class FixtureChannel(db.Model):
    __tablename__ = 'fixturechannel'
    id = db.Column(db.Integer, primary_key=True)
    fixtureID = db.Column(db.Integer, db.ForeignKey("fixture.id"), nullable=False)
    channelNo = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=True)
    icon = db.Column(db.String(100), nullable=True)

class FixtureChannelValue(db.Model):
    __tablename__ = 'fixturechannelvalue'
    id = db.Column(db.Integer, primary_key=True)
    channelID = db.Column(db.Integer, db.ForeignKey("fixturechannel.id"), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100), nullable=True)
    
class DMXPatchedChannel(db.Model):
    __tablename__ = 'dmxpatchedchannel'
    id = db.Column(db.Integer, primary_key=True)
    channelId = db.Column(db.Integer)
    fixtureChannelID = db.Column(db.Integer, db.ForeignKey("fixturechannel.id"), nullable=False)
    
class CustomHomeScreenPreset(db.Model):
    __tablename__ = 'customhomescreenpreset'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    isActive = db.Column(db.Boolean, nullable=False)
    
class PresetCard(db.Model):
    __tablename__ = 'presetcard'
    id = db.Column(db.Integer, primary_key=True)
    cardId = db.Column(db.Integer, nullable=False)
    homeScreenPresetId = db.Column(db.Integer, db.ForeignKey("customhomescreenpreset.id"), nullable=False)
    isActive = db.Column(db.Boolean, nullable=False)