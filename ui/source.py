from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QCheckBox, QSpacerItem, QSizePolicy, QButtonGroup, QLineEdit, QPushButton, QHBoxLayout
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
        self.layout.addWidget(self.spotify_checkbox)
        
        # Añadir input para Playlists
        self.spotify_playlist_layout = QHBoxLayout()
        self.spotify_playlist_input = QLineEdit(self)
        self.spotify_playlist_input.setPlaceholderText("Paste Spotify PLAYLIST link or URI here...")
        self.spotify_playlist_input.setEnabled(False)
        
        self.spotify_add_playlist_button = QPushButton("Load Playlist", self)
        self.spotify_add_playlist_button.setEnabled(False)
        
        self.spotify_playlist_layout.addWidget(self.spotify_playlist_input)
        self.spotify_playlist_layout.addWidget(self.spotify_add_playlist_button)
        
        self.layout.addLayout(self.spotify_playlist_layout)
        
        # Añadir input para canciones específicas
        self.spotify_input_layout = QHBoxLayout()
        self.spotify_url_input = QLineEdit(self)
        self.spotify_url_input.setPlaceholderText("Paste Spotify TRACK link or URI here...")
        self.spotify_url_input.setEnabled(False) # Deshabilitado por defecto
        
        self.spotify_add_button = QPushButton("Add Track", self)
        self.spotify_add_button.setEnabled(False)
        
        self.spotify_input_layout.addWidget(self.spotify_url_input)
        self.spotify_input_layout.addWidget(self.spotify_add_button)
        
        self.layout.addLayout(self.spotify_input_layout)
        
        # Spacer final para empujar todo hacia arriba
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.spacer)
