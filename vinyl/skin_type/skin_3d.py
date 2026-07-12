import math
import os
from PySide6.QtCore import Qt, QUrl
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtQml import QQmlApplicationEngine

class Skin3D:
    def __init__(self):
        # We use QQuickWidget to embed QML inside a standard QWidget
        self.view = QQuickWidget()
        self.view.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.view.setAttribute(Qt.WA_AlwaysStackOnTop)
        self.view.setClearColor(Qt.transparent)
        
        # Path to the glb file (uses the model normalized by 3d_fixer.py)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        model_path = os.path.abspath(os.path.join(project_root, "skins", "vinyl_fixed.glb"))
        
        # Fallback to original model if the fixed one doesn't exist
        if not os.path.exists(model_path):
            model_path = os.path.abspath(os.path.join(project_root, "skins", "very_simple_cd-_disc.glb"))
        
        # Format path for QML URL
        model_url = model_path.replace("\\", "/")
        
        # Path to HDRI lighting map
        hdr_path = os.path.abspath(os.path.join(project_root, "skins", "studio.hdr"))
        hdr_url = hdr_path.replace("\\", "/")
        
        qml_code = f"""
import QtQuick
import QtQuick3D
import QtQuick3D.AssetUtils

Item {{
    id: root
    width: 800
    height: 800
    
    // Vinyl angle (controlled from Python)
    property real vinylAngle: 0
    property real vinylTiltY: 0
    
    // 3D model URL
    property url modelSource: "file:///{model_url}"
    
    // Camera properties
    property real camX: 0
    property real camY: 0
    property real camZ: 18
    property real camPitch: 0
    property real camYaw: 0
    property real camRoll: 0

    View3D {{
        anchors.fill: parent
        
        environment: SceneEnvironment {{
            clearColor: "#202020"
            backgroundMode: SceneEnvironment.Color
            
            // Maximum Anti-Aliasing quality (Super Sampling) to eliminate jagged edges
            antialiasingMode: SceneEnvironment.SSAA
            antialiasingQuality: SceneEnvironment.VeryHigh
            
            // Temporal AA: Greatly helps reduce flickering in vinyl grooves
            temporalAAEnabled: true
            
            // Specific for smoothing specular highlights (white reflections)
            specularAAEnabled: true
            
            // Image Based Lighting (IBL) for realistic PBR reflections
            lightProbe: Texture {{
                source: "file:///{hdr_url}"
            }}
            probeExposure: 0.3 // Keep HDRI dim just for texture
            
            // Greatly improves PBR materials
            tonemapMode: SceneEnvironment.TonemapACES
        }}

        PerspectiveCamera {{
            id: camera
            x: root.camX
            y: root.camY
            z: root.camZ
            eulerRotation.x: root.camPitch
            eulerRotation.y: root.camYaw
            eulerRotation.z: root.camRoll
            
            // Allow camera to get very close without clipping the model
            clipNear: 0.1
            clipFar: 1000.0
        }}

        // Flashlight / Spotlight effect that you liked before
        PointLight {{
            x: 0
            y: 5
            z: 12
            brightness: 2.0
            linearFade: 0.05
            ambientColor: "#111111"
        }}

        // Parent Node for Y tilt
        Node {{
            eulerRotation.y: root.vinylTiltY
            
            // Child Node applies ONLY vinyl Z rotation
            Node {{
                eulerRotation.z: root.vinylAngle
                
                RuntimeLoader {{
                    id: vinylModel
                    source: root.modelSource
                    scale: Qt.vector3d(3.5, 3.5, 3.5)
                }}
            }}
        }}
    }}
}}
"""
        # Save QML to a temporary file or load from data
        qml_path = os.path.join(os.path.dirname(__file__), "scene.qml")
        with open(qml_path, "w", encoding="utf-8") as f:
            f.write(qml_code)
            
        self.view.setSource(QUrl.fromLocalFile(qml_path))
        
        # Reference to root object to set property
        self.root_obj = self.view.rootObject()
        
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
