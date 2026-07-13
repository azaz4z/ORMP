import sys
import os
import json
import threading
import time
import math
from tinytag import TinyTag
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QAbstractItemView, QFileDialog, QListWidgetItem
from PySide6.QtCore import QTimer, QStringListModel, Qt, Slot, QMetaObject, Q_ARG
from PySide6.QtGui import QKeySequence, QShortcut
import subprocess

from ui.main_interface import Ui_MainWindow
from ui.source import SourceFrame
from ui.player import PlayerWidget
from ui.skins import SkinFrame
from vinyl.vinyl_physics import VinylPhysics
from vinyl.vinyl_visual import VinylVisual
from ui.progress_bar import ProgressBar
from audio.audio_engine import AudioEngine
from audio.volume_control import VolumeControl
from audio.spot_tools import SpotTools
from file_handler import FileHandler

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.resize(1120, 720)
        
        self.is_running = True
        self.audio_lock = threading.Lock()
        
        # Initialize audio engine
        self.audio_engine = AudioEngine()
        
        # Find the first available song in the default local directory
        self.current_local_dir = "songs"
        songs_dir = self.current_local_dir
        song_path = None
        if os.path.exists(songs_dir):
            valid_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')
            for f in os.listdir(songs_dir):
                if f.lower().endswith(valid_extensions):
                    song_path = os.path.join(songs_dir, f)
                    break
                    
        if song_path:
            self.audio_engine.load_file(song_path)
            # Extract Metadata
            tag = TinyTag.get(song_path)
            artist = tag.artist or "Unknown Artist"
            title = tag.title or "Unknown Title"
        else:
            artist = "No songs found"
            title = "Add music to the songs/ directory"
            
        rate = self.audio_engine.rate if song_path else 44100
        frames = self.audio_engine.total_frames if song_path else 44100
        
        # Physical Object (Model)
        self.vinyl_physics = VinylPhysics(rate, frames)
        
        # Add Player Frame to Stacked Widget
        self.player_widget = PlayerWidget()
        self.stacked_widget.addWidget(self.player_widget)
        
        # Add Source Frame to Stacked Widget
        self.source_frame = SourceFrame()
        self.stacked_widget.addWidget(self.source_frame)
        
        # Add Skin Frame to Stacked Widget
        self.skin_frame = SkinFrame()
        self.stacked_widget.addWidget(self.skin_frame)
        
        # Additional aliases for controls
        self.upper_frame = self.player_widget.upper_frame
        self.program_title = self.player_widget.program_title
        self.vinyl_frame = self.player_widget.vinyl_frame
        self.song_list = self.player_widget.song_list
        self.play_button = self.player_widget.play_button
        self.stop_button = self.player_widget.stop_button
        self.next_track_button = self.player_widget.next_track_button
        self.prev_track_button = self.player_widget.prev_track_button
        self.progress_bar = self.player_widget.progress_bar
        self.song_title_label = self.player_widget.song_title_label
        self.song_controls_layout = self.player_widget.song_controls_layout
        self.song_info_frame = self.player_widget.song_info_frame
        
        # Inject the vinyl into the Designer frame with adjusted paddings
        layout_vinilo = QVBoxLayout(self.vinyl_frame)
        layout_vinilo.setContentsMargins(0, 10, 0, 10)
        self.vinyl_ui = VinylVisual(self.vinyl_physics)
        layout_vinilo.addWidget(self.vinyl_ui)
        
        # Replace the standard Designer bar with our interactive bar
        self.progress_bar.hide()
        self.custom_progress_bar = ProgressBar(self.vinyl_physics, self.song_info_frame)
        # Add to the controls Layout
        self.song_controls_layout.addWidget(self.custom_progress_bar, stretch=1)
        self.custom_progress_bar.show()
        
        # Connect jump signal
        self.custom_progress_bar.jump_requested.connect(self.vinyl_physics.request_jump)
        
        # System Volume Control Setup
        self.volume_manager = VolumeControl()
        current_volume = self.volume_manager.get_volume()
        
        # Calculate inverse cubic curve to set initial slider position
        slider_initial_val = int(math.pow(current_volume, 1.0/3.0) * 100)
        self.player_widget.volume_slider.setValue(slider_initial_val)
        self.player_widget.volume_slider.valueChanged.connect(self.on_volume_changed)
        
        # Spotify Tools
        self.spot_tools = SpotTools()
        
        # Setup Metadata and Timer
        self.song_title_label.setText(f"{artist} - {title}")
        self.song_title_label.adjustSize()
        
        # Playback Controls
        self.is_playing = False
        self.play_button.clicked.connect(self.play_clicked)
        self.stop_button.clicked.connect(self.stop_clicked)
        
        # Global Shortcut for R (Rotate)
        self.shortcut_r = QShortcut(QKeySequence("R"), self)
        self.shortcut_r.activated.connect(self.toggle_rotation)
        
        # Connect keys
        self.pressed_keys = {'u': False, 'j': False, 'l': False, 'o': False}
        # Option List
        self.option_model = QStringListModel(["Player", "Source", "Skin"])
        self.option_list.setModel(self.option_model)
        self.option_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.option_list.clicked.connect(self.on_option_selected)
        
        # Connect Source Checkboxes
        self.source_frame.local_checkbox.toggled.connect(self.on_source_changed)
        self.source_frame.spotify_checkbox.toggled.connect(self.on_source_changed)
        self.source_frame.spotify_add_button.clicked.connect(self.handle_spotify_add)
        
        # Connect Local Checkboxes & Buttons
        self.source_frame.local_browse_button.clicked.connect(self.browse_local_folder)
        self.source_frame.local_load_button.clicked.connect(self.load_local_folder)
        
        # Connect History Lists
        self.source_frame.local_saved_list.itemChanged.connect(self.on_local_item_changed)
        self.source_frame.spotify_saved_list.itemChanged.connect(self.on_spotify_item_changed)
        
        # Connect Skin Checkboxes & Buttons
        self.skin_frame.default_checkbox.toggled.connect(self.on_skin_changed)
        self.skin_frame.model_3d_checkbox.toggled.connect(self.on_skin_changed)
        self.skin_frame.load_skin_button.clicked.connect(self.load_custom_skin)
        # Load configurations
        self.file_handler = FileHandler()
        self.album_skins = self.file_handler.load_album_skins()
        self.saved_sources = self.file_handler.load_saved_sources()
        self.refresh_saved_lists()
        
        # Start with empty song list
        self.current_source = None
        self.current_local_dir = "songs"
        self.current_songs_map = {}
        self.spotify_playlist_cache = {}
        self.song_model = QStringListModel(["(No source selected)"])
        self.song_list.setModel(self.song_model)
        self.song_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.song_list.clicked.connect(self.on_song_selected)
        
        # Restore states from last session
        self.restore_states()
        
        # Timer at ~125 FPS
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(8) # 8 ms for ~125 FPS, smoother

    def on_source_changed(self):
        is_spotify = self.source_frame.spotify_checkbox.isChecked()
        self.source_frame.spotify_url_input.setEnabled(is_spotify)
        self.source_frame.spotify_add_button.setEnabled(is_spotify)
        self.source_frame.spotify_saved_list.setEnabled(is_spotify)
        
        self.source_frame.local_folder_input.setEnabled(not is_spotify)
        self.source_frame.local_browse_button.setEnabled(not is_spotify)
        self.source_frame.local_load_button.setEnabled(not is_spotify)
        self.source_frame.local_saved_list.setEnabled(not is_spotify)
        
        if is_spotify:
            self.populate_song_list("spotify")
        else:
            self.populate_song_list("local")
            
    def on_skin_changed(self):
        is_3d = self.skin_frame.model_3d_checkbox.isChecked()
        if is_3d:
            self.vinyl_ui.set_skin("3d")
        else:
            self.vinyl_ui.set_skin("default")
            
    def browse_local_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder_path:
            self.source_frame.local_folder_input.setText(folder_path)

    def load_local_folder(self):
        folder_path = self.source_frame.local_folder_input.text().strip()
        if os.path.isdir(folder_path):
            self.current_local_dir = folder_path
            folder_name = os.path.basename(folder_path)
            if not folder_name:
                folder_name = folder_path
            self.add_to_history("local", {"name": folder_name, "path": folder_path})
            self.populate_song_list("local")
        else:
            print(f"Invalid directory: {folder_path}")
            
    def load_custom_skin(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 3D Model",
            "skins",
            "3D Models (*.glb *.obj *.gltf)"
        )
        if file_path:
            self.set_skin_from_path(file_path)

    def set_skin_from_path(self, skin_path):
        if os.path.exists(skin_path):
            success = self.vinyl_ui.skin_3d.load_model(skin_path)
            if success:
                self.skin_frame.model_3d_checkbox.blockSignals(True)
                self.skin_frame.model_3d_checkbox.setChecked(True)
                self.skin_frame.model_3d_checkbox.blockSignals(False)
                
                self.skin_frame.default_checkbox.blockSignals(True)
                self.skin_frame.default_checkbox.setChecked(False)
                self.skin_frame.default_checkbox.blockSignals(False)
                
                self.vinyl_ui.set_skin("3d")
        else:
            print(f"Skin not found: {skin_path}")

    def handle_spotify_add(self):
        input_url = self.source_frame.spotify_url_input.text().strip()
        if not input_url:
            return
            
        if "open.spotify.com/playlist/" in input_url:
            self._add_spotify_playlist(input_url)
        elif "open.spotify.com/track/" in input_url:
            self._add_spotify_track(input_url)
        else:
            print("Enlace de Spotify inválido. Por favor, pega una URL válida de Track o Playlist.")
            
        self.source_frame.spotify_url_input.clear()

    def _add_spotify_track(self, track_url_or_uri):
        if "open.spotify.com" in track_url_or_uri:
            track_id = track_url_or_uri.split("track/")[1].split("?")[0]
            track_uri = f"spotify:track:{track_id}"
        else:
            track_uri = track_url_or_uri
            
        # Check if we already have it in history to avoid slow network request
        track_info = None
        for item in self.saved_sources.get("spotify", []):
            if item.get("uri") == track_uri:
                track_info = item
                break
                
        if track_info:
            print(f"Track ya en historial, cargando rápido: {track_uri}")
        else:
            print("Fetching song title (this may take a while)...")
            track_info = self.spot_tools.get_track_metadata_full(track_uri)
            self.add_to_history("spotify", track_info)
        
        song_name = f"{track_info['title']} - {track_info['artist']}"
        
        songs_dict = {song_name: track_uri}
        self.spotify_playlist_cache[track_uri] = songs_dict
        
        if self.current_source == "spotify":
            self.populate_song_list("spotify")
            
        # Start background download and UI will be updated via signal
        import threading
        threading.Thread(target=self._background_download, args=(songs_dict,), daemon=True).start()

    def _add_spotify_playlist(self, playlist_url):
            
        print("Loading playlist (this may take a while)...")
        if playlist_url not in self.spotify_playlist_cache:
            songs = self.spot_tools.get_playlist_songs(playlist_url, limit=50)
            self.spotify_playlist_cache[playlist_url] = songs
        else:
            songs = self.spotify_playlist_cache[playlist_url]
            
        if self.current_source == "spotify":
            self.populate_song_list("spotify")
        
        playlist_name = f"Playlist: {playlist_url.split('/')[-1].split('?')[0]}"
        playlist_info = {
            "title": playlist_name,
            "artist": "Spotify",
            "album": "Playlist",
            "uri": playlist_url
        }
        self.add_to_history("spotify", playlist_info)
        
        # Start background download
        import threading
        threading.Thread(target=self._background_download, args=(songs,), daemon=True).start()

    def _background_download(self, songs_to_download):
        import os
        
        # UI Message
        QMetaObject.invokeMethod(self.source_frame.download_status_label, "setText", Qt.QueuedConnection, Q_ARG(str, "Downloading songs, they may not appear already on the Player tab..."))
        
        cache_dir = os.path.join("songs", ".spotify")
        os.makedirs(cache_dir, exist_ok=True)
        for song_name, uri in songs_to_download.items():
            track_id = uri.split(":")[-1]
            cache_path = os.path.join(cache_dir, f"{track_id}.wav")
            
            # Check if history already has path
            has_path = False
            for item in self.saved_sources.get("spotify", []):
                if item.get("uri") == uri and item.get("path") and os.path.exists(item["path"]):
                    has_path = True
                    break
                    
            if not has_path and not os.path.exists(cache_path):
                print(f"[BgDownloader] Descargando {uri}...")
                self.spot_tools.download_track_wav(uri, cache_path)
                
                # Update history JSON with path if possible
                self.saved_sources = self.file_handler.add_to_history(
                    self.saved_sources, "spotify", {"uri": uri, "path": cache_path}
                )
                        
            # Safely update the main UI from this thread
            QMetaObject.invokeMethod(self, "on_track_downloaded", Qt.QueuedConnection, Q_ARG(str, song_name), Q_ARG(str, uri))
            
        print("[BgDownloader] Proceso completado para fuente añadida.")
        QMetaObject.invokeMethod(self.source_frame.download_status_label, "setText", Qt.QueuedConnection, Q_ARG(str, ""))

    @Slot(str, str)
    def on_track_downloaded(self, song_name, uri):
        # We don't need to rebuild the list here, populate_song_list already did it
        pass

    def populate_song_list(self, source="local"):
        self.current_source = source
        self.current_songs_map = {}
        
        if source == "local":
            all_songs = []
            for i in range(self.source_frame.local_saved_list.count()):
                item = self.source_frame.local_saved_list.item(i)
                if item.checkState() == Qt.Checked:
                    item_data = item.data(Qt.UserRole)
                    if item_data and "path" in item_data:
                        path = item_data["path"]
                        if os.path.exists(path):
                            songs, songs_map = self.file_handler.get_local_songs(path)
                            all_songs.extend(songs)
                            self.current_songs_map.update(songs_map)
                            
            if not all_songs:
                self.song_model.setStringList(["(No music found or no folder selected)"])
            else:
                self.song_model.setStringList(all_songs)
                
        elif source == "spotify":
            all_songs = []
            for i in range(self.source_frame.spotify_saved_list.count()):
                item = self.source_frame.spotify_saved_list.item(i)
                if item.checkState() == Qt.Checked:
                    item_data = item.data(Qt.UserRole)
                    if item_data and "uri" in item_data:
                        uri = item_data["uri"]
                        if uri in self.spotify_playlist_cache:
                            songs_map = self.spotify_playlist_cache[uri]
                            self.current_songs_map.update(songs_map)
                            all_songs.extend(list(songs_map.keys()))
                            
            if not all_songs:
                self.song_model.setStringList(["(No source selected)"])
            else:
                self.song_model.setStringList(all_songs)

        self.song_list.setModel(self.song_model)
        self.song_list.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def on_option_selected(self, index):
        option_name = self.option_model.data(index)
        
        if option_name == "Player":
            self.stacked_widget.setCurrentIndex(0)
        elif option_name == "Source":
            self.stacked_widget.setCurrentIndex(1)
        elif option_name == "Skin":
            self.stacked_widget.setCurrentIndex(2)
        else:
            self.stacked_widget.setCurrentIndex(0)

    def add_to_history(self, category, data_dict):
        self.saved_sources = self.file_handler.add_to_history(self.saved_sources, category, data_dict)
        self.refresh_saved_lists()

    def refresh_saved_lists(self):
        self.source_frame.local_saved_list.blockSignals(True)
        self.source_frame.spotify_saved_list.blockSignals(True)
        
        self.source_frame.local_saved_list.clear()
        for item_data in self.saved_sources.get("local", []):
            name = item_data.get("name", "Unknown")
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, item_data)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.source_frame.local_saved_list.addItem(item)
            
        self.source_frame.spotify_saved_list.clear()
        for item_data in self.saved_sources.get("spotify", []):
            name = item_data.get("title", "Unknown")
            if "artist" in item_data:
                name = f"{name} - {item_data['artist']}"
                
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, item_data)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.source_frame.spotify_saved_list.addItem(item)
            
        self.source_frame.local_saved_list.blockSignals(False)
        self.source_frame.spotify_saved_list.blockSignals(False)

    def add_to_history(self, category, data_dict):
        self.saved_sources = self.file_handler.add_to_history(self.saved_sources, category, data_dict)
        self.refresh_saved_lists()

    def on_local_item_changed(self, item):
        if self.current_source == "local":
            self.populate_song_list("local")

    def on_spotify_item_changed(self, item):
        if item.checkState() == Qt.Checked:
            item_data = item.data(Qt.UserRole)
            uri = item_data.get("uri") if item_data else None
            
            if uri:
                if "playlist" in uri or "album" in uri:
                    self._add_spotify_playlist(uri)
                else:
                    self._add_spotify_track(uri)
        else:
            if self.current_source == "spotify":
                self.populate_song_list("spotify")

    def on_song_selected(self, index, auto_play=True):
        song_name = self.song_model.data(index)
        song_uri_or_path = self.current_songs_map[song_name]
        
        # Stop background processing and swap engine safely
        with self.audio_lock:
            self.audio_engine.close()
            self.audio_engine = AudioEngine()
            
            if self.current_source == "spotify":
                cache_dir = os.path.join("songs", ".spotify")
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir, exist_ok=True)
                track_id = song_uri_or_path.split(":")[-1]
                cache_path = os.path.join(cache_dir, f"{track_id}.wav")
                
                needs_download = True
                
                # Check history
                for item in self.saved_sources.get("spotify", []):
                    if item.get("uri") == song_uri_or_path:
                        if item.get("path") and os.path.exists(item["path"]):
                            cache_path = item["path"]
                            needs_download = False
                        else:
                            item["path"] = cache_path
                            self.file_handler.save_sources(self.saved_sources)
                        break
                        
                if os.path.exists(cache_path):
                    needs_download = False
                    
                if needs_download:
                    print(f"Downloading from Spotify: {song_name}...")
                    success = self.spot_tools.download_track_wav(song_uri_or_path, cache_path)
                    if not success:
                        print("Error: Could not retrieve audio for the track.")
                        return
                else:
                    print(f"Cargando track desde caché local: {cache_path}")
                
                self.audio_engine.load_file(cache_path)
                
                # Split Title - Artist if present
                if " - " in song_name:
                    title, artist = song_name.split(" - ", 1)
                else:
                    artist = "Spotify (librespot)"
                    title = song_name
            else:
                self.audio_engine.load_file(song_uri_or_path)
                
                tag = TinyTag.get(song_uri_or_path)
                artist = tag.artist if tag.artist else "Unknown Artist"
                title = tag.title if tag.title else song_name
                
            # Album Skin Mapping
            album_name = None
            if self.current_source == "spotify":
                for item in self.saved_sources.get("spotify", []):
                    if item.get("uri") == song_uri_or_path:
                        album_name = item.get("album")
                        break
            else:
                try:
                    tag = TinyTag.get(song_uri_or_path)
                    album_name = tag.album
                except Exception as e:
                    pass
                    
            if album_name and artist and artist in self.album_skins:
                if album_name in self.album_skins[artist]:
                    skin_path = self.album_skins[artist][album_name]
                    self.set_skin_from_path(skin_path)
                
            self.vinyl_physics.load_new_track(self.audio_engine.rate, self.audio_engine.total_frames)
            
            # Reset UI interactions
            self.custom_progress_bar.is_dragging = False
            self.vinyl_ui.is_dragging = False
            
        # Update Metadata
        self.song_title_label.setText(f"{artist} - {title}")
        self.song_title_label.adjustSize()
        
        # Short pause before playing (simulates needle dropping or gives user time)
        self.is_playing = False
        if auto_play:
            QTimer.singleShot(500, self.play_clicked)

    def update_ui(self):
        self.vinyl_ui.update()
        self.custom_progress_bar.update()

    def on_volume_changed(self, value):
        normalized = value / 100.0
        # Logarithmic (cubic) volume curve for natural human perception
        volume_level = math.pow(normalized, 3.0)
        self.volume_manager.set_volume(volume_level)

    def play_clicked(self):
        self.is_playing = True

    def stop_clicked(self):
        self.is_playing = False

    def toggle_rotation(self):
        if self.vinyl_ui.tilt_y_active:
            self.vinyl_ui.stop_rotate()
        else:
            self.vinyl_ui.start_rotate()

    def keyPressEvent(self, event):
        key = event.text().lower()
        if key in self.pressed_keys:
            self.pressed_keys[key] = True

    def keyReleaseEvent(self, event):
        # Prevent false negatives from OS autorepeat
        if event.isAutoRepeat():
            return
        key = event.text().lower()
        if key in self.pressed_keys:
            self.pressed_keys[key] = False

    def closeEvent(self, event):
        self.save_states()
        self.is_running = False
        time.sleep(0.1)
        self.audio_engine.close()
        event.accept()

    def save_states(self):
        # 1. Sources State
        sources_state = {
            "is_spotify": self.source_frame.spotify_checkbox.isChecked(),
            "checked_local": [],
            "checked_spotify": []
        }
        for i in range(self.source_frame.local_saved_list.count()):
            item = self.source_frame.local_saved_list.item(i)
            if item.checkState() == Qt.Checked:
                sources_state["checked_local"].append(item.text())
        for i in range(self.source_frame.spotify_saved_list.count()):
            item = self.source_frame.spotify_saved_list.item(i)
            if item.checkState() == Qt.Checked:
                sources_state["checked_spotify"].append(item.text())
        self.file_handler.save_state("sources", sources_state)

        # 2. Skin State
        skin_state = {
            "is_3d": self.skin_frame.model_3d_checkbox.isChecked()
        }
        self.file_handler.save_state("skin", skin_state)

        # 3. Player State
        current_song_name = None
        current_song_uri = None
        selected_indexes = self.song_list.selectedIndexes()
        if selected_indexes:
            current_song_name = self.song_model.data(selected_indexes[0], Qt.DisplayRole)
            current_song_uri = self.current_songs_map.get(current_song_name)
            
        current_progress = 0.0
        if getattr(self, "vinyl_physics", None) and self.vinyl_physics.max_angle > 0:
            current_progress = self.vinyl_physics.angle / self.vinyl_physics.max_angle
            
        player_state = {
            "volume": self.player_widget.volume_slider.value(),
            "current_song_name": current_song_name,
            "current_song_uri": current_song_uri,
            "current_source": self.current_source,
            "current_local_dir": getattr(self, "current_local_dir", ""),
            "progress": current_progress,
            "is_playing": getattr(self, "is_playing", False)
        }
        self.file_handler.save_state("player", player_state)

    def restore_states(self):
        # 1. Skin
        skin_state = self.file_handler.load_state("skin")
        if skin_state:
            is_3d = skin_state.get("is_3d", False)
            self.skin_frame.model_3d_checkbox.setChecked(is_3d)
            self.skin_frame.default_checkbox.setChecked(not is_3d)

        # 2. Sources
        sources_state = self.file_handler.load_state("sources")
        if sources_state:
            is_spotify = sources_state.get("is_spotify", False)
            self.source_frame.spotify_checkbox.setChecked(is_spotify)
            self.source_frame.local_checkbox.setChecked(not is_spotify)
            
            for i in range(self.source_frame.local_saved_list.count()):
                item = self.source_frame.local_saved_list.item(i)
                if item.text() in sources_state.get("checked_local", []):
                    item.setCheckState(Qt.Checked)
                    
            for i in range(self.source_frame.spotify_saved_list.count()):
                item = self.source_frame.spotify_saved_list.item(i)
                if item.text() in sources_state.get("checked_spotify", []):
                    item.setCheckState(Qt.Checked)

        # 3. Player
        player_state = self.file_handler.load_state("player")
        if player_state:
            vol = player_state.get("volume", 50)
            self.player_widget.volume_slider.setValue(vol)
            
            song_name = player_state.get("current_song_name")
            song_uri = player_state.get("current_song_uri")
            
            self.current_source = player_state.get("current_source", self.current_source)
            self.current_local_dir = player_state.get("current_local_dir", getattr(self, "current_local_dir", ""))
            progress = player_state.get("progress", 0.0)
            is_playing = player_state.get("is_playing", False)
            
            if song_name and song_uri and song_name != "(No source selected)":
                self.current_songs_map[song_name] = song_uri
                self.song_model.setStringList(list(self.current_songs_map.keys()))
                
                rows = self.song_model.stringList()
                if song_name in rows:
                    index = self.song_model.index(rows.index(song_name), 0)
                    self.song_list.setCurrentIndex(index)
                    # Trigger load with saved playback state
                    self.on_song_selected(index, auto_play=is_playing)
                    self.vinyl_physics.request_jump(progress)


    def audio_loop(self):
        while self.is_running:
            if self.custom_progress_bar.is_dragging:
                # Pause physics so the song doesn't advance on its own while dragging the bar
                self.vinyl_physics.velocity = 0
            elif not self.vinyl_ui.is_dragging:
                if not self.is_playing:
                    target_velocity = 0
                elif self.pressed_keys.get('u'):
                    target_velocity = -3.0 * self.vinyl_physics.normal_velocity
                elif self.pressed_keys.get('o'):
                    target_velocity = 3.0 * self.vinyl_physics.normal_velocity
                elif self.pressed_keys.get('j'):
                    target_velocity = -1.5 * self.vinyl_physics.normal_velocity
                elif self.pressed_keys.get('l'):
                    target_velocity = 1.5 * self.vinyl_physics.normal_velocity
                else:
                    target_velocity = self.vinyl_physics.normal_velocity

                self.vinyl_physics.update(target_velocity)
            else:
                self.vinyl_physics.drag_spring()

            start_pos, end_pos = self.vinyl_physics.get_audio_range()

            with self.audio_lock:
                self.audio_engine.process(start_pos, end_pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Start audio thread in background
    thread = threading.Thread(target=window.audio_loop, daemon=True)
    thread.start()

    sys.exit(app.exec())
