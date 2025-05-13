from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
import asyncio
import datetime

class MediaBPMFetcher:
    def __init__(self):
        self.current_song = None
        self.current_bpm = None
        self.current_album = None

    async def _get_media_info_async(self):
        try:
            sessions = await MediaManager.request_async()
            current_session = sessions.get_current_session()
            if current_session:
                # Fetch media properties asynchronously
                info = await current_session.try_get_media_properties_async()
                return info.artist, info.title, info.album_title
        except Exception as e:
            print(f"Error fetching media info at {datetime.datetime.now}: {e}")
        return None, None, None

    # def _get_song_bpm(self, artist, title):
    #     try:
    #         result = musicbrainzngs.search_recordings(query=f'"{title}" AND artist:"{artist}"', limit=1)
    #         recordings = result.get('recording-list', [])
    #         if recordings:
    #             mbid = recordings[0]['id']
    #             response = requests.get(f'https://acousticbrainz.org/api/v1/high-level/{mbid}')
    #             if response.status_code == 200:
    #                 data = response.json()
    #                 if 'rhythm' in data and 'bpm' in data['rhythm']:
    #                     return data['rhythm']['bpm']
    #         return "BPM not found"
    #     except Exception as e:
    #         return f"Error: {e}"

    def fetch_details(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            artist, title, album = loop.run_until_complete(self._get_media_info_async())
        finally:
            loop.close()

        if artist and title:
            # bpm = self._get_song_bpm(artist, title)
            self.current_song = f"{artist} - {title}"
            self.current_bpm = 0
            self.current_album = album
        elif title:
            self.current_song = title
            self.current_bpm = None
            self.current_album = None
        else:
            self.current_song = "No media playing"
            self.current_bpm = None
            self.current_album = None
            
    def get_current_song_and_bpm(self):
        self.fetch_details()
        
        return self.current_song, self.current_album, self.current_bpm