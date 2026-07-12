import math
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QPointF

def draw_2d_vinyl(painter: QPainter, width: int, height: int, visual_angle: float):
    painter.setRenderHint(QPainter.Antialiasing)

    # Responsive calculations
    center_x = width / 2
    center_y = height / 2
    # Max radius is 95% of the shortest dimension (padding of 5%)
    radius = min(center_x, center_y) * 0.95

    # Base of the record
    painter.setBrush(QBrush(QColor("#111111")))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(
        QPointF(center_x, center_y),
        radius, radius
    )
    
    # Red label in the center (a third of the radius)
    label_radius = radius * 0.33
    painter.setBrush(QBrush(QColor("#e74c3c")))
    painter.drawEllipse(
        QPointF(center_x, center_y),
        label_radius, label_radius
    )
    
    # White center hole
    hole_radius = radius * 0.05
    painter.setBrush(QBrush(QColor("#ffffff")))
    painter.drawEllipse(QPointF(center_x, center_y), hole_radius, hole_radius)
    
    # Rotation line (record marker)
    painter.setPen(QPen(QColor("#ecf0f1"), max(2, int(radius*0.02)))) # Dynamic thickness
    
    x = center_x + (radius * 0.85) * math.cos(visual_angle)
    y = center_y + (radius * 0.85) * math.sin(visual_angle)
    x_inner = center_x + label_radius * math.cos(visual_angle)
    y_inner = center_y + label_radius * math.sin(visual_angle)
    painter.drawLine(QPointF(x_inner, y_inner), QPointF(x, y))
