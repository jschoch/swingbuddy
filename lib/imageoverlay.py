
import sys
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QWidget,QVBoxLayout,QHBoxLayout
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor
from PySide6.QtCore import QTimer, QRectF,Qt,QEvent
import os
import random
import pandas as pd
from util import load_pipes
from lib.enums import LoadHint, TrcT

class ImageOverlay(QGraphicsView):
    def __init__(self, pixmap, data,trcT,raw_frames=[]):
        super().__init__()

        self.data = data
        self.index = 0
        
        # Load the base image
        self.pixmap = pixmap
        self.raw_frames = raw_frames
        self.pipes = load_pipes() 
        self.static_items = []
        self.trcT = trcT
        if not self.pixmap.isNull():
            # Create a QGraphicsScene and add the base image to it
            self.scene = QGraphicsScene(self)
            # Set the minimum height for the scene
            min_height = 800  # Example minimum height in pixels
            self.scene.setSceneRect(self.scene.sceneRect().adjusted(0, 0, 0, min_height))
            self.image_item = QGraphicsPixmapItem(self.pixmap)
            self.scene.addItem(self.image_item)
            # TODO: do we need to make static frames on init?  Probly not
            #self.make_static_frame()
            # Pre-render all frames
            self.frames = {}
            self.make_frames()
            # Create a QGraphicsPixmapItem for the overlay and add it to the scene
            self.overlay_item = QGraphicsPixmapItem(self.raw_frames[self.index])
            self.scene.addItem(self.overlay_item)
            scale_factor = 0.3
            self.image_item.setScale(scale_factor)
            self.overlay_item.setScale(scale_factor)
            for item in self.static_items:
                item.setScale(scale_factor)
            #self.static_item.setScale(scale_factor)
            # Set the scene for the view
            self.setScene(self.scene)
            
        else:
            print(f"Failed to load image. {os.getcwd()}")

    def make_static_frames(self):
        if self.data.empty:
            print("no data for static frames, skipping")
            return
        self.static_items = []
        frame_pixmap = QPixmap(self.raw_frames[0].size())
        frame_pixmap.fill(QColor('transparent'))
        for pipe in self.pipes:
            print(f"checking pipe {pipe.config['name']}")
            if pipe.config['render_static']:
                print(f"found static image pipe {pipe.config['name']}")
                frame = pipe.process_static_frame(frame_pixmap,self.data,0) 
                item = QGraphicsPixmapItem(frame)
                self.static_items.append(item)
                self.scene.addItem(item)


    def make_frames(self):
        self.make_static_frames()
        frame_count = len(self.raw_frames)
        #print(f"makeing {frame_count} frames {len(self.data)} {self.raw_frames}")
        if frame_count < 2:
            print(f"no frames, make_frames() skipping")
            return
            #scene_rect = QRectF(0, 0, aframe.width(), aframe.height())
            #self.scene.setSceneRect(scene_rect)

        # first run there will be no frames
        for idx,frame in enumerate(self.raw_frames):
            self.frames[idx] = frame.copy()
        
        for pipe in self.pipes:
            print(f"checking pipe: {pipe.config['name']}")
            if pipe.config['render_tracking']:
                print(f"found trace image pipe {pipe.config['name']}")
                for idx,key in enumerate( self.frames):
                    frame = self.frames[key]
                    new_frame = pipe.process_tracking_frame(frame,self.data,idx)
                    #print(f" idx: {idx} frame {frame} new_frame {new_frame}")
                    self.frames[idx] = new_frame

        self.resize(self.size())
    

    def next_frame(self):
        if self.index < len(self.frames):
            self.image_item.setPixmap(self.raw_frames[self.index])
            self.overlay_item.setPixmap(self.frames[self.index])
            self.index += 1
        else:
            #self.timer.stop()  # Stop the timer when all frames have been displayed
            self.index = 0
    def update_frame(self,idx):
        if idx > len(self.raw_frames):
            return
        if idx not in self.frames:
            print(f"{self.trcT}Frame {idx} was none {len(self.frames)}")
            return 
        frame = self.frames[idx]
        raw_frame = self.raw_frames[idx]
        #print(f"updating frame {idx} {frame} {raw_frame}")
        self.fitInView(self.image_item, Qt.KeepAspectRatio)
        self.image_item.setPixmap(raw_frame)
        self.overlay_item.setPixmap(frame)

    #def trigger_resize(self):
        # Manually create and pass a QResizeEvent
        #resize_event = QEvent.QResizeEvent(self.size(), self.size())
        #self.resizeEvent(resize_event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        new_size = event.size()
        scene_rect = QRectF(0, 0, new_size.width(), new_size.height())
        self.scene.setSceneRect(scene_rect)

        # Scale the items to fit the new size
        scale_x = new_size.width() / self.pixmap.width()
        scale_y = new_size.height() / self.pixmap.height()
        scale_factor = min(scale_x, scale_y)
        
        self.image_item.setScale(scale_factor)
        self.overlay_item.setScale(scale_factor)
        for item in self.static_items:
            item.setScale(scale_factor)  # Scale the static item as well
        #print(f"scale factor was {scale_factor}")