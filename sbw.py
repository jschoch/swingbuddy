# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_SBW
#from PySide6 import QtCore
from PySide6.QtCore import QObject, QThread, Signal,  Qt,QPoint, Slot,QTimer,QThreadPool,QRunnable
from PySide6.QtGui import QAction,QIcon,QMovie, QStandardItemModel, QStandardItem,QImage, QPixmap,QPainter,QTransform
from PySide6.QtWidgets import (QMainWindow, QListView, QPushButton, QTextEdit,QSlider,QFileDialog,
    QHBoxLayout, QWidget, QVBoxLayout, QLabel,
    QSizePolicy, QMessageBox,QDialog, QGridLayout, QTextEdit)
from flask import Flask, request,jsonify
import logging
from swingdb import Swing, Session,Config
from peewee import *
from wlog import QtWindowHandler
#from moviepy.video.io.VideoFileClip import VideoFileClip
import av
from util import find_swing, test_fetch_trc, fetch_trc
import pyqtgraph as pg
import numpy as np
import json
import pandas as pd
from io import StringIO,TextIOWrapper
import chardet
import difflib
import time
import traceback
from playhouse.shortcuts import model_to_dict, dict_to_model


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
        app2.run(host='127.0.0.1', port=5004)
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
        self.threadpool = QThreadPool()

        self.video_clip = None
        self.video_playback_Ui = VideoPlayBackUi()
        self.video_playback = None
        #player = VideoPlayBackUi()
        self.ui.horizontalLayout.addWidget(self.video_playback_Ui)

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


        # Connect signals to slots
        self.video_playback_Ui.play_button.clicked.connect(self.play)
        self.video_playback_Ui.pause_button.clicked.connect(self.pause)
        self.play_rev_action.triggered.connect(self.play_reverse)
        self.video_playback_Ui.play_reverse_button.clicked.connect(self.play_reverse)
        self.video_playback_Ui.slider.sliderMoved.connect(self.slider_moved)
        #self.video_playback_Ui.video_label.mousePressEvent = self.overlay_mouse_press
        #self.video_playback_Ui.video_label.mouseMoveEvent = self.overlay_mouse_move
        self.video_playback_Ui.speed_slider.valueChanged.connect(self.set_playback_speed)


        #  Flask stuff

        self.flask_thread = FlaskThread()


        self.find_swings()
        #self.ui.play_btn.clicked.connect(self.foo)
        self.ui.del_swing_btn.clicked.connect(self.del_swing)
        self.ui.create_db_btn.clicked.connect(self.create_db)

        self.flask_thread.start()


        db.connect()
        tables = db.get_tables()
        self.logger.debug(f" tables: {tables}")
        if "swing" in tables:
            self.logger.debug("found swing table")
            #self.foo("swings")
        else:
            None
            #self.foo("no swings")

            #self.foo("made seings")
        print(f"tables: {tables}")
        self.ui.pop_btn.clicked.connect(self.populate_test_data)
        self.ui.sw_btn.clicked.connect(self.start_get_screen)
        self.ui.run_a_btn.clicked.connect(self.start_request_trc)
        self.config = self.create_db()
        self.logger.debug("end of widget init")

        # graph stuff

        #self.plot_graph = pg.PlotWidget()
        #self.ui.gridLayout.addWidget(self.plot_graph)
        #time = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        #temperature = [30, 32, 34, 32, 33, 31, 29, 32, 35, 30]
        #self.plot_graph.plot(time, temperature)
        self.plot = SineWavePlot(self.logger,self)
        self.ui.gridLayout.addWidget(self.plot)

        #self.slider.valueChanged.connect(self.update_vline)
        self.video_playback_Ui.slider.valueChanged.connect(self.plot.update_vline)
        self.loading_widget = LoadingWidget(self.logger)

    def start_request_trc(self):
        w = Worker(self.request_trc)
        self.threadpool.start(w)

    def request_trc(self):

        result = fetch_trc(self.config,self.current_swing,self.logger)
        clean = result.replace('\\r','')

        sio = StringIO(clean)
        df = pd.read_csv(sio)
        self.logger.debug(f"df info: {df.info()}")

        self.current_swing.trc = clean
        #self.logger.debug(repr(clean))
        #self.logger.debug(clean)
        self.current_swing.save()
        self.logger.error("Add teh swing to the list view")
        self.logger.debug(f"columns: {df.head()}")
        self.plot.update_data(df['Speed'].to_list())

    def print_output(self,s):
        self.logger.debug(f"output: {s}")

    def get_screen(self,progress_callback):
        self.logger.debug("in get_screen")
        time.sleep(1)
        return "Done"

    def start_get_screen(self):
        self.logger.debug("Get Screen Clicked")
        w = Worker(self.get_screen)
        w.signals.result.connect(self.print_output)
        self.threadpool.start(w)

    def start_loading(self):
        self.prev_cw = self.centralWidget()
        self.logger.debug("starting loading screen")

        self.setCentralWidget(self.loading_widget)
        self.loading_widget.show()
        # Start background task here (e.g., loading data, processing files)
        # ...

    def del_swing(self):
        self.logger.debug(f" current swing: {model_to_dict(self.current_swing)}")
        self.current_swing.delete_instance()
        self.find_swings()

    def stop_loading(self):
        # When the task is finished:
        self.logger.debug("stop loading screen")
        self.setCentralWidget(self.prev_cw)

    def add_swing_to_model(self,item):
        i = QStandardItem(f"item.name {item.id}")
        i.setData(item.id,Qt.UserRole)
        self.fuckyoumodel.appendRow(i)


    def find_swings(self):
        items = Swing.select().limit(15)
        # Create a model to hold the items
        model = QStandardItemModel()
        self.fuckyoumodel = model

        # Add items to the model

        for item in items:
            self.add_swing_to_model(item)

        # Set the model to the list view

        self.ui.swings_lv.setModel(model)
        self.ui.swings_lv.clicked.connect(self.item_clicked)

    def item_clicked(self, index):

        self.logger.debug(f" row: {index.row()}")
        item = self.fuckyoumodel.itemFromIndex(index)

        item_id = item.data(Qt.UserRole)
        self.logger.debug(f"item {item} id: {item_id}")
        w = Worker(self.load_swing,item_id)
        self.threadpool.start(w)


    def load_swing(self,id):
        swing = Swing.get_by_id(id)
        self.logger.debug(f"swing date: {swing.sdate}")
        right =  swing.rightVid
        left = swing.leftVid

        maybe_trc = swing.trc
        self.logger.debug(f" peewee type: {type(swing.trc)}")
        self.current_swing = swing

        self.open_file(right)
        self.open_file2(left)

        if(maybe_trc != "no trc"):
            self.logger.debug(f"found trc")
        else:
            self.logger.error("no trc data")
            return
        df = pd.read_csv(StringIO(maybe_trc))

        self.logger.debug(f"info: {df.info()}")

        if(df.empty):
            self.logger.debug("EMPTY")
            return

        self.trc_data = df
        self.logger.debug(f"columns: {df.head()}")
        self.plot.update_data(df['Speed_filtered'].to_list())

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
        #self.find_swings()
        return config

    def populate_config(self,config):
        self.ui.vid_dir_le.setText(config.vidDir)
        #self.ui.vid_dir_le.setText("fuck fuck me")

    def populate_test_data(self):
        ##names = "abcdefg".split()
        #names = list("abcdefg")
        #for n in names:
        #    Swing.create(name = n)
        find_swings()

    Slot()
    def unf(self):
        print("unf")

    Slot(str)
    def foo(self,s):
        self.current_swing = Swing.create()

        self.logger.debug(f" s was: {s}")
        if isinstance(s,str):
            self.ui.out_msg.setText(s)
            swings = find_swing("c:/Files/test_swings","mp4")
            self.logger.debug(f"swings found: {swings}")
            self.current_swing.leftVid = swings[0]
            self.current_swing.rightVid = swings[1]
            self.current_swing.save()
            self.add_swing_to_model(self.current_swing)
            w = Worker(self.load_swing,self.current_swing.id)
            self.threadpool.start(w)

        else:
            self.ui.out_msg.setText("you are the worst programmer ever")

            print("shit out of luck")



    # Function to open a video file
    def open_file(self,file_path):
       if file_path == None or file_path == False:
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
       self.logger.debug(f"file path: {file_path}")
       if file_path:
           #self.video_clip = VideoFileClip(file_path)
           #self.video_clip = self.orient_clip(file_path)
           self.video_clip = av.open(file_path)
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

           self.logger.debug("done open file")

    def open_file2(self,file_path):
      if file_path == None or file_path == False:
         file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
      self.logger.debug(f"file path2: {file_path}")
      if file_path:
          self.video_clip2 = av.open(file_path)
          self.video_playback.video_clip2 = self.video_clip2
          self.logger.debug("trying to load the frame2")
          self.video_playback.load_frame(1)
          self.video_playback.update_frame(1)
          self.logger.debug("done loading frame2")

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
        self.logger.debug(f"pos: {position}")
        self.video_playback.current_frame_index = position
        self.video_playback.update_frame(0)
        self.video_playback.update_frame(1)

    def slider_update(self,position):
        self.logger.debug(f"pos: {position}")
        self.video_playback_Ui.slider.setValue(position)

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

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)

class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        #self.kwargs['progress_callback'] = self.signals.progress

    @Slot()  # QtCore.Slot
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class LoadingThread(QThread):
    status_update = Signal(str)

    def __init__(self):
        super().__init__()


    def run(self):
        self.status_update.emit(f"Loading file ...")

class LoadingWidget(QWidget):
    def __init__(self, logger):
        super().__init__()

        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.logger = logger

        # Create loading animation
        self.movie = QMovie("loading.gif")  # Replace with your GIF path
        self.movie_label = QLabel()
        self.movie_label.setMovie(self.movie)
        self.movie.start()
        layout.addWidget(self.movie_label)

        # Create status label
        self.status_label = QLabel("Loading...")
        layout.addWidget(self.status_label)

        # Create loading thread
        self.thread = LoadingThread()
        self.thread.status_update.connect(self.update_status)
        self.thread.start()
        self.logger.debug("LW init done")

    def update_status(self, message):
        self.status_label.setText(message)

class SineWavePlot(QWidget):
    def __init__(self,logger,parent):
        super().__init__()

        # Create a sine wave data
        x = np.arange(241)  # x-axis values from 0 to 240
        y = np.sin(x * 2 * np.pi / 240)  # Adjust frequency for 241 points

        self.y = y
        self.x = x
        self.logger = logger
        self.parent = parent
        logger.debug(f" x was:\n{x}")

        # Create a plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_item = self.plot_widget.plot(x, y, pen='b')

        # Create a vertical line item
        self.vline = pg.InfiniteLine(angle=90, movable=False)
        self.plot_widget.addItem(self.vline)

        # Create a slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 240)
        self.slider.setSingleStep(1)
        self.slider.setValue(120)  # Initial position

        # Connect the slider's valueChanged signal to a slot
        self.slider.valueChanged.connect(self.update_vline)
        self.slabel = QLabel("V:")
        # Create the layout
        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        layout.addWidget(self.slabel)
        layout.addWidget(self.slider)
        self.y_value_label = QLabel()
        layout.addWidget(self.y_value_label)

        self.setLayout(layout)
        self.plot_item.scene().sigMouseMoved.connect(self.mouse_moved)

    def update_vline(self, value):
        # Update the position of the vertical line based on the slider value
        self.slabel.setText(f"v:{value}")
        self.vline.setPos(value)
    def mouse_moved(self, pos):
        #pos = evt[0]  # Get the mouse position

        if self.plot_item.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_item.vb.mapSceneToView(pos)
            x_mouse = mouse_point.x()

            # Find the closest x value in the data
            closest_x_index = np.argmin(np.abs(self.x - x_mouse))
            y_value = self.y[closest_x_index]

            self.y_value_label.setText(f"Y value: {y_value:.2f}")
        else:
            self.y_value_label.setText("")
    def update_data(self, new_y_data):
        self.y = new_y_data
        self.x = list(range(len(new_y_data)))
        self.plot_item.setData(self.x, self.y, pen='b')

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

        video_stream = video_clip.streams.video[0]
        print(f" meta:\n {video_stream.metadata}")

        for frame in video_clip.decode(video=0):
            img = frame.to_image()
            q_image = QImage(img.tobytes(),img.width, img.height,  QImage.Format_RGB888)
            my_transform = QTransform()
            my_transform.rotate(-90)
            q_image = q_image.transformed(my_transform)
            scaled_image = q_image.scaledToHeight(parent_size.height()-100,Qt.SmoothTransformation)


            if(lr):
                self.qimage_frames2.append(scaled_image)
            else:
                self.qimage_frames.append(scaled_image)
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
            #self.current_frame_index += 1
        else:
            self.current_frame_index = 0

        self.video_playback_ui.slider_label.setText(f"Fame: {self.current_frame_index}")
        if(self.video_playback_ui.slider.value() != self.current_frame_index):
            self.logger.debug(f"mis match in values: fi: {self.current_frame_index} v: {self.video_playback_ui.slider.value()}")
        else:
            self.logger.debug("values matched")

    # Function to reverse the frame
    def reverse_frame(self):
        self.current_frame_index -= 1
        self.update_frame(0)
        self.update_frame(1)
        self.current_frame_index -= 1

    def update_all_frames(self):
        self.current_frame_index += 1
        self.update_frame(0)
        self.update_frame(1)

    # Function to toggle play/pause
    def toggle_play_pause(self):
        stream = self.video_clip.streams.video[0]
        fps = int(stream.average_rate)

        if self.is_playing:
            self.timer.stop()
        else:
            self.timer.timeout.connect(self.update_all_frames)
            self.timer.start(1000 / (fps * self.playback_speed))
        self.is_playing = not self.is_playing

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
        self.playback_speed = value / 100.0

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
        self.pause_button = QPushButton("Pause")
        self.play_reverse_button = QPushButton("Play Reverse")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider_label = QLabel("Frame Slider:")
        self.slider.setSingleStep(1)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider_label = QLabel("Playback Speed:")

        # Create layout and add widgets
        video_button_layout = QHBoxLayout()
        video_button_layout.addWidget(self.play_button, 1)
        video_button_layout.addWidget(self.pause_button, 1)
        video_button_layout.addWidget(self.play_reverse_button, 1)
        video_button_layout.addWidget(self.slider_label)
        video_button_layout.addWidget(self.slider, 5)
        video_button_layout.addWidget(self.speed_slider_label)
        video_button_layout.addWidget(self.speed_slider, 3)

        video_button_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        # Create video label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Create video label
        self.video_label2 = QLabel()
        self.video_label2.setAlignment(Qt.AlignmentFlag.AlignRight)
        # Add widgets to layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.vid_layout = QHBoxLayout()
        self.vid_layout1 = QVBoxLayout()
        self.vid_layout2 = QVBoxLayout()
        self.vid1_fname = QLabel("Load a Video")
        self.vid1_fname.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vid2_fname = QLabel("Load another Video")
        self.main_layout.addChildLayout(self.vid_layout)

        self.vid_layout.addChildLayout(self.vid_layout1)
        self.vid_layout1.addWidget(self.vid1_fname, alignment=Qt.AlignLeft)
        self.vid_layout1.addWidget(self.video_label, alignment=Qt.AlignLeft)


        self.vid_layout2.addWidget(self.vid2_fname, alignment=Qt.AlignRight)
        self.vid_layout2.addWidget(self.video_label2, alignment=Qt.AlignRight)
        self.vid_layout.addChildLayout(self.vid_layout2)

        #self.main_layout.addWidget(self.overlay_widget)
        self.main_layout.addLayout(video_button_layout)


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
