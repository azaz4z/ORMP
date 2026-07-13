import io
import av

class VorbisDecoder:
    @staticmethod
    def decode(audio_bytes):
        # Abrimos los bytes en memoria con PyAV
        container = av.open(io.BytesIO(audio_bytes), mode='r')
        
        # Configuramos un resampler para asegurar 44.1kHz, Estéreo, 16-bit PCM (s16le)
        # s16 es el equivalente en PyAV para s16le (16-bit little-endian)
        resampler = av.AudioResampler(
            format='s16', 
            layout='stereo', 
            rate=44100
        )
        
        pcm_data = bytearray()
        
        # Iteramos y decodificamos todos los paquetes del flujo de audio
        for frame in container.decode(audio=0):
            resampled_frames = resampler.resample(frame)
            for r_frame in resampled_frames:
                # Extraemos los bytes puros usando to_ndarray
                pcm_data.extend(r_frame.to_ndarray().tobytes())
                
        # Vaciamos el buffer final del resampler (flush)
        for r_frame in resampler.resample(None):
            pcm_data.extend(r_frame.to_ndarray().tobytes())
            
        return bytes(pcm_data)
