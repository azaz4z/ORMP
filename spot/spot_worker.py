import os
from PySide6.QtCore import QThread, Signal
from spot.spot_tools import SpotTools

class SpotifyWorker(QThread):
    songs_discovered = Signal(dict, str, str) # songs_dict, playlist_uri, playlist_name
    track_downloaded = Signal(dict) # item_data dict
    error = Signal(str)

    def __init__(self, spot_tools: SpotTools, url_or_uri: str, is_playlist: bool, cache_dir: str):
        super().__init__()
        self.spot_tools = spot_tools
        self.url_or_uri = url_or_uri
        self.is_playlist = is_playlist
        self.cache_dir = cache_dir
        self.is_cancelled = False
        
    def stop(self):
        self.is_cancelled = True

    def run(self):
        try:
            songs_dict = {}
            playlist_name = ""
            playlist_uri = self.url_or_uri

            if self.is_playlist:
                if "open.spotify.com/playlist/" in playlist_uri:
                    playlist_id = playlist_uri.split("playlist/")[1].split("?")[0]
                    playlist_uri = f"spotify:playlist:{playlist_id}"
                
                playlist_name, songs_dict = self.spot_tools.get_playlist_songs(self.url_or_uri, limit=50)
                
                # Extract ID for folder name
                folder_name = playlist_uri.split(":")[-1]
                self.cache_dir = os.path.join(self.cache_dir, folder_name)
            else:
                track_info = self.spot_tools.get_track_metadata_full(self.url_or_uri)
                song_name = f"{track_info['title']} - {track_info['artist']}"
                songs_dict = {song_name: self.url_or_uri}
                playlist_name = "No Playlist"
                playlist_uri = "spotify:playlist:no_playlist"
                
                folder_name = "No Playlist"
                self.cache_dir = os.path.join(self.cache_dir, folder_name)
                
                # For a single track, we can emit the metadata before downloading so it shows up in history
                self.track_downloaded.emit(track_info)

            # Emit discovered songs so the UI updates the list immediately
            self.songs_discovered.emit(songs_dict, playlist_uri, playlist_name)

            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)

            # Start downloading one by one
            for song_name, track_uri in songs_dict.items():
                if self.is_cancelled:
                    print("[BgDownloader] Download cancelled by user.")
                    break
                    
                track_id = track_uri.split(":")[-1]
                cache_path = os.path.join(self.cache_dir, f"{track_id}.flac")
                
                if not os.path.exists(cache_path):
                    print(f"[BgDownloader] Downloading {song_name}...")
                    success = self.spot_tools.download_track_flac(track_uri, cache_path)
                    if success:
                        self.track_downloaded.emit({"uri": track_uri, "path": cache_path, "playlist_uri": playlist_uri})
                else:
                    print(f"[BgDownloader] {song_name} already exists in cache.")
                    if self.is_playlist:
                        try:
                            track_info = self.spot_tools.get_track_metadata_full(track_uri)
                            track_info["path"] = cache_path
                            self.track_downloaded.emit(track_info)
                        except Exception as e:
                            pass

        except Exception as e:
            print(f"[BgDownloader] Error in thread: {e}")
            self.error.emit(str(e))
