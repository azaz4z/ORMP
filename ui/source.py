from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QCheckBox, QSpacerItem, QSizePolicy, QButtonGroup, QLineEdit, QPushButton, QHBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt

class SourceFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("source_frame")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        
        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Título
        self.title_label = QLabel("Source Configuration", self)
        self.title_label.setObjectName("source_title")
        self.title_label.setAlignment(Qt.AlignCenter)
        
        font = self.title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.title_label.setFont(font)
        
        self.layout.addWidget(self.title_label)
        
        # Espaciador
        self.layout.addSpacing(20)
        
        # Checkboxes
        self.local_checkbox = QCheckBox("Local Music (Physical files)", self)
        self.local_checkbox.setObjectName("local_checkbox")
        self.local_checkbox.setChecked(True) # Por defecto
        
        self.spotify_checkbox = QCheckBox("Spotify Music (Streaming)", self)
        self.spotify_checkbox.setObjectName("spotify_checkbox")
        
        self.source_group = QButtonGroup(self)
        self.source_group.addButton(self.local_checkbox)
        self.source_group.addButton(self.spotify_checkbox)
        
        self.layout.addWidget(self.local_checkbox)
        
        # Local Folder input
        self.local_folder_layout = QHBoxLayout()
        self.local_folder_input = QLineEdit(self)
        self.local_folder_input.setPlaceholderText("Paste local folder path here...")
        
        self.local_browse_button = QPushButton("Browse...", self)
        self.local_load_button = QPushButton("Load Folder", self)
        
        self.local_folder_layout.addWidget(self.local_folder_input)
        self.local_folder_layout.addWidget(self.local_browse_button)
        self.local_folder_layout.addWidget(self.local_load_button)
        
        self.layout.addLayout(self.local_folder_layout)
        
        # Split Local view: Albums (Left) and Songs Preview (Right)
        self.local_lists_layout = QHBoxLayout()
        
        self.local_albums_list = QListWidget(self)
        self.local_albums_list.setObjectName("local_albums_list")
        self.local_albums_list.setFixedHeight(150)
        
        self.local_tracks_preview_list = QListWidget(self)
        self.local_tracks_preview_list.setObjectName("local_tracks_preview_list")
        self.local_tracks_preview_list.setFixedHeight(150)
        self.local_tracks_preview_list.setSelectionMode(QListWidget.SingleSelection)
        
        self.local_lists_layout.addWidget(self.local_albums_list, 1)
        self.local_lists_layout.addWidget(self.local_tracks_preview_list, 2)
        
        self.layout.addLayout(self.local_lists_layout)
        
        # Local Controls Layout
        self.local_controls_layout = QHBoxLayout()
        self.local_remove_root_button = QPushButton("Remove Selected Root Folder", self)
        self.local_controls_layout.addWidget(self.local_remove_root_button)
        self.layout.addLayout(self.local_controls_layout)
        
        self.layout.addWidget(self.spotify_checkbox)
        
        # Single Spotify Input for both Tracks and Playlists
        self.spotify_input_layout = QHBoxLayout()
        self.spotify_url_input = QLineEdit(self)
        self.spotify_url_input.setPlaceholderText("Paste Spotify URL (Track or Playlist) here...")
        self.spotify_url_input.setEnabled(False) # Deshabilitado por defecto
        
        self.spotify_add_button = QPushButton("Add", self)
        self.spotify_add_button.setEnabled(False)
        
        self.spotify_input_layout.addWidget(self.spotify_url_input)
        self.spotify_input_layout.addWidget(self.spotify_add_button)
        
        self.layout.addLayout(self.spotify_input_layout)
        
        # Split Spotify view: Playlists (Left) and Songs Preview (Right)
        self.spotify_lists_layout = QHBoxLayout()
        
        self.spotify_playlists_list = QListWidget(self)
        self.spotify_playlists_list.setObjectName("spotify_playlists_list")
        self.spotify_playlists_list.setFixedHeight(150)
        self.spotify_playlists_list.setEnabled(False) # Disabled by default
        
        self.spotify_tracks_preview_list = QListWidget(self)
        self.spotify_tracks_preview_list.setObjectName("spotify_tracks_preview_list")
        self.spotify_tracks_preview_list.setFixedHeight(150)
        self.spotify_tracks_preview_list.setEnabled(False)
        self.spotify_tracks_preview_list.setSelectionMode(QListWidget.SingleSelection) # Allow selection for track deletion
        
        self.spotify_lists_layout.addWidget(self.spotify_playlists_list, 1) # 1 part width
        self.spotify_lists_layout.addWidget(self.spotify_tracks_preview_list, 2) # 2 parts width
        
        self.layout.addLayout(self.spotify_lists_layout)
        
        # Spotify Controls Layout
        self.spotify_controls_layout = QHBoxLayout()
        self.spotify_delete_playlist_button = QPushButton("Delete Playlist", self)
        self.spotify_delete_playlist_button.setEnabled(False)
        self.spotify_delete_track_button = QPushButton("Delete Track", self)
        self.spotify_delete_track_button.setEnabled(False)
        self.spotify_stop_download_button = QPushButton("Stop Download", self)
        self.spotify_stop_download_button.setEnabled(False)
        
        self.spotify_controls_layout.addWidget(self.spotify_delete_playlist_button)
        self.spotify_controls_layout.addWidget(self.spotify_delete_track_button)
        self.spotify_controls_layout.addWidget(self.spotify_stop_download_button)
        self.layout.addLayout(self.spotify_controls_layout)
        
        # Download Status Label
        self.download_status_label = QLabel("", self)
        self.download_status_label.setObjectName("download_status_label")
        self.download_status_label.setAlignment(Qt.AlignCenter)
        self.download_status_label.setStyleSheet("color: gray; font-style: italic;")
        self.layout.addWidget(self.download_status_label)
        
        # Spacer final para empujar todo hacia arriba
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.spacer)
