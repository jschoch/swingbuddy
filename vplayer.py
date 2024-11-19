# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from PySide6.QtCore import QObject, QThread, Signal,  Qt,QPoint, Slot,QTimer,QThreadPool,QRunnable,QStringListModel
from PySide6.QtGui import QAction,QIcon,QMovie,QPen, QStandardItemModel, QStandardItem,QImage, QPixmap,QPainter,QTransform
from PySide6.QtWidgets import (QMainWindow, QListView, QPushButton, QTextEdit,QSlider,QFileDialog,
    QHBoxLayout, QWidget, QVBoxLayout, QLabel,QDialog,QDialogButtonBox,QGraphicsView, QGraphicsScene,
    QSizePolicy, QMessageBox,QDialog, QGridLayout, QTextEdit)
import threading
import queue
import concurrent.futures
from util import load_pipes
import pandas as pd
import traceback
import math
import time
from lib.imageoverlay import ImageOverlay
from lib.enums import LoadHint, TrcT

class WorkerError(Exception):
    pass
    
class WorkerThread(QThread):
    result = Signal(object)

    def __init__(self, clip, parent_size, lr,df,doreload=False):
        super().__init__()
        self.clip = clip
        if clip is None and (parent_size == 0 and lr == 0 and df.empty):
            print("video player worker thread :(  worker init)")
        elif clip is None:
            raise WorkerError(f"Need the clip yo {lr}")
        self.lr = lr
        self.df = df
        #print(f"worker init: {clip} {parent_size} {lr} {df.head()}")
        self.isRunning = False
        self.doreload = doreload
        self.startT = time.time()

    def get_raw_frames(self):
        try:
            self.isRunning = True
            results = {}
            vid_stream = self.clip.streams.video[0] 
            vid_stream.thread_type = 'AUTO' 
            #vid_stream
            frames = self.clip.decode(vid_stream) 
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                future_to_frame = {
                    executor.submit(self.process_raw_frame, i,frame): (i, frame) for i,frame in enumerate(frames)
                }
                for future in concurrent.futures.as_completed(future_to_frame):
                    (frame,frame_index) = future_to_frame[future]
                    try:
                        (raw_frame,idx,processed_frame) = future.result()
                        #print(f" {idx} ",end="")
                        results[idx] = (raw_frame,processed_frame)
                    except Exception as e:
                        print(f'Generated an exception: {e}')
                        tb = traceback.format_exc()
                        print(tb)
            sorted_data = dict(sorted(results.items()))
            processedFrames = [value[0] for value in sorted_data.values()]
            obj = (processedFrames,self.lr)
            self.result.emit(obj)
            vid_stream.close()
            self.isRunning = False 
        except Exception as e:
            print(f'Generated an exception: {e}')
            self.isRunning = False

    def process_raw_frame(self,i,frame):
        img = frame.to_image()
        raw_q_image = QImage(img.tobytes(),img.width, img.height,  QImage.Format_RGB888)
        #(q_image, fooIdx) = self.process_frame(i,raw_q_image)
        q_image = None
        return (raw_q_image,i,q_image)

    def run(self):
        """Override run method
        """
        self.get_raw_frames()


# Video playback class responsible for managing the actual playback of the video.
class VideoPlayBack:
    def __init__(self, video_playback_ui, logger):
        self.video_playback_ui = video_playback_ui

        self.face_video_clip = None
        self.dtl_video_clip = None
        self.current_frame_index = 0
        self.is_playing = False
        self.dtldf = pd.DataFrame()
        self.facedf = pd.DataFrame() 
        self.playback_speed = 1.0
        #self.lr = lr
        
        self.t1 = WorkerThread(None, 0, 0,pd.DataFrame())
        self.t0 = WorkerThread(None, 0, 0,pd.DataFrame())
        self.timer = QTimer()
        self.logger = logger
        self.start()

    def reset(self):
        self.current_frame_index = 0
        self.is_playing = False
        self.dtldf = pd.DataFrame()
        self.facedf = pd.DataFrame() 

    def shutdown(self):
        if self.face_video_clip is not None:
            self.face_video_clip.close()
        if self.dtl_video_clip is not None:
            self.dtl_video_clip.close()
    # Function to load frames from the video clip
    def do_load_frame(self,lr,clip, worker):
        
        if clip is None:
            self.logger.error(f"clip {lr} was NONE!!!!!!!!!!!")
            return
        self.logger.debug(f"{lr} the clip: {clip}  ")
        if worker.isRunning:
            self.logger.error("worker is already running")
            return
        worker.result.connect(self.frames_done)
        worker.start()

    def load_frame(self,lr,reload=False):
        """
        loads the workers up to process the frames 
        """
        self.logger.debug(f"load_frame() starting to load {lr}")
        parent_size = self.video_playback_ui.parent().size() 
        if not reload:
            if(lr):
                self.t1 = WorkerThread(self.dtl_video_clip, parent_size, lr,self.dtldf.copy())
                self.do_load_frame(lr,self.dtl_video_clip, self.t1)
            else:
                self.t0 = WorkerThread(self.face_video_clip, parent_size, lr,self.facedf.copy())
                self.do_load_frame(lr,self.face_video_clip, self.t0)
        else:
            self.logger.debug("running reload in load_frame")
            if(lr):
                self.video_playback_ui.dtl_overlay.data = self.dtldf.copy()
                self.video_playback_ui.dtl_overlay.make_frames()
                self.is_playing = True
            else:
                self.video_playback_ui.face_overlay.data = self.facedf.copy()
                self.video_playback_ui.face_overlay.make_frames()
                self.is_playing = True


        self.logger.debug("VideoPlayBack load_frames() done queueing framse")


    def frames_done(self,obj):
        (frames, lr) = obj
        #self.logger.debug(f"frames done count: {len(frames)} lr: {lr}") 
        #self.logger.debug(f"rf: \n{rawFrames}\nfr:{frames}")
        self.logger.debug(f"frames dones lr:{lr} {len(frames)}") 

        if lr: 
            self.dtlRawFrames = frames
            self.video_playback_ui.slider.setRange(0,len(self.dtlRawFrames)-1)
            self.update_frame(lr)
            self.logger.debug(f"done loading frames time was: {self.t1.startT - time.time()}")
            self.video_playback_ui.dtl_overlay.data = self.dtldf.copy() 
            pixmaps = []
            for frame in frames:
                opixmap = QPixmap.fromImage(frame)
                transform = QTransform()
                pixmap = opixmap.transformed(transform.rotate(-90))
                pixmaps.append(pixmap)
            self.video_playback_ui.dtl_overlay.raw_frames = pixmaps
            self.logger.debug(f"DTL raw frames were: {len(self.dtlRawFrames)} ")
            self.video_playback_ui.dtl_overlay.make_frames()
            self.is_playing = True
            #self.play()
        else:
            self.faceRawFrames = frames
            self.video_playback_ui.slider.setRange(0,len(self.faceRawFrames)-1)
            self.video_playback_ui.face_overlay.data = self.facedf.copy() 
            pixmaps = []
            for frame in frames:
                opixmap = QPixmap.fromImage(frame)
                transform = QTransform()
                pixmap = opixmap.transformed(transform.rotate(-90))
                pixmaps.append(pixmap)
            self.video_playback_ui.face_overlay.raw_frames = pixmaps
            self.logger.debug(f"Face raw frames were: {len(self.faceRawFrames)} ")
            self.video_playback_ui.face_overlay.make_frames()
            self.is_playing = True
            #self.play()
            self.update_frame(lr)

    # Function to update the frame
    def update_frame(self,lr):

        # reset index if overflowed
        if self.current_frame_index < 0:
            self.current_frame_index = 0
        if self.current_frame_index >= len(self.video_playback_ui.dtl_overlay.raw_frames):
            self.current_frame_index = 0


        if(lr):
            self.video_playback_ui.dtl_overlay.update_frame(self.current_frame_index)
        else:
            self.video_playback_ui.face_overlay.update_frame(self.current_frame_index)
        self.video_playback_ui.slider.setValue(self.current_frame_index)

        self.video_playback_ui.slider_label.setText(f"Frame: {self.current_frame_index}")



    def update_all_frames(self):
        self.current_frame_index += 1
        if not self.is_playing:
            return
        self.update_frame(0)
        self.update_frame(1)

    # Function to toggle play/pause
    def toggle_play_pause(self):
        self.logger.debug(f"MORE WTF {self.is_playing}")
        

        if self.is_playing:
            self.is_playing = False
        else:
            self.is_playing = True

    @Slot()
    def play(self):
        if(self.is_playing):
            self.is_playing = False
        else:
            self.is_playing = True

    @Slot()
    def pause(self):
        self.is_playing = False

    @Slot()
    def stop(self):
        if self.is_playing:
            self.is_playing = False

    @Slot()
    def start(self):
        if not self.is_playing:
            self.is_playing = True
            self.timer.timeout.connect(self.update_all_frames)
            self.timer.start(1000/60)


    # Function to set playback speed
    def set_playback_speed(self, value):
        #TODO get thsi working again
        self.speed_slider_label.setText(f"Speeed: {value}")
        self.playback_speed = value

    # Function to set overlay position
    #def set_overlay_position(self, position):
        #self.video_playback_ui.overlay_widget.position = position
        #self.video_playback_ui.overlay_widget.update()


# Video playback UI class responsible for managing the user interface elements related to video playback.
class VideoPlayBackUi(QWidget):
    def __init__(self):
        super().__init__()

        # Create play, pause, slider, speed slider, overlay, and save frame button
        self.play_button = QPushButton("Play")
        self.play_button.setEnabled(False)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider_label = QLabel("Frame Slider:")
        self.slider.setSingleStep(1)
        self.slider.setMaximum(250)
        self.slider.setValue(0)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider_label = QLabel("Playback Speed:")

        # Create grid layout for video labels
        self.vid_layout = QHBoxLayout()

        loading_pixmap = QPixmap("loading.gif")  # Replace with your loading image path
        self.dtl_overlay = ImageOverlay(loading_pixmap, pd.DataFrame(),TrcT.DTL, [loading_pixmap])
        self.dtl_overlay.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dtl_overlay.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.vid_layout.addWidget(self.dtl_overlay)  # Add the overlay to the main layout

        self.face_overlay = ImageOverlay(loading_pixmap, pd.DataFrame(),TrcT.FACE, [loading_pixmap])
        self.vid_layout.addWidget(self.face_overlay)  # Add the overlay to the main layout

        # Create layout and add widgets
        video_button_layout = QHBoxLayout()
        slider_layout = QHBoxLayout()

        video_button_layout.addWidget(self.play_button, 1)
        video_button_layout.addWidget(self.slider_label)
        slider_layout.addWidget(self.slider, 5)
        video_button_layout.addWidget(self.speed_slider_label)
        video_button_layout.addWidget(self.speed_slider, 3)

        video_button_layout.setAlignment(Qt.AlignBottom)

        # Create a QWidget to hold the controls
        ctrl_widget = QWidget()
        ctrl_widget.setLayout(video_button_layout)
        ctrl_widget.setStyleSheet("background-color: #f0f0f0;")
        ctrl_widget.setMaximumHeight(75)

        # Create main layout and add layouts
        self.main_layout = QVBoxLayout()

        self.setLayout(self.main_layout)
        self.main_layout.addWidget(ctrl_widget)
        self.main_layout.addLayout(slider_layout)
        self.main_layout.addLayout(self.vid_layout)