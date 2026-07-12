import subprocess

class VorbisDecoder:
    @staticmethod
    def decode(audio_bytes):
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-i", "pipe:0",
                "-f", "s16le",
                "-ar", "44100",
                "-ac", "2",
                "pipe:1"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        pcm, err = process.communicate(audio_bytes)
        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg decoding failed: {err.decode('utf-8', errors='ignore')}")
        return pcm
