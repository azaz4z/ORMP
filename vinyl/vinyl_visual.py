import math
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt

from vinyl.skin_type.skin_2d import draw_2d_vinyl
from vinyl.skin_type.skin_3d import Skin3D

class VinylVisual(QWidget):
    def __init__(self, vinyl_model, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.vinyl_model = vinyl_model
        
        self.is_dragging = False
        self.prev_mouse_angle = 0.0
        # Visual animation of the record
        self.visual_angle = 0.0
        
        # Additional Y tilt
        self.tilt_y_active = False
        self.returning_to_zero = False
        self.current_tilt_y = 0.0
        self.current_velocity_y = 0.0
        
        # Skin configuration
        self.current_skin = "default"
        
        # Layout for 3D container
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Instantiate and configure 3D
        self.skin_3d = Skin3D()
        self.container_3d = self.skin_3d.get_view()
        self.container_3d.setParent(self)
        
        # Transparent for mouse events so scratch still works
        self.container_3d.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.container_3d.hide() # Hidden by default
        
        self.layout.addWidget(self.container_3d)

    def set_skin(self, skin_name):
        self.current_skin = skin_name
        if skin_name == "3d":
            self.container_3d.show()
        else:
            self.container_3d.hide()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Visual angle animation (chases the physical angle to avoid sudden jumps)
        diff = self.vinyl_model.angle - self.visual_angle
        self.visual_angle += diff * 0.15 # Approaches 15% per frame
        
        # Y rotation physics (acceleration and braking)
        if self.tilt_y_active:
            # Smoothly accelerate towards max speed (0.25)
            self.current_velocity_y += (0.25 - self.current_velocity_y) * 0.02
            self.current_tilt_y += self.current_velocity_y
            
            if self.current_tilt_y >= 360.0:
                self.current_tilt_y -= 360.0
                
        elif self.returning_to_zero:
            # Smooth braking towards position 360 (which equals 0)
            diff = 360.0 - self.current_tilt_y
            
            # Target speed decreases as we approach the goal
            velocidad_ideal = diff * 0.03
            velocidad_ideal = min(velocidad_ideal, 3.0) # Limit max return speed
            
            # Interpolate current speed towards ideal speed
            self.current_velocity_y += (velocidad_ideal - self.current_velocity_y) * 0.1
            self.current_tilt_y += self.current_velocity_y
            
            # If almost at 0 (minimal difference), snap and stop
            if diff < 0.2 or self.current_tilt_y >= 360.0:
                self.current_tilt_y = 0.0
                self.current_velocity_y = 0.0
                self.returning_to_zero = False

        if self.current_skin == "3d":
            self.skin_3d.update_rotation(self.visual_angle)
            self.skin_3d.update_tilt_y(self.current_tilt_y)
            # We don't draw 2D if 3D is active, the container handles rendering
        elif self.current_skin == "default":
            draw_2d_vinyl(painter, self.width(), self.height(), self.visual_angle)
        else:
            draw_2d_vinyl(painter, self.width(), self.height(), self.visual_angle)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x, y = event.position().x(), event.position().y()
            center_x = self.width() / 2
            center_y = self.height() / 2
            radius = min(center_x, center_y) * 0.95
            
            dist = math.hypot(x - center_x, y - center_y)
            if dist <= radius:
                self.is_dragging = True
                self.prev_mouse_angle = math.atan2(y - center_y, x - center_x)
                
                # Match the physical mouse angle to the current record position to grab it
                self.vinyl_model.mouse_angle = self.vinyl_model.angle

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            x, y = event.position().x(), event.position().y()
            center_x = self.width() / 2
            center_y = self.height() / 2
            
            current_mouse_angle = math.atan2(y - center_y, x - center_x)
            
            delta = current_mouse_angle - self.prev_mouse_angle
            
            if delta > math.pi:
                delta -= 2 * math.pi
            elif delta < -math.pi:
                delta += 2 * math.pi
                
            self.vinyl_model.move_mouse(delta)
            self.prev_mouse_angle = current_mouse_angle

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    def keyPressEvent(self, event):
        if self.current_skin != "3d":
            super().keyPressEvent(event)
            return
            
        params = self.skin_3d.get_camera_params()
        if not params: return
        
        step_pos = 1.0
        step_rot = 5.0
        
        # Get current rotation in radians to calculate directional vectors
        pitch = math.radians(params['pitch'])
        yaw = math.radians(params['yaw'])
        
        # Forward Vector
        fx = -math.sin(yaw) * math.cos(pitch)
        fy = math.sin(pitch)
        fz = -math.cos(yaw) * math.cos(pitch)
        
        # Right Vector
        rx = math.cos(yaw)
        rz = -math.sin(yaw)
        
        # Continuous Y rotation (toggled with R)
        if event.key() == Qt.Key_R:
            if self.tilt_y_active:
                # If active, deactivate it but mark it to return to zero
                self.tilt_y_active = False
                if self.current_tilt_y > 0.0:
                    self.returning_to_zero = True
                    print("=== [Y ROTATION] Stopping... waiting to return to 0 ===")
                else:
                    print("=== [Y ROTATION] Stopped at position 0 ===")
            elif not self.returning_to_zero:
                # Only activate if not currently returning to zero
                self.tilt_y_active = True
                print("=== [Y ROTATION] ACTIVATED ===")
            return
            
        # Rotation (Look around) - Arrows
        if event.key() == Qt.Key_Up:
            params['pitch'] += step_rot
        elif event.key() == Qt.Key_Down:
            params['pitch'] -= step_rot
        elif event.key() == Qt.Key_Left:
            params['yaw'] += step_rot
        elif event.key() == Qt.Key_Right:
            params['yaw'] -= step_rot
            
        # Relative movement (WASD) like an FPS game
        elif event.key() == Qt.Key_W:
            params['x'] += fx * step_pos
            params['y'] += fy * step_pos
            params['z'] += fz * step_pos
        elif event.key() == Qt.Key_S:
            params['x'] -= fx * step_pos
            params['y'] -= fy * step_pos
            params['z'] -= fz * step_pos
        elif event.key() == Qt.Key_D:
            params['x'] += rx * step_pos
            params['z'] += rz * step_pos
        elif event.key() == Qt.Key_A:
            params['x'] -= rx * step_pos
            params['z'] -= rz * step_pos
        # Absolute Up/Down with Q/E
        elif event.key() == Qt.Key_E:
            params['y'] += step_pos
        elif event.key() == Qt.Key_Q:
            params['y'] -= step_pos
        else:
            super().keyPressEvent(event)
            return
            
        self.skin_3d.set_camera_params(params)
        
        print(f"=== [CAMERA] ===")
        print(f"Position:  x: {params['x']:.1f},  y: {params['y']:.1f},  z: {params['z']:.1f}")
        print(f"Rotation:  pitch: {params['pitch']:.1f},  yaw: {params['yaw']:.1f},  roll: {params['roll']:.1f}")
        print("================")
