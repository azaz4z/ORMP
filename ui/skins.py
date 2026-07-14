from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QCheckBox, QSpacerItem, QSizePolicy, QButtonGroup, QPushButton
from PySide6.QtCore import Qt

class SkinFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("skin_frame")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        
        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Título
        self.title_label = QLabel("Skin Configuration", self)
        self.title_label.setObjectName("skin_title")
        self.title_label.setAlignment(Qt.AlignCenter)
        
        font = self.title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.title_label.setFont(font)
        
        self.layout.addWidget(self.title_label)
        
        # Espaciador
        self.layout.addSpacing(20)
        
        self.default_checkbox = QCheckBox("2D Default Skin", self)
        self.default_checkbox.setObjectName("default_skin_checkbox")
        self.default_checkbox.setChecked(True) # Por defecto
        
        self.model_3d_checkbox = QCheckBox("3D Model Skin (.glb)", self)
        self.model_3d_checkbox.setObjectName("model_3d_checkbox")
        
        self.skin_group = QButtonGroup(self)
        self.skin_group.addButton(self.default_checkbox)
        self.skin_group.addButton(self.model_3d_checkbox)
        
        self.layout.addWidget(self.default_checkbox)
        self.layout.addWidget(self.model_3d_checkbox)
        
        self.load_skin_button = QPushButton("Load Custom Model (.glb)...", self)
        self.load_skin_button.setObjectName("load_skin_button")
        self.layout.addWidget(self.load_skin_button)
        
        self.layout.addSpacing(20)
        
        self.fixer_button = QPushButton("🛠️ Open 3D Model Fixer...", self)
        self.fixer_button.setObjectName("fixer_button")
        self.fixer_button.setToolTip("Open the tool to normalize and correct 3D models")
        self.layout.addWidget(self.fixer_button)
        
        # Spacer final para empujar todo hacia arriba
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.spacer)
