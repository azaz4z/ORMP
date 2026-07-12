import os
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

class VolumeControl:
    def __init__(self):
        self.pid = os.getpid()

    def get_audio_sessions(self):
        try:
            return AudioUtilities.GetAllSessions()
        except Exception:
            return []

    def set_volume(self, volume_level: float):
        """
        Sets the volume level for the current python process.
        volume_level should be between 0.0 and 1.0.
        """
        volume_level = max(0.0, min(1.0, volume_level))
        sessions = self.get_audio_sessions()
        
        for session in sessions:
            if session.Process and session.Process.pid == self.pid:
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                volume.SetMasterVolume(volume_level, None)

    def get_volume(self) -> float:
        """
        Gets the current volume level.
        Returns a float between 0.0 and 1.0, or 1.0 if session not found.
        """
        sessions = self.get_audio_sessions()
        for session in sessions:
            if session.Process and session.Process.pid == self.pid:
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                return volume.GetMasterVolume()
        return 1.0 # Default to max if not found
