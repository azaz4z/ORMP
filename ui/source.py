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
        
        # Saved local folders list
        self.local_saved_list = QListWidget(self)
        self.local_saved_list.setObjectName("local_saved_list")
        self.local_saved_list.setFixedHeight(100) # Small fixed height
        self.layout.addWidget(self.local_saved_list)
        
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
        
        # Saved spotify sources list
        self.spotify_saved_list = QListWidget(self)
        self.spotify_saved_list.setObjectName("spotify_saved_list")
        self.spotify_saved_list.setFixedHeight(100)
        self.spotify_saved_list.setEnabled(False) # Disabled by default
        self.layout.addWidget(self.spotify_saved_list)
        
        # Download Status Label
        self.download_status_label = QLabel("", self)
        self.download_status_label.setObjectName("download_status_label")
        self.download_status_label.setAlignment(Qt.AlignCenter)
        self.download_status_label.setStyleSheet("color: gray; font-style: italic;")
        self.layout.addWidget(self.download_status_label)
        
        # Spacer final para empujar todo hacia arriba
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.spacer)
