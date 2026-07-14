"""
3D Model Fixer — Interactive visual tool for normalizing GLB models.

Pipeline:
  1. Auto-fix: PCA analysis → center → rotate disc normal to +Z → scale
  2. Interactive preview: Qt window with same renderer as the app
  3. Manual adjustment: Quick-rotate buttons + fine sliders + mouse orbit
  4. Save: Export corrected model

Usage:
  python 3d_fixer.py                         # Uses default model in skins/
  python 3d_fixer.py my_model.glb            # Custom model
  python 3d_fixer.py input.glb output.glb    # Separate input and output
"""

import sys
import os
import math
import numpy as np
import trimesh

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QGroupBox, QFrame, QSplitter,
    QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtGui import QPalette


# =============================================================================
# AUTO-FIX LOGIC (preserved from original)
# =============================================================================

def load_model(path):
    """Loads a GLB/GLTF model and combines the meshes WITH the scene graph transformations applied."""
    print(f"[3D Fixer] Loading model: {path}")
    scene = trimesh.load(path)
    
    if isinstance(scene, trimesh.Scene):
        meshes = []
        for node_name in scene.graph.nodes_geometry:
            transform, geometry_name = scene.graph[node_name]
            geom = scene.geometry[geometry_name]
            if isinstance(geom, trimesh.Trimesh):
                mesh_copy = geom.copy()
                mesh_copy.apply_transform(transform)
                meshes.append(mesh_copy)
                print(f"  - Mesh: '{geometry_name}' (node: '{node_name}', {len(geom.vertices)} vertices, {len(geom.faces)} faces)")
                from trimesh.transformations import euler_from_matrix
                angles = np.degrees(euler_from_matrix(transform))
                pos = transform[:3, 3]
                print(f"    Transform: pos=({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}) rot=({angles[0]:.1f}, {angles[1]:.1f}, {angles[2]:.1f}) deg")
        
        if not meshes:
            print("[3D Fixer] ERROR: No meshes found in the model.")
            sys.exit(1)
        
        combined = trimesh.util.concatenate(meshes)
        return scene, combined
    elif isinstance(scene, trimesh.Trimesh):
        print(f"  - Single mesh: {len(scene.vertices)} vertices, {len(scene.faces)} faces")
        return None, scene
    else:
        print(f"[3D Fixer] ERROR: Unsupported model type: {type(scene)}")
        sys.exit(1)


def analyze_model(mesh):
    """Analyzes the current orientation of the model."""
    bounds = mesh.bounds
    center = mesh.centroid
    extents = mesh.extents

    print(f"\n=== MODEL ANALYSIS ===")
    print(f"Geometric center: ({center[0]:.4f}, {center[1]:.4f}, {center[2]:.4f})")
    print(f"X Extent: {extents[0]:.4f}")
    print(f"Y Extent: {extents[1]:.4f}")
    print(f"Z Extent: {extents[2]:.4f}")

    thin_axis = np.argmin(extents)
    axis_names = ['X', 'Y', 'Z']
    print(f"Thinnest axis (record normal): {axis_names[thin_axis]} ({extents[thin_axis]:.4f})")

    covariance = np.cov(mesh.vertices.T)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    normal_idx = np.argmin(eigenvalues)
    disc_normal = eigenvectors[:, normal_idx]

    print(f"\n=== PCA (Principal Component Analysis) ===")
    for i in range(3):
        ev = eigenvalues[i]
        vec = eigenvectors[:, i]
        label = " <-- RECORD NORMAL (thinnest axis)" if i == normal_idx else ""
        print(f"  Eigenvalue {i}: {ev:.6f}  Vector: ({vec[0]:.4f}, {vec[1]:.4f}, {vec[2]:.4f}){label}")

    return disc_normal, center


def compute_rotation_matrix(current_normal, target_normal):
    """Calculates the rotation matrix to align current_normal with target_normal."""
    current_normal = current_normal / np.linalg.norm(current_normal)
    target_normal = target_normal / np.linalg.norm(target_normal)

    cross = np.cross(current_normal, target_normal)
    dot = np.dot(current_normal, target_normal)

    if np.linalg.norm(cross) < 1e-8:
        if dot > 0:
            print("[3D Fixer] The normal already points in the correct direction.")
            return np.eye(4)
        else:
            perp = np.array([1, 0, 0]) if abs(current_normal[0]) < 0.9 else np.array([0, 1, 0])
            axis = np.cross(current_normal, perp)
            axis = axis / np.linalg.norm(axis)
            return trimesh.transformations.rotation_matrix(np.pi, axis)

    axis = cross / np.linalg.norm(cross)
    angle = np.arccos(np.clip(dot, -1.0, 1.0))
    print(f"[3D Fixer] Required rotation: {np.degrees(angle):.2f}° around axis ({axis[0]:.4f}, {axis[1]:.4f}, {axis[2]:.4f})")
    return trimesh.transformations.rotation_matrix(angle, axis)


def auto_fix(input_path):
    """Runs the auto-fix pipeline. Returns (scene, correction_matrix)."""
    scene, combined_mesh = load_model(input_path)
    disc_normal, center = analyze_model(combined_mesh)

    target_normal = np.array([0.0, 0.0, 1.0])
    if disc_normal[2] < 0:
        disc_normal = -disc_normal

    rotation_matrix = compute_rotation_matrix(disc_normal, target_normal)

    translation = trimesh.transformations.translation_matrix(-center)
    
    # Apply translation and rotation to a copy to get the true axis-aligned extents
    temp_mesh = combined_mesh.copy()
    temp_mesh.apply_transform(rotation_matrix @ translation)
    
    TARGET_SIZE = 2.0
    current_size = max(temp_mesh.extents)
    scale_factor = TARGET_SIZE / current_size
    print(f"[3D Fixer] Normalizing scale to [-1, 1]: factor {scale_factor:.4f} (from {current_size:.4f} to {TARGET_SIZE})")

    scale_matrix = trimesh.transformations.scale_matrix(scale_factor)
    correction = scale_matrix @ rotation_matrix @ translation

    if scene is not None:
        scene.apply_transform(correction)
    else:
        combined_mesh.apply_transform(correction)
        scene = combined_mesh

    print("[3D Fixer] Auto-fix complete.")
    return scene


def save_scene(scene, output_path):
    """Exports the scene to a GLB file."""
    print(f"[3D Fixer] Saving fixed model to: {output_path}")
    scene.export(output_path)
    print(f"[OK] Model saved successfully!")


# =============================================================================
# INTERACTIVE FIXER WINDOW
# =============================================================================

class FixerWindow(QMainWindow):
    def __init__(self, scene, input_path, output_path):
        super().__init__()
        self.scene = scene
        self.input_path = input_path
        self.output_path = output_path
        
        # Manual rotation offsets (degrees) applied on top of auto-fix
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.rot_z = 0.0
        
        # Camera orbit state
        self.cam_yaw = 0.0
        self.cam_pitch = 0.0
        self.orbit_dragging = False
        self.last_mouse_pos = None
        
        self.setWindowTitle("3D Model Fixer — Interactive Preview")
        self.setMinimumSize(1000, 650)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QLabel { color: #ccc; }
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4a4a4a; }
            QPushButton:pressed { background-color: #2a2a2a; }
            QPushButton#save_btn {
                background-color: #2d7d46;
                border-color: #3a9a56;
                font-weight: bold;
            }
            QPushButton#save_btn:hover { background-color: #3a9a56; }
            QPushButton#cancel_btn {
                background-color: #7d2d2d;
                border-color: #9a3a3a;
            }
            QPushButton#cancel_btn:hover { background-color: #9a3a3a; }
            QPushButton#reset_btn {
                background-color: #2d5a7d;
                border-color: #3a6a9a;
            }
            QPushButton#reset_btn:hover { background-color: #3a6a9a; }
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
                padding: 0 3px;
            }
            QSlider::groove:horizontal {
                background: #444;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #aaa;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """)
        
        # ── Main layout ──
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ── LEFT: 3D Viewport ──
        viewport_frame = QFrame()
        viewport_frame.setStyleSheet("QFrame { background-color: #1a1a1a; border-radius: 8px; }")
        viewport_layout = QVBoxLayout(viewport_frame)
        viewport_layout.setContentsMargins(0, 0, 0, 0)
        
        self.qml_view = QQuickWidget()
        self.qml_view.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.qml_view.setClearColor(Qt.transparent)
        
        # Write and load QML scene
        self._setup_qml_scene()
        
        viewport_layout.addWidget(self.qml_view)
        main_layout.addWidget(viewport_frame, 3)
        
        # ── RIGHT: Controls ──
        controls_frame = QFrame()
        controls_frame.setFixedWidth(300)
        controls_frame.setStyleSheet("QFrame { background-color: #2b2b2b; border-radius: 8px; }")
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(15, 15, 15, 15)
        controls_layout.setSpacing(12)
        
        title = QLabel("Model Adjustment")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        title.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(title)
        
        # ── Quick Rotate (90°) ──
        quick_group = QGroupBox("Quick Rotate (90°)")
        quick_layout = QVBoxLayout(quick_group)
        
        for axis_name, axis_idx in [("X", 0), ("Y", 1), ("Z", 2)]:
            row = QHBoxLayout()
            btn_plus = QPushButton(f"+90° {axis_name}")
            btn_minus = QPushButton(f"-90° {axis_name}")
            btn_plus.clicked.connect(lambda checked, a=axis_idx: self._quick_rotate(a, 90))
            btn_minus.clicked.connect(lambda checked, a=axis_idx: self._quick_rotate(a, -90))
            row.addWidget(btn_minus)
            row.addWidget(btn_plus)
            quick_layout.addLayout(row)
        
        controls_layout.addWidget(quick_group)
        
        # ── Fine Adjustment Sliders ──
        fine_group = QGroupBox("Fine Adjustment (±45°)")
        fine_layout = QVBoxLayout(fine_group)
        
        self.slider_x = self._create_axis_slider("X", fine_layout, 0)
        self.slider_y = self._create_axis_slider("Y", fine_layout, 1)
        self.slider_z = self._create_axis_slider("Z", fine_layout, 2)
        
        controls_layout.addWidget(fine_group)
        
        # ── Status ──
        self.status_label = QLabel("Rotation: X=0° Y=0° Z=0°")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; font-style: italic; font-size: 12px;")
        controls_layout.addWidget(self.status_label)
        
        # ── Orbit hint ──
        orbit_hint = QLabel("🖱️ Drag on viewport to orbit camera")
        orbit_hint.setAlignment(Qt.AlignCenter)
        orbit_hint.setStyleSheet("color: #666; font-size: 11px;")
        controls_layout.addWidget(orbit_hint)
        
        controls_layout.addStretch(1)
        
        # ── Bottom buttons ──
        reset_btn = QPushButton("↺  Reset to Auto-Fix")
        reset_btn.setObjectName("reset_btn")
        reset_btn.clicked.connect(self._reset_rotation)
        controls_layout.addWidget(reset_btn)
        
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self._cancel)
        
        save_btn = QPushButton("💾  Save && Close")
        save_btn.setObjectName("save_btn")
        save_btn.clicked.connect(self._save_and_close)
        
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        controls_layout.addLayout(btn_row)
        
        main_layout.addWidget(controls_frame)
        
        # ── Slow rotation timer ──
        self.auto_spin = True
        self.spin_angle = 0.0
        self.spin_timer = QTimer()
        self.spin_timer.setInterval(16)  # ~60fps
        self.spin_timer.timeout.connect(self._spin_tick)
        self.spin_timer.start()
        
        # Install event filter for mouse orbit on viewport
        self.qml_view.installEventFilter(self)
    
    def _setup_qml_scene(self):
        """Creates and loads the QML scene for previewing the model."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Save the auto-fixed scene to a temp file for preview
        self.temp_model_path = os.path.join(project_root, "skins", "_fixer_preview.glb")
        self.scene.export(self.temp_model_path)
        
        model_url = self.temp_model_path.replace("\\", "/")
        
        hdr_path = os.path.abspath(os.path.join(project_root, "skins", "studio.hdr"))
        hdr_url = hdr_path.replace("\\", "/")
        
        bg_color = "#1a1a1a"
        
        qml_code = f"""
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick3D.AssetUtils

Item {{
    id: root
    width: 800
    height: 600
    
    property color bgColor: "{bg_color}"
    
    property real vinylAngle: 0
    property real manualRotX: 0
    property real manualRotY: 0
    property real manualRotZ: 0
    
    property real camX: 0
    property real camY: 0
    property real camZ: 8.1
    property real camPitch: 0
    property real camYaw: 0
    
    property url modelSource: "file:///{model_url}"

    View3D {{
        id: view
        anchors.fill: parent
        
        environment: ExtendedSceneEnvironment {{
            backgroundMode: SceneEnvironment.Color
            clearColor: root.bgColor
            
            antialiasingMode: SceneEnvironment.SSAA
            antialiasingQuality: SceneEnvironment.VeryHigh
            temporalAAEnabled: true
            specularAAEnabled: true
            
            lightProbe: Texture {{
                source: "file:///{hdr_url}"
            }}
            probeExposure: 2.0
            
            tonemapMode: SceneEnvironment.TonemapACES
        }}

        PerspectiveCamera {{
            id: camera
            x: root.camX
            y: root.camY
            z: root.camZ
            eulerRotation.x: root.camPitch
            eulerRotation.y: root.camYaw
            clipNear: 0.1
            clipFar: 1000.0
        }}

        PointLight {{
            x: 0; y: 5; z: 12
            brightness: 2.0
            linearFade: 0.05
            ambientColor: "#111111"
        }}
        
        DirectionalLight {{
            eulerRotation.x: -20
            eulerRotation.y: -30
            brightness: 1.5
            ambientColor: "#333333"
        }}

        // Manual rotation node (user adjustments)
        Node {{
            eulerRotation.x: root.manualRotX
            eulerRotation.y: root.manualRotY
            eulerRotation.z: root.manualRotZ
            
            // Spin animation node
            Node {{
                eulerRotation.z: root.vinylAngle
                
                RuntimeLoader {{
                    id: vinylModel
                    source: root.modelSource
                    property real scaleFactor: 3.5 * Math.min(1.0, root.width / Math.max(1.0, root.height))
                    scale: Qt.vector3d(scaleFactor, scaleFactor, scaleFactor)
                }}
            }}
        }}
    }}
    
    // Grid helper lines
    Rectangle {{
        anchors.centerIn: parent
        width: parent.width
        height: 1
        color: "#33ffffff"
    }}
    Rectangle {{
        anchors.centerIn: parent
        width: 1
        height: parent.height
        color: "#33ffffff"
    }}
}}
"""
        qml_path = os.path.join(project_root, "vinyl", "skin_type", "_fixer_scene.qml")
        with open(qml_path, "w", encoding="utf-8") as f:
            f.write(qml_code)
        
        self.qml_view.setSource(QUrl.fromLocalFile(qml_path))
        self.root_obj = self.qml_view.rootObject()
    
    def _create_axis_slider(self, axis_name, layout, axis_idx):
        """Creates a fine-adjustment slider for one axis."""
        row = QHBoxLayout()
        label = QLabel(f"{axis_name}:")
        label.setMinimumWidth(20)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(-450)  # -45.0 degrees * 10
        slider.setMaximum(450)
        slider.setValue(0)
        slider.setSingleStep(5)
        
        val_label = QLabel("0.0°")
        val_label.setMinimumWidth(45)
        val_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        def on_change(v):
            deg = v / 10.0
            val_label.setText(f"{deg:.1f}°")
            if axis_idx == 0:
                self.rot_x = deg
            elif axis_idx == 1:
                self.rot_y = deg
            else:
                self.rot_z = deg
            self._update_preview()
        
        slider.valueChanged.connect(on_change)
        
        row.addWidget(label)
        row.addWidget(slider)
        row.addWidget(val_label)
        layout.addLayout(row)
        return slider
    
    def _quick_rotate(self, axis_idx, degrees):
        """Applies a quick 90° rotation."""
        if axis_idx == 0:
            self.rot_x += degrees
        elif axis_idx == 1:
            self.rot_y += degrees
        else:
            self.rot_z += degrees
        
        # Update sliders (clamp fine part to slider range, keep total in rot_*)
        self._update_preview()
    
    def _update_preview(self):
        """Updates the QML properties to reflect current rotation."""
        if self.root_obj:
            self.root_obj.setProperty("manualRotX", self.rot_x)
            self.root_obj.setProperty("manualRotY", self.rot_y)
            self.root_obj.setProperty("manualRotZ", self.rot_z)
        
        self.status_label.setText(f"Rotation: X={self.rot_x:.1f}° Y={self.rot_y:.1f}° Z={self.rot_z:.1f}°")
    
    def _reset_rotation(self):
        """Resets manual rotation to 0."""
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.rot_z = 0.0
        self.slider_x.setValue(0)
        self.slider_y.setValue(0)
        self.slider_z.setValue(0)
        self.cam_yaw = 0.0
        self.cam_pitch = 0.0
        if self.root_obj:
            self.root_obj.setProperty("camYaw", 0.0)
            self.root_obj.setProperty("camPitch", 0.0)
        self._update_preview()
    
    def _spin_tick(self):
        """Slow auto-rotation for preview."""
        if self.auto_spin and self.root_obj:
            self.spin_angle += 0.3
            if self.spin_angle >= 360:
                self.spin_angle -= 360
            self.root_obj.setProperty("vinylAngle", self.spin_angle)
    
    def eventFilter(self, obj, event):
        """Mouse orbit on the QML viewport."""
        from PySide6.QtCore import QEvent
        
        if obj == self.qml_view:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.orbit_dragging = True
                    self.last_mouse_pos = event.position()
                    self.auto_spin = False
                    return True
            elif event.type() == QEvent.MouseMove and self.orbit_dragging:
                pos = event.position()
                if self.last_mouse_pos:
                    dx = pos.x() - self.last_mouse_pos.x()
                    dy = pos.y() - self.last_mouse_pos.y()
                    self.cam_yaw += dx * 0.3
                    self.cam_pitch -= dy * 0.3
                    self.cam_pitch = max(-89, min(89, self.cam_pitch))
                    if self.root_obj:
                        self.root_obj.setProperty("camYaw", self.cam_yaw)
                        self.root_obj.setProperty("camPitch", self.cam_pitch)
                self.last_mouse_pos = pos
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self.orbit_dragging = False
                    self.last_mouse_pos = None
                    return True
        
        return super().eventFilter(obj, event)
    
    def _save_and_close(self):
        """Applies manual rotations to the trimesh scene and saves."""
        # Build rotation matrix from manual adjustments
        rx = trimesh.transformations.rotation_matrix(math.radians(self.rot_x), [1, 0, 0])
        ry = trimesh.transformations.rotation_matrix(math.radians(self.rot_y), [0, 1, 0])
        rz = trimesh.transformations.rotation_matrix(math.radians(self.rot_z), [0, 0, 1])
        manual_correction = rz @ ry @ rx
        
        # Apply to scene
        self.scene.apply_transform(manual_correction)
        
        # Save
        save_scene(self.scene, self.output_path)
        
        # Clean up temp file
        if os.path.exists(self.temp_model_path):
            try:
                os.remove(self.temp_model_path)
            except:
                pass
        
        print(f"[3D Fixer] Model saved with manual adjustments: X={self.rot_x:.1f}° Y={self.rot_y:.1f}° Z={self.rot_z:.1f}°")
        self.close()
    
    def _cancel(self):
        """Closes without saving."""
        # Clean up temp file
        if hasattr(self, 'temp_model_path') and os.path.exists(self.temp_model_path):
            try:
                os.remove(self.temp_model_path)
            except:
                pass
        print("[3D Fixer] Cancelled. No changes saved.")
        self.close()
    
    def closeEvent(self, event):
        self.spin_timer.stop()
        super().closeEvent(event)


# =============================================================================
# MAIN
# =============================================================================

def run_fixer():
    app = QApplication.instance() or QApplication(sys.argv)
    
    from PySide6.QtWidgets import QFileDialog
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select 3D Model to Fix",
        os.path.join(os.getcwd(), "skins"),
        "3D Models (*.glb *.gltf *.obj)"
    )
    if not file_path:
        print("[3D Fixer] No file selected. Exiting.")
        return
        
    input_path = file_path
    name, ext = os.path.splitext(input_path)
    output_path = f"{name}_fixed{ext}"

    if not os.path.exists(input_path):
        print(f"[3D Fixer] ERROR: File not found: {input_path}")
        return

    # Step 1: Auto-fix
    print("=" * 50)
    print("STEP 1: Auto-Fix (PCA Analysis)")
    print("=" * 50)
    scene = auto_fix(input_path)

    # Step 2: Interactive preview
    print("\n" + "=" * 50)
    print("STEP 2: Interactive Preview")
    print("=" * 50)
    print("Opening preview window... Adjust the model and click Save when ready.")
    
    window = FixerWindow(scene, input_path, output_path)
    window.show()
    # If this is called from the main app, we don't need to call app.exec() since the main loop is running.
    # We will just keep a reference to the window so it doesn't get garbage collected.
    global _fixer_window_instance
    _fixer_window_instance = window
    if not QApplication.instance().startingUp():
        # If it's standalone, run the event loop
        if __name__ == "__main__":
            app.exec()

if __name__ == "__main__":
    run_fixer()
