import soundfile as sf
import pyaudio
import numpy as np
import io

from audio.vorbis_decoder import VorbisDecoder

CHUNK = 1024
CROSSFADE_LEN = 64

class AudioEngine:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.audio = None
        self.total_frames = 0
        self.channels = 2
        self.rate = 44100
        self.sampwidth = 2
        
        self.audio_overlap = np.zeros(
            (CROSSFADE_LEN, self.channels),
            dtype=np.float32
        )

        self.fade_in = np.linspace(
            0, 1, CROSSFADE_LEN, dtype=np.float32
        ).reshape(-1, 1)

        self.fade_out = 1.0 - self.fade_in

    def load_file(self, file_path):
        data, samplerate = sf.read(file_path, dtype='int16')
        
        if data.ndim == 1:
            data = data.reshape(-1, 1)
            self.channels = 1
        else:
            self.channels = data.shape[1]
            
        self.audio = data
        self.rate = samplerate
        self.sampwidth = 2
        self._init_audio()
        
    def load_byte(self, raw_bytes, rate=44100, channels=2, sampwidth=2):
        if raw_bytes.startswith(b'OggS'):
            print("[AudioEngine] Flujo Ogg Vorbis detectado. Decodificando con FFmpeg...")
            pcm_bytes = VorbisDecoder.decode(raw_bytes)
            data = np.frombuffer(pcm_bytes, dtype=np.int16)
            samplerate = 44100
            channels = 2
        else:
            virtual_file = io.BytesIO(raw_bytes)
            try:
                # 1. Intentar decodificar automáticamente
                data, samplerate = sf.read(virtual_file, dtype='int16')
            except Exception as e1:
                print(f"[AudioEngine] Fallo al decodificar como OGG nativo: {e1}")
                # 2. Si falla, intentar forzar como RAW PCM
                virtual_file.seek(0)
                try:
                    data, samplerate = sf.read(virtual_file, channels=channels, samplerate=rate, format='RAW', subtype='PCM_16', dtype='int16')
                except Exception as e2:
                    print(f"[AudioEngine] Fallo al decodificar como RAW PCM: {e2}")
                    raise ValueError("No se pudo decodificar el flujo de audio. FFmpeg no fue utilizado porque no era OggS.")

        if data.ndim == 1:
            data = data.reshape(-1, channels if channels > 1 else 1)
        
        self.audio = data
        self.rate = samplerate
        self.channels = data.shape[1]
        self.sampwidth = sampwidth
        self._init_audio()

    def _init_audio(self):
        self.total_frames = len(self.audio)
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        self.stream = self.p.open(
            format=self.p.get_format_from_width(self.sampwidth),
            channels=self.channels,
            rate=self.rate,
            output=True
        )
        
        self.audio_overlap = np.zeros(
            (CROSSFADE_LEN, self.channels),
            dtype=np.float32
        )
        
        self.fade_in = np.linspace(
            0, 1, CROSSFADE_LEN, dtype=np.float32
        ).reshape(-1, 1)

        self.fade_out = 1.0 - self.fade_in

    def generate_chunk(self, start_pos, end_pos):
        if abs(end_pos - start_pos) < 0.1:
            data_float = np.zeros(
                (CHUNK + CROSSFADE_LEN, self.channels),
                dtype=np.float32
            )
        else:
            data_float = self._interpolate(start_pos, end_pos)

        data_float = self._apply_crossfade(data_float)
        return data_float[:-CROSSFADE_LEN]

    def _interpolate(self, start_pos, end_pos):
        frames_velocity = (end_pos - start_pos) / CHUNK
        extended_end_pos = end_pos + frames_velocity * CROSSFADE_LEN

        indices = np.linspace(
            start_pos,
            extended_end_pos,
            CHUNK + CROSSFADE_LEN,
            endpoint=False
        )

        idx = np.clip(
            np.floor(indices),
            0,
            self.total_frames - 2
        ).astype(int)

        frac = (indices - idx).reshape(-1, 1).astype(np.float32)

        data0 = self.audio[idx].astype(np.float32)
        data1 = self.audio[idx + 1].astype(np.float32)

        return data0 * (1.0 - frac) + data1 * frac

    def _apply_crossfade(self, data):
        data[:CROSSFADE_LEN] = (
            data[:CROSSFADE_LEN] * self.fade_in
            + self.audio_overlap * self.fade_out
        )

        self.audio_overlap = data[-CROSSFADE_LEN:].copy()
        return data

    def write(self, data):
        data = np.clip(data, -32768, 32767)
        self.stream.write(data.astype(np.int16).tobytes())

    def process(self, start_pos, end_pos):
        data = self.generate_chunk(start_pos, end_pos)
        self.write(data)

    def close(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()