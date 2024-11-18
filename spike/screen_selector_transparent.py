import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication, QMainWindow

from PyQt6.QtGui import QPainter

class Img(QMainWindow):
    def __init__(self, img_path, parent=None):
        super().__init__(parent)
        self.qimg = QImage(img_path)
        self.setStyleSheet('QMainWindow {background:transparent}')
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, qpaint_event):
        painter = QPainter(self)
        rect = qpaint_event.rect()
        painter.drawImage(rect, self.qimg)
        self.showFullScreen()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    img_path = 'coords.png'
    window = Img(img_path)
    window.show()
    sys.exit(app.exec())