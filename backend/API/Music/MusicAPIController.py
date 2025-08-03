import os
import threading
import time
from collections import deque
from datetime import datetime

import vlc
from API.Supervisor import Supervisor
from data.models import *
from data.models import Song, PlayList
from flask import Blueprint, jsonify, request, Flask
from flask_sqlalchemy import SQLAlchemy

from backend.data.models import InternalServerError

MusicBlueprint = Blueprint("music", __name__)
f = Format("Music")

class MusicAPIController:
    def __init__(self, supervisor: Supervisor, context: SQLAlchemy, secrets: dict[str, str], app: Flask, dir, dmx):
        self.registerMusicRoutes(app)
        
        self._supervisor = supervisor
        self._context = context
        self._secrets = secrets
        self._dmx = dmx
        self._app : Flask = app
        self._dir = dir
        
        self.instance : vlc.Instance = vlc.Instance()
        self.player : vlc.MediaPlayer = self.instance.media_player_new()
        
        # Queue system variables
        self.queue = deque()  # Main queue for songs
        self.currentSong: Song = Song()
        self.currentPlaylist: PlayList = PlayList()
        self.queueLock = threading.Lock()  # Thread safety for queue operations
        self.stopRequested = False
        self.playerThread = None
        self.songEndEvent = threading.Event()
        self.fullPlaylist = [] # Full playlist for queue playback
        
        self.setVolume(self._secrets["DefaultVolume"] if "DefaultVolume" in self._secrets else 50)
        
    def registerMusicRoutes(self, app):
        @MusicBlueprint.route("/api/music/songs", methods=["GET"])
        def getSongs():
            self.getDownloadedSongs()
            
            return [song.to_dict() for song in self.getSongs()]
        
        @MusicBlueprint.route("/api/music/songs", methods=["POST"])
        def addSong():
            return self.addSong().to_dict()
        
        @MusicBlueprint.route("/api/music/songs/<songId>", methods=["GET"])
        def getSong(songId):
            return jsonify(self.getSong(songId).to_dict()), 200
        
        @MusicBlueprint.route("/api/music/songs/<songId>", methods=["PUT"])
        def updateSong(songId):
            return jsonify(self.updateSong(songId).to_dict()), 200
        
        @MusicBlueprint.route("/api/music/queue", methods=["GET"])
        def getQueue():
            return jsonify([song.to_dict() for song in self.getQueue()]), 200
        
        @MusicBlueprint.route("/api/music/queue", methods=["POST"])
        def addToQueue():
            data = request.json
            song = self.getSong(data["songId"])
            if not song:
                return jsonify({"error": "Song not found"}), 404
            
            if self.addToQueue(song):
                return jsonify({"message": "Song added to queue"}), 200
            return jsonify({"error": "Failed to add song to queue"}), 500
        
        @MusicBlueprint.route("/api/music/queue/play", methods=["POST"])
        def startQueue():
            if self.startQueuePlayback():
                return jsonify({"message": "Queue playback started"}), 200
            return jsonify({"error": "Failed to start queue playback"}), 500
        
        @MusicBlueprint.route("/api/music/queue/stop", methods=["POST"])
        def stopQueue():
            if self.stopQueuePlayback():
                return jsonify({"message": "Queue stopped"}), 200
            return jsonify({"error": "Failed to stop queue"}), 500
        
        @MusicBlueprint.route("/api/music/queue/clear", methods=["POST"])
        def clearQueue():
            if self.clearQueue():
                return jsonify({"message": "Queue cleared"}), 200
            return jsonify({"error": "Failed to clear queue"}), 500
        
        @MusicBlueprint.route("/api/music/queue/remove/<int:position>", methods=["DELETE"])
        def removeFromQueue(position):
            if self.removeFromQueue(position):
                return jsonify({"message": "Song removed from queue"}), 200
            return jsonify({"error": "Failed to remove song from queue"}), 500
        
        @MusicBlueprint.route("/api/music/queue/next", methods=["POST"])
        def nextSong():
            if self.next():
                return jsonify({"message": "Playing next song"}), 200
            return jsonify({"error": "No next song available"}), 500
        
        @MusicBlueprint.route("/api/music/queue/previous", methods=["POST"])
        def previousSong():
            if self.previous():
                return jsonify({"message": "Playing previous song"}), 200
            return jsonify({"error": "No previous song available"}), 500
        
        @MusicBlueprint.route("/api/music/player/play", methods=["POST"])
        def playMusic():
            if self.play():
                return jsonify({"message": "Music playing"}), 200
            return jsonify({"error": "Failed to play music"}), 500
        
        @MusicBlueprint.route("/api/music/player/pause", methods=["POST"])
        def pauseMusic():
            if self.pause():
                return jsonify({"message": "Music paused"}), 200
            return jsonify({"error": "Failed to pause music"}), 500
        
        @MusicBlueprint.route("/api/music/player/toggle", methods=["POST"])
        def toggleMusic():
            if self.togglePauseMusic():
                return jsonify({"message": "Music toggled"}), 200
            return jsonify({"error": "Failed to toggle music"}), 500
        
        @MusicBlueprint.route("/api/music/player/volume", methods=["POST"])
        def setVolume():
            data = request.json
            volume = self.setVolume(data.get("volume", 50))
            return jsonify({"volume": volume}), 200
        
        @MusicBlueprint.route("/api/music/player/volume", methods=["GET"])
        def getVolume():
            return jsonify({"volume": self.getVolume()}), 200
        
        @MusicBlueprint.route("/api/music/player/current", methods=["GET"])
        def getCurrentSong():
            return jsonify(self.currentSongDetails().to_dict()), 200
        
        @MusicBlueprint.route("/api/music/playlists", methods=["GET"])
        def getPlaylists():
            return jsonify([playlist.to_dict() for playlist in self.getPlaylists()]), 200
        
        @MusicBlueprint.route("/api/music/playlists", methods=["POST"])
        def createPlaylist():
            return jsonify(self.createPlaylist().to_dict()), 200
        
        @MusicBlueprint.route("/api/music/playlists/<playlistId>", methods=["GET"])
        def getPlaylist(playlistId):
            if playlistId == 0:
                return jsonify({"message": "No playlist selected"}), 200
            return jsonify(self.getPlaylist(playlistId).to_dict()), 200
        
        @MusicBlueprint.route("/api/music/playlists/<playlistId>/songs", methods=["GET"])
        def getPlaylistSongs(playlistId):
            return jsonify([song.to_dict() for song in self.getPlaylistSongs(playlistId)]), 200
        
        @MusicBlueprint.route("/api/music/playlists/<playlistId>/songs/<songId>", methods=["DELETE"])
        def removeSongFromPlaylist(playlistId, songId):
            song = self.getSong(songId)
            if not song:
                return jsonify({"error": "Song not found"}), 404
            
            playlistSong = self._context.session.query(PlaylistSong).filter(
                PlaylistSong.playlistId == playlistId,
                PlaylistSong.songId == song.id,
                PlaylistSong.isActive == True
            ).first()
            
            if playlistSong:
                playlistSong.isActive = False
                self._context.session.commit()
                return jsonify({"message": "Song removed from playlist"}), 200
            
            return jsonify({"error": "Song not found in playlist"}), 404
        
        @MusicBlueprint.route("/api/music/playlists/<playlistId>/load", methods=["POST"])
        def loadPlaylistToQueue(playlistId):
            if self.loadPlaylistToQueue(playlistId):
                self.play()
                
                return jsonify({"message": "Playlist loaded to queue"}), 200
            
            return jsonify({"error": "Failed to load playlist to queue"}), 500
        
        @MusicBlueprint.route("/api/music/playlists/<playlistId>/songs", methods=["POST"])
        def addSongToPlaylist(playlistId):
            data = request.json
            song = self.getSong(data["songId"])
            if not song:
                song = self.addSong()
            
            if self.addSongToPlaylist(song, playlistId):
                return jsonify({"message": "Song added to playlist"}), 200
            
        @MusicBlueprint.route("/api/music/getDownloadedSongs", methods=["GET"])
        def getDownloadedSongs(playlistId):
            return jsonify({self.getDownloadedSongs()}), 200
        
        @MusicBlueprint.route("/api/music/removeSongFromQueue", methods=["DELETE"])
        def removeSongFromQueue():
            data = request.json
            songId = data.get("songId")
            if not songId:
                return jsonify({"error": "Song ID is required"}), 400
            
            self.removeFromQueueWithSongId(songId=songId)
            
            return jsonify("Success"), 200
            
        app.register_blueprint(MusicBlueprint)
    
    def getDownloadedSongs(self):
        try:
            musiDir = self._dir + "/data/music"
            songs = []
            for filename in os.listdir(musiDir):
                if filename.endswith(".mp3") or filename.endswith(".m4a"):
                    song_name = os.path.splitext(filename)[0]
                    song : Song = self._context.session.query(Song).filter(Song.name == song_name).first()
                    if not song:
                        song = Song(name=song_name, isDownloaded=True)
                        self._context.session.add(song)
                        self._context.session.commit()
                    else:
                        song.isDownloaded = True
                        
                    songs.append(song.to_dict())
            return songs
        except Exception as e:
            self.logError("Get Downloaded Songs", e)
            return []
    
    def addToQueue(self, song: Song, priority: bool = False) -> bool:
        """Add a song to the queue. If priority is True, add to front of queue."""
        try:
            with self.queueLock:
                if priority:
                    self.queue.appendleft(song)
                else:
                    self.queue.append(song)
            return True
        except Exception as e:
            self.logError("Add to Queue", e)
            return False
    
    def getQueue(self) -> list[Song]:
        """Get current queue as a list."""
        try:
            with self.queueLock:
                return list(self.queue)
        except Exception as e:
            self.logError("Get Queue", e)
            return []
    
    def clearQueue(self) -> bool:
        """Clear the entire queue."""
        try:
            with self.queueLock:
                self.queue.clear()
            return True
        except Exception as e:
            self.logError("Clear Queue", e)
            return False
    
    def removeFromQueueWithSongId(self, songId: int) -> bool:
        """Remove a song from the queue by its ID."""
        try:
            with self.queueLock:
                queue_list = list(self.queue)
                for i, song in enumerate(queue_list):
                    if str(song.id) == str(songId):
                        queue_list.pop(i)
                        self.queue = deque(queue_list)
                        return True
            return False
        except Exception as e:
            self.logError("Remove from Queue by ID", e)
            return False
    
    def removeFromQueue(self, position: int) -> bool:
        """Remove song at specific position from queue."""
        try:
            with self.queueLock:
                if 0 <= position < len(self.queue):
                    queue_list = list(self.queue)
                    queue_list.pop(position)
                    self.queue = deque(queue_list)
                    return True
            return False
        except Exception as e:
            self.logError("Remove from Queue", e)
            return False
    
    def getNextSongFromQueue(self) -> Song:
        """Get and remove the next song from queue. Refill from fullPlaylist if empty."""
        try:
            with self.queueLock:
                if len(self.queue) == 0 and self.fullPlaylist:
                    self.queue.extend(self.fullPlaylist)
                if self.queue:
                    return self.queue.popleft()
            return None
        except Exception as e:
            self.logError("Get Next Song from Queue", e)
            return None

    def startQueuePlayback(self) -> bool:
        """Start playing songs from the queue in a loop until stopped."""
        try:
            self.stopQueuePlayback()

            if not self.queue:
                return False

            self.stopRequested = False
            self.songEndEvent.clear()

            self.fullPlaylist = list(self.queue)

            def queuePlayerLoop():
                while not self.stopRequested:
                    next_song = self.getNextSongFromQueue()

                    if not next_song:
                        time.sleep(1)
                        continue

                    self.currentSong = next_song

                    if self.loadSong(next_song):
                        self.play()
                        self.waitForSongEnd()
                    else:
                        time.sleep(1)

            self.playerThread = threading.Thread(target=queuePlayerLoop, daemon=True)
            self.playerThread.start()
            return True

        except Exception as e:
            self.logError("Start Queue Playback", e)
            return False
    
    def stopQueuePlayback(self) -> bool:
        """Stop queue playback."""
        try:
            self.stopRequested = True
            self.songEndEvent.set()
            self.stop()
            
            if self.playerThread and self.playerThread.is_alive():
                self.playerThread.join(timeout=2)
            
            self.playerThread = None
            self.currentSong : Song = None
            return True
        except Exception as e:
            self.logError("Stop Queue Playback", e)
            return False
    
    def loadSong(self, song: Song) -> bool:
        try:
            with self._app.app_context():
                path = self._dir + f"/data/music/{song.name}.mp3"
                if not os.path.isfile(path):
                    path = self._dir + f"/data/music/{song.name}.m4a"
                    if not os.path.isfile(path):
                        song.isDownloaded = False
                        return False
                
                song.isDownloaded = True
                    
                self._context.session.commit()
                
            media = self.instance.media_new(path)
            self.player.set_media(media)
            return True
        except Exception as e:
            self.logError("Load Song", e)
            return False
    
    def waitForSongEnd(self):
        """Wait for current song to end."""
        self.songEndEvent.clear()
        
        def end_callback(event):
            self.songEndEvent.set()
            try:
                self._dmx.checkForSongTriggers(self.currentSong.name if self.currentSong.name else "")
            except Exception as e:
                self._supervisor.logInternalServerError(ise=InternalServerError(
                    exception_message=e,
                    timestamp=datetime.now(),
                    process="Check for DMX song triggers when song changes",
                    service="Music API",
                    severity=2
                ))

        self.player.event_manager().event_detach(vlc.EventType.MediaPlayerEndReached)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, end_callback)
        
        self.songEndEvent.wait()
        
    def fadeVolumeFrom(self, start : int, end : int):
        for vol in range(start, end):
            self.setVolume(vol)
            print(f"Raised volume to {vol}")
            time.sleep(0.01)

    def fadeVolumeTo(self, volume : int):
        currentVolume : int = self.getVolume()

        if currentVolume == volume:
            return

        step = 1 if volume > currentVolume else -1
        for vol in range(currentVolume, volume, step):
            self.setVolume(vol)
            # print(f"Set volume to {vol}")
            time.sleep(0.02)

        self.setVolume(volume)

        return
                
    def play(self) -> bool:
        try:
            if not self.player.is_playing():
                if not self.player.get_media():
                    if self.queue:
                        return self.startQueuePlayback()
                    else:
                        self.loadPlaylistToQueue(1)
                        self.startQueuePlayback()

                self.player.play()
                self.fadeVolumeTo(100)
            return True
        except Exception as e:
            self.logError("Play", e)
            return False

    def pause(self) -> bool:
        try:
            if self.player.is_playing():
                self.fadeVolumeTo(0)
                self.player.pause()
            return True
        except Exception as e:
            self.logError("Pause", e)
            return False

    def stop(self) -> bool:
        try:
            if self.player.is_playing():
                self.fadeVolumeTo(0)
                self.player.stop()
            return True
        except Exception as e:
            self.logError("Stop", e)
            return False
        
    def togglePauseMusic(self) -> bool:
        try:
            if self.player.is_playing():
                self.pause()
            else:
                self.play()
            return True
        except Exception as e:
            self.logError("Toggle Pause", e)
            return False

    def next(self) -> bool:
        """Skip to next song in queue."""
        try:
            if self.queue:
                self.songEndEvent.set()
                return True
            else:
                self.loadPlaylistToQueue(self.currentPlaylist.id if self.currentPlaylist else 1)
                self.songEndEvent.set()
                return True
            return False
        except Exception as e:
            self.logError("Next", e)
            return False
        
    def restart(self) -> bool:
        try:
            self.player.set_position(0)
            return True
        except Exception as e:
            self.logError("Restart", e)
            return False
        
    def previous(self) -> bool:
        # Need to implement a previous song tracker
        try:
            return self.restart()
        except Exception as e:
            self.logError("Previous", e)
            return False
    
    def loadPlaylistToQueue(self, playlistId: int) -> bool:
        try:
            with self._app.app_context():
                playlist = self._context.session.query(PlayList).filter(PlayList.id == playlistId).first()
                if not playlist:
                    return False
                
                playlistSongs = self._context.session.query(PlaylistSong).filter(
                    PlaylistSong.playlistId == playlistId,
                    PlaylistSong.isActive == True
                ).all()
                
                playListSongIds = [song.songId for song in playlistSongs]
                songs = self._context.session.query(Song).filter(Song.id.in_(playListSongIds)).all()
                
                self._context.session.flush()
                self._context.session.expunge(playlist)
                
                self.currentPlaylist = playlist
            
            self.queue.clear()
            
            for song in songs:
                self.addToQueue(song)
            
            return True
        except Exception as e:
            self.logError("Load Playlist to Queue", e)
            return False
        
    def getPlaylistSongs(self, playListId: int) -> list[Song]:
        try:
            playlistSongs = self._context.session.query(PlaylistSong).filter(PlaylistSong.playlistId == playListId).filter(PlaylistSong.isActive == True).all()
            if not playlistSongs:
                return []
            
            songs = []
            for playlistSong in playlistSongs:
                song = self._context.session.query(Song).filter(Song.id == playlistSong.songId).first()
                if song:
                    songs.append(song)
            return songs
        except Exception as e:
            self._supervisor.logInternalServerError(InternalServerError(
                exception_message = str(e),
                timestamp = datetime.now(),
                process = "Music API - Get Playlist Songs",
                service = "Music API",
                severity = 1
            ))
            
            return []
        
    def logError(self, process, e):
        self._supervisor.logInternalServerError(InternalServerError(
            exception_message=str(e),
            timestamp=datetime.now(),
            process=f"Music API - {process}",
            service="Music API",
            severity=1
        ))
        
    def setVolume(self, volume: int) -> int:
        try:
            volume = int(volume)
            if 0 <= volume <= 100:
                self.player.audio_set_volume(volume)
                return self.player.audio_get_volume()
        except Exception as e:
            self.logError("Set Volume", e)
            
            return self.player.audio_get_volume()
        
    def getVolume(self) -> int:
        try:
            return self.player.audio_get_volume()
        except Exception as e:
            self.logError("Get Volume", e)
            
            return -1
        
    def currentSongDetails(self) -> SongDetailsDTO:
        try:
            if not self.currentSong:
                return SongDetailsDTO("No song playing", "", "", 0, 0, False, self.getVolume())
                
            duration = 0
            timeLeft = 0
            album = ""
            artist = ""
            songName = ""
            currentSongId = self.currentSong.id
            
            try:
                media = self.player.get_media()  
                
                duration = self.player.get_length() / 1000
                timeLeft = (duration - self.player.get_time() / 1000) 
                              
                metaKeys = {
                    vlc.Meta.Title: "Title",
                    vlc.Meta.Artist: "Artist",
                    vlc.Meta.Album: "Album",
                    vlc.Meta.Publisher: "Publisher",
                    vlc.Meta.AlbumArtist: "AlbumArtist",
                    vlc.Meta.Actors: "Actors",
                }

                for key, field in metaKeys.items():
                    value = media.get_meta(key)
                    if value:
                        if field == "Title":
                            songName = value
                        elif field == "Artist":
                            artist = value
                        elif field == "Album":
                            album = value
                        elif field == "Publisher" and artist == "":
                            artist = value
                        elif field == "AlbumArtist" and artist == "":
                            artist = value
                        elif field == "Actors" and artist == "":
                            artist = value
                            
            except:
                songName = self.currentSong.name if self.currentSong.name else "Unknown"
            
            with self._app.app_context():
                songInDB = (
                    self._context.session
                    .query(Song)
                    .filter(Song.id == currentSongId)
                    .first()
                )
                if songInDB:
                    songInDB.duration = duration
                    songInDB.album  = album
                    songInDB.artist = artist

                    self._context.session.flush()
                    self._context.session.expunge(songInDB)
                    self._context.session.commit()
                    
                    self.currentSong = songInDB

                    with self.queueLock:
                        for index, queuedSong in enumerate(self.queue):
                            if queuedSong.id == songInDB.id:
                                self.queue[index] = songInDB
                                break

            return SongDetailsDTO(
                name=songName,
                album=album,
                artist=artist,
                duration=duration,
                timeleft=timeLeft,
                isPlaying=self.player.is_playing() == 1,
                currentVolume=self.getVolume()
            )
            
        except Exception as e:
            self.logError("Get Current Song Details", e)
            return SongDetailsDTO("Error getting song details", "", "", 0, 0, False, self.getVolume())
        
    def getSongs(self) -> list[Song]:
        try:
            songs = self._context.session.query(Song).all()
            return songs
        except Exception as e:
            self._supervisor.logInternalServerError(InternalServerError(
                exception_message = str(e),
                timestamp = datetime.now(),
                process = "Music API - Get Songs",
                service = "Music API",
                severity = 1
            ))
            
            return []
        
    def addSong(self) -> Song:
        try:        
            data = request.json
            
            existingSong = self._context.session.query(Song).filter(Song.name == data["name"]).first()
            if existingSong:
                return existingSong
                
            newSong = Song(
                name= data["name"] if data["name"] is not None else "New Song",
                youtubeLink = data["songUrl"] if "songUrl" in data else None,
            )
            self._context.session.add(newSong)
            self._context.session.commit()
            
            return newSong
        except Exception as e:
            self._supervisor.logInternalServerError(InternalServerError(
                exception_message = str(e),
                timestamp = datetime.now(),
                process = "Music API - Add Song",
                service = "Music API",
                severity = 1
            ))
            
            return Song()
        
    def getSong(self, songId: int) -> Song:
        try:
            song = self._context.session.query(Song).filter(Song.id == songId).first()
            if not song:
                return None
            
            return song
        except Exception as e:
            self._supervisor.logInternalServerError(InternalServerError(
                exception_message = str(e),
                timestamp = datetime.now(),
                process = "Music API - Get Song",
                service = "Music API",
                severity = 1
            ))
            
            return None
        
    def updateSong(self, songId: int) -> Song:
        try:
            data = request.json
            
            song = self._context.session.query(Song).filter(Song.id == songId).first()
            if not song:
                return None
            
            if "name" in data:
                song.name = data["name"]
            
            self._context.session.commit()
            return song
        except Exception as e:
            self._supervisor.logInternalServerError(InternalServerError(
                exception_message = str(e),
                timestamp = datetime.now(),
                process = "Music API - Update Song",
                service = "Music API",
                severity = 1
            ))
            
            return Song()
        
    def getPlaylists(self) -> list[PlayList]:
        try:
            playlists = self._context.session.query(PlayList).all()
            return playlists
        except Exception as e:
            self._supervisor.logInternalServerError(InternalServerError(
                exception_message = str(e),
                timestamp = datetime.now(),
                process = "Music API - Get Playlists",
                service = "Music API",
                severity = 1
            ))
            
            return []
        
    def createPlaylist(self) -> PlayList:
        try:
            data = request.json
            
            newPlaylist = PlayList(
                name=data["name"] if "name" in data else "New Playlist",
            )
            self._context.session.add(newPlaylist)
            self._context.session.commit()
            
            return newPlaylist
        except Exception as e:
            self._supervisor.logInternalServerError(InternalServerError(
                exception_message = str(e),
                timestamp = datetime.now(),
                process = "Music API - Create Playlist",
                service = "Music API",
                severity = 1
            ))
            
            return jsonify({"error": "Failed to create playlist"}), 500
        
    def getPlaylist(self, playlistId: int) -> PlayList:
        try:
            playlist = self._context.session.query(PlayList).filter(PlayList.id == playlistId).first()
            if not playlist:
                return None
            
            return playlist
        except Exception as e:
            self._supervisor.logInternalServerError(InternalServerError(
                exception_message = str(e),
                timestamp = datetime.now(),
                process = "Music API - Get Playlist",
                service = "Music API",
                severity = 1
            ))
            
            return None
        
    def addSongToPlaylist(self, song: Song, playlistId: int) -> bool:
        try:
            playlist = self._context.session.query(PlayList).filter(PlayList.id == playlistId).first()
            if not playlist:
                return False
            
            existingPlaylistSong = self._context.session.query(PlaylistSong).filter(
                PlaylistSong.playlistId == playlistId,
                PlaylistSong.songId == song.id,
            ).first()
            
            if existingPlaylistSong:
                existingPlaylistSong.isActive = True
                self._context.session.commit()
                
                return True
            
            if song not in playlist.songs:
                self._context.session.add(PlaylistSong(
                    playlistId = playlistId,
                    songId = song.id,
                    isActive = True
                ))
                
                self._context.session.commit()
                
                return True
            
            return False
        except Exception as e:
            self._supervisor.logInternalServerError(InternalServerError(
                exception_message = str(e),
                timestamp = datetime.now(),
                process = "Music API - Add Song to Playlist",
                service = "Music API",
                severity = 1
            ))
            
            return False