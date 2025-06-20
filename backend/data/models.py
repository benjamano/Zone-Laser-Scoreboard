from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass, asdict
from datetime import datetime

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

class DMXSceneEvent(db.Model):
    __tablename__ = 'dmxsceneevent'
    id = db.Column(db.Integer, primary_key=True)
    sceneID = db.Column(db.Integer, db.ForeignKey("dmxscene.id"), nullable=False)
    name = db.Column(db.String(60), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    updateDate = db.Column(db.DateTime, nullable=True)
    scene = db.relationship("DMXScene", back_populates="events")
    
    def to_dict(self):
        return {
            "id": self.id,
            "sceneId": self.sceneID,
            "name": self.name,
            "duration": self.duration,
            "updateDate": self.updateDate.isoformat() if self.updateDate else None,
        }

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
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "duration": self.duration,
            "updateDate": self.updateDate.isoformat() if self.updateDate else None,
            "createDate": self.createDate.isoformat(),
            "repeat": self.repeat,
            "flash": self.flash,
            "keyboard_keybind": self.keyboard_keybind,
            "song_keybind": self.song_keybind,
            "game_event_keybind": self.game_event_keybind,
        }

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
    
class PatchedFixture(db.Model):
    __tablename__ = 'patchedfixtures'
    id = db.Column(db.Integer, primary_key=True)
    fixtureId = db.Column(db.Integer, db.ForeignKey("fixture.id", name="fk_patchedfixtures_fixture_id"), nullable=False)
    groupId = db.Column(db.Integer, db.ForeignKey("patchedfixturegroups.id", name="fk_patchedfixtures_group_id"), nullable=True)
    dmxControllerFixtureId = db.Column(db.Integer, nullable=False)
    dmxStartAddress = db.Column(db.Integer, nullable=False)
    dmxEndAddress = db.Column(db.Integer, nullable=False)
    fixtureName = db.Column(db.String(100), nullable=False)

class PatchedFixtureGroup(db.Model):
    __tablename__ = 'patchedfixturegroups'
    id = db.Column(db.Integer, primary_key=True)
    groupName = db.Column(db.String(100), nullable=False)
    isActive = db.Column(db.Boolean, nullable=False)
    
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
    
class NewFeatureRequest(db.Model):
    __tablename__ = 'NewFeatureRequests'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    use_case = db.Column(db.String(255), nullable=False)
    expected = db.Column(db.String(255), nullable=False)
    details = db.Column(db.String(255), nullable=False)
    submitter_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "use_case": self.use_case,
            "expected": self.expected,
            "details": self.details,
            "submitter_name": self.submitter_name,
            "created_at": self.created_at.isoformat(),
        }

class BugReport(db.Model):
    __tablename__ = 'BugReports'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    when_occurs = db.Column(db.String(255), nullable=False)
    expected_behavior = db.Column(db.String(255), nullable=False)
    steps_to_reproduce = db.Column(db.String(255), nullable=False)
    submitter_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "when_occurs": self.when_occurs,
            "expected_behavior": self.expected_behavior,
            "steps_to_reproduce": self.steps_to_reproduce,
            "submitter_name": self.submitter_name,
            "created_at": self.created_at.isoformat(),
        }

class SongRequest(db.Model):
    __tablename__ = 'SongRequests'
    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(255), nullable=False)
    naughty_words = db.Column(db.String(20), nullable=False)
    submitter_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "song_name": self.song_name,
            "naughty_words": self.naughty_words,
            "submitter_name": self.submitter_name,
            "created_at": self.created_at.isoformat(),
        }

class RestartRequest(db.Model):
    __tablename__ = 'RestartRequests'
    id = db.Column(db.Integer, primary_key=True)
    create_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_service_name = db.Column(db.String(255), nullable=False)
    complete = db.Column(db.Boolean, default=False, nullable=False)
    reason = db.Column(db.String(1024), nullable=True)
    
class DashboardCategory(db.Model):
    __tablename__ = 'DashboardCategories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=True, default=0)
    isActive = db.Column(db.Boolean, nullable=False, default=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
            "isActive": self.isActive,
            "widgets": [widget.to_dict() for widget in DashboardWidget.query.filter_by(categoryId=self.id and DashboardWidget.isActive == True).all()]
        }
        
class DashboardWidget(db.Model):
    __tablename__ = 'DashboardWidgets'
    id = db.Column(db.Integer, primary_key=True)
    height = db.Column(db.Integer, nullable=False, default=1)
    width = db.Column(db.Integer, nullable=False, default=1)
    left = db.Column(db.Integer, nullable=False, default=0)
    top = db.Column(db.Integer, nullable=False, default=0)
    typeId = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=True)
    isActive = db.Column(db.Boolean, nullable=False, default=True)
    categoryId = db.Column(db.Integer, db.ForeignKey('DashboardCategories.id'), nullable=False)
    
    category = db.relationship('DashboardCategory', backref='DashboardWidgets')
    
    def to_dict(self):
        return {
            "id": self.id,
            "height": self.height,
            "width": self.width,
            "left": self.left,
            "top": self.top,
            "typeId": self.typeId,
            "content": self.content,
            "categoryId": self.categoryId,
            "isActive": self.isActive,
        }
        
class PlayList(db.Model):
    __tablename__ = 'Playlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    songs = db.relationship("PlaylistSong", back_populates="playlist", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "songs": [ps.song.to_dict() for ps in self.songs if ps.isActive]
        }

class Song(db.Model):
    __tablename__ = 'Songs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    youtubeLink = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    isDownloaded = db.Column(db.Boolean, nullable=True)

    songs = db.relationship("PlaylistSong", back_populates="song", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "youtubeLink": self.youtubeLink,
            "isDownloaded": self.isDownloaded,
            "duration": self.duration
        }

class PlaylistSong(db.Model):
    __tablename__ = 'playlistSongs'
    playlistId = db.Column(db.Integer, db.ForeignKey('Playlists.id'), primary_key=True)
    songId = db.Column(db.Integer, db.ForeignKey('Songs.id'), primary_key=True)
    isActive = db.Column(db.Boolean, nullable=False, default=True)

    playlist = db.relationship("PlayList", back_populates="songs")
    song = db.relationship("Song", back_populates="songs")
    
class SongDetailsDTO():
    def __init__(self, name, album, duration, timeleft, isPlaying, currentVolume):
        self.name = name
        self.album = album
        self.duration = duration
        self.timeleft = timeleft
        self.isPlaying = isPlaying
        self.currentVolume = currentVolume

    def to_dict(self):
        return {
            "name": self.name,
            "album": self.album,
            "duration": self.duration,
            "timeleft": self.timeleft,
            "isPlaying": self.isPlaying,
            "currentVolume": self.currentVolume
        }