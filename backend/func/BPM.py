import asyncio
import threading
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class MediaBPMFetcher:
    def __init__(self, spotify_client_id, spotify_client_secret):
        # Initialize Spotify client
        self.auth_manager = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
        self.spotify = spotipy.Spotify(auth_manager=self.auth_manager)

        # Initialize data storage and thread control
        self.current_song = None
        self.current_bpm = None
        self.current_album = None
        self.lock = threading.Lock()  # To ensure thread-safe data access

    async def get_media_info_async(self):
        # Async function to get media info
        sessions = await MediaManager.request_async()
        current_session = sessions.get_current_session()
        if current_session:
            info = await current_session.try_get_media_properties_async()
            return info.artist, info.title, info.album_title
        return None, None, None

    def get_song_bpm(self, artist, title):
        # Search for the song on Spotify and return its BPM (tempo)
        try:
            result = self.spotify.search(q=f"track:{title} artist:{artist}", type='track')
            track_id = result['tracks']['items'][0]['id']

            audio_features = self.spotify.audio_features(track_id)
            bpm = audio_features[0]['tempo']
            return bpm
        except IndexError:
            return "Song not found"
        except Exception as e:
            return f"Error: {e}"

    async def fetch_once(self):
        # Fetch media info and BPM once
        artist, title, album = await self.get_media_info_async()
        if artist and title:
            bpm = self.get_song_bpm(artist, title)

            # Use a lock to safely update the shared data
            with self.lock:
                self.current_song = f"{artist} - {title}"
                self.current_bpm = bpm
                self.current_album = album
        elif title:
            with self.lock:
                self.current_song = title
                self.current_bpm = None
                self.current_album = None
        else:
            with self.lock:
                self.current_song = "No media playing"
                self.current_bpm = None
                self.current_album = None

    def fetch(self):
        # Run the async method in a synchronous context
        asyncio.run(self.fetch_once())

    def get_current_song_and_bpm(self):
        # Use a lock to safely retrieve the song and bpm data
        with self.lock:
            return self.current_song, self.current_bpm, self.current_album
