import sys
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor
from PySide6.QtCore import QTimer
import os
import random

class ImageOverlay(QGraphicsView):
    def __init__(self, pixmap, data):
        super().__init__()

        self.data = data
        self.index = 0
        
        # Load the base image
        self.pixmap = pixmap
        
        if not self.pixmap.isNull():
            # Create a QGraphicsScene and add the base image to it
            self.scene = QGraphicsScene(self)
            self.image_item = QGraphicsPixmapItem(self.pixmap)
            self.scene.addItem(self.image_item)

            static_pixmap = self.make_static_frame()

            self.scene.addItem(static_pixmap)
            # Pre-render all frames
            self.frames = []
            for i in range(len(data)):
                self.make_frame(i)

            # Create a QGraphicsPixmapItem for the overlay and add it to the scene
            self.overlay_item = QGraphicsPixmapItem(self.frames[self.index])
            self.scene.addItem(self.overlay_item)

            # Set the scene for the view
            self.setScene(self.scene)
            
            

        else:
            print(f"Failed to load image. {os.getcwd()}")

    def make_static_frame(self):
        frame_pixmap = QPixmap(pixmap.size())
        frame_pixmap.fill(QColor('transparent'))
        
        painter = QPainter(frame_pixmap)
        pen = QPen(QColor('green'), 5)  # Red color and 2 pixels thick line
        painter.setPen(pen)
        painter.drawLine(0,0, 800,600)
        painter.end()
        return QGraphicsPixmapItem(frame_pixmap)
        
    def make_frame(self,i):
        frame_pixmap = QPixmap(pixmap.size())
        frame_pixmap.fill(QColor('transparent'))
        
        painter = QPainter(frame_pixmap)
        pen = QPen(QColor('red'), 2)  # Red color and 2 pixels thick line
        painter.setPen(pen)
        
        point = self.data[i]
        painter.drawLine(0, random.randint(0, 600), point[0], point[1])
        
        painter.end()
        self.frames.append(frame_pixmap)

    def next_frame(self):
        if self.index < len(self.frames):
            if self.index % 2 == 0:
                p2 = QPixmap("test1.png")
                self.image_item.setPixmap(p2)
            else:
                self.image_item.setPixmap(self.pixmap)
            self.overlay_item.setPixmap(self.frames[self.index])
            self.index += 1
        else:
            #self.timer.stop()  # Stop the timer when all frames have been displayed
            self.index = 0

if __name__ == "__main__":
    app = QApplication(sys.argv)

    image_path = "20241102-101435-left_screen.png"
    data = [
        (100, 100), (200, 200), (300, 350),
        (400, 400), (500, 500), (600, 60),
        (0, 700), (0, 800), (0, 900), (0, 1000)
    ]
    
    pixmap = QPixmap(image_path)
    window = ImageOverlay(pixmap, data)
    # Start the timer to switch between frames
    timer = QTimer()
    timer.timeout.connect(window.next_frame)
    timer.start(1000)  # Change frame every second
    window.setWindowTitle("Image Overlay Example")
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())