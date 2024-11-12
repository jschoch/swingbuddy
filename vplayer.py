# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from PySide6.QtCore import QObject, QThread, Signal,  Qt,QPoint, Slot,QTimer,QThreadPool,QRunnable,QStringListModel
from PySide6.QtGui import QAction,QIcon,QMovie,QPen, QStandardItemModel, QStandardItem,QImage, QPixmap,QPainter,QTransform
from PySide6.QtWidgets import (QMainWindow, QListView, QPushButton, QTextEdit,QSlider,QFileDialog,
    QHBoxLayout, QWidget, QVBoxLayout, QLabel,QDialog,QDialogButtonBox,
    QSizePolicy, QMessageBox,QDialog, QGridLayout, QTextEdit)
import threading
import queue
import concurrent.futures

    
class WorkerThread(QThread):
    result = Signal(object)

    def __init__(self, clip, parent_size, lr,dtldf):
        super().__init__()
        self.clip = clip
        self.parent_size = parent_size
        self.lr = lr
        self.dtldf = dtldf
        self.isRunning = False

    def do_work3(self):
        """
        works but shoudl delete in favor of mulltithreading version 
        """
        self.isRunning = True
        qimage_frames = []
        #container = av.open(path, mode='r', format='mp4') 
        vid_stream = self.clip.streams.video[0] 
        vid_stream.thread_type = 'AUTO' 
        frames = self.clip.decode(vid_stream) 
        i = 0
        print("Frames: ")
        for frame in frames: 
            print(f" {i} ",end="")
            i = i + 1
            scaled_image = self.process_frame(frame) 
            qimage_frames.append(scaled_image)
        obj = (qimage_frames,self.lr)
        self.result.emit(obj)
        self.isRunning = False 
    
    def draw_hip_start(self,painter,height):
        """
        This draws the starting hip position on every frame 
        """
        pen = QPen(Qt.green, 4)
        painter.setPen(pen)
        x_pos, y_pos = self.get_pose_data(0)
        painter.drawLine(x_pos, 0, x_pos, height) 

    def process_frame(self,index,frame):
        x_pos, y_pos = self.get_pose_data(index)
        img = frame.to_image()
        q_image = QImage(img.tobytes(),img.width, img.height,  QImage.Format_RGB888)
        my_transform = QTransform()
        my_transform.rotate(-90)
        q_image = q_image.transformed(my_transform)
        if self.lr:
            painter = QPainter(q_image)
            self.draw_hip_start(painter,q_image.height())
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            painter.drawLine(x_pos, 0, x_pos, q_image.height())
            painter.end()
        height = 450
        #height = self.parent_size.height() - 100
        scaled_image = q_image.scaledToHeight(height,Qt.SmoothTransformation)
        # TODO:  map this to the TRC data via some sort of pipeline
        #  you should be able the chain them based on some config and or boolieans
        
        
        return (scaled_image,index)

    def do_work(self):
        self.isRunning = True
        qimage_frames = []
        results = {}
        vid_stream = self.clip.streams.video[0] 
        vid_stream.thread_type = 'AUTO' 
        frames = self.clip.decode(vid_stream) 
        print("frames: ")
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_to_frame = {
                executor.submit(self.process_frame, i,frame): (i, frame) for i,frame in enumerate(frames)
            }
            for future in concurrent.futures.as_completed(future_to_frame):
                (frame,frame_index) = future_to_frame[future]
                try:
                    (data,idx) = future.result()
                    print(f" {idx} ",end="")
                    results[idx] = data
                except Exception as e:
                    print(f'Generated an exception: {e}')
        qimage_frames = [results[key] for key in sorted(results.keys())]
        obj = (qimage_frames,self.lr)
        self.result.emit(obj)
        self.isRunning = False 
     
    def get_pose_data(self, frame_number):
        x = self.dtldf.iloc[frame_number]
        y = 100
        print(f"*{frame_number} _ {x}*",end="")
        return x,y

    def run(self):
        """Override run method
        """
        self.do_work()


# Video playback class responsible for managing the actual playback of the video.
class VideoPlayBack:
    def __init__(self, video_playback_ui, video_clip):
        self.video_playback_ui = video_playback_ui
        self.video_clip = video_clip
        self.video_clip2 = None
        self.qimage_frames = []
        self.qimage_frames2 = []
        self.current_frame_index = 0
        self.is_playing = False
        self.dtldf = []
        self.facedf = []
        self.playback_speed = 1.0
        #self.lr = lr
        self.t1 = WorkerThread(None, 0, 0,[])
        self.t0 = WorkerThread(None, 0, 0,[])
        self.timer = QTimer()
        self.start()

    # Function to load frames from the video clip
    def load_frame(self,lr):
        self.logger.debug("load_frame() starting to load")
        parent_size = self.video_playback_ui.parent().size()

        video_clip = None
        if(lr):
            self.qimage_frames2 = []
            video_clip = self.video_clip2
            #self.video_playback_ui.vid2_text.setText(f"Begin Loading!\n{self.video_clip2.format.name}")
            if self.t1.isRunning:
                self.logger.error("t1 is already running")
                return
            
            self.t1 = WorkerThread(video_clip, parent_size, lr,self.dtldf)
            self.t1.result.connect(self.frames_done)
            self.t1.finished.connect(self.t1.deleteLater)
            self.t1.start()


        else:
            self.qimage_frames = []
            video_clip = self.video_clip
            #self.video_playback_ui.vid1_text.setText(f"Begin Loading!\n{self.video_clip.format.name}")
            if self.t0.isRunning:
                self.logger.error("t0 is already running")
                return

            self.t0 = WorkerThread(video_clip, parent_size, lr,self.facedf)
            self.t0.result.connect(self.frames_done)
            self.t0.finished.connect(self.t0.deleteLater)
            self.t0.start()

        if video_clip is None:
            self.logger.debug("class: VideoPlayBack, fun: load_frame: video_clip is Null")
            return

        self.logger.debug("VideoPlayBack load_frames() done loading framse")

        if(lr):
            self.video_playback_ui.vid2_text.setText(f"{self.video_clip2}")
        else:
            self.video_playback_ui.vid1_text.setText(f"{self.video_clip}")
        return

    def frames_done(self,obj):
        (frames, lr) = obj
        
        if lr: 
            self.qimage_frames2 = frames
            self.update_frame(lr)
            self.video_playback_ui.slider.setRange(0,len(self.qimage_frames2)-1)
        else:
            self.qimage_frames = frames
            self.video_playback_ui.slider.setRange(0,len(self.qimage_frames)-1)
            self.update_frame(lr)

    # Function to update the frame
    def update_frame(self,lr):
        qimage_frames = None

        
        #  dont start stop the timer, just don't update if it is not playing

        
        if(lr):
            qimage_frames = self.qimage_frames2
        else:
            qimage_frames = self.qimage_frames

        if qimage_frames == None or qimage_frames == []:
            return


        if self.current_frame_index < 0:
            self.current_frame_index = 0
        if self.current_frame_index < len(qimage_frames):
            qimage_frame = qimage_frames[self.current_frame_index]
            pixmap = QPixmap.fromImage(qimage_frame)

            if(lr):
                self.video_playback_ui.video_label2.setPixmap(pixmap)
                self.video_playback_ui.video_label2.setAlignment(Qt.AlignLeft)
            else:
                self.video_playback_ui.video_label1.setPixmap(pixmap)
                self.video_playback_ui.video_label1.setAlignment(Qt.AlignLeft)
            self.video_playback_ui.slider.setValue(self.current_frame_index)
        else:
            self.current_frame_index = 0

        self.video_playback_ui.slider_label.setText(f"Frame: {self.current_frame_index}")


    # Function to reverse the frame
    def reverse_frame(self):
        self.current_frame_index -= 1
        self.update_frame(0)
        self.update_frame(1)
        self.current_frame_index -= 1

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

    # Function to play video in reverse
    def reverse_play(self):
        stream = self.video_clip.streams.video[0]
        fps = int(stream.average_rate)
        if self.video_clip is None:
            QMessageBox.warning(self.video_playback_ui, "File not found", "Load the video file first")
            return
        self.timer.timeout.connect(self.reverse_frame)
        self.timer.start(1000 / (fps * self.playback_speed))

    # Function to set playback speed
    def set_playback_speed(self, value):
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
        self.play_reverse_button = QPushButton("Play Reverse")
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
        self.vid_layout = QGridLayout()

        # Create video labels
        self.video_label1 = QLabel()
        self.video_label1.setStyleSheet("border: 1px solid red;")
        self.video_label1.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.video_label1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Ensure it expands

        self.video_label2 = QLabel()
        self.video_label2.setStyleSheet("border: 1px solid black;")
        self.video_label2.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.video_label2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Ensure it expands

        # Add widgets to video layout
        self.vid1_text = QLabel("No Vid1 Loaded")
        self.vid_layout.addWidget(self.vid1_text, 0, 0, alignment=Qt.AlignLeft)  # Placeholder for video file name
        self.vid_layout.addWidget(self.video_label1, 1, 0, alignment=Qt.AlignLeft)

        self.vid2_text = QLabel("No Vid2 Loaded")
        self.vid_layout.addWidget(self.vid2_text, 0, 1, alignment=Qt.AlignRight)  # Placeholder for video file name
        self.vid_layout.addWidget(self.video_label2, 1, 1, alignment=Qt.AlignRight)

        self.screen_label2 = QLabel()
        self.vid_layout.addWidget(self.screen_label2,1,2)

        # Create layout and add widgets
        video_button_layout = QHBoxLayout()
        slider_layout = QHBoxLayout()
        video_button_layout.addWidget(self.play_button, 1)
        video_button_layout.addWidget(self.play_reverse_button, 1)
        video_button_layout.addWidget(self.slider_label)
        slider_layout.addWidget(self.slider, 5)
        video_button_layout.addWidget(self.speed_slider_label)
        video_button_layout.addWidget(self.speed_slider, 3)

        video_button_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        # Create main layout and add layouts
        self.main_layout = QVBoxLayout()

        self.setLayout(self.main_layout)

        self.main_layout.addLayout(self.vid_layout)
        self.main_layout.addLayout(video_button_layout)
        self.main_layout.addLayout(slider_layout)


        # Set size policy on main widget
        self.setSizePolicy(
            QSizePolicy.MinimumExpanding,
            QSizePolicy.MinimumExpanding
        )

class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.position = QPoint(10, 10)
        self.overlay_image = QImage("Overlay.PNG")
        self.overlay_image = self.overlay_image.scaledToWidth(100)
        self.setFixedSize(self.overlay_image.size())

    # Function to paint the overlay image
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.overlay_image)

    # Function to handle mouse press event
    def mousePressEvent(self, event):
        self.position = event.pos()
        self.update()

    # Function to handle mouse move event
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.position = event.pos()
            self.update()
