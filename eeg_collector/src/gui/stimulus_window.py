from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QPolygon
from ..config import TaskType

class StimulusWindow(QWidget):
    keyPressed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EEG Experiment Stimulus")
        self.showFullScreen()
        
        # White background
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.GlobalColor.white)
        self.setPalette(p)
        
        self.current_task = None
        self.is_relax = False
        
        self.feedback_mode = False
        self.feedback_correct = False
        self.feedback_prediction = None
        
    def set_task(self, task_name):
        self.feedback_mode = False # Reset feedback
        
        if task_name == "Relax":
            self.is_relax = True
            self.current_task = None
        else:
            self.is_relax = False
            self.current_task = task_name
            
        self.repaint()
        
    def show_feedback(self, prediction, is_correct):
        self.feedback_mode = True
        self.feedback_correct = is_correct
        self.feedback_prediction = prediction
        self.repaint()

    def keyPressEvent(self, event):
        self.keyPressed.emit(event.key())
        super().keyPressEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        center_x = w // 2
        center_y = h // 2
        
        pen = QPen(Qt.GlobalColor.black)
        pen.setWidth(5)
        painter.setPen(pen)
        
        # Draw background explicitely
        bg_rect = self.rect()
        if self.feedback_mode:
            bg_color = Qt.GlobalColor.green if self.feedback_correct else Qt.GlobalColor.red
            painter.fillRect(bg_rect, bg_color)
            task_to_draw = None 
        else:
            painter.fillRect(bg_rect, Qt.GlobalColor.white)
            task_to_draw = self.current_task

        # Draw content
        if self.feedback_mode and task_to_draw:
             self._draw_task_symbol(painter, center_x, center_y, task_to_draw)
             
        elif self.is_relax:
            # Draw Fixation Cross
            size = 50
            painter.drawLine(center_x - size, center_y, center_x + size, center_y)
            painter.drawLine(center_x, center_y - size, center_x, center_y + size)
            
        elif task_to_draw:
            self._draw_task_symbol(painter, center_x, center_y, task_to_draw)
            
    def _draw_task_symbol(self, painter, center_x, center_y, task_name):
        size = 100
        
        if "LEFT" in task_name:
            self._draw_arrow(painter, center_x, center_y, size, "left")
        elif "RIGHT" in task_name:
            self._draw_arrow(painter, center_x, center_y, size, "right")
        elif "BOTH" in task_name:
            # Double Up Arrow side by side
            offset = int(size / 1.5)
            self._draw_arrow(painter, center_x - offset, center_y, size, "up")
            self._draw_arrow(painter, center_x + offset, center_y, size, "up")
        elif "FEET" in task_name:
            # Double Down Arrow side by side
            offset = int(size / 1.5)
            self._draw_arrow(painter, center_x - offset, center_y, size, "down")
            self._draw_arrow(painter, center_x + offset, center_y, size, "down")
        elif "RELAX" in task_name:
             painter.drawEllipse(QPoint(center_x, center_y), size, size)

    def _draw_arrow(self, painter: QPainter, x: int, y: int, size: int, direction: str):
        # Simple arrow drawing
        path = QPolygon()
        
        if direction == "left":
            # <
            path.append(QPoint(x + size, y - size//2))
            path.append(QPoint(x - size, y))
            path.append(QPoint(x + size, y + size//2))
        elif direction == "right":
            # >
            path.append(QPoint(x - size, y - size//2))
            path.append(QPoint(x + size, y))
            path.append(QPoint(x - size, y + size//2))
        elif direction == "up":
            # ^
            path.append(QPoint(x - size//2, y + size))
            path.append(QPoint(x, y - size))
            path.append(QPoint(x + size//2, y + size))
        elif direction == "down":
            # v
            path.append(QPoint(x - size//2, y - size))
            path.append(QPoint(x, y + size))
            path.append(QPoint(x + size//2, y - size))
            
        painter.drawPolyline(path)
