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
from flask_socketio import SocketIO, emit, send,join_room
import logging
from swingdb import Swing, Session,Config
from peewee import *
from wlog import QtWindowHandler
#from moviepy.video.io.VideoFileClip import VideoFileClip
import av
from util import find_swing, fetch_trc,get_pairs
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
from qwid import QwStatusWidget
from trcqm import TrcQueueWorker

app2 = Flask(__name__)
socketio = SocketIO(app2, cors_allowed_origins="*")

db = SqliteDatabase('swingbuddy.db')

class MessageReceivedSignal(QObject):
    messageReceived = Signal(str)
    wsSignal = Signal(str)
    msg_to_send = Signal(object)
    doany = Signal()

class SharedObject:
    def __init__(self):
        self.message_signal = MessageReceivedSignal()

shared_object = SharedObject()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  

handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler) 

class FlaskThread(QThread):
    def __init__(self, logger):
        super().__init__()
        #self.logging = logger

    def run(self):
        global shared_object
        socketio.run(app2, host='0.0.0.0', port=5004)
        shared_object.message_signal.messageReceived.emit("i started ok?")
        shared_object.message_signal.msg_to_send.connect(self.on_msg_to_send)
        shared_object.message_signal.doany.connect(self.on_do_any)
        log.debug("Flask Run finished")

    @app2.route('/')
    def index():
        return "Flask App is running"

    @app2.route('/s')
    def handle_message():
        message = request.args.get('message')

        if not message:
            return jsonify({'error': 'Message is required'}), 410

        shared_object.message_signal.messageReceived.emit(message)
        return jsonify({'message': message})
    
    @socketio.on('connect', namespace='/remote')
    def handle_connect(sid):
        log.debug(f"Client connected {sid}")
        join_room(sid,'remote')

    # WebSocket event handler
    @socketio.on('message')
    def handle_client_message(data):
        # Emit the received message back to all clients
        log.debug("Handle Client triggered")
        #emit('message_received', data, broadcast=True)
        #emit('do_ocr',"some/file/path")
        #shared_object.message_signal.wsSignal.emit(data)

    @socketio.on('ocr_data')
    def handle_ocr_data(data):
        log.debug(f"Got the data fool: {data}")
    
    #@Slot()
    #def on_msg_to_send(self,obj):
        #"""
        #why do i need to do this?
        #the signals don't work
        #just call emit directly!?
        #"""
        #(a,b) = obj
        #log.debug("got a signal on_msg_to_send")
        ##socketio.emit(a,b,broadcast=True)
        ##socketio.emit(a, {'data': b}, room='remote')
        #socketio.emit(a,b)
    #@Slot()
    #def on_do_any(self):
        #log.debug("Somethign happend thank god")




class SBW(QMainWindow):
    main_play_signal = Signal()
    main_pause_signal = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_SBW()
        self.ui.setupUi(self)
        self.logger =  logging.getLogger("__main__")
        self.threadpool = QThreadPool()

        #  Flask stuff

        self.flask_thread = FlaskThread(self.logger)
        self.flask_thread.start()
        self.flask_thread.logging = self.logger


        # setup db
        self.create_db()
        self.ui.cw = ConfigWindow()
        self.ui.cw.logger = self.logger
        self.ui.verticalLayout_5.addWidget(self.ui.cw)
        self.config = self.ui.cw.load_config()
        self.current_swing = None

        self.timer = QTimer()

        self.ui.sw = SwingWidget()
        self.ui.verticalLayout_6.addWidget(self.ui.sw)
        self.video_clip = None
        self.video_playback_Ui = VideoPlayBackUi()
        vpbusize_policy = self.video_playback_Ui.sizePolicy()
        vpbusize_policy.setHorizontalPolicy(QSizePolicy.Expanding)
        vpbusize_policy.setVerticalPolicy(QSizePolicy.Expanding)
        self.video_playback_Ui.setSizePolicy(vpbusize_policy)
        self.video_playback = None
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
        self.shared_object = shared_object
        #self.message_signal = MessageReceivedSignal()
        self.shared_object.message_signal.messageReceived.connect(self.foo, Qt.QueuedConnection)
        self.shared_object.message_signal.wsSignal.connect(self.ws_sig,Qt.QueuedConnection)
        
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
        self.play_rev_action.triggered.connect(self.play_reverse)
        self.video_playback_Ui.play_reverse_button.clicked.connect(self.play_reverse)
        self.video_playback_Ui.slider.sliderMoved.connect(self.slider_moved)
        #self.video_playback_Ui.video_label.mousePressEvent = self.overlay_mouse_press
        #self.video_playback_Ui.video_label.mouseMoveEvent = self.overlay_mouse_move
        self.video_playback_Ui.speed_slider.valueChanged.connect(self.set_playback_speed)


        




        self.find_swings()
        self.session = Session(name="Default Session")
        self.session.save()

        self.ui.del_swing_btn.clicked.connect(self.del_swing)

        self.ui.do_ocr_btn.clicked.connect(self.test_ws)
        self.ui.sw_btn.clicked.connect(self.do_screen_timer)




        db.connect()
        tables = db.get_tables()
        self.logger.debug(f" tables: {tables}")
        if "swing" in tables:
            self.logger.debug("found swing table")
        else:
            None

        print(f"tables: {tables}")

        self.pairs = []

        self.ui.run_a_btn.clicked.connect(self.start_request_trc)
        self.ui.add_btn.clicked.connect(self.add_swing_clicked)

        self.logger.debug("end of widget init")

        # graph stuff

        self.plot = SineWavePlot(self.logger,self)
        self.ui.gridLayout.addWidget(self.plot)

        #self.slider.valueChanged.connect(self.update_vline)
        self.video_playback_Ui.slider.valueChanged.connect(self.plot.update_vline)
        self.loading_widget = LoadingWidget(self.logger)

        self.screenlabel = QLabel()
        self.ui.horizontalLayout.addWidget(self.screenlabel)
        self.ui.stop_btn.clicked.connect(self.take_screen)

        self.ui.cw.reload_signal.connect(self.reload_config)


        self.trc_queue_worker = TrcQueueWorker(self.logger,tasks=[])
        self.ui.qs = QwStatusWidget(self.logger, queue_worker=self.trc_queue_worker)
        self.ui.verticalLayout_5.addWidget(self.ui.qs)
        self.trc_thread = QThread()
        self.trc_queue_worker.moveToThread(self.trc_thread)
        self.trc_thread.started.connect(self.trc_queue_worker.run)
        self.trc_queue_worker.complete.connect(self.stop_queue)
        self.trc_queue_worker.progress_s.connect(self.update_status)
        self.trc_queue_worker.complete_trc.connect(self.trc_result)
        self.start_queue()

    # Connect the main window's close event to a method in the debug window
        #self.closeEvent.connect(self.on_main_window_close)

    @Slot()    
    def ws_sig(self,s):
        self.logger.info(f"WebSocket signal received {s}")
    
    def on_main_window_close(self, event):
        self.debug_window.close()
        event.accept()  # Accept the close event
    

    def start_queue(self):

        if not self.trc_queue_worker.is_running:
            self.trc_queue_worker.is_running = True
            self.trc_thread.start()

    def stop_queue(self):
        self.trc_queue_worker.is_running = False

    #@Slot(int)
    #def add_task(self):
    def add_task(self, id):
        """ adds a swing id to the trc queue """
        try:
            self.trc_queue_worker.add_task(id)
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    @Slot(int)
    def update_status(self, progress):
        self.ui.status_label.setText(progress)
    @Slot()
    def reload_config(self,id):
        self.logger.debug(f"reloading config: id: {id} old config \n{model_to_dict(self.config)}")
        try:
            self.config = Config.get_by_id(1)
        except DoesNotExist:
            print("fuck you peewee")
        self.logger.debug(f"reloading config:  new config \n{model_to_dict(self.config)}")
    def convert_screen_string(self,s):
        # Split the input string by commas
        parts = s.split(',')
        
        # Convert each part to an integer
        converted_parts = [int(part) for part in parts]
        
        # Ensure the result is a tuple of four integers
        if len(converted_parts) != 4:
            raise ValueError("Input string must contain exactly four comma-separated values.")
        
        return tuple(converted_parts)

    @Slot()
    def take_screen(self):
      try:
        # Get the current date and time
        now = datetime.now()

        fname = f"{self.config.screenDir}/{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}_screen.png"
        #self.test_ws()

        if self.current_swing is None:
            self.logger.debug("no loaded swing")
            return
        ss = pyautogui.screenshot(fname, region=self.convert_screen_string(self.config.screen_coords))
        self.logger.debug(f"screenshot: {fname}")
        self.current_swing.screen = fname
        try:
            self.logger.debug("saving swing to db")
            #self.current_swing.save

        except Exception as e:
            self.logger.error(f"error saving swing: {e}")
            return
        qimage = QImage(ss.tobytes(), ss.width, ss.height, QImage.Format_RGB888)
        if qimage == None:  
            logger.error("QImage is None")
            return
        parent_size = self.screenlabel.parent().size()
        self.logger.debug(f"parent size: {parent_size} qimage {qimage}")
        scaled_image = qimage.scaledToHeight(parent_size.height()-100,Qt.SmoothTransformation)
        pixmap = QPixmap.fromImage(scaled_image)
        self.logger.debug("setting pixmap label")
        self.screenlabel.setPixmap(pixmap)
        return fname
      except Exception as e:
           self.logger.error(f"HORRROR error taking screenshot: {e}")
           return None

    def add_swing_clicked(self, s):
        print("click", s)

        dlg = AddDialog(self,self.config)
        dlg.sfiles.connect(self.manual_add_swing)
        if dlg.exec():

            print(f"Success! {dlg.files}")
            self.manual_add_swing(dlg.files)
        else:
            print("Cancel!")

    @Slot()
    def manual_add_swing(self,files):
        self.logger.debug(f" got files {files}")
        
        lv = [file for file in files if 'left.mp4' in file]
        rv = [file for file in files if 'right.mp4' in file]
        screen = [file for file in files if 'screen.png' in file]
        try:
            self.current_swing = Swing.create(session = self.session,
                leftVid = lv,
                rightVid = rv,
                screen = screen)
        except Exception as e:
            self.logger.error(f"db excption {e}")
            return

        vid_dir = self.config.vidDir
        if len(lv) > 0:
            self.current_swing.leftVid = vid_dir + "/"+ lv[0]
        else:
            self.logger.error("no right vid found")
        if len(rv) > 0:
            self.current_swing.rightVid = vid_dir + "/"+ rv[0]
        else:
            self.logger.error("no left vid found")
        if len(screen) > 0:
            self.current_swing.screen = self.config.screenDir + "/"+ screen[0]
        else:
            self.logger.error(f"no screen found {files}")
        self.current_swing.save()
        self.add_swing_to_model(self.current_swing)
        self.load_swing(self.current_swing.id)

    @Slot()
    def start_request_trc(self):
        """ 
        should just add to the trc queue
        """
        self.logger.debug("Adding a swing to the queue")
        if self.current_swing != None:
            self.add_task(self.current_swing.id)



    @Slot()
    def trc_result(self,obj):
        if obj == None:
            self.logger.error("trc_result obj was None")
            return
        df,clean,id = obj

        swing = Swing.get_by_id(id)
        swing.trc = clean
        swing.save()

        if(swing.id == self.current_swing.id):
            self.current_swing = swing
            #self.plot.update_data(df['Speed'].to_list())
            self.plot.update_data(df)

    def print_output(self,s):
        self.logger.debug(f"output: {s}")

    def do_screen_timer(self):
        self.logger.debug(f"starting timer for screenshot {self.config.screen_timeout} seconds")
        #self.timer = QTimer()
        print("in do_screen_timer, creating timer")
        self.timer.timeout.connect(lambda: self.dst_done( self.current_swing.id))
        self.timer.start(self.config.screen_timeout * 1000)

    @Slot()
    def dst_done(self,id):

        #TODO: this screams for some sort of locking
        fname = self.take_screen()
        self.logger.debug(f"done screen timer: id was {id}")
        swing = Swing.get_by_id(id)
        swing.screen = fname
        swing.save()
        self.timer.stop()


    #def get_screen(self,progress_callback):
        #self.logger.debug("in get_screen")
        #time.sleep(1)
        #return "Done"

    #def start_get_screen(self):
        #self.logger.debug("Get Screen Clicked")
        #w = Worker(self.get_screen)
        #w.signals.result.connect(self.print_output)
        #self.threadpool.start(w)

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
        #self.fuckyoumodel.appendRow(i)
        self.fuckyoumodel.insertRow(0,[i])


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

    

    def load_swing(self,id):
        swing = Swing.get_by_id(id)
        if self.video_playback != None and self.video_playback.is_playing:
            self.main_pause_signal.emit()
            #self.video_playback.stop()
            #self.video_playback.stop.connect
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

        # this setups the swing data in the tab
        self.ui.sw.set_swing_data(swing)

        self.video_clip = None
        self.video_playback = VideoPlayBack(self.video_playback_Ui, self.video_clip)
        self.main_play_signal.connect(self.video_playback.play)
        self.main_pause_signal.connect(self.video_playback.pause)
        self.video_playback.logger = self.logger
        self.video_playback_Ui.play_button.setEnabled(True)
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

        

        #image_path = f"c:/Files/test_swings/{swing.screen}"  # Replace with the path to your PNG file
        image_path = swing.screen
        if image_path == "no Screen":
            self.logger.debug("no screen")

        else:
            self.logger.debug(f"Screenshot path {image_path}")
            if (os.path.exists(image_path)):
                pixmap_big = QPixmap(image_path)
                parent_size = self.screenlabel.parent().size()
                pixmap = pixmap_big.scaledToHeight(parent_size.height()-100,Qt.SmoothTransformation)
                self.video_playback_Ui.screen_label2.setPixmap(pixmap)
            else:
                self.logger.debug(f"No path for screen {image_path}")


        if(maybe_trc != "no trc" and maybe_trc != None):
            self.logger.debug(f"found trc")
        else:
            self.logger.error("no trc data")
            if(self.config.enableTRC):
                self.logger.debug("auto trc, fetching")
                self.add_task(self.current_swing.id)
            return

        #w3 = Worker(self.parse_csv,maybe_trc)
        #self.threadpool.start(w3)
        #self.parse_csv(self,maybe_trc)
        obj = self.trc_queue_worker.parse_csv(maybe_trc)
        if obj != None:
            (df,hip_df,shoulder_df,maybe_trc) = self.trc_queue_worker.parse_csv(maybe_trc)
            self.plot.update_data(df,hip_df,shoulder_df)
        else:
            self.logger.error("trc data not parsed correctly")

    def of1wdone(self,result):
        self.logger.debug("of1wdone done {result}")

    def test_ws(self):
        self.logger.debug("ocr btn clicked")
        if self.current_swing != None:
            self.logger.debug("swing found")
            if self.current_swing.screen != "no Screen": 
                self.logger.debug(f"sending screen: {self.current_swing.screen}")
                socketio.emit("do_ocr", self.current_swing.screen)
        return

    def create_db(self):
        db.create_tables([Swing,Config,Session])
        try:
            self.config = Config.get_by_id(1)
        except DoesNotExist:
            self.logger.debug("No config found, trying to create one")
            self.config = Config.create()
            self.config.save



    Slot()
    def unf(self):
        print("unf")

    Slot(str)
    def foo(self,s):
        """
        this gets called twice because kinovea does it for each video :(

        you must ignor the errors from the 2nd attempt.
            
        """
        
        self.logger.debug(f"foo() s was: {s}")
        if isinstance(s,str):
            self.ui.out_msg.setText(s)
            swings = find_swing(self.config.vidDir,"mp4")
            self.logger.debug(f"swings found: {swings}")
            try: 
                self.logger.debug("trying to creat th efucking swing")
                self.current_swing = Swing.create(session = self.session,
                    rightVid = swings[0],
                    leftVid = swings[1])
                self.logger.debug("Trying to take the fucking screenshot")

                if(self.config.enableScreen ):
                    self.do_screen_timer()
                else:
                    self.logger.debug(f"enable screen was set to {self.config.enableScreen}")
                self.add_swing_to_model(self.current_swing)
                self.load_swing(self.current_swing.id)
            except Exception as e:
                self.logger.debug(f"couldn't create swing, likely unique fname issue\nKINOVEA calls this twice so should expect failure on every swing {e}")
                return
        else:
            self.logger.debug("foo() s was not a string")

        


    # Function to open a video file
    def open_file(self,file_path):
        #if  os.path.exists(file_path):
        if file_path == None or file_path == False:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        else:
            self.logger.debug("Not using file menu, but maybe problem")

        if not os.path.exists(file_path):
            return "OF1 no file "

        self.logger.debug(f"file path: {file_path}")
        if file_path:
           self.video_clip = av.open(file_path)
           self.video_playback.video_clip = self.video_clip
           self.logger.debug("trying to load the frame")
           self.video_playback.load_frame(0)
           self.video_playback.update_frame(0)
           if self.video_playback.qimage_frames == None or self.video_playback.qimage_frames == []:
               self.logger.error("no quimageframes in open_file() return")
               return
           self.video_playback_Ui.slider.setRange(0, len(self.video_playback.qimage_frames) )
           self.logger.debug("done loading frame")
           if(self.config.autoplay):
                if not self.video_playback.is_playing:
                    self.video_playback.is_playing = True


    def open_file2(self,file_path):
        if file_path == None or file_path == False:
        #if  os.path.exists(file_path):
             file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        else:
             self.logger.error(f"OF2: can't find file {file_path}")
             #return "this is bad, but no workie"
            
        if not os.path.exists(file_path):
            return "OF1 no file "

        self.logger.debug(f"file path2: {file_path}")
        if file_path:
              self.video_clip2 = av.open(file_path)
              self.video_playback.video_clip2 = self.video_clip2
              self.logger.debug("trying to load the frame2")
              self.video_playback.load_frame(1)
              self.video_playback.update_frame(1)
              self.logger.debug("done loading frame2")
              if(self.config.autoplay):
                if not self.video_playback.is_playing:
                    self.video_playback.is_playing = True

    # Function to play the video
    @Slot()
    def play(self):
        self.logger.debug("Like WTF!")
        #self.video_playback.toggle_play_pause()
        self.main_play_signal.emit()


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
        if self.video_playback.is_playing:
            self.main_pause_signal.emit()
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
            #self.quit()
            #self.wait()
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
        self.plot_item = self.plot_widget.plot(self.x, self.y, pen={'color': 'r', 'width': 4})
        self.plot_item2 = self.plot_widget.plot(self.x, self.y, pen={'color': 'g', 'width': 1})
        self.hip_plot_item = self.plot_widget.plot(self.x, self.y, pen={'color': 'g', 'width': 1})
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
        self.plot_item.setData(self.x, self.y, pen={'color': 'r', 'width': 2})
        self.plot_item2.setData(self.x, self.y, pen={'color': 'r', 'width': 2})
    @Slot()
    #def update_data(self, new_y_data):
    def update_data(self,df, df2 = None, df3 = None):
        self.y = df['Speed_filtered'].to_list()
        self.x = list(range(len(self.y)))
        self.plot_item.setData(self.x, self.y, pen={'color': 'cyan', 'width': 4})
        self.y2 = df['Speed'].to_list()
        pen = {'color': 'r', 'width': 1}
        self.plot_item2.setData(self.x,self.y2,pen=pen)

        if df2.empty:
            self.logger.debug("Got some Shoulder data! now you have to update the plot and add the ui stuff to toggle and stuff")
            self.hip_plot_item.setData(self.x, df2['Speed'],pen={'color':'g','width':2})

        #brush = {'color': (0, 255, 255), 'alpha': 0.5}  # Neon green with alpha=0.7
        #brush = {'color':'r','alpha': 0.5}
        #self.plot_item2.setData(self.x, self.y2, pen=pen, brush=brush)
        #self.plot_item2.setData(self.x, self.y2, pen={'color': 'pink', 'width': 2}, brush={'alpha': 0.5})


class AddDialog(QDialog):
    sfiles = Signal(list)
    def __init__(self,parent=None,config=None):
        super().__init__(parent)

        self.setWindowTitle("Select a swing to add")

        QBtn = (
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.files = []
        self.config = config
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
        data_dict = get_pairs(self.config.vidDir)
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
            #print(f"Selected key: {key}, files: {self.data_dict[key]}")
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
