from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class SongFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("song_frame")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        
        from PySide6.QtWidgets import QSizePolicy
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        self.layout.addStretch(1)
        
        # Title & Artist
        self.title_label = QLabel("No song loaded", self)
        self.title_label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 20px;")
        self.title_label.setWordWrap(True)
        self.title_label.setMinimumHeight(45)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.layout.addWidget(self.title_label)
        
        # Album Cover
        self.cover_label = QLabel(self)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setFixedSize(250, 250)
        self.cover_label.setScaledContents(True)
        self.layout.addWidget(self.cover_label, alignment=Qt.AlignCenter)
        
        # Album Name
        self.album_label = QLabel("-", self)
        self.album_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.album_label.setStyleSheet("font-size: 14px; color: gray;")
        self.album_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.album_label.setWordWrap(True)
        self.album_label.setMinimumHeight(45)
        self.layout.addWidget(self.album_label)
        
        self.layout.addStretch(1)
        
    def update_song_info(self, song_path):
        import os
        from tinytag import TinyTag
        from PySide6.QtGui import QPixmap

        if not song_path or not os.path.exists(song_path):
            self.title_label.setText("No song loaded")
            self.album_label.setText("-")
            self.cover_label.clear()
            return
            
        try:
            tag = TinyTag.get(song_path, image=True)
            artist = tag.artist or "Unknown Artist"
            title = tag.title or "Unknown Title"
            album = tag.album
            
            # Fallback a Mutagen si TinyTag falló al leer el tag (por temas de case-sensitivity en FLAC)
            if not album:
                try:
                    from mutagen import File
                    audio = File(song_path)
                    if audio and hasattr(audio, 'tags') and audio.tags:
                        if 'album' in audio.tags:
                            album = audio.tags['album'][0]
                        elif 'ALBUM' in audio.tags:
                            album = audio.tags['ALBUM'][0]
                except Exception:
                    pass
                    
            album = album or "Unknown Album"
            
            self.title_label.setText(title)
            self.album_label.setText(f"{artist} • {album}")
            
            image_data = tag.get_image()
            if image_data:
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                pixmap = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.cover_label.setPixmap(pixmap)
            else:
                self.cover_label.clear()
                self.cover_label.setText("No Cover")
        except Exception as e:
            self.title_label.setText("Error loading metadata")
            self.album_label.setText("-")
            self.cover_label.clear()
            print(f"Error loading tag for {song_path}: {e}")

    def show_downloading(self):
        self.title_label.setText("Downloading...")
        self.album_label.setText("Please wait")
        self.cover_label.clear()
        self.cover_label.setText("⏳")
