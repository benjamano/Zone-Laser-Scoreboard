from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class InternalServerError(db.Model):
    __tablename__ = 'internal_server_error'
    id = db.Column(db.Integer, primary_key=True)
    exception_message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    process = db.Column(db.String(255), nullable=True)
    service = db.Column(db.String(255), nullable=True)
    severity = db.Column(db.Integer, nullable=False)

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

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    teamColour = db.Column(db.String(10), nullable=False)
    gamePlayers = db.relationship("GamePlayers", backref="team_ref", lazy=True)

class GamePlayers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gameID = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    gunID = db.Column(db.Integer, db.ForeignKey("gun.id"), nullable=False)
    playerID = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    playerWon = db.Column(db.Boolean, nullable=False)
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