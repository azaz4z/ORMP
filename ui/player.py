from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                               QLabel, QListView, QProgressBar, QPushButton, QSizePolicy, QSlider)

class PlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("player_widget")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        
        # Upper Frame
        self.upper_frame = QFrame(self)
        self.upper_frame.setObjectName(u"upper_frame")
        self.upper_frame.setFrameShape(QFrame.StyledPanel)
        self.upper_frame.setFrameShadow(QFrame.Raised)
        self.upper_frame.setFixedHeight(40)
        self.upper_layout = QHBoxLayout(self.upper_frame)
        self.upper_layout.setContentsMargins(10, 0, 10, 0)
        self.program_title = QLabel(self.upper_frame)
        self.program_title.setObjectName(u"program_title")
        self.upper_layout.addWidget(self.program_title)
        
        # Middle layout to hold vinyl and volume frames side-by-side
        self.middle_layout = QHBoxLayout()
        self.middle_layout.setContentsMargins(0, 0, 0, 0)
        self.middle_layout.setSpacing(10)
        
        # Vinyl frame
        self.vinyl_frame = QFrame(self)
        self.vinyl_frame.setObjectName(u"vinyl_frame")
        self.vinyl_frame.setFrameShape(QFrame.StyledPanel)
        self.vinyl_frame.setFrameShadow(QFrame.Raised)
        self.vinyl_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.middle_layout.addWidget(self.vinyl_frame, stretch=1)
        
        # Volume frame
        self.volume_frame = QFrame(self)
        self.volume_frame.setObjectName(u"volume_frame")
        self.volume_frame.setFrameShape(QFrame.StyledPanel)
        self.volume_frame.setFrameShadow(QFrame.Raised)
        self.volume_frame.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        
        self.volume_layout = QVBoxLayout(self.volume_frame)
        self.volume_layout.setContentsMargins(10, 15, 10, 15) # left, top, right, bottom
        
        self.volume_slider = QSlider(Qt.Vertical, self.volume_frame)
        self.volume_slider.setObjectName(u"volume_slider")
        self.volume_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_layout.addWidget(self.volume_slider, alignment=Qt.AlignHCenter)
        
        self.middle_layout.addWidget(self.volume_frame)
        
        self.main_layout.addLayout(self.middle_layout, stretch=2)
        
        # Song Info frame
        self.song_info_frame = QFrame(self)
        self.song_info_frame.setObjectName(u"song_info_frame")
        self.song_info_frame.setFrameShape(QFrame.StyledPanel)
        self.song_info_frame.setFrameShadow(QFrame.Raised)
        self.song_info_frame.setFixedHeight(80)
        
        # Main vertical layout for song info (Title top, controls bottom)
        self.song_info_layout = QVBoxLayout(self.song_info_frame)
        self.song_info_layout.setContentsMargins(5, 5, 5, 5)
        
        # Title on top
        self.song_title_label = QLabel(self.song_info_frame)
        self.song_title_label.setObjectName(u"song_title_label")
        self.song_info_layout.addWidget(self.song_title_label, alignment=Qt.AlignCenter)
        
        # Horizontal layout for buttons and progress bar
        self.song_controls_layout = QHBoxLayout()
        
        self.prev_track_button = QPushButton(self.song_info_frame)
        self.prev_track_button.setObjectName(u"prev_track_button")
        self.prev_track_button.setFixedWidth(35)
        self.play_button = QPushButton(self.song_info_frame)
        self.play_button.setObjectName(u"play_button")
        self.play_button.setFixedWidth(35)
        self.stop_button = QPushButton(self.song_info_frame)
        self.stop_button.setObjectName(u"stop_button")
        self.stop_button.setFixedWidth(35)
        self.next_track_button = QPushButton(self.song_info_frame)
        self.next_track_button.setObjectName(u"next_track_button")
        self.next_track_button.setFixedWidth(35)
        
        self.song_controls_layout.addWidget(self.prev_track_button)
        self.song_controls_layout.addWidget(self.play_button)
        self.song_controls_layout.addWidget(self.stop_button)
        self.song_controls_layout.addWidget(self.next_track_button)
        
        self.progress_bar = QProgressBar(self.song_info_frame)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(24)
        self.progress_bar.setTextVisible(False)
        self.song_controls_layout.addWidget(self.progress_bar, stretch=1)
        
        self.song_info_layout.addLayout(self.song_controls_layout)
        self.main_layout.addWidget(self.song_info_frame)
        
        # Song list
        self.song_list = QListView(self)
        self.song_list.setObjectName(u"song_list")
        self.main_layout.addWidget(self.song_list, stretch=1)
        
        self.retranslateUi()

    def retranslateUi(self):
        self.next_track_button.setText(QCoreApplication.translate("PlayerWidget", u"\u23ed", None))
        self.stop_button.setText(QCoreApplication.translate("PlayerWidget", u"\u23f8", None))
        self.play_button.setText(QCoreApplication.translate("PlayerWidget", u"\u25b6", None))
        self.prev_track_button.setText(QCoreApplication.translate("PlayerWidget", u"\u23ee", None))
        self.song_title_label.setText(QCoreApplication.translate("PlayerWidget", u"Title", None))
        self.program_title.setText(QCoreApplication.translate("PlayerWidget", u"...", None))
