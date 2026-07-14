from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QSlider, QCheckBox, QGroupBox, QScrollArea, QFrame)
from PySide6.QtCore import Qt, Signal

class PostProcessingFrame(QFrame):
    # Signals to notify main.py of changes
    exposure_changed = Signal(float)
    bloom_enabled_changed = Signal(bool)
    bloom_strength_changed = Signal(float)
    ao_enabled_changed = Signal(bool)
    ao_strength_changed = Signal(float)
    metalness_changed = Signal(float)
    roughness_changed = Signal(float)
    anisotropy_changed = Signal(float)
    anisotropy_rotation_changed = Signal(float)
    sheen_changed = Signal(float)
    sheen_roughness_changed = Signal(float)
    specular_changed = Signal(float)
    clearcoat_changed = Signal(float)
    clearcoat_roughness_changed = Signal(float)
    opacity_changed = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("postprocessing_frame")
        self.setStyleSheet("""
            QFrame#postprocessing_frame {
                background-color: #2b2b2b;
                border-radius: 10px;
            }
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QLabel {
                color: #ccc;
            }
            QCheckBox {
                color: #ccc;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        title = QLabel("Post-Processing Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        main_layout.addWidget(title)
        
        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 10, 0)
        scroll_layout.setSpacing(15)
        
        # === ENVIRONMENT GROUP ===
        env_group = QGroupBox("Environment")
        env_layout = QVBoxLayout(env_group)
        
        self.exposure_slider = self.create_slider("Exposure", env_layout, 1, 50, 20) # 0.1 to 5.0 (default 2.0)
        self.exposure_slider.valueChanged.connect(lambda v: self.exposure_changed.emit(v / 10.0))
        
        scroll_layout.addWidget(env_group)
        
        # === BLOOM GROUP ===
        bloom_group = QGroupBox("Bloom (Glow)")
        bloom_layout = QVBoxLayout(bloom_group)
        
        self.bloom_check = QCheckBox("Enable Bloom")
        self.bloom_check.setChecked(False)
        self.bloom_check.stateChanged.connect(lambda v: self.bloom_enabled_changed.emit(bool(v)))
        bloom_layout.addWidget(self.bloom_check)
        
        self.bloom_slider = self.create_slider("Strength", bloom_layout, 0, 100, 50) # 0.0 to 1.0 (default 0.5)
        self.bloom_slider.valueChanged.connect(lambda v: self.bloom_strength_changed.emit(v / 100.0))
        
        scroll_layout.addWidget(bloom_group)
        
        # === AMBIENT OCCLUSION GROUP ===
        ao_group = QGroupBox("Ambient Occlusion (SSAO)")
        ao_layout = QVBoxLayout(ao_group)
        
        self.ao_check = QCheckBox("Enable SSAO")
        self.ao_check.setChecked(False)
        self.ao_check.stateChanged.connect(lambda v: self.ao_enabled_changed.emit(bool(v)))
        ao_layout.addWidget(self.ao_check)
        
        self.ao_slider = self.create_slider("Strength", ao_layout, 0, 100, 50) # 0.0 to 1.0 (default 0.5)
        self.ao_slider.valueChanged.connect(lambda v: self.ao_strength_changed.emit(v / 100.0))
        
        scroll_layout.addWidget(ao_group)
        
        # === MATERIAL CHANNELS GROUP ===
        mat_group = QGroupBox("Material Channels")
        mat_layout = QVBoxLayout(mat_group)
        
        # Metalness: 0 = dielectric (plastic), 1 = full metal
        self.metalness_slider = self.create_slider("Metalness", mat_layout, 0, 100, 100)
        self.metalness_slider.valueChanged.connect(lambda v: self.metalness_changed.emit(v / 100.0))
        
        # Roughness: 0 = mirror/glass, 1 = matte/diffuse — KEY for making CD shiny
        self.roughness_slider = self.create_slider("Roughness", mat_layout, 0, 100, 30)
        self.roughness_slider.valueChanged.connect(lambda v: self.roughness_changed.emit(v / 100.0))
        
        # Specular F0: controls how reflective the surface is at glancing angles
        self.specular_slider = self.create_slider("Specular F0", mat_layout, 0, 100, 50)
        self.specular_slider.valueChanged.connect(lambda v: self.specular_changed.emit(v / 100.0))
        
        # Opacity: transparency of the material
        self.opacity_slider = self.create_slider("Opacity", mat_layout, 0, 100, 100)
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_changed.emit(v / 100.0))
        
        scroll_layout.addWidget(mat_group)
        
        # === ANISOTROPY GROUP ===
        aniso_group = QGroupBox("Anisotropy")
        aniso_layout = QVBoxLayout(aniso_group)
        
        # Anisotropy level: stretches reflections (rainbow ring effect on CDs)
        self.anisotropy_slider = self.create_slider("Level", aniso_layout, 0, 100, 0)
        self.anisotropy_slider.valueChanged.connect(lambda v: self.anisotropy_changed.emit(v / 100.0))
        
        # Anisotropy rotation: rotates the direction of the stretched reflections (0-360 degrees mapped to 0-1)
        self.anisotropy_rotation_slider = self.create_slider("Rotation", aniso_layout, 0, 360, 0)
        self.anisotropy_rotation_slider.valueChanged.connect(lambda v: self.anisotropy_rotation_changed.emit(v / 360.0))
        
        scroll_layout.addWidget(aniso_group)
        
        # === CLEAR COAT GROUP ===
        cc_group = QGroupBox("Clear Coat")
        cc_layout = QVBoxLayout(cc_group)
        
        # Clear Coat: adds a secondary glossy layer (like the plastic cover on a CD)
        self.clearcoat_slider = self.create_slider("Amount", cc_layout, 0, 100, 0)
        self.clearcoat_slider.valueChanged.connect(lambda v: self.clearcoat_changed.emit(v / 100.0))
        
        # Clear Coat Roughness: how rough the clear coat layer is
        self.clearcoat_roughness_slider = self.create_slider("Roughness", cc_layout, 0, 100, 0)
        self.clearcoat_roughness_slider.valueChanged.connect(lambda v: self.clearcoat_roughness_changed.emit(v / 100.0))
        
        scroll_layout.addWidget(cc_group)
        
        # === SHEEN GROUP ===
        sheen_group = QGroupBox("Sheen")
        sheen_layout = QVBoxLayout(sheen_group)
        
        # Sheen: soft velvet-like reflection at edges
        self.sheen_slider = self.create_slider("Amount", sheen_layout, 0, 100, 0)
        self.sheen_slider.valueChanged.connect(lambda v: self.sheen_changed.emit(v / 100.0))
        
        # Sheen Roughness
        self.sheen_roughness_slider = self.create_slider("Roughness", sheen_layout, 0, 100, 0)
        self.sheen_roughness_slider.valueChanged.connect(lambda v: self.sheen_roughness_changed.emit(v / 100.0))
        
        scroll_layout.addWidget(sheen_group)
        
        # Spacer
        scroll_layout.addStretch(1)
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
    def create_slider(self, label_text, layout, min_val, max_val, default_val):
        h_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(80)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default_val)
        
        val_label = QLabel(str(default_val))
        val_label.setMinimumWidth(30)
        val_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Update value label on drag
        slider.valueChanged.connect(lambda v: val_label.setText(str(v)))
        
        h_layout.addWidget(label)
        h_layout.addWidget(slider)
        h_layout.addWidget(val_label)
        layout.addLayout(h_layout)
        
        return slider
