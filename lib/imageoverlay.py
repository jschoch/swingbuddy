
import sys
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QWidget,QVBoxLayout,QHBoxLayout
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor
from PySide6.QtCore import QTimer, QRectF
import os
import random
import pandas as pd

class ImageOverlay(QGraphicsView):
    def __init__(self, pixmap, data,raw_frames=[]):
        super().__init__()

        self.data = data
        self.index = 0
        
        # Load the base image
        self.pixmap = pixmap
        self.raw_frames = raw_frames
        
        if not self.pixmap.isNull():
            # Create a QGraphicsScene and add the base image to it
            self.scene = QGraphicsScene(self)
            self.image_item = QGraphicsPixmapItem(self.pixmap)
            self.scene.addItem(self.image_item)

            self.static_item = self.make_static_frame()

            self.scene.addItem(self.static_item)
            # Pre-render all frames
            self.frames = []
            self.make_frames(self.raw_frames)
            # Create a QGraphicsPixmapItem for the overlay and add it to the scene
            self.overlay_item = QGraphicsPixmapItem(self.frames[self.index])
            self.scene.addItem(self.overlay_item)

            # Set the scene for the view
            self.setScene(self.scene)
            
        else:
            print(f"Failed to load image. {os.getcwd()}")

    def make_static_frame(self):
        frame_pixmap = QPixmap(self.pixmap.size())
        frame_pixmap.fill(QColor('transparent'))
        
        painter = QPainter(frame_pixmap)
        pen = QPen(QColor('green'), 5)  # Red color and 2 pixels thick line
        painter.setPen(pen)
        painter.drawLine(0,0, 800,600)
        painter.end()
        return QGraphicsPixmapItem(frame_pixmap)

    def make_frames(self,raw_frames):
        for i in range(len(raw_frames)):
                self.make_frame(i)
    

    def make_frame(self,i):
        
        frame_pixmap = QPixmap(self.pixmap.size())
        frame_pixmap.fill(QColor('transparent'))
        
        painter = QPainter(frame_pixmap)
        pen = QPen(QColor('red'), 2)  # Red color and 2 pixels thick line
        painter.setPen(pen)
        
        if not self.data.empty:
            x_pos = self.data['HipMiddle_x'].iloc[i].copy()
            #ipainter.drawLine(0, random.randint(0, 600), point[0], point[1])
            h = frame_pixmap.height() 
            print(f" Xpos: {x_pos}, h: {h}")
            painter.drawLine(x_pos/2, 0, x_pos/2, h)
            #painter.drawLine(0,0,800,800)
            painter.end()
        else:
            print("Data is empty")
        self.frames.append(frame_pixmap)

    def next_frame(self):
        if self.index < len(self.frames):
            self.image_item.setPixmap(self.raw_frames[self.index])
            self.overlay_item.setPixmap(self.frames[self.index])
            self.index += 1
        else:
            #self.timer.stop()  # Stop the timer when all frames have been displayed
            self.index = 0

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        print("Resize, TODO add back")
        return
        new_size = event.size()
        scene_rect = QRectF(0, 0, new_size.width(), new_size.height())
        self.scene.setSceneRect(scene_rect)

        # Scale the items to fit the new size
        scale_x = new_size.width() / self.pixmap.width()
        scale_y = new_size.height() / self.pixmap.height()
        scale_factor = min(scale_x, scale_y)
        
        self.image_item.setScale(scale_factor)
        self.overlay_item.setScale(scale_factor)
        self.static_item.setScale(scale_factor)  # Scale the static item as well
        print(f"scale factor was {scale_factor}")