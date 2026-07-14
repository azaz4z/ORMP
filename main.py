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
from ui.postprocessing import PostProcessingFrame
from vinyl.vinyl_physics import VinylPhysics
from vinyl.vinyl_visual import VinylVisual
from ui.custom_widgets.progress_bar import ProgressBar
from audio.audio_engine import AudioEngine
from audio.volume_control import VolumeControl
from spot.spot_tools import SpotTools
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtCore import QUrl
from file_handler import FileHandler

class QuietWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass  # Suppress all JS console messages from the web view

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.resize(1080, 700)
        
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
        
        # Add Post-Processing Frame to Stacked Widget
        self.postprocessing_frame = PostProcessingFrame()
        self.stacked_widget.addWidget(self.postprocessing_frame)
        
        # Add Spotify Web View to Stacked Widget
        self.spotify_web = QWebEngineView()
        
        # Create a persistent profile to keep session logged in
        profile = QWebEngineProfile("spotify_profile", self.spotify_web)
        cache_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".spotify_web_cache"))
        profile.setPersistentStoragePath(cache_path)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        
        self.quiet_page = QuietWebPage(profile, self.spotify_web)
        self.quiet_page.featurePermissionRequested.connect(
            lambda url, feature: self.quiet_page.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
        )
        self.spotify_web.setPage(self.quiet_page)
        self.spotify_web.load(QUrl("https://open.spotify.com/"))
        self.stacked_widget.addWidget(self.spotify_web)
        
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
        
        # Wire Post-Processing Signals
        self.postprocessing_frame.exposure_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("envExposure", v)
        )
        self.postprocessing_frame.bloom_enabled_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("envBloom", v)
        )
        self.postprocessing_frame.bloom_strength_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("envBloomStrength", v)
        )
        self.postprocessing_frame.ao_enabled_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("envAo", v)
        )
        self.postprocessing_frame.ao_strength_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("envAoStrength", v)
        )
        self.postprocessing_frame.metalness_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("matMetalness", v)
        )
        self.postprocessing_frame.roughness_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("matRoughness", v)
        )
        self.postprocessing_frame.anisotropy_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("matAnisotropy", v)
        )
        self.postprocessing_frame.anisotropy_rotation_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("matAnisotropyRotation", v)
        )
        self.postprocessing_frame.sheen_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("matSheen", v)
        )
        self.postprocessing_frame.sheen_roughness_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("matSheenRoughness", v)
        )
        self.postprocessing_frame.specular_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("matSpecular", v)
        )
        self.postprocessing_frame.clearcoat_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("matClearcoat", v)
        )
        self.postprocessing_frame.clearcoat_roughness_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("matClearcoatRoughness", v)
        )
        self.postprocessing_frame.opacity_changed.connect(
            lambda v: self.vinyl_ui.set_postprocessing("matOpacity", v)
        )
        
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
        self.option_model = QStringListModel(["Player", "Source", "Skin", "Postprocessing", "Spotify"])
        self.option_list.setModel(self.option_model)
        self.option_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.option_list.clicked.connect(self.on_option_selected)
        
        # Connect Source Checkboxes
        self.source_frame.local_checkbox.toggled.connect(self.on_source_changed)
        self.source_frame.spotify_checkbox.toggled.connect(self.on_source_changed)
        self.source_frame.spotify_add_button.clicked.connect(self.handle_spotify_add)
        
        # Connect Local Checks & Buttons
        self.source_frame.local_browse_button.clicked.connect(self.browse_local_folder)
        self.source_frame.local_load_button.clicked.connect(self.load_local_folder)
        
        # Connect History Lists
        self.source_frame.local_albums_list.itemClicked.connect(self.on_local_album_clicked)
        self.source_frame.local_remove_root_button.clicked.connect(self.remove_local_root)
        self.source_frame.spotify_playlists_list.itemChanged.connect(self.on_spotify_item_changed)
        self.source_frame.spotify_playlists_list.itemClicked.connect(self.on_spotify_playlist_clicked)
        self.source_frame.spotify_tracks_preview_list.itemClicked.connect(self.on_spotify_track_clicked)
        
        self.source_frame.spotify_delete_playlist_button.clicked.connect(self.delete_spotify_playlist)
        self.source_frame.spotify_delete_track_button.clicked.connect(self.delete_spotify_track)
        self.source_frame.spotify_stop_download_button.clicked.connect(self.stop_spotify_download)
        
        self.skin_frame.default_checkbox.toggled.connect(self.on_skin_changed)
        self.skin_frame.model_3d_checkbox.toggled.connect(self.on_skin_changed)
        self.skin_frame.load_skin_button.clicked.connect(self.load_custom_skin)
        self.skin_frame.fixer_button.clicked.connect(self.run_3d_fixer)
        # Load configurations
        self.file_handler = FileHandler()
        self.album_skins = self.file_handler.load_album_skins()
        self.saved_sources = self.file_handler.load_saved_sources()
        
        # Start with empty song list
        self.current_source = None
        self.current_local_dir = "songs"
        self.current_songs_map = {}
        
        # Load Spotify Cache
        self.spotify_playlist_cache = self.file_handler.load_state("spotify_cache") or {"tracks": {}, "playlists": {}}
        if "tracks" not in self.spotify_playlist_cache:
            self.spotify_playlist_cache = {"tracks": {}, "playlists": {}}
            
        # Migrate existing tracks into cache
        if not self.spotify_playlist_cache.get("tracks"):
            has_migrated_tracks = False
            for item in self.saved_sources.get("spotify", []):
                if "uri" in item and "title" in item and "playlist" not in item["uri"]:
                    uri = item["uri"]
                    artist = item.get("artist", "")
                    title = item["title"]
                    song_name = f"{title} - {artist}" if artist else title
                    self.spotify_playlist_cache["tracks"][uri] = song_name
                    has_migrated_tracks = True
            
            if has_migrated_tracks:
                self.spotify_playlist_cache["playlists"]["spotify:playlist:no_playlist"] = "No Playlist"
                self.file_handler.save_state("spotify_cache", self.spotify_playlist_cache)
                
        self.refresh_saved_lists()
        
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
        self.source_frame.spotify_playlists_list.setEnabled(is_spotify)
        self.source_frame.spotify_tracks_preview_list.setEnabled(is_spotify)
        self.source_frame.spotify_delete_playlist_button.setEnabled(is_spotify and bool(self.source_frame.spotify_playlists_list.currentItem()))
        self.source_frame.spotify_delete_track_button.setEnabled(is_spotify and bool(self.source_frame.spotify_tracks_preview_list.currentItem()))
        # Stop download button is only enabled when there are active workers
        self.source_frame.spotify_stop_download_button.setEnabled(is_spotify and hasattr(self, 'spotify_workers') and len(self.spotify_workers) > 0)
        
        self.source_frame.local_folder_input.setEnabled(not is_spotify)
        self.source_frame.local_browse_button.setEnabled(not is_spotify)
        self.source_frame.local_load_button.setEnabled(not is_spotify)
        self.source_frame.local_albums_list.setEnabled(not is_spotify)
        self.source_frame.local_tracks_preview_list.setEnabled(not is_spotify)
        self.source_frame.local_remove_root_button.setEnabled(not is_spotify)
        
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
            self.refresh_local_albums()
        else:
            print(f"Invalid directory: {folder_path}")
            
    def run_3d_fixer(self):
        try:
            # We import it here so we don't load trimesh globally on startup unless needed
            import importlib
            from fixer import model_fixer
            importlib.reload(model_fixer)
            model_fixer.run_fixer()
        except Exception as e:
            print(f"Error launching 3D Fixer: {e}")
            
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
            print("Invalid Spotify link. Please paste a valid Track or Playlist URL.")
            
        self.source_frame.spotify_url_input.clear()

    def _add_spotify_track(self, track_url_or_uri):
        if "open.spotify.com" in track_url_or_uri:
            track_id = track_url_or_uri.split("track/")[1].split("?")[0]
            track_uri = f"spotify:track:{track_id}"
        else:
            track_uri = track_url_or_uri
            
        self._start_spotify_worker(track_uri, is_playlist=False)

    def _add_spotify_playlist(self, playlist_url):
        self._start_spotify_worker(playlist_url, is_playlist=True)

    def _start_spotify_worker(self, url_or_uri, is_playlist):
        from spot.spot_worker import SpotifyWorker
        cache_dir = os.path.join("songs", ".spotify")
        
        if not hasattr(self, 'spotify_workers'):
            self.spotify_workers = []
            
        worker = SpotifyWorker(self.spot_tools, url_or_uri, is_playlist, cache_dir)
        worker.songs_discovered.connect(self.on_songs_discovered)
        worker.track_downloaded.connect(self.on_worker_track_downloaded)
        worker.finished.connect(lambda: self.on_worker_finished(worker))
        
        self.spotify_workers.append(worker)
        self.source_frame.spotify_stop_download_button.setEnabled(True)
        worker.start()
        
        if is_playlist:
            self.source_frame.download_status_label.setText("Adding a playlist can take a little, please wait...")
        else:
            self.source_frame.download_status_label.setText("Adding a song can take a little, please wait...")
        

    def on_worker_finished(self, worker):
        if worker in getattr(self, 'spotify_workers', []):
            self.spotify_workers.remove(worker)
        if not self.spotify_workers:
            self.source_frame.spotify_stop_download_button.setEnabled(False)
        self.source_frame.download_status_label.setText("")

    @Slot(dict, str, str)
    def on_songs_discovered(self, songs_dict, playlist_uri, playlist_name):
        
        # Always register as a playlist (even No Playlist)
        self.spotify_playlist_cache["playlists"][playlist_uri] = playlist_name
        
        # Map the tracks
        for song_name, track_uri in songs_dict.items():
            self.spotify_playlist_cache["tracks"][track_uri] = song_name
                
        self.file_handler.save_state("spotify_cache", self.spotify_playlist_cache)
        
        # Refresh the UI lists
        self.populate_spotify_sources(select_uri=playlist_uri)
        if self.current_source == "spotify":
            self.populate_song_list("spotify")

    @Slot(dict)
    def on_worker_track_downloaded(self, track_info):
        print(f"[DEBUG] on_worker_track_downloaded called with: {track_info}")
        
        # If the currently clicked playlist in the left pane is the one receiving a track, refresh the right pane
        current_item = self.source_frame.spotify_playlists_list.currentItem()
        if current_item:
            print(f"[DEBUG] current_item data: {current_item.data(Qt.UserRole)}, track_info playlist_uri: {track_info.get('playlist_uri')}")
            if current_item.data(Qt.UserRole) == track_info.get("playlist_uri"):
                self.on_spotify_playlist_clicked(current_item)
        else:
            print("[DEBUG] current_item is None")
                
        # If the playlist is currently checked (active), refresh the main song list
        if self.current_source == "spotify":
            for i in range(self.source_frame.spotify_playlists_list.count()):
                item = self.source_frame.spotify_playlists_list.item(i)
                if item.checkState() == Qt.Checked and item.data(Qt.UserRole) == track_info.get("playlist_uri"):
                    self.populate_song_list("spotify")
                    break
        
        # Auto-play if user is waiting
        uri = track_info.get("uri")
        if uri and getattr(self, "pending_play_uri", None) == uri:
            self.pending_play_uri = None
            self.vinyl_ui.is_downloading = False
            for i in range(self.song_model.rowCount()):
                index = self.song_model.index(i, 0)
                song_name = self.song_model.data(index)
                if self.current_songs_map.get(song_name) == uri:
                    self.song_list.setCurrentIndex(index)
                    self.on_song_selected(index)
                    break

    def populate_song_list(self, source="local"):
        self.current_source = source
        self.current_songs_map = {}
        
        if source == "local":
            all_songs = []
            album_item = self.source_frame.local_albums_list.currentItem()
            if album_item:
                album_data = album_item.data(Qt.UserRole)
                if album_data:
                    for song_name, song_path in album_data.items():
                        all_songs.append(song_name)
                        self.current_songs_map[song_name] = song_path
                            
            if not all_songs:
                self.song_model.setStringList(["(No local album selected)"])
            else:
                self.song_model.setStringList(all_songs)
                
        elif source == "spotify":
            all_songs = []
            for i in range(self.source_frame.spotify_playlists_list.count()):
                item = self.source_frame.spotify_playlists_list.item(i)
                if item.checkState() == Qt.Checked:
                    playlist_uri = item.data(Qt.UserRole)
                    if playlist_uri == "spotify:playlist:no_playlist":
                        folder_name = "No Playlist"
                    else:
                        folder_name = playlist_uri.split(":")[-1]
                        
                    folder_path = os.path.join("songs", ".spotify", folder_name)
                    if os.path.exists(folder_path):
                        for file_name in os.listdir(folder_path):
                            if file_name.endswith(".flac"):
                                track_id = file_name.replace(".flac", "")
                                track_uri = f"spotify:track:{track_id}"
                                track_name = self.spotify_playlist_cache.get("tracks", {}).get(track_uri, file_name)
                                self.current_songs_map[track_name] = track_uri
                                all_songs.append(track_name)
                                
            if not all_songs:
                self.song_model.setStringList(["(No source selected)"])
            else:
                self.song_model.setStringList(all_songs)

        self.song_list.setModel(self.song_model)
        self.song_list.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def on_option_selected(self, index):
        self.source_frame.download_status_label.setText("")
        selected_option = self.option_model.data(index)
        
        if selected_option == "Player":
            self.stacked_widget.setCurrentIndex(0)
        elif selected_option == "Source":
            self.stacked_widget.setCurrentIndex(1)
        elif selected_option == "Skin":
            self.stacked_widget.setCurrentIndex(2)
        elif selected_option == "Postprocessing":
            self.stacked_widget.setCurrentIndex(3)
        elif selected_option == "Spotify":
            self.stacked_widget.setCurrentIndex(4)
        else:
            self.stacked_widget.setCurrentIndex(0)

    def add_to_history(self, category, data_dict):
        self.saved_sources = self.file_handler.add_to_history(self.saved_sources, category, data_dict)
        self.refresh_saved_lists()

    def refresh_saved_lists(self):
        self.refresh_local_albums()
        self.populate_spotify_sources()

    def refresh_local_albums(self):
        self.source_frame.local_albums_list.clear()
        self.source_frame.local_tracks_preview_list.clear()
        
        for item in self.saved_sources.get("local", []):
            path = item.get("path")
            if path and os.path.exists(path):
                albums = self.file_handler.get_local_albums(path)
                for album_name, album_songs in albums.items():
                    list_item = QListWidgetItem(f"{album_name} ({len(album_songs)} tracks)")
                    list_item.setData(Qt.UserRole, album_songs)
                    self.source_frame.local_albums_list.addItem(list_item)
                    
    def on_local_album_clicked(self, item):
        self.source_frame.local_tracks_preview_list.clear()
        album_songs = item.data(Qt.UserRole)
        if album_songs:
            for song_name in album_songs.keys():
                self.source_frame.local_tracks_preview_list.addItem(song_name)
        if self.current_source == "local":
            self.populate_song_list("local")
            
    def remove_local_root(self):
        # Clears all saved root folders to start fresh
        self.saved_sources["local"] = []
        self.file_handler.save_sources(self.saved_sources)
        self.refresh_local_albums()
        if self.current_source == "local":
            self.populate_song_list("local")

    def populate_spotify_sources(self, select_uri=None):
        # Preserve check state (only 1 allowed)
        checked_uri = None
        for i in range(self.source_frame.spotify_playlists_list.count()):
            item = self.source_frame.spotify_playlists_list.item(i)
            if item.checkState() == Qt.Checked:
                checked_uri = item.data(Qt.UserRole)
                break
                
        self.source_frame.spotify_playlists_list.blockSignals(True)
        self.source_frame.spotify_playlists_list.clear()
        
        item_to_select = None
        # Add Playlists (this now includes "No Playlist" dynamically since we register it)
        for uri, name in self.spotify_playlist_cache.get("playlists", {}).items():
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, uri)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if checked_uri == uri else Qt.Unchecked)
            self.source_frame.spotify_playlists_list.addItem(item)
            if select_uri and uri == select_uri:
                item_to_select = item
                
        if item_to_select:
            self.source_frame.spotify_playlists_list.setCurrentItem(item_to_select)
            self.on_spotify_playlist_clicked(item_to_select)
            
        self.source_frame.spotify_playlists_list.blockSignals(False)

    def on_spotify_item_changed(self, item):
        # Ensure only one is checked
        if item.checkState() == Qt.Checked:
            self.source_frame.spotify_playlists_list.blockSignals(True)
            for i in range(self.source_frame.spotify_playlists_list.count()):
                other = self.source_frame.spotify_playlists_list.item(i)
                if other != item:
                    other.setCheckState(Qt.Unchecked)
            self.source_frame.spotify_playlists_list.blockSignals(False)
            
        if self.current_source == "spotify":
            self.populate_song_list("spotify")

    def on_spotify_playlist_clicked(self, item):
        playlist_uri = item.data(Qt.UserRole)
        
        # Don't allow deleting the 'No Playlist' folder
        self.source_frame.spotify_delete_playlist_button.setEnabled(playlist_uri != "spotify:playlist:no_playlist")
        
        if playlist_uri == "spotify:playlist:no_playlist":
            folder_name = "No Playlist"
        else:
            folder_name = playlist_uri.split(":")[-1]
            
        folder_path = os.path.join("songs", ".spotify", folder_name)
        
        self.source_frame.spotify_tracks_preview_list.clear()
        if os.path.exists(folder_path):
            for file_name in os.listdir(folder_path):
                if file_name.endswith(".flac"):
                    track_id = file_name.replace(".flac", "")
                    track_uri = f"spotify:track:{track_id}"
                    track_name = self.spotify_playlist_cache.get("tracks", {}).get(track_uri, file_name)
                    item = QListWidgetItem(track_name)
                    item.setData(Qt.UserRole, track_uri)
                    item.setData(Qt.UserRole + 1, os.path.join(folder_path, file_name))
                    self.source_frame.spotify_tracks_preview_list.addItem(item)
                    
    def on_spotify_track_clicked(self, item):
        self.source_frame.spotify_delete_track_button.setEnabled(True)

    def delete_spotify_playlist(self):
        item = self.source_frame.spotify_playlists_list.currentItem()
        if not item:
            return
            
        playlist_uri = item.data(Qt.UserRole)
        
        # Guard clause: double check we don't delete No Playlist
        if playlist_uri == "spotify:playlist:no_playlist":
            return
            
        folder_name = playlist_uri.split(":")[-1]
            
        # 1. Remove from cache
        if playlist_uri in self.spotify_playlist_cache.get("playlists", {}):
            del self.spotify_playlist_cache["playlists"][playlist_uri]
            self.file_handler.save_state("spotify_cache", self.spotify_playlist_cache)
            
        # 2. Delete physically
        folder_path = os.path.join("songs", ".spotify", folder_name)
        import shutil
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)
            except Exception as e:
                print(f"Error removing folder {folder_path}: {e}")
                
        # 3. Refresh UI
        self.populate_spotify_sources()
        self.source_frame.spotify_tracks_preview_list.clear()
        self.source_frame.spotify_delete_playlist_button.setEnabled(False)
        
        # If it was active in main list, clear it
        if self.current_source == "spotify":
            self.populate_song_list("spotify")

    def delete_spotify_track(self):
        track_item = self.source_frame.spotify_tracks_preview_list.currentItem()
        if not track_item:
            return
            
        track_uri = track_item.data(Qt.UserRole)
        track_path = track_item.data(Qt.UserRole + 1)
        
        # 1. Remove from cache
        if track_uri in self.spotify_playlist_cache.get("tracks", {}):
            del self.spotify_playlist_cache["tracks"][track_uri]
            self.file_handler.save_state("spotify_cache", self.spotify_playlist_cache)
            
        # 2. Delete physically
        if track_path and os.path.exists(track_path):
            try:
                os.remove(track_path)
            except Exception as e:
                print(f"Error removing song {track_path}: {e}")
                
        # 3. Refresh preview UI (re-trigger playlist click)
        playlist_item = self.source_frame.spotify_playlists_list.currentItem()
        if playlist_item:
            self.on_spotify_playlist_clicked(playlist_item)
            
        self.source_frame.spotify_delete_track_button.setEnabled(False)
        
        # 4. Refresh main UI if needed
        if self.current_source == "spotify":
            self.populate_song_list("spotify")

    def stop_spotify_download(self):
        if hasattr(self, 'spotify_workers'):
            for worker in self.spotify_workers:
                worker.stop()
            self.source_frame.download_status_label.setText("Canceling...")

    def on_song_selected(self, index, auto_play=True):
        song_name = self.song_model.data(index)
        song_uri_or_path = self.current_songs_map[song_name]
        
        # Stop playback immediately so vinyl stops spinning while loading/downloading
        self.is_playing = False
        
        # Stop background processing and swap engine safely
        with self.audio_lock:
            # Reset downloading state in case it was left hanging
            self.vinyl_ui.is_downloading = False
            
            self.audio_engine.close()
            self.audio_engine = AudioEngine()
            
            if self.current_source == "spotify":
                cache_path = ""
                # Find track recursively in songs/.spotify
                base_dir = os.path.join("songs", ".spotify")
                track_id = song_uri_or_path.split(":")[-1]
                target_file = f"{track_id}.flac"
                
                if os.path.exists(base_dir):
                    for root, dirs, files in os.walk(base_dir):
                        if target_file in files:
                            cache_path = os.path.join(root, target_file)
                            break
                            
                if not os.path.exists(cache_path):
                    print(f"The song {song_name} is still downloading in the background. Please wait.")
                    self.player_widget.song_frame.show_downloading()
                    self.pending_play_uri = song_uri_or_path
                    self.vinyl_ui.is_downloading = True
                    # We release the lock because we are returning early
                    return
                else:
                    print(f"Loading track from local cache: {cache_path}")
                
                try:
                    self.audio_engine.load_file(cache_path)
                except Exception as e:
                    print(f"Error loading file {cache_path}: {e}")
                    if os.path.exists(cache_path):
                        os.remove(cache_path)
                        print("Corrupted file deleted.")
                    return
                
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
        
        # Update Song Frame Metadata
        if self.current_source == "spotify":
            self.player_widget.song_frame.update_song_info(cache_path)
        else:
            self.player_widget.song_frame.update_song_info(song_uri_or_path)
        
        # Short pause before playing (simulates needle dropping or gives user time)
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
            "checked_spotify": []
        }
        for i in range(self.source_frame.spotify_playlists_list.count()):
            item = self.source_frame.spotify_playlists_list.item(i)
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
                    
            for i in range(self.source_frame.spotify_playlists_list.count()):
                item = self.source_frame.spotify_playlists_list.item(i)
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
