from librespot.core import Session
from librespot.metadata import PlaylistId, TrackId
from librespot.audio.decoders import AudioQuality, VorbisOnlyAudioQuality
from audio.vorbis_decoder import VorbisDecoder
import soundfile as sf
import numpy as np

class SpotTools:
    def __init__(self):
        self.session = None

    def _ensure_session(self):
        if not self.session:
            self.session = Session.Builder().stored_file().create()

    def get_playlist_songs(self, playlist_uri_or_url: str, limit: int = 20) -> tuple:
        """
        Returns a dictionary { "Title - Artist": "spotify:track:..." }
        of the songs in a playlist.
        """
        self._ensure_session()
        
        if "open.spotify.com/playlist/" in playlist_uri_or_url:
            playlist_id = playlist_uri_or_url.split("playlist/")[1].split("?")[0]
            uri = f"spotify:playlist:{playlist_id}"
        else:
            uri = playlist_uri_or_url

        try:
            p_id = PlaylistId.from_uri(uri)
            playlist = self.session.api().get_playlist(p_id)
            
            # Limit the amount to avoid freezing the UI too long
            items = playlist.contents.items[:limit]
            
            songs_map = {}
            for item in items:
                track_uri = item.uri
                try:
                    t_id = TrackId.from_uri(track_uri)
                    metadata = self.session.api().get_metadata_4_track(t_id)
                    title = metadata.name
                    artist = metadata.artist[0].name if metadata.artist else "Unknown Artist"
                    key = f"{title} - {artist}"
                    songs_map[key] = track_uri
                except Exception as e:
                    print(f"Error fetching metadata for {track_uri}: {e}")
                    songs_map[f"Unknown Track ({track_uri})"] = track_uri
                    
            return playlist.attributes.name, songs_map
        except Exception as e:
            print(f"Error loading playlist {uri}: {e}")
            return "Unknown Playlist", {}

    def get_track_metadata(self, track_uri: str) -> str:
        """
        Gets the 'Title - Artist' metadata for a single track.
        """
        self._ensure_session()
        try:
            t_id = TrackId.from_uri(track_uri)
            metadata = self.session.api().get_metadata_4_track(t_id)
            title = metadata.name
            artist = metadata.artist[0].name if metadata.artist else "Unknown Artist"
            return f"{title} - {artist}"
        except Exception as e:
            print(f"Error fetching metadata for {track_uri}: {e}")
            return f"Unknown Track ({track_uri})"

    def get_track_metadata_full(self, track_uri: str) -> dict:
        """
        Gets the full metadata for a single track as a dictionary.
        """
        self._ensure_session()
        try:
            t_id = TrackId.from_uri(track_uri)
            metadata = self.session.api().get_metadata_4_track(t_id)
            title = metadata.name
            artist = metadata.artist[0].name if metadata.artist else "Unknown Artist"
            album = metadata.album.name if metadata.album else "Unknown Album"
            return {
                "title": title,
                "artist": artist,
                "album": album,
                "uri": track_uri
            }
        except Exception as e:
            print(f"Error fetching metadata for {track_uri}: {e}")
            return {
                "title": f"Unknown Track ({track_uri})",
                "artist": "Unknown Artist",
                "album": "Unknown Album",
                "uri": track_uri
            }

    def download_track_flac(self, track_uri: str, save_path: str) -> bool:
        """
        Downloads the track in OGG, saves it as FLAC, and embeds metadata and cover art.
        """
        self._ensure_session()
        
        try:
            t_id = TrackId.from_uri(track_uri)
            
            # 1. Get metadata and image
            metadata = self.session.api().get_metadata_4_track(t_id)
            title = metadata.name
            artist = metadata.artist[0].name if metadata.artist else "Unknown Artist"
            album = metadata.album.name if metadata.album else "Unknown Album"
            
            image_data = None
            if metadata.album and metadata.album.cover_group and metadata.album.cover_group.image:
                file_id_hex = metadata.album.cover_group.image[0].file_id.hex()
                image_url = f"https://i.scdn.co/image/{file_id_hex}"
                import urllib.request
                try:
                    req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        image_data = response.read()
                except Exception as e:
                    print(f"[SpotTools] Failed to download cover art: {e}")
            
            # 2. Download the audio
            pcm_bytes = None
            qualities = [AudioQuality.VERY_HIGH, AudioQuality.HIGH, AudioQuality.NORMAL]
            
            for quality in qualities:
                try:
                    stream = self.session.content_feeder().load(
                        t_id, 
                        VorbisOnlyAudioQuality(quality), 
                        False, 
                        None
                    )
                    if stream and stream.input_stream:
                        temp_bytes = stream.input_stream.stream().read(-1)
                        # Verify we got data and it is reasonably large
                        if temp_bytes and len(temp_bytes) > 4096:
                            try:
                                pcm_bytes = VorbisDecoder.decode(temp_bytes)
                                print(f"[SpotTools] Audio downloaded and decoded in quality: {quality}")
                                break
                            except Exception as decode_err:
                                print(f"[SpotTools] Error decoding quality {quality}: {decode_err}")
                except Exception as e:
                    print(f"[SpotTools] Failed attempt with quality {quality}: {e}")
            
            if not pcm_bytes:
                print(f"[SpotTools] Could not download/decode valid audio for {track_uri}")
                return False
            
            # 3. Save as FLAC in temp file
            temp_save_path = f"{save_path}.temp.flac"
            data = np.frombuffer(pcm_bytes, dtype=np.int16).reshape(-1, 2)
            sf.write(temp_save_path, data, 44100)
            
            # 4. Embed metadata with Mutagen
            from mutagen.flac import FLAC, Picture
            audio_tag = FLAC(temp_save_path)
            audio_tag["TITLE"] = title
            audio_tag["ARTIST"] = artist
            audio_tag["ALBUM"] = album
            
            if image_data:
                pic = Picture()
                pic.type = 3 # Front cover
                pic.mime = "image/jpeg"
                pic.desc = "Front Cover"
                pic.data = image_data
                audio_tag.add_picture(pic)
                
            audio_tag.save()
            
            # 5. Rename temp file to final destination
            import os
            if os.path.exists(save_path):
                os.remove(save_path)
            os.rename(temp_save_path, save_path)
            
            print(f"[SpotTools] Track cached as FLAC with metadata: {save_path}")
            return True
            
        except Exception as e:
            print(f"Error downloading {track_uri}: {e}")
            return False
