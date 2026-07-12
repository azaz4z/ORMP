from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt, Signal

class ProgressBar(QWidget):
    # Qt Signal that emits a float between 0.0 and 1.0
    jump_requested = Signal(float)

    def __init__(self, vinyl_model, parent=None):
        super().__init__(parent)
        self.vinyl_model = vinyl_model
        self.is_dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Dark background (unplayed portion)
        painter.setBrush(QBrush(QColor("#1a252f")))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width(), self.height())
        
        # Current progress based on physical model
        progress = self.vinyl_model.angle / self.vinyl_model.max_angle if self.vinyl_model.max_angle > 0 else 0
        progress = max(0, min(progress, 1.0))
        current_width = self.width() * progress
        
        # Blue bar (played portion)
        painter.setBrush(QBrush(QColor("#3498db")))
        painter.drawRect(0, 0, current_width, self.height())

    def calculate_mouse_progress(self, event):
        x = event.position().x()
        progress = x / self.width()
        progress = max(0.0, min(progress, 1.0))
        return progress

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            progress = self.calculate_mouse_progress(event)
            self.jump_requested.emit(progress)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            progress = self.calculate_mouse_progress(event)
            self.jump_requested.emit(progress)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
