from librespot.core import Session
from librespot.metadata import PlaylistId, TrackId
from librespot.audio.decoders import AudioQuality, VorbisOnlyAudioQuality
from audio.vorbis_decoder import VorbisDecoder

class SpotTools:
    def __init__(self):
        self.session = None

    def _ensure_session(self):
        if not self.session:
            self.session = Session.Builder().stored_file().create()

    def get_playlist_songs(self, playlist_uri_or_url: str, limit: int = 20) -> dict:
        """
        Devuelve un diccionario { "Titulo - Artista": "spotify:track:..." }
        de las canciones de una playlist.
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
            
            # Limitar la cantidad para no demorar demasiado la UI
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
                    
            return songs_map
        except Exception as e:
            print(f"Error cargando playlist {uri}: {e}")
            return {}

    def get_track_metadata(self, track_uri: str) -> str:
        """
        Obtiene el metadato 'Titulo - Artista' para una canción suelta.
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

    def get_track_pcm(self, track_uri: str) -> bytes:
        """
        Descarga el track completo en formato Ogg Vorbis y lo decodifica a raw PCM.
        """
        self._ensure_session()
        
        try:
            t_id = TrackId.from_uri(track_uri)
            stream = self.session.content_feeder().load(
                t_id, 
                VorbisOnlyAudioQuality(AudioQuality.VERY_HIGH), 
                False, 
                None
            )
            # Read the entire stream byte by byte (returns bytes object in Ogg Vorbis)
            ogg_bytes = stream.input_stream.stream().read(-1)
            
            print(f"[SpotTools] Decodificando Ogg Vorbis para {track_uri}...")
            pcm_bytes = VorbisDecoder.decode(ogg_bytes)
            
            return pcm_bytes
        except Exception as e:
            print(f"[SpotTools] Fallo al descargar o decodificar el track {track_uri}: {e}")
            return None
