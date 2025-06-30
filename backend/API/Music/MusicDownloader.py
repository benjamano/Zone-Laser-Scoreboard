"""
YouTube Music Downloader with Album Metadata
Downloads songs from YouTube as MP3 files and adds album information to metadata.

Yes this was made by claude, yes im proud of it, yes i am lazy
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON

class YouTubeMusicDownloader:
    """Downloads music from YouTube and manages metadata."""
    
    def __init__(self, download_path: str = "./downloads", ffmpeg_path: str = None):
        """
        Initialize the downloader.
        
        Args:
            download_path: Directory where MP3 files will be saved
            ffmpeg_path: Path to FFmpeg executable (optional)
        """
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)
        self.ffmpeg_path = ffmpeg_path
        
        # yt-dlp options for audio extraction
        # Try to use FFmpeg first, fallback to direct download if not available
        base_opts = {
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'noplaylist': True,
        }
        
        # Add FFmpeg path if provided
        if self.ffmpeg_path:
            base_opts['ffmpeg_location'] = self.ffmpeg_path
        
        try:
            import subprocess
            # Test FFmpeg availability
            ffmpeg_cmd = str(Path(self.ffmpeg_path) / 'ffmpeg.exe') if self.ffmpeg_path else 'ffmpeg'
            subprocess.run([ffmpeg_cmd, '-version'], capture_output=True, check=True)
            
            # FFmpeg is available
            self.ydl_opts = {
                **base_opts,
                'format': 'bestaudio/best',
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': '192',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            print("✅ FFmpeg detected - will convert to MP3")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # FFmpeg not available, use direct download
            print("⚠️  FFmpeg not found. Downloading in original format (may not be MP3).")
            self.ydl_opts = {
                **base_opts,
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
            }
    
    def search_and_download(self, song_name: str, album_name: str, 
                           artist_name: Optional[str] = None) -> Optional[str]:
        """
        Search for a song on YouTube and download it.
        
        Args:
            song_name: Name of the song to search for
            album_name: Album name to add to metadata
            artist_name: Artist name (optional, will be extracted if not provided)
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        try:
            # Create search query
            search_query = f"{song_name}"
            if artist_name:
                search_query = f"{artist_name} {song_name}"
            
            search_query += " audio"  # Prefer audio-only results
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Search for the song
                search_results = ydl.extract_info(
                    f"ytsearch1:{search_query}", 
                    download=False
                )
                
                if not search_results or 'entries' not in search_results:
                    print(f"❌ No results found for: {song_name}")
                    return None
                
                video_info = search_results['entries'][0]
                video_url = video_info['webpage_url']
                video_title = video_info.get('title', song_name)
                
                print(f"🎵 Downloading: {video_title}")
                
                # Download the audio
                ydl.download([video_url])
                
                # Find the downloaded file
                downloaded_file = self._find_downloaded_file(video_title)
                
                if downloaded_file:
                    # Add metadata
                    self._add_metadata(
                        downloaded_file, 
                        song_name, 
                        album_name, 
                        artist_name or video_info.get('uploader', 'Unknown Artist')
                    )
                    print(f"✅ Downloaded and tagged: {downloaded_file.name}")
                    return str(downloaded_file)
                else:
                    print(f"❌ Could not locate downloaded file for: {song_name}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error downloading {song_name}: {str(e)}")
            return None
    
    def _find_downloaded_file(self, title: str) -> Optional[Path]:
        """Find the downloaded audio file based on the video title."""
        # Clean the title for filename matching
        clean_title = self._clean_filename(title)
        
        # Look for audio files that might match (mp3, m4a, webm, etc.)
        audio_extensions = ['*.mp3', '*.m4a', '*.webm', '*.opus', '*.ogg']
        
        for ext in audio_extensions:
            for file_path in self.download_path.glob(ext):
                if clean_title.lower() in file_path.stem.lower():
                    return file_path
        
        # If exact match not found, return the most recently created audio file
        audio_files = []
        for ext in audio_extensions:
            audio_files.extend(self.download_path.glob(ext))
        
        if audio_files:
            return max(audio_files, key=lambda x: x.stat().st_mtime)
        
        return None
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename by removing problematic characters."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        return filename.strip()
    
    def _add_metadata(self, file_path: Path, title: str, album: str, artist: str):
        """Add metadata to the audio file."""
        try:
            file_ext = file_path.suffix.lower()
            
            if file_ext == '.mp3':
                # Handle MP3 files with ID3 tags
                audio_file = MP3(file_path, ID3=ID3)
                
                # Add ID3 tag if it doesn't exist
                if not audio_file.tags:
                    audio_file.add_tags()
                
                # Set metadata
                audio_file.tags[TIT2] = TIT2(encoding=3, text=title)          # Title
                audio_file.tags[TPE1] = TPE1(encoding=3, text=artist)         # Artist
                audio_file.tags[TALB] = TALB(encoding=3, text=album)          # Album
                audio_file.tags[TCON] = TCON(encoding=3, text='Music')        # Genre
                
                # Save the changes
                audio_file.save()
                
            elif file_ext == '.m4a':
                # Handle M4A files with MP4 tags
                from mutagen.mp4 import MP4
                audio_file = MP4(file_path)
                
                audio_file['\xa9nam'] = [title]    # Title
                audio_file['\xa9ART'] = [artist]   # Artist
                audio_file['\xa9alb'] = [album]    # Album
                audio_file['\xa9gen'] = ['Music']  # Genre
                
                audio_file.save()
                
            else:
                print(f"⚠️ Warning: Metadata not supported for {file_ext} files")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not add metadata to {file_path.name}: {str(e)}")
    
    def download_playlist(self, songs_info: List[Dict[str, str]]) -> List[str]:
        """
        Download multiple songs.
        
        Args:
            songs_info: List of dictionaries with keys: 'song', 'album', 'artist' (optional)
            
        Returns:
            List of successfully downloaded file paths
        """
        downloaded_files = []
        
        print(f"🎼 Starting download of {len(songs_info)} songs...")
        
        for i, song_info in enumerate(songs_info, 1):
            song_name = song_info.get('song')
            album_name = song_info.get('album')
            artist_name = song_info.get('artist')
            
            if not song_name or not album_name:
                print(f"❌ Skipping invalid entry {i}: missing song or album name")
                continue
            
            print(f"\n[{i}/{len(songs_info)}] Processing: {song_name}")
            
            downloaded_file = self.search_and_download(song_name, album_name, artist_name)
            if downloaded_file:
                downloaded_files.append(downloaded_file)
        
        print(f"\n🎉 Download complete! {len(downloaded_files)} songs downloaded successfully.")
        return downloaded_files


def main():
    """Example usage of the YouTube Music Downloader."""
    
    # Configuration
    download_folder = "backend/data/music"  # Change this to your preferred folder
    
    # Specify FFmpeg path if it's not in your system PATH
    # Since FFmpeg is working in your terminal, try None first, then the path if needed
    ffmpeg_location = None  # Use system PATH first
    # ffmpeg_location = r"C:\ffmpeg\bin"  # Uncomment this line if None doesn't work
    
    # Example song list - modify this with your songs
    songs = [
        {
            'song': 'Moves Like Jagger - Radio Edit',
            'album': 'My Songs 2011',
            'artist': 'Maroon 5'
        },
        {
            'song': 'In the End',
            'album': 'Hybrid Theory (Bonus Edition)',
            'artist': 'Linkin Park'
        },
        {
            'song': 'Bad To The Bone',
            'album': 'BAD TO THE BONE',
            'artist': 'George Thorogood & The Destroyers'
        },
        {
            'song': 'Chelsea Dagger',
            'album': 'Costello Music',
            'artist': 'The Fratellis'
        },
        {
            'song': 'Hard Times',
            'album': 'After Laughter',
            'artist': 'Paramore'
        },
        {
            'song': 'Apple',
            'album': 'BRAT',
            'artist': 'Charli xcx'
        },
        {
            'song': "Crazy In Love (feat. JAY-Z)",
            'album': 'Dangerously In Love',
            'artist': 'Beyoncé'
        },
        {
            'song': 'Just Dance',
            'album': 'The Fame',
            'artist': 'Lady Gaga'
        },
        {
            'song': 'TiK ToK',
            'album': 'Animal (Expanded Edition)',
            'artist': 'Kesha'
        },
        {
            'song': 'Borderline',
            'album': 'The Slow Rush',
            'artist': 'Tame Impala'
        },
        {
            'song': 'Uptown Girl',
            'album': 'An Innocent Man',
            'artist': 'Billy Joel'
        },
        {
            'song': 'Last Friday Night (T.G.I.F.)',
            'album': 'Teenage Dream',
            'artist': 'Katy Perry'
        },
        {
            'song': 'Party In The U.S.A.',
            'album': 'The Time Of Our Lives',
            'artist': 'Miley Cyrus'
        },
        {
            'song': "DJ Got Us Fallin' In Love (feat. Pitbull)",
            'album': 'Raymond v Raymond (Expanded Edition)',
            'artist': 'USHER'
        },
        {
            'song': 'Domino',
            'album': 'Who You Are (Platinum Edition)',
            'artist': 'Jessie J'
        },
        {
            'song': 'Do I Wanna Know?',
            'album': 'AM',
            'artist': 'Arctic Monkeys'
        },
        {
            'song': 'We Like To Party! (The Vengabus)',
            'album': 'The Party Album!',
            'artist': 'Vengaboys'
        },
        {
            'song': 'Gimme! Gimme! Gimme! (A Man After Midnight)',
            'album': 'Voulez-Vous',
            'artist': 'ABBA'
        },
        {
            'song': 'Lay All Your Love On Me',
            'album': 'Super Trouper',
            'artist': 'ABBA'
        },
        {
            'song': 'Waterloo',
            'album': 'Waterloo',
            'artist': 'ABBA'
        },
        {
            'song': 'My Type',
            'album': 'My Type',
            'artist': 'Saint Motel'
        },
        {
            'song': 'Under Pressure - Remastered 2011',
            'album': 'Hot Space (2011 Remaster)',
            'artist': 'Queen'
        },
        {
            'song': 'The Gnomes Cometh (B)',
            'album': 'Unknown Album',
            'artist': 'Unknown Artist'
        },
        {
            'song': 'Beat It',
            'album': 'Thriller',
            'artist': 'Michael Jackson'
        },
        {
            'song': "Livin' la Vida Loca",
            'album': 'Ricky Martin',
            'artist': 'Ricky Martin'
        },
        {
            'song': 'Mamma Mia',
            'album': 'Abba',
            'artist': 'ABBA'
        },
        {
            'song': 'Bad Romance',
            'album': 'The Fame Monster (Deluxe Edition)',
            'artist': 'Lady Gaga'
        },
        {
            'song': 'Bad - 2012 Remaster',
            'album': 'Bad (Remastered)',
            'artist': 'Michael Jackson'
        },
        {
            'song': "U Can't Touch This",
            'album': "Please Hammer Don't Hurt 'Em",
            'artist': 'MC Hammer'
        },
        {
            'song': 'Snap Out Of It',
            'album': 'AM',
            'artist': 'Arctic Monkeys'
        },
        {
            'song': "Don't Stop Me Now - Remastered 2011",
            'album': 'Jazz (2011 Remaster)',
            'artist': 'Queen'
        },
        {
            'song': 'Take on Me',
            'album': 'Hunting High and Low',
            'artist': 'a-ha'
        },
        {
            'song': 'Sweet Dreams (Are Made of This) - 2005 Remaster',
            'album': 'Sweet Dreams (Are Made Of This)',
            'artist': 'Eurythmics'
        },
        {
            'song': "Everybody (Backstreet's Back) - Radio Edit",
            'album': "Backstreet's Back",
            'artist': 'Backstreet Boys'
        },
        {
            'song': 'Wake Me Up Before You Go-Go',
            'album': 'Make It Big',
            'artist': 'Wham!'
        },
        {
            'song': 'I Gotta Feeling',
            'album': 'THE E.N.D. (THE ENERGY NEVER DIES) [Deluxe Version]',
            'artist': 'Black Eyed Peas'
        },
        {
            'song': 'Another One Bites The Dust - Remastered 2011',
            'album': 'The Game (2011 Remaster)',
            'artist': 'Queen'
        },
        {
            'song': 'All Star',
            'album': 'Astro Lounge',
            'artist': 'Smash Mouth'
        },
        {
            'song': 'Dancing Queen',
            'album': 'Arrival',
            'artist': 'ABBA'
        },
        {
            'song': 'Bohemian Rhapsody - Remastered 2011',
            'album': 'A Night At The Opera (2011 Remaster)',
            'artist': 'Queen'
        }
    ]
    
    # Create downloader instance
    downloader = YouTubeMusicDownloader(download_folder, ffmpeg_location)
    
    # Download all songs
    downloaded_files = downloader.download_playlist(songs)
    
    # Print summary
    print(f"\n📁 All files saved to: {os.path.abspath(download_folder)}")
    print("Downloaded files:")
    for file_path in downloaded_files:
        print(f"  • {os.path.basename(file_path)}")


if __name__ == "__main__":
    # Check if required packages are installed
    try:
        import yt_dlp
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON
    except ImportError as e:
        print("❌ Missing required packages. Please install them using:")
        print("pip install yt-dlp mutagen")
        print("\nNote: For MP3 conversion, you also need FFmpeg installed.")
        print("Without FFmpeg, files will be downloaded in their original format (usually M4A).")
        sys.exit(1)
    
    main()