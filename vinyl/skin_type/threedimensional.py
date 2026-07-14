import math
import os
from PySide6.QtCore import Qt, QUrl
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette

class Skin3D:
    def __init__(self):
        # We use QQuickWidget to embed QML inside a standard QWidget
        self.view = QQuickWidget()
        self.view.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.view.setClearColor(Qt.transparent)
        
        # Path to the glb file (uses the model normalized by 3d_fixer.py)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        model_path = os.path.abspath(os.path.join(project_root, "skins", "vinyl_fixed.glb"))
        # Fallback to original model if the fixed one doesn't exist
        if not os.path.exists(model_path):
            model_path = os.path.abspath(os.path.join(project_root, "skins", "compact_disc_fixed.glb"))
        
        # Format path for QML URL
        model_url = model_path.replace("\\", "/")
        
        # Path to HDRI lighting map
        hdr_path = os.path.abspath(os.path.join(project_root, "skins", "studio.hdr"))
        hdr_url = hdr_path.replace("\\", "/")
        
        # Get PyQt window background color
        bg_color = QApplication.palette().color(QPalette.Window).name()
        
        qml_path = os.path.join(os.path.dirname(__file__), "scene.qml")
        self.view.setSource(QUrl.fromLocalFile(qml_path))
        
        # Reference to root object to set property
        self.root_obj = self.view.rootObject()
        
        if self.root_obj:
            self.root_obj.setProperty("bgColor", bg_color)
            self.root_obj.setProperty("hdrSource", QUrl.fromLocalFile(hdr_path))
        
        if os.path.exists(model_path):
            print(f"[Skin3D] QML Quick3D Scene loaded with model: {model_path}")
        else:
            print(f"[Skin3D] WARNING: Model {model_path} does not exist.")

    def get_view(self):
        return self.view
        
    def update_rotation(self, angle_radians):
        if self.root_obj:
            angle_degrees = math.degrees(angle_radians)
            self.root_obj.setProperty("vinylAngle", -angle_degrees)
            
    def update_tilt_y(self, angle_degrees):
        if self.root_obj:
            self.root_obj.setProperty("vinylTiltY", angle_degrees)
            
    def load_model(self, file_path):
        if not os.path.exists(file_path):
            print(f"[Skin3D] Error: File {file_path} does not exist.")
            return False
            
        model_url = file_path.replace("\\", "/")
        if self.root_obj:
            self.root_obj.setProperty("modelSource", QUrl.fromLocalFile(file_path))
            print(f"[Skin3D] New model loaded: {file_path}")
            return True
        return False
    
            
    def get_camera_params(self):
        if not self.root_obj: return {}
        return {
            'x': self.root_obj.property("camX"),
            'y': self.root_obj.property("camY"),
            'z': self.root_obj.property("camZ"),
            'pitch': self.root_obj.property("camPitch"),
            'yaw': self.root_obj.property("camYaw"),
            'roll': self.root_obj.property("camRoll"),
        }
        
    def set_camera_params(self, params):
        if not self.root_obj: return
        if 'x' in params: self.root_obj.setProperty("camX", params['x'])
        if 'y' in params: self.root_obj.setProperty("camY", params['y'])
        if 'z' in params: self.root_obj.setProperty("camZ", params['z'])
        if 'pitch' in params: self.root_obj.setProperty("camPitch", params['pitch'])
        if 'yaw' in params: self.root_obj.setProperty("camYaw", params['yaw'])
        if 'roll' in params: self.root_obj.setProperty("camRoll", params['roll'])
        
    def set_postprocessing(self, effect, value):
        if hasattr(self, "root_obj") and self.root_obj:
            self.root_obj.setProperty(effect, value)
