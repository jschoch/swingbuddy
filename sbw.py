# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_SBW
#from PySide6 import QtCore
from PySide6.QtCore import QObject, QThread, Signal,  Qt,QPoint, Slot,QTimer,QThreadPool,QRunnable,QStringListModel
from PySide6.QtGui import QAction,QIcon,QMovie, QStandardItemModel, QStandardItem,QImage, QPixmap,QPainter,QTransform
from PySide6.QtWidgets import (QMainWindow, QListView, QPushButton, QTextEdit,QSlider,QFileDialog,
    QHBoxLayout, QWidget, QVBoxLayout, QLabel,QDialog,QDialogButtonBox,
    QSizePolicy, QMessageBox,QDialog, QGridLayout, QTextEdit)
from flask import Flask, request,jsonify
import logging
from swingdb import Swing, Session,Config
from peewee import *
from wlog import QtWindowHandler
#from moviepy.video.io.VideoFileClip import VideoFileClip
import av
from util import find_swing, test_fetch_trc, fetch_trc,get_pairs
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
import pyautogui
from datetime import datetime
from vplayer import OverlayWidget, VideoPlayBackUi,VideoPlayBack
from cfg import ConfigWindow
from showswing import SwingWidget
import os


app2 = Flask(__name__)

db = SqliteDatabase('swingbuddy.db')

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


        # setup db
        self.create_db()
        self.ui.cw = ConfigWindow()
        self.ui.cw.logger = self.logger
        self.ui.verticalLayout_5.addWidget(self.ui.cw)
        self.config = self.ui.cw.load_config()


        self.ui.sw = SwingWidget()
        self.ui.verticalLayout_6.addWidget(self.ui.sw)
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

        self.timer = QTimer()

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
        self.session = Session(name="Default Session")
        self.session.save()

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

        self.pairs = []

        self.ui.sw_btn.clicked.connect(self.start_get_screen)
        self.ui.run_a_btn.clicked.connect(self.start_request_trc)
        self.ui.add_btn.clicked.connect(self.add_swing_clicked)

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

        # test add image for screenshot
        pixmap_big = QPixmap("c:/Files/test_swings/20241025-140527-left_screen.png")
        self.max_width = 400
        pixmap = pixmap_big.scaled(self.max_width, pixmap_big.height() * (self.max_width / pixmap_big.width()), Qt.KeepAspectRatio)
        self.screenlabel = QLabel()
        self.screenlabel.setPixmap(pixmap)
        self.ui.horizontalLayout.addWidget(self.screenlabel)
        self.ui.stop_btn.clicked.connect(self.take_screen)

        self.ui.pop_btn.clicked.connect(self.populate_test_data)
        self.ui.cw.reload_signal.connect(self.reload_config)

    @Slot()
    def reload_config(self,id):
        self.logger.debug(f"reloading config: id: {id} old config \n{model_to_dict(self.config)}")
        try:
            self.config = Config.get_by_id(1)
        except DoesNotExist:
            print("fuck you peewee")
        self.logger.debug(f"reloading config:  new config \n{model_to_dict(self.config)}")

    @Slot()
    def take_screen(self):
        # Get the current date and time
        now = datetime.now()

        fname = f"{self.config.screenDir}/{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}_screen.png"

        #fname = "c:/Files/test_swings/ss.png"
        ss = pyautogui.screenshot(fname, region=(0,0,300,400))
        self.logger.debug(f"screenshot: {fname}")
        self.current_swing.screen = fname

        self.current_swing.save
        qimage = QImage(ss.tobytes(), ss.width, ss.height, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.screenlabel.setPixmap(pixmap)
        return fname

    def add_swing_clicked(self, s):
        print("click", s)

        dlg = AddDialog(self)
        dlg.sfiles.connect(self.manual_add_swing)
        if dlg.exec():

            print(f"Success! {dlg.files}")
            self.manual_add_swing(dlg.files)
        else:
            print("Cancel!")

    @Slot()
    def manual_add_swing(self,files):
        self.logger.debug(f" got files {files}")
        self.current_swing = Swing.create(session = self.session)
        lv = [file for file in files if 'left.mp4' in file]
        rv = [file for file in files if 'right.mp4' in file]
        screen = [file for file in files if 'screen.png' in file]

        # TODO: unhardcode this
        bd = "c:/Files/test_swings/"
        if len(lv) > 0:
            self.current_swing.leftVid = bd + lv[0]
        else:
            self.logger.error("no right vid found")
        if len(rv) > 0:
            self.current_swing.rightVid = bd + rv[0]
        else:
            self.logger.error("no left vid found")
        if len(screen) > 0:
            self.current_swing.screen = bd + screen[0]
        else:
            self.logger.error(f"no screen found {files}")
        self.current_swing.save()
        self.add_swing_to_model(self.current_swing)
        self.load_swing(self.current_swing.id)

    @Slot()
    def start_request_trc(self):
        if not hasattr(self, 'trc_w') or not self.trc_w.isRunning():
            self.trc_w = Worker(self.request_trc)
            self.trc_w.signals.result.connect(self.trc_result)
            self.trc_w.signals.finished.connect(self.on_request_trc_finished)
            self.threadpool.start(self.trc_w)
        else:
            self.logger.debug("already running trc request")

    def request_trc(self):

        result = fetch_trc(self.config,self.current_swing,self.logger)
        clean = result.replace('\\r','')

        sio = StringIO(clean)
        df = pd.read_csv(sio)

        self.logger.debug(f"df info: {df.info()}")
        obj = (df,clean)
        self.trc_w.signals.result.emit(obj)

    @Slot()
    def on_request_trc_finished(self):
        self.logger.debug("got fnishied, why do i need this?")

    @Slot()
    def trc_result(self,obj):
        if obj == None:
            self.logger.error("trc_result obj was None")
            return
        df,clean = obj

        self.logger.debug(f"got a result: \n{df.head()}")
        self.current_swing.trc = clean
        self.current_swing.save()
        self.plot.update_data(df['Speed'].to_list())

    def print_output(self,s):
        self.logger.debug(f"output: {s}")

    def do_screen_timer(self):
        self.logger.debug(f"starting timer for screenshot {self.config.screen_timeout} seconds")
        self.timer = QTimer()
        #self.timer.timeout.connect(self.dst_done,self.current_swing.id)
        self.timer.timeout.connect(lambda: self.dst_done( self.current_swing.id))
        self.timer.start(self.config.screen_timeout * 1000)

    @Slot()
    def dst_done(self,id):

        #TODO: this screams for some sort of locking
        fname = self.take_screen()
        self.timer.stop()
        self.logger.debug(f"done screen timer: id was {id}")
        swing = Swing.get_by_id(id)
        swing.screen = fname
        swing.save()


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
        b = 0
        if item.screen != "no Screen":
            b = 1
        i = QStandardItem(f"{item.name} {item.id} {item.sdate} {b}")
        i.setData(item.id,Qt.UserRole)
        self.fuckyoumodel.appendRow(i)


    def find_swings(self):
        items = Swing.select().order_by(-Swing.id).limit(30)
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
        self.load_swing(item_id)

    def parse_csv(self,maybe_trc):
        df = pd.read_csv(StringIO(maybe_trc))

        self.logger.debug(f"info: {df.info()}")

        if(df.empty):
            self.logger.debug("EMPTY")
            return

        self.trc_data = df
        self.logger.debug(f"columns: {df.head()}")
        self.plot.update_data(df['Speed_filtered'].to_list())


    def load_swing(self,id):
        swing = Swing.get_by_id(id)
        if self.video_playback != None:
            self.video_playback.stop()
        if swing == None:
            self.logger.error(f"cant' find the swing id {id}")
            return

        # reset stuff
        self.video_clip = None
        self.video_clip2 = None

        self.qimage_frames = []
        self.qimage_frames2 = []
        self.video_playback_Ui.video_label2.setPixmap(QPixmap())
        self.video_playback_Ui.video_label1.setPixmap(QPixmap())
        self.logger.debug(f"swing date: {swing.sdate}")
        self.plot.reset_data()

        # grabbie
        right =  swing.rightVid
        left = swing.leftVid

        maybe_trc = swing.trc

        self.current_swing = swing
        self.ui.sw.set_swing_data(swing)

        self.video_clip = None
        self.video_playback = VideoPlayBack(self.video_playback_Ui, self.video_clip)
        self.video_playback.logger = self.logger
        self.video_playback_Ui.play_button.setEnabled(True)
        self.video_playback_Ui.pause_button.setEnabled(True)
        self.video_playback_Ui.slider.setEnabled(True)
        self.video_playback_Ui.speed_slider.setRange(50, 200)
        self.video_playback_Ui.speed_slider.setValue(100)
        self.video_playback_Ui.speed_slider.setEnabled(True)

        if not hasattr(self, 'of1w') or not self.of1w.isRunning():
            self.of1w = Worker(self.open_file,right)
            self.of1w.signals.result.connect(self.of1wdone)
            self.threadpool.start(self.of1w)
        else:
            self.logger.debug("already loading file 1")

        if not hasattr(self, 'of2w') or not self.of2w.isRunning():
            self.of2w = Worker(self.open_file2,left)
            self.of2w.signals.result.connect(self.of1wdone)
            self.threadpool.start(self.of2w)
        else:
            self.logger.debug("already loading file 2")

        if(self.config.autoplay):
            self.video_playback.start()

        #image_path = f"c:/Files/test_swings/{swing.screen}"  # Replace with the path to your PNG file
        image_path = swing.screen
        if image_path == "no Screen":
            self.logger.debug("no screen")

        else:
            self.logger.debug(f"Screenshot path {image_path}")
            pixmap_big = QPixmap(image_path)
            pixmap = pixmap_big.scaled(self.max_width, pixmap_big.height() * (self.max_width / pixmap_big.width()), Qt.KeepAspectRatio)
            self.screenlabel.setPixmap(pixmap)


        if(maybe_trc != "no trc"):
            self.logger.debug(f"found trc")
        else:
            self.logger.error("no trc data")
            if(self.config.enableTRC):
                self.logger.debug("auto trc, fetching")
                self.start_request_trc()
            return
        w3 = Worker(self.parse_csv,maybe_trc)
        self.threadpool.start(w3)

    def of1wdone(self,result):
        self.logger.debug("of1wdone done {result}")

    def create_db(self):
        db.create_tables([Swing,Config,Session])






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
        self.current_swing = Swing.create(session = self.session)
        self.logger.debug(f" s was: {s}")
        if isinstance(s,str):
            self.ui.out_msg.setText(s)
            swings = find_swing(self.config.vidDir,"mp4")
            self.logger.debug(f"swings found: {swings}")
            self.current_swing.leftVid = swings[0]
            self.current_swing.rightVid = swings[1]
            self.current_swing.save()
            self.add_swing_to_model(self.current_swing)
            self.load_swing(self.current_swing.id)


        else:
            self.ui.out_msg.setText("you are the worst programmer ever")

            print("shit out of luck")
        if(self.config.enableScreen):
            self.do_screen_timer()


    # Function to open a video file
    def open_file(self,file_path):
        #if  os.path.exists(file_path):
        if file_path == None or file_path == False:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        else:
           self.logger.error(f"OF1: can't find file {file_path}")
           #return "this is suck"
        if file_path == "no right vid":
            return "suck"

        self.logger.debug(f"file path: {file_path}")
        if file_path:
           self.video_clip = av.open(file_path)
           self.video_playback.video_clip = self.video_clip
           self.logger.debug("trying to load the frame")
           self.video_playback.load_frame(0)
           self.video_playback.update_frame(0)
           if self.video_playback.qimage_frames == None:
               self.logger.error("no quimageframes in open_file() return")
               return
           self.video_playback_Ui.slider.setRange(0, len(self.video_playback.qimage_frames) )
           self.logger.debug("done loading frame")


    def open_file2(self,file_path):
        if file_path == None or file_path == False:
        #if  os.path.exists(file_path):
             file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        else:
             self.logger.error(f"OF2: can't find file {file_path}")
             #return "this is bad, but no workie"

        if file_path == "no left vid":
            return "suck2"
        self.logger.debug(f"file path2: {file_path}")
        if file_path:
              self.video_clip2 = av.open(file_path)
              self.video_playback.video_clip2 = self.video_clip2
              self.logger.debug("trying to load the frame2")
              self.video_playback.load_frame(1)
              self.video_playback.update_frame(1)
              self.logger.debug("done loading frame2")

    # Function to play the video
    @Slot()
    def play(self):
        self.logger.debug("Like WTF!")
        self.video_playback.toggle_play_pause()

    # Function to pause the video
    @Slot()
    def pause(self):
        self.video_playback.toggle_play_pause()

    # Function to play the video in reverse
    @Slot()
    def play_reverse(self):
        if self.video_clip is None:
            QMessageBox.warning(self, "File not found", "Load the video file first")
            return
        self.video_playback.reverse_play()

    # Function to handle slider movement
    def slider_moved(self, position):
        #self.logger.debug(f"pos: {position}")
        self.video_playback.current_frame_index = position
        self.video_playback.update_frame(0)
        self.video_playback.update_frame(1)

    def slider_update(self,position):
        #self.logger.debug(f"pos: {position}")
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
        self.running = False

        # Add the callback to our kwargs
        #self.kwargs['progress_callback'] = self.signals.progress

    @Slot()  # QtCore.Slot
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            self.running = True
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.running = False
            self.signals.finished.emit()  # Done
    @Slot()
    def isRunning(self):
        return self.running

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
        self.ox = np.arange(241)  # x-axis values from 0 to 240
        self.oy = np.sin(self.ox * 2 * np.pi / 240)  # Adjust frequency for 241 points

        self.y = self.oy
        self.x = self.ox
        self.y1 = self.x
        self.x1 = self.y
        self.logger = logger
        self.parent = parent


        # Create a plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_item = self.plot_widget.plot(self.x, self.y, pen='b')
        #self.plot_item = self.plot_widget.plot(x1, y1, pen='r')
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
    @Slot()
    def reset_data(self):
        self.y = self.oy
        self.x = self.ox
        self.plot_item.setData(self.x, self.y, pen='r')
    @Slot()
    def update_data(self, new_y_data):
        self.y = new_y_data
        self.x = list(range(len(new_y_data)))
        self.plot_item.setData(self.x, self.y, pen='b')


class AddDialog(QDialog):
    sfiles = Signal(list)
    def __init__(self,parent=None):
        super().__init__(parent)

        self.setWindowTitle("Select a swing to add")

        QBtn = (
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.files = []
        #self.sfiles = Signal()
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        message = QLabel("Select the swing to add and click ok")
        layout.addWidget(message)
        layout.addWidget(self.buttonBox)
        # Create the QListView
        self.list_view = QListView()
        layout.addWidget(self.list_view)
        data_dict = get_pairs("c:/Files/test_swings")
        self.data_dict = data_dict
        # Populate the QListView with keys from the dictionary
        key_list = list(sorted(data_dict.keys(),reverse=True))
        self.model = QStringListModel(key_list)
        self.list_view.setModel(self.model)

        # Connect selection changed signal to slot
        self.list_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.setLayout(layout)
        print("AddDialog init done")
    def on_selection_changed(self, selected, deselected):
        for index in selected.indexes():
            key = self.model.data(index)
            print(f"Selected key: {key}, files: {self.data_dict[key]}")
            self.files = self.data_dict[key]
            #self.sfiles.emit(self.files)



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
