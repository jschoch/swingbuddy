# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_SBW
#from PySide6 import QtCore
from PySide6.QtCore import QObject, QThread, Signal,  Qt,QPoint, Slot,QTimer
from PySide6.QtGui import QAction,QIcon, QStandardItemModel, QStandardItem,QImage, QPixmap,QPainter
from PySide6.QtWidgets import (QMainWindow, QListView, QPushButton, QTextEdit,QSlider,QFileDialog,
    QHBoxLayout, QWidget, QVBoxLayout, QLabel,
    QSizePolicy, QMessageBox,QDialog, QGridLayout, QTextEdit)
from flask import Flask, request,jsonify
import logging
from swingdb import Swing, Session,Config
from peewee import *
from wlog import QtWindowHandler
from moviepy.video.io.VideoFileClip import VideoFileClip


app2 = Flask(__name__)

db = SqliteDatabase('people.db')

class MessageReceivedSignal(QObject):
    messageReceived = Signal(str)

class SharedObject:
    def __init__(self):
        self.message_signal = MessageReceivedSignal()

shared_object = SharedObject()

class FlaskThread(QThread):

    def run(self):
        global shared_object
        app2.run(host='127.0.0.1', port=5000)
        shared_object.message_signal.messageReceived.emit("i started ok?")


    @app2.route('/s')
    def handle_message():
        message = request.args.get('message')

        if not message:
            logging.debug("fuck fuck fuck")
            return jsonify({'error': 'Message is required'}), 410

        shared_object.message_signal.messageReceived.emit(message)
        return jsonify({'message': message})

    @app2.route('/foo')
    def ham():
        shared_object.message_signal.messageReceived.emit("i hate you")
        return "bar"



class MyReceiver(QObject):
    def receive_signal(self, message):
        self.ui.out_msg.setText(" god damn you ")
        print("Received signal:", message)




class SBW(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_SBW()
        self.ui.setupUi(self)
        self.logger =  logging.getLogger("__main__")

        self.video_clip = None
        self.video_playback_Ui = VideoPlayBackUi()
        self.video_playback = None
        #player = VideoPlayBackUi()
        self.ui.verticalLayout_2.addWidget(self.video_playback_Ui)

        # Adding MenuBar with File, Tool, and Help menus
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("&File")
        self.tool_menu = self.menu_bar.addMenu("&Tool")
        self.help_menu = self.menu_bar.addMenu("&Help")

        # Add actions to the File menu
        self.open_action = QAction("&Open", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_file)
        self.file_menu.addAction(self.open_action)

        self.open_action2 = QAction("&Open2", self)
        self.open_action2.setShortcut("Ctrl+O")
        self.open_action2.triggered.connect(self.open_file2)
        self.file_menu.addAction(self.open_action2)

        self.quit_action = QAction("&Quit", self)
        self.quit_action.setShortcut("Ctrl+Q")
        self.quit_action.triggered.connect(self.quit_application)
        self.file_menu.addAction(self.quit_action)

        # Setup share obj for flask messages
        self.message_signal = MessageReceivedSignal()
        self.message_signal.messageReceived.connect(self.foo, Qt.QueuedConnection)
        self.shared_object = shared_object
        self.shared_object.message_signal.messageReceived.connect(self.foo, Qt.QueuedConnection)

        # Add action to the Tool menu
        self.play_rev_action = QAction("&Play Reverse", self)
        self.play_rev_action.setShortcut("Ctrl+R")
        self.tool_menu.addAction(self.play_rev_action)

        # Add action to the Help menu
        self.shortcut_help_action = QAction("&Shortcut Help", self)
        self.shortcut_help_action.triggered.connect(self.show_shortcut_help)
        self.help_menu.addAction(self.shortcut_help_action)

        # Set the central widget to the video playback UI
        #self.setCentralWidget(self.video_playback_Ui)
        #self.setCentralWidget(self.ui.tabWidget_2)
        # Connect signals to slots
        self.video_playback_Ui.play_button.clicked.connect(self.play)
        self.video_playback_Ui.pause_button.clicked.connect(self.pause)
        self.play_rev_action.triggered.connect(self.play_reverse)
        self.video_playback_Ui.play_reverse_button.clicked.connect(self.play_reverse)
        self.video_playback_Ui.slider.sliderMoved.connect(self.slider_moved)
        self.video_playback_Ui.video_label.mousePressEvent = self.overlay_mouse_press
        self.video_playback_Ui.video_label.mouseMoveEvent = self.overlay_mouse_move
        self.video_playback_Ui.speed_slider.valueChanged.connect(self.set_playback_speed)
        self.video_playback_Ui.save_frame_button.clicked.connect(self.save_frame)

        #  Flask stuff

        self.flask_thread = FlaskThread()


        self.find_swings()
        self.ui.play_btn.clicked.connect(self.foo)
        self.ui.create_db_btn.clicked.connect(self.create_db)
        self.ui.pop_btn.clicked.connect(self.populate_test_data)
        self.flask_thread.start()
        db.connect()
        tables = db.get_tables()
        self.logger.debug(f" tables: {tables}")
        if "swing" in tables:
            self.logger.debug("found swing table")
            self.foo("swings")
        else:
            self.foo("no swings")

            self.foo("made seings")
        print(f"tables: {tables}")

        self.logger.debug("end of widget init")

    def find_swings(self):
        items = Swing.select().limit(10)
        # Create a model to hold the items
        model = QStandardItemModel()

        # Add items to the model
        #items = ["Swing 1", "swing 2", "Item 3"]
        for item in items:
            model.appendRow(QStandardItem(item.name))

        # Set the model to the list view
        self.ui.swings_lv.setModel(model)

    def create_db(self):
        db.create_tables([Swing,Config,Session])
        config = "n"
        try:
            #config,created = Config.get_or_create(Config.id = 1)
            config = Config.get_by_id(1)
            self.logger.debug(f" the config was: {config}")
        except DoesNotExist:
            config = Config.create()

        self.populate_config(config)
        find_swings()

    def populate_config(self,config):
        self.ui.vid_dir_le.setText(config.vidDir)
        #self.ui.vid_dir_le.setText("fuck fuck me")

    def populate_test_data(self):
        #names = "abcdefg".split()
        names = list("abcdefg")
        for n in names:
            Swing.create(name = n)
        find_swings()

    Slot()
    def unf(self):
        print("unf")

    Slot(str)
    def foo(self,s):
        if isinstance(s,str):
            self.ui.out_msg.setText(s)
        else:
            self.ui.out_msg.setText("you are the worst programmer ever")
            print("shit out of luck")




    # Function to open a video file
    def open_file(self):
       file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
       self.logger.debug(f"file path: {file_path}")
       if file_path:
           self.video_clip = VideoFileClip(file_path)
           self.video_playback = VideoPlayBack(self.video_playback_Ui, self.video_clip)
           self.video_playback.logger = self.logger
           self.logger.debug("trying to load the frame")
           self.video_playback.load_frame(0)
           self.video_playback.update_frame(0)
           self.logger.debug("done loading frame")
           self.video_playback_Ui.play_button.setEnabled(True)
           self.video_playback_Ui.pause_button.setEnabled(True)
           self.video_playback_Ui.slider.setRange(0, len(self.video_playback.qimage_frames) - 1)
           self.video_playback_Ui.slider.setEnabled(True)
           self.video_playback_Ui.speed_slider.setRange(50, 200)
           self.video_playback_Ui.speed_slider.setValue(100)
           self.video_playback_Ui.speed_slider.setEnabled(True)
           self.video_playback_Ui.save_frame_button.setEnabled(True)
           self.logger.debug("done open file")
    def open_file2(self):
      file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
      self.logger.debug(f"file path2: {file_path}")
      if file_path:
          self.video_clip2 = VideoFileClip(file_path)
          #self.video_playback = VideoPlayBack(self.video_playback_Ui, self.video_clip2,1)
          self.video_playback.video_clip2 = self.video_clip2
          #self.video_playback.logger = self.logger
          self.logger.debug("trying to load the frame2")
          self.video_playback.load_frame(1)
          self.video_playback.update_frame(1)
          self.logger.debug("done loading frame2")
          #self.video_playback_Ui.play_button.setEnabled(True)
          #self.video_playback_Ui.pause_button.setEnabled(True)
          #self.video_playback_Ui.slider.setRange(0, len(self.video_playback.qimage_frames) - 1)
          #self.video_playback_Ui.slider.setEnabled(True)
          #self.video_playback_Ui.speed_slider.setRange(50, 200)
          #self.video_playback_Ui.speed_slider.setValue(100)
          #self.video_playback_Ui.speed_slider.setEnabled(True)
          #self.video_playback_Ui.save_frame_button.setEnabled(True)
          #self.logger.debug("done open file2")
    # Function to play the video
    def play(self):
        self.video_playback.toggle_play_pause()

    # Function to pause the video
    def pause(self):
        self.video_playback.toggle_play_pause()

    # Function to play the video in reverse
    def play_reverse(self):
        if self.video_clip is None:
            QMessageBox.warning(self, "File not found", "Load the video file first")
            return
        self.video_playback.reverse_play()

    # Function to handle slider movement
    def slider_moved(self, position):
        self.video_playback.current_frame_index = position
        self.video_playback.update_frame(0)
        self.video_playback.update_frame(1)

    # Function to handle overlay mouse press event
    def overlay_mouse_press(self, event):
        if event.buttons() == Qt.LeftButton:
            self.video_playback.set_overlay_position(event.pos())

    # Function to handle overlay mouse move event
    def overlay_mouse_move(self, event):
        if event.buttons() == Qt.LeftButton:
            self.video_playback.set_overlay_position(event.pos())

    # Function to quit the application
    def quit_application(self):
        self.close()

    # Function to show shortcut help dialog
    def show_shortcut_help(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Shortcut Help")
        layout = QGridLayout()
        text_edit = QTextEdit()
        text_edit.setPlainText("Shortcuts:\n"
                               "Open: Ctrl + O\n"
                               "Quit: Ctrl + Q\n"
                               "Play Reverse: Ctrl + R")
        layout.addWidget(text_edit)
        dialog.setLayout(layout)
        dialog.exec_()

    # Function to set the playback speed
    def set_playback_speed(self, value):
        self.video_playback.set_playback_speed(value)

    # Function to save the current frame
    def save_frame(self):
        if (hasattr(self, 'video_playback') and self.video_playback is not None and
                self.video_playback.current_frame_index < len(self.video_playback.qimage_frames)):
            frame_index = self.video_playback.current_frame_index
            frame_image = self.video_playback.qimage_frames[frame_index]
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Frame", "", "PNG Files (*.png);;JPEG Files (*.jpg)")
            if file_path:
                frame_image.save(file_path)
        else:
            QMessageBox.warning(self, "Error", "No frame to save.")


# Video playback class responsible for managing the actual playback of the video.
class VideoPlayBack:
    def __init__(self, video_playback_ui, video_clip):
        self.video_playback_ui = video_playback_ui
        self.video_clip = video_clip
        self.video_clip2 = None
        self.qimage_frames = None
        self.qimage_frames2 = None
        self.current_frame_index = 0
        self.is_playing = False
        self.playback_speed = 1.0
        #self.lr = lr
        self.timer = QTimer()

    # Function to load frames from the video clip
    def load_frame(self,lr):

        parent_size = self.video_playback_ui.parent().size()
        video_clip = None
        if(lr):
            self.qimage_frames2 = []
            video_clip = self.video_clip2
        else:
            self.qimage_frames = []
            video_clip = self.video_clip

        if video_clip is None:
            self.logger.debug("class: VideoPlayBack, fun: load_frame: video_clip is Null")
        for frame in video_clip.iter_frames():
            height, width, channels = frame.shape
            bytes_per_line = channels * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            scaled_image = q_image.scaledToHeight(parent_size.height(),Qt.SmoothTransformation)
            if(lr):
                self.qimage_frames2.append(scaled_image)
            else:
                self.qimage_frames.append(scaled_image)
        #self.logger.debug(f"frames found a:{len(self.qimage_frames)} b: {len(self.qimage_frames2)}")
        #return self.qimage_frames
        return

    # Function to update the frame
    def update_frame(self,lr):
        qimage_frames = None
        if(lr):
            qimage_frames = self.qimage_frames2
        else:
            qimage_frames = self.qimage_frames

        if qimage_frames == None:
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
                self.video_playback_ui.video_label.setPixmap(pixmap)
                self.video_playback_ui.video_label.setAlignment(Qt.AlignRight)
            self.video_playback_ui.slider.setValue(self.current_frame_index)
            self.current_frame_index += 1
        else:
            self.current_frame_index = 0
            #self.timer.stop()

    # Function to reverse the frame
    def reverse_frame(self):
        self.current_frame_index -= 1
        self.update_frame(0)
        self.update_frame(1)
        self.current_frame_index -= 1

    def update_all_frames(self):
        self.update_frame(0)
        self.update_frame(1)

    # Function to toggle play/pause
    def toggle_play_pause(self):
        if self.is_playing:
            self.timer.stop()
        else:
            self.timer.timeout.connect(self.update_all_frames)
            self.timer.start(1000 / (self.video_clip.fps * self.playback_speed))
        self.is_playing = not self.is_playing

    # Function to play video in reverse
    def reverse_play(self):
        if self.video_clip is None:
            QMessageBox.warning(self.video_playback_ui, "File not found", "Load the video file first")
            return
        self.timer.timeout.connect(self.reverse_frame)
        self.timer.start(1000 / (self.video_clip.fps * self.playback_speed))

    # Function to set playback speed
    def set_playback_speed(self, value):
        self.playback_speed = value / 100.0

    # Function to set overlay position
    def set_overlay_position(self, position):
        self.video_playback_ui.overlay_widget.position = position
        self.video_playback_ui.overlay_widget.update()

# Video playback UI class responsible for managing the user interface elements related to video playback.
class VideoPlayBackUi(QWidget):
    def __init__(self):
        super().__init__()

        # Create play, pause, slider, speed slider, overlay, and save frame button
        self.play_button = QPushButton("Play")
        self.play_button.setEnabled(False)
        self.pause_button = QPushButton("Pause")
        self.play_reverse_button = QPushButton("Play Reverse")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider_label = QLabel("Frame Slider:")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider_label = QLabel("Playback Speed:")
        self.overlay_widget = OverlayWidget()
        self.save_frame_button = QPushButton("Save Frame")
        self.save_frame_button.setEnabled(False)

        # Create layout and add widgets
        video_button_layout = QHBoxLayout()
        video_button_layout.addWidget(self.play_button, 1)
        video_button_layout.addWidget(self.pause_button, 1)
        video_button_layout.addWidget(self.play_reverse_button, 1)
        video_button_layout.addWidget(self.slider_label)
        video_button_layout.addWidget(self.slider, 5)
        video_button_layout.addWidget(self.speed_slider_label)
        video_button_layout.addWidget(self.speed_slider, 3)
        video_button_layout.addWidget(self.save_frame_button)
        video_button_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        # Create video label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Create video label
        self.video_label2 = QLabel()
        self.video_label2.setAlignment(Qt.AlignmentFlag.AlignRight)
        # Add widgets to layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.video_label)
        main_layout.addWidget(self.video_label2)
        main_layout.addWidget(self.overlay_widget)
        main_layout.addLayout(video_button_layout)
        self.setLayout(main_layout)

        # Set size policy
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    f = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    window_handler = QtWindowHandler()
    window_handler.setFormatter(f)
    logger.addHandler(window_handler)

    logger = logging.getLogger(__name__)
    logger.debug("test debug")
    logger.info("test info")
    logger.warning("test warn")

    widget = SBW()
    widget.show()
    sys.exit(app.exec())
