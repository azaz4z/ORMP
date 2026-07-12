import io
import time
from librespot.core import Session
from librespot.metadata import TrackId
from librespot.audio.decoders import AudioQuality, VorbisOnlyAudioQuality

from audio_engine import AudioEngine

def main():
    print("Iniciando sesión en Spotify (librespot)...")
    session = Session.Builder().oauth(None).create()

    print("Buscando pista...")
    track_id = TrackId.from_uri("spotify:track:4RnvS1tmh1ERhjXX6dxv95")
    stream = session.content_feeder().load(track_id, VorbisOnlyAudioQuality(AudioQuality.VERY_HIGH), False, None)

    print("Descargando flujo comprimido de Spotify (Ogg Vorbis)...")
    # Leemos todo el flujo en memoria
    audio_bytes = stream.input_stream.stream().read(-1)
    
    print(f"Descargados {len(audio_bytes) / 1024 / 1024:.2f} MB.")
    print(audio_bytes[:32])
    
    print("Iniciando AudioEngine para decodificar Ogg Vorbis...")
    engine = AudioEngine()
    
    # librespot genera audio RAW PCM int16 a 44100Hz Stereo
    engine.load_byte(audio_bytes, rate=44100, channels=2, sampwidth=2)
    
    print(f"Éxito: Pista cargada. {engine.channels} canales, {engine.rate} Hz, {engine.total_frames} frames totales.")
    
    # Bucle de reproducción directa en consola (sin UI)
    chunk_size = 1024
    start_pos = 0
    
    print("\n▶ Reproduciendo música... (Presiona Ctrl+C para detener)")
    try:
        while start_pos < engine.total_frames:
            end_pos = start_pos + chunk_size
            engine.process(start_pos, end_pos)
            start_pos = end_pos
    except KeyboardInterrupt:
        print("\n⏹ Reproducción detenida por el usuario.")
    finally:
        engine.close()

if __name__ == "__main__":
    main()