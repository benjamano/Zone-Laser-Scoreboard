import asyncio
import threading
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class MediaBPMFetcher:
    def __init__(self, spotify_client_id, spotify_client_secret):
        self.auth_manager = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
        self.spotify = spotipy.Spotify(auth_manager=self.auth_manager)

        self.current_song = None
        self.current_bpm = None
        self.current_album = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run_fetch_loop, daemon=True)

    async def _get_media_info_async(self):
        try:
            sessions = await MediaManager.request_async()
            current_session = sessions.get_current_session()
            if current_session:
                info = await current_session.try_get_media_properties_async()
                return info.artist, info.title, info.album_title
        except Exception as e:
            print(f"Error fetching media info: {e}")
        return None, None, None

    def _get_song_bpm(self, artist, title):
        try:
            result = self.spotify.search(q=f"track:{title} artist:{artist}", type='track', limit=1)
            if result['tracks']['items']:
                track_id = result['tracks']['items'][0]['id']
                audio_features = self.spotify.audio_features(track_id)
                if audio_features and audio_features[0]:
                    return audio_features[0]['tempo']
            return "BPM not found"
        except Exception as e:
            return f"Error: {e}"

    async def _fetch_once(self):
        artist, title, album = await self._get_media_info_async()
        if artist and title:
            bpm = self._get_song_bpm(artist, title)
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

    def _run_fetch_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while not self.stop_event.is_set():
            loop.run_until_complete(self._fetch_once())
            self.stop_event.wait(5) 

    def start(self):
        if not self.thread.is_alive():
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join()

    def get_current_song_and_bpm(self):
        with self.lock:
            return self.current_song, self.current_bpm, self.current_album
        
    def fetch(self):
        asyncio.run(self._fetch_once())

