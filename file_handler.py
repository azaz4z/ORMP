import os
import json

class FileHandler:
    def __init__(self):
        self.album_skins_file = "album_skins.json"
        self.saved_sources_file = "saved_sources.json"

    def load_album_skins(self):
        album_skins = {}
        if os.path.exists(self.album_skins_file):
            try:
                with open(self.album_skins_file, "r", encoding="utf-8") as f:
                    album_skins = json.load(f)
            except Exception as e:
                print(f"Error loading album_skins: {e}")
        else:
            album_skins = {
                "Playboi Carti": {
                    "Whole Lotta Red": "skins/carti_fixed.glb"
                }
            }
            self.save_album_skins(album_skins)
        return album_skins

    def save_album_skins(self, album_skins):
        try:
            with open(self.album_skins_file, "w", encoding="utf-8") as f:
                json.dump(album_skins, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving album_skins: {e}")
            return False

    def load_saved_sources(self):
        saved_sources = {"local": [], "spotify": []}
        if os.path.exists(self.saved_sources_file):
            try:
                with open(self.saved_sources_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data.get("local"), dict) or isinstance(data.get("spotify"), dict):
                        print("Old JSON format detected, resetting history.")
                    else:
                        saved_sources = data
            except Exception as e:
                print(f"Error loading saved sources: {e}")
        return saved_sources

    def save_sources(self, saved_sources):
        try:
            with open(self.saved_sources_file, "w", encoding="utf-8") as f:
                json.dump(saved_sources, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving sources: {e}")
            return False

    def add_to_history(self, saved_sources, category, data_dict):
        # Prevent duplicates
        if category == "local":
            for item in saved_sources["local"]:
                if item.get("path") == data_dict.get("path"):
                    return saved_sources
        elif category == "spotify":
            for item in saved_sources["spotify"]:
                if item.get("uri") == data_dict.get("uri"):
                    return saved_sources
                    
        saved_sources[category].append(data_dict)
        self.save_sources(saved_sources)
        return saved_sources

    def get_local_songs(self, directory):
        songs = []
        songs_map = {}
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")
                return songs, songs_map
                
        valid_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')
        try:
            for f in os.listdir(directory):
                if f.lower().endswith(valid_extensions):
                    songs.append(f)
                    songs_map[f] = os.path.join(directory, f)
        except Exception as e:
            print(f"Error reading directory {directory}: {e}")
            
        return songs, songs_map

    def load_state(self, module):
        state_dir = "states"
        file_path = os.path.join(state_dir, f"{module}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading state {module}: {e}")
        return {}

    def save_state(self, module, data):
        state_dir = "states"
        if not os.path.exists(state_dir):
            os.makedirs(state_dir, exist_ok=True)
            
        file_path = os.path.join(state_dir, f"{module}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving state {module}: {e}")
            return False
