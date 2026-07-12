import sys
import os
import threading
import time
import math
from tinytag import TinyTag
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QAbstractItemView, QFileDialog
from PySide6.QtCore import QTimer, QStringListModel
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

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.is_running = True
        self.audio_lock = threading.Lock()
        
        # Initialize audio engine
        self.audio_engine = AudioEngine()
        
        # Find the first available song in the songs/ directory
        songs_dir = "songs"
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
        self.source_frame.spotify_add_button.clicked.connect(self.add_spotify_track)
        self.source_frame.spotify_add_playlist_button.clicked.connect(self.add_spotify_playlist)
        
        # Connect Skin Checkboxes & Buttons
        self.skin_frame.default_checkbox.toggled.connect(self.on_skin_changed)
        self.skin_frame.model_3d_checkbox.toggled.connect(self.on_skin_changed)
        self.skin_frame.load_skin_button.clicked.connect(self.load_custom_skin)
        
        # Populate song list
        self.current_source = "local"
        self.populate_song_list("local")
        self.song_list.clicked.connect(self.on_song_selected)
        
        # Timer at ~125 FPS
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(8) # 8 ms for ~125 FPS, smoother

    def on_source_changed(self):
        is_spotify = self.source_frame.spotify_checkbox.isChecked()
        self.source_frame.spotify_url_input.setEnabled(is_spotify)
        self.source_frame.spotify_add_button.setEnabled(is_spotify)
        self.source_frame.spotify_playlist_input.setEnabled(is_spotify)
        self.source_frame.spotify_add_playlist_button.setEnabled(is_spotify)
        
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
            
    def load_custom_skin(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load 3D Model", "", "3D Models (*.glb)"
        )
        if file_path:
            print(f"Loading custom model directly: {file_path}")
            
            # Load the model exactly as the user selected it
            success = self.vinyl_ui.skin_3d.load_model(file_path)
                
            if success:
                # Activate 3D view automatically if loaded successfully
                self.skin_frame.model_3d_checkbox.setChecked(True)
                self.vinyl_ui.set_skin("3d")

    def add_spotify_track(self):
        track_url = self.source_frame.spotify_url_input.text().strip()
        if not track_url:
            return
            
        print("Fetching song title (this may take a while)...")
            
        # Extract URI if it's a URL
        if "open.spotify.com/track/" in track_url:
            track_id = track_url.split("track/")[1].split("?")[0]
            track_uri = f"spotify:track:{track_id}"
        else:
            track_uri = track_url
            
        song_name = self.spot_tools.get_track_metadata(track_uri)
        self.current_songs_map[song_name] = track_uri
        
        # Update model
        self.song_model.setStringList(list(self.current_songs_map.keys()))
        self.source_frame.spotify_url_input.clear()

    def add_spotify_playlist(self):
        playlist_url = self.source_frame.spotify_playlist_input.text().strip()
        if not playlist_url:
            return
            
        print("Loading playlist (this may take a while)...")
        songs = self.spot_tools.get_playlist_songs(playlist_url, limit=50)
        self.current_songs_map.update(songs)
        
        self.song_model.setStringList(list(self.current_songs_map.keys()))
        self.source_frame.spotify_playlist_input.clear()

    def populate_song_list(self, source="local"):
        self.current_source = source
        self.current_songs_map = {}
        
        if source == "local":
            songs_dir = "songs"
            if not os.path.exists(songs_dir):
                os.makedirs(songs_dir)
                
            valid_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')
            songs = []
            for f in os.listdir(songs_dir):
                if f.lower().endswith(valid_extensions):
                    songs.append(f)
                    self.current_songs_map[f] = os.path.join(songs_dir, f)
            
            self.song_model = QStringListModel(songs)
        elif source == "spotify":
            # Start with empty map, wait for user to add
            self.song_model = QStringListModel(["(Add a playlist or track from Source)"])
            self.current_songs_map = {}

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

    def on_song_selected(self, index):
        song_name = self.song_model.data(index)
        song_uri_or_path = self.current_songs_map[song_name]
        
        # Stop background processing and swap engine safely
        with self.audio_lock:
            self.audio_engine.close()
            self.audio_engine = AudioEngine()
            
            if self.current_source == "spotify":
                print(f"Downloading from Spotify: {song_name}...")
                audio_bytes = self.spot_tools.get_track_pcm(song_uri_or_path)
                if not audio_bytes:
                    print("Error: Could not retrieve audio for the track.")
                    return
                
                self.audio_engine.load_byte(audio_bytes, rate=44100, channels=2, sampwidth=2)
                
                # Split Title - Artist if present
                if " - " in song_name:
                    title, artist = song_name.split(" - ", 1)
                else:
                    artist = "Spotify (librespot)"
                    title = song_name
            else:
                self.audio_engine.load_file(song_uri_or_path)
                tag = TinyTag.get(song_uri_or_path)
                artist = tag.artist or "Unknown Artist"
                title = tag.title or "Unknown Title"
                
            self.vinyl_physics.load_new_track(self.audio_engine.rate, self.audio_engine.total_frames)
            
            # Reset UI interactions
            self.custom_progress_bar.is_dragging = False
            self.vinyl_ui.is_dragging = False
            
        # Update Metadata
        self.song_title_label.setText(f"{artist} - {title}")
        self.song_title_label.adjustSize()
        
        # Short pause before playing (simulates needle dropping or gives user time)
        self.is_playing = False
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
        self.is_running = False
        time.sleep(0.1)
        self.audio_engine.close()
        event.accept()


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
