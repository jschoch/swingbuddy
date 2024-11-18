# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget


# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py


from ui_form import Ui_SBW
from PySide6.QtCore import QObject, QThread, Signal,  Qt,QPoint, Slot,QTimer,QThreadPool,QRunnable,QStringListModel,QSettings
from PySide6.QtGui import QAction,QIcon,QMovie, QStandardItemModel, QStandardItem,QImage, QPixmap,QPainter,QTransform
from PySide6.QtWidgets import (QMainWindow, QListView, QPushButton, QTextEdit,QSlider,QFileDialog,
    QHBoxLayout, QWidget, QVBoxLayout, QLabel,QDialog,QDialogButtonBox,QDockWidget,
    QSizePolicy, QMessageBox,QDialog, QGridLayout, QTextEdit,QTabWidget)
from flask import Flask, request,jsonify
from flask_socketio import SocketIO, emit, send,join_room
import logging
from swingdb import Swing, Session,Config,LMData
from peewee import *
from wlog import QtWindowHandler
import av
from util import find_swing, fetch_trc,get_pairs,load_pipes, move_files
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
from dataa import pre_speed, gen_speed
import threading
import signal
from lib.enums import LoadHint, TrcT
from lib.swing_loader import SwingLoader
from lib.wait_connection_dialog import ConnectionDialog

app2 = Flask(__name__)
socketio = SocketIO(app2, cors_allowed_origins="*")

db = SqliteDatabase('swingbuddy.db')

# Get the Peewee logger
plogger = logging.getLogger('peewee')

# Set the logging level to WARNING or higher to suppress debug messages
plogger.setLevel(logging.WARNING)

class MessageReceivedSignal(QObject):
    messageReceived = Signal(str)
    wsSignal = Signal(str)
    msg_to_send = Signal(object)
    doany = Signal()
    serverConnect = Signal()
    serverDisconnect = Signal()
    got_trc_for_swing = Signal(object)

#  this is what flask uses to bridget into the QT app

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
    
    def do_stop(self):
        log.debug("wow, no apparent way to shut this off")
        #self.stop()
        #self.exit()

    @app2.route('/')
    def index():
        return "Flask App is running"

    @app2.route('/s')
    def handle_message():
        """
        This is what responds teh the curl request from kinvovea 

        """
        message = request.args.get('message')

        if not message:
            return jsonify({'error': 'Message is required'}), 410

        shared_object.message_signal.messageReceived.emit(message)
        return jsonify({'message': message})
    
    @socketio.on('connect', namespace='/')
    def handle_connect(sid):
        log.debug(f"Client connected to '/' {sid}")
        #join_room(sid,'remote')
        shared_object.message_signal.serverConnect.emit()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        log.debug(f"Client disconnected {1}")
        shared_object.message_signal.serverDisconnect.emit()

    # WebSocket event handler
    @socketio.on('message')
    def handle_client_message(data):
        # Emit the received message back to all clients
        log.debug("Handle Client triggered")
        #shared_object.message_signal.wsSignal.emit(data)

    @socketio.on('ocr_data')
    def handle_ocr_data(data_txt):
        #log.debug(f"Got the video data fool: {data_txt}")
        data = json.loads(data_txt)
        swing = Swing.get_by_id(data['swingid'])
        maybe_json = data['ocr_data_text']
        
        # get rid of first line and the last line
        lines = maybe_json.splitlines()
        if lines:
            lines.pop(0)
            lines.pop()
        else:
            log.error("No lines found in OCR data")
            return 
        new_maybe_json = '\n'.join(lines)
        unescaped_json_str = new_maybe_json.encode('utf-8').decode('unicode_escape')
        log.info(f"data looks like \n{unescaped_json_str}")
        try:
            maybedata = json.loads(unescaped_json_str)
            log.debug(f"parsed ocr json: {maybedata}")
        except Exception as e:
            log.error(f"Error parsing OCR data: {e} json: \n{unescaped_json_str}")
            return

        try:
            lmdata = LMData.get_by_id(swing.lmdata.id)
            lmdata.raw_txt = unescaped_json_str
            log.info(f"lmdata model: {model_to_dict(lmdata)}")
            lmdata.save()
        except Exception as e:
            log.error(f"Error saving OCR data to LMData: {e}")


    @socketio.on('video_data')
    def handle_video_data(data_txt):
        #log.debug(f"Got the video data fool: {data_txt}")
        data = None
        if(data_txt == "ERROR"):
            log.error("Received error message from TRC processing")
            return
        try:
            data = json.loads(data_txt)
            log.debug(f"Got trc data for swing id: {data['swingid']} type: {data['vtype']}")
        except Exception as e:
            log.error(f"Error parsing json: {e}\n{data_txt[:200]}")
            return

        try: 
            swing = Swing.get_by_id(data['swingid'])
            if(data['vtype'] == "face"):
                log.debug("got vtype face")
                swing.faceTrc = data['trc_txt']
            if(data['vtype'] == "dtl"):
                swing.dtlTrc = data['trc_txt']
                log.debug("got vtype dtl")
            #log.debug(f"got some crap {swing.faceTrc[:100]}")
            swing.save()
            obj = (swing, data['vtype'])
            shared_object.message_signal.got_trc_for_swing.emit(obj)
            
        except Exception as e:
            log.error(f"Error getting swing by id: {e}")

        
    


class SBW(QMainWindow):
    main_play_signal = Signal()
    main_pause_signal = Signal()
    clip_loaded = Signal(object)
    def __init__(self, parent=None, log_window_handler=None):
        super().__init__(parent)
        
        self.logger =  logging.getLogger("__main__")
        # Restore the saved window geometry from a setting
        settings = QSettings("schoch", "swingbuddy")
        if settings.contains("windowPosition"):
            self.logger.debug("Restoring window geometry from settings." )
            self.window().setGeometry(settings.value("windowPosition"))
        self.ui = Ui_SBW()
        self.ui.setupUi(self)
        
        # UI hacking

        self.central_widget = QWidget()
        self.grid_layout = QGridLayout(self.central_widget)
        self.testl = QLabel("TEST123")
        self.grid_layout.addWidget(self.testl, 0, 0)
        self.setCentralWidget(self.central_widget)

        self.tabWidget_main = QTabWidget(self.central_widget)
        self.tab_main_vid = QWidget()
        self.testl2 = QLabel("main tab vid")
        self.tabWidget_main.addTab(self.tab_main_vid, "Video")
        self.tab_main_vid_l = QHBoxLayout()
        self.tab_main_vid.setLayout(self.tab_main_vid_l)
        self.grid_layout.addWidget(self.tabWidget_main, 1, 0)    

        self.tab_main_swing= QWidget()
        self.tab_main_swing_l = QVBoxLayout()
        self.tab_main_swing.setLayout(self.tab_main_swing_l)
        self.tabWidget_main.addTab(self.tab_main_swing, "Swing Data")
        
        self.tab_main_config = QWidget()
        self.tab_main_config_l = QVBoxLayout()
        self.tab_main_config.setLayout(self.tab_main_config_l)
        self.tabWidget_main.addTab(self.tab_main_config, "Config")
        #self.grid_layout.addWidget(self., 0, 0)


        # a list for the swings from the db
        self.dock_swing_list = QDockWidget("Swing List", self)
        self.dock_swing_list.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        self.swings_lv = QListView()
        self.swings_lv.setMinimumWidth(250)
        self.dock_swing_list.setWidget(self.swings_lv)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_swing_list)

        # a list for the lm data from the db
        self.dock_lmdata = QDockWidget("LM Data", self)
        self.dock_lmdata.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        dock_lmdata_text_edit = QTextEdit("lmdata goes here")
        self.dock_lmdata.setWidget(dock_lmdata_text_edit)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_lmdata)

        
        # the dock for plots
        self.dock_plot= QDockWidget("Plots", self)
        self.dock_plot.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        dock_plot_widget = QWidget()
        self.dock_plot_l = QHBoxLayout()
        self.dock_plot.setWidget(dock_plot_widget)
        dock_plot_widget.setLayout(self.dock_plot_l)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_plot)
        
        self.threadpool = QThreadPool()
        if log_window_handler:
            self.log_window_handler = log_window_handler

        #  Flask stuff

        self.flask_thread = FlaskThread(self.logger)
        self.flask_thread.start()
        self.flask_thread.logging = self.logger


        # setup db
        self.create_db()
        self.ui.cw = ConfigWindow()
        self.ui.cw.logger = self.logger

        #  TODO1
        #self.ui.verticalLayout_5.addWidget(self.ui.cw)
        self.tab_main_config_l.addWidget(self.ui.cw)
        self.config = self.ui.cw.load_config()

        

        self.timer = QTimer(self, singleShot=True)

        self.ui.sw = SwingWidget()
        # TODO1
        #self.ui.verticalLayout_6.addWidget(self.ui.sw)
        #self.grid_layout.addWidget(self.ui.sw, 0, 0)
        self.tab_main_swing_l.addWidget(self.ui.sw)
        self.video_playback_Ui = VideoPlayBackUi()
        vpbusize_policy = self.video_playback_Ui.sizePolicy()
        vpbusize_policy.setHorizontalPolicy(QSizePolicy.Expanding)
        vpbusize_policy.setVerticalPolicy(QSizePolicy.Expanding)
        self.video_playback_Ui.setSizePolicy(vpbusize_policy)
        self.video_playback = VideoPlayBack(self.video_playback_Ui, self.logger)
        #TODO1
        #self.ui.horizontalLayout.addWidget(self.video_playback_Ui)
        self.tab_main_vid_l.addWidget(self.video_playback_Ui)

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

        self.clip_loaded.connect(self.post_load_video_clip)

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
        self.shared_object.message_signal.messageReceived.connect(self.http_process_swing, Qt.QueuedConnection)
        self.shared_object.message_signal.wsSignal.connect(self.ws_sig,Qt.QueuedConnection)
        self.shared_object.message_signal.serverConnect.connect(self.server_connect)
        self.shared_object.message_signal.serverDisconnect.connect(self.server_disconnect)
        self.shared_object.message_signal.got_trc_for_swing.connect(self.do_got_trc_for_swing)
        

        # Add action to the Help menu
        self.shortcut_help_action = QAction("&Shortcut Help", self)
        self.shortcut_help_action.triggered.connect(self.show_shortcut_help)
        self.help_menu.addAction(self.shortcut_help_action)


        # Connect signals to slots
        self.video_playback_Ui.play_button.clicked.connect(self.play)
        self.video_playback_Ui.slider.sliderMoved.connect(self.slider_moved)
        #self.video_playback_Ui.video_label.mousePressEvent = self.overlay_mouse_press
        #self.video_playback_Ui.video_label.mouseMoveEvent = self.overlay_mouse_move
        self.video_playback_Ui.speed_slider.valueChanged.connect(self.set_playback_speed)

        self.find_swings()
        self.session = Session(name="Default Session")
        self.session.save()

        self.ctrl_btn_l = QHBoxLayout()
        self.del_swing_btn = QPushButton("Delete Swing")
        self.add_swing_btn = QPushButton("Add Swing")
        self.add_swing_btn.clicked.connect(self.add_swing_clicked)
        #self.
        self.ctrl_btn_l.addWidget(self.del_swing_btn)
        self.ctrl_btn_l.addWidget(self.add_swing_btn)
        self.grid_layout.addLayout(self.ctrl_btn_l, 2, 0, 1, 2)
        self.del_swing_btn.clicked.connect(self.del_swing)
        

        #TODO: consider adding tehse somewhere
        self.ui.do_ocr_btn.setEnabled(False)
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

        self.ui.run_a_btn.clicked.connect(self.ws_request_face_trc)
        self.ui.run_a_btn.setEnabled(False)
        

        self.logger.debug("end of widget init")

        # graph stuff

        self.plot = SineWavePlot(self.logger,self)
        self.dock_plot_l.addWidget(self.plot)
        #TODO1
        #self.ui.gridLayout.addWidget(self.plot)

        #self.slider.valueChanged.connect(self.update_vline)
        self.video_playback_Ui.slider.valueChanged.connect(self.plot.update_vline)

        self.screenlabel = QLabel()
        #TODO1
        self.ui.horizontalLayout.addWidget(self.screenlabel)
        self.tab_main_vid_l.addWidget(self.screenlabel)
        self.ui.stop_btn.clicked.connect(self.take_screen)

        self.ui.cw.reload_signal.connect(self.reload_config)
        self.av_options = {
            'threads': 'auto',
            #'buffer_size': 10 * 1024 * 1024,  # Adjust the buffer size as needed
        }

        self.current_swing = None
        self.swingloader = SwingLoader(self)
        self.cd = None

    def load_last_swing(self):
        try:
            lastswing = Swing.select().order_by(Swing.id.desc()).get()
            #self.load_swing(lastswing.id)
            self.swingloader.load_swing(lastswing,LoadHint.LOAD)
            self.logger.debug(f"Load Swing id: {lastswing.id}, waiting for threads.  SBW init should be done")
        except Exception as e:
            self.logger.error(f"No Swing found to load default on init ya {e}")
            tb = traceback.format_exc()
            self.logger.error(tb)

    def show_connection_dialog(self):
        self.cd = ConnectionDialog(self)
        self.cd.show()
    # Connect the main window's close event to a method in the debug window
    #self.closeEvent.connect(self.on_main_window_close)
    def closeEvent(self, event):
        # Perform actions before closing the window
        print("Window is closing...")
        # Save the current window geometry to a setting
        settings = QSettings("schoch", "swingbuddy")
        settings.setValue("windowPosition", self.window().geometry())
        db.close()
        self.shutdown_logger()
        event.accept()

    @Slot()
    def shutdown_logger(self):
        logger = logging.getLogger(__name__)
        if self.log_window_handler in logger.handlers:
            logger.removeHandler(self.log_window_handler)
        self.logger.debug("closing flask maybe")
        self.flask_thread.quit()
        self.logger.debug("calling close_handler")
        self.log_window_handler.close_handler()

    @Slot()
    def do_got_trc_for_swing(self,obj):
        (swing,vtype) = obj
        self.logger.debug(f"do_got_trc_for_swing Loading TRC {vtype}")
        if vtype == 'face':
            self.logger.debug("do_got_trc_foor_swing Face TRC, loading data and requesting DTL trc")
            self.swingloader.load_swing(swing,LoadHint.NEW_TRC,TrcT.FACE)
            self.logger.debug("getting dtl TRC")
            request_data = {
                'file_path' : swing.dtlVid,
                'vtype': 'dtl',
                'swingid' : swing.id
            }
            request_txt = json.dumps(request_data)
            socketio.emit('do_vid',request_txt) 
        else:
            self.logger.debug("do_got_trc_foor_swing DTL TRC, loading data")
            self.swingloader.load_swing(swing,LoadHint.NEW_TRC,TrcT.DTL)
        self.ui.sw.set_swing_data(swing)

    
    @Slot()
    def server_connect(self):
        self.cd.got_connection()
        self.load_last_swing()
        self.ui.run_a_btn.setEnabled(True)
        self.ui.do_ocr_btn.setEnabled(True)
        #self.ui.w
    @Slot()
    def server_disconnect(self):
        self.ui.run_a_btn.setEnabled(False)
        self.ui.do_ocr_btn.setEnabled(False)

    @Slot()    
    def ws_sig(self,s):
        self.logger.info(f"WebSocket signal received {s}")
    
    def on_main_window_close(self, event):
        self.debug_window.close()
        event.accept()  # Accept the close event
    


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
        # TODO: this file prefix should match the swing

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
        self.add_and_load_swing(files)
        

    @Slot()
    def ws_request_face_trc(self,swing):
        """
        sends to server, should see a signal called got_trc_for_swing, connected to do_got_trc_for_swing
        """
        request_data = {
            'file_path' : swing.faceVid,
            'vtype': 'face',
            'swingid' : swing.id
        }
        request_txt = json.dumps(request_data)
        self.logger.debug(f"ws_request_face_trc: request {request_data}")
        socketio.emit('do_vid',request_txt)


    def print_output(self,s):
        self.logger.debug(f"output: {s}")

    def do_screen_timer(self):
        self.logger.debug(f"starting timer for screenshot {self.config.screen_timeout} seconds")
        #self.timer = QTimer()
        print("in do_screen_timer, creating timer")
        if not self.timer.isActive():
            #self.timer.disconnect(self.)
            self.timer.timeout.disconnect(self.dst_done)
            self.timer.timeout.connect(self.dst_done)
            self.timer.start(self.config.screen_timeout * 1000)
        else:
            self.logger.debug("timer already active")

    @Slot()
    def dst_done(self):

        #TODO: this screams for some sort of locking
        fname = self.take_screen()
        self.logger.debug(f"done screen timer: id was {id}")
        #swing = Swing.get_by_id(id)
        self.current_swing.screen = fname
        self.current_swing.save()
        self.timer.stop()
        self.timer.timeout.disconnect(self.dst_done)
        pixmap_big = QPixmap(fname)
        parent_size = self.screenlabel.parent().size()
        pixmap = pixmap_big.scaledToHeight(parent_size.height()-100,Qt.SmoothTransformation)
        self.video_playback_Ui.screen_label2.setPixmap(pixmap)
        if self.config.enableOcr:
           self.test_ws() 


    def start_loading(self):
        self.prev_cw = self.centralWidget()
        self.logger.debug("starting loading screen")

        self.setCentralWidget(self.loading_widget)
        self.loading_widget.show()
        # Start background task here (e.g., loading data, processing files)
        # ...

    def del_swing(self):
        self.logger.debug(f"DELETE current swing: {self.current_swing.id}")
        #TODO delete from the list
        # do you need to unloadswing?
        self.current_swing.delete_instance()
        self.current_swing = None
        self.load_last_swing()
        self.find_swings()

    def stop_loading(self):
        # When the task is finished:
        self.logger.debug("stop loading screen")
        self.setCentralWidget(self.prev_cw)

    def add_swing_to_model(self,item):
        i = QStandardItem(f"{item.id} --- {item.name}")
        i.setData(item.id,Qt.UserRole)
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

        self.swings_lv.setModel(model)
        self.swings_lv.clicked.connect(self.item_clicked)

    def item_clicked(self, index):

        self.logger.debug(f" row: {index.row()}")
        item = self.fuckyoumodel.itemFromIndex(index)

        item_id = item.data(Qt.UserRole)
        self.logger.debug(f"item {item} id: {item_id}")
        swing = Swing.get_by_id(item_id)
        self.swingloader.load_swing(swing,LoadHint.LOAD)

    def unload_swing_video(self):
        if self.video_playback != None and self.video_playback.is_playing:
            self.main_pause_signal.emit()
        self.logger.debug("resetting swing UI")
        self.video_playback_Ui.video_label2.setPixmap(QPixmap())
        self.video_playback_Ui.video_label1.setPixmap(QPixmap())
        self.plot.reset_data()
        self.video_playback = VideoPlayBack(self.video_playback_Ui, None)
        self.main_play_signal.connect(self.video_playback.play)
        self.main_pause_signal.connect(self.video_playback.pause)
        self.video_playback.logger = self.logger
        self.video_playback_Ui.play_button.setEnabled(True)
        self.video_playback_Ui.slider.setEnabled(True)
        self.video_playback_Ui.speed_slider.setRange(50, 200)
        self.video_playback_Ui.speed_slider.setValue(100)
        self.video_playback_Ui.speed_slider.setEnabled(True)

    def load_swing_videos(self,swing):
        self.logger.debug(f"loading videos for {swing}")
        self.unload_swing_video()
        

        if not hasattr(self, 'of1w') or not self.of1w.isRunning():
            self.of1w = Worker(self.open_file,swing.faceVid)
            self.of1w.signals.result.connect(self.of1wdone)
            self.threadpool.start(self.of1w)
            self.logger.debug("starting of1w")
            #QThreadPool.globalInstance().start(self.of1w)
        else:
            self.logger.debug("already loading file 1")

        if not hasattr(self, 'of2w') or not self.of2w.isRunning():
            self.of2w = Worker(self.open_file2,self.swing.dtlVid)
            self.of2w.signals.result.connect(self.of1wdone)
            self.logger.debug("starting of2w")
            #QThreadPool.globalInstance().start(self.of2w)
            self.threadpool.start(self.of2w)
            None
        else:
            self.logger.debug("already loading file 2") 
        self.logger.debug("Done loading video load_swing_video()")


    def of1wdone(self,result):
        self.logger.debug(f"of1wdone done {result}")

    def test_ws(self):
        self.logger.debug("ocr btn clicked")
        if self.current_swing != None:
            self.logger.debug("swing found")
            if self.current_swing.screen != "no Screen": 
                self.logger.debug(f"sending screen: {self.current_swing.screen}")
                request_data = {'file_path':self.current_swing.screen,'swingid':self.current_swing.id}
                request_text = json.dumps(request_data)
                socketio.emit("do_ocr", request_text)
            else:
                self.logger.debug("test_ws no screen found")
        return

    def create_db(self):
        db.create_tables([Swing,Config,Session,LMData])
        try:
            self.config = Config.get_by_id(1)
        except DoesNotExist:
            self.logger.debug("No config found, trying to create one")
            self.config = Config.create()
            self.config.save()



    Slot()
    def unf(self):
        print("unf")

    Slot(str)
    def http_process_swing(self,s):
        """
        this gets called twice because kinovea does it for each video :(

        you must ignor the errors from the 2nd attempt.
            
        """
        
        self.logger.debug(f"http_process_swing() s was: {s}")
        if isinstance(s,str):
            #swings = find_swing(self.config.kinoveaDir,"mp4")
            swings = find_swing(self.config.vidDir,"mp4")
            #TODO get swing move working
            #kva = find_swing(self.config.kinoveaDir,"kva")  
            #swings_kva = swings + kva
            #self.logger.debug(f"found {swings_kva} swings")
            #new_folder = move_files(swings_kva)
            #self.logger.debug(f"new folder: {new_folder}")
            self.add_and_load_swing(swings)
        else:
            self.logger.debug("http_process_swing() s was not a string")
            
    def add_and_load_swing(self,files, maybeScreen=False,autoTrc=False, autoScreen=False):
        dtlVid = [file for file in files if 'left.mp4' in file]
        faceVid = [file for file in files if 'right.mp4' in file]
        screen = [file for file in files if 'screen.png' in file]
        swing = None

        if len(dtlVid) > 0:
            dtlVid = dtlVid[0]
        else:
            self.logger.error("no face on vid found")
            dtlVid = Swing.dtlVid.default
        if len(faceVid) > 0:
            faceVid = faceVid[0]
        else:
            self.logger.error("no down the line vid found")
            faceVid = Swing.faceVid.default
        if len(screen) > 0:
            screen = screen[0]
        else:
            self.logger.debug(f"no screen found {files}")
            screen = Swing.screen.default
        try:
            lmdata = LMData.create()
            parts = faceVid.split('-')[:2]
            sname = "-".join(parts)
            swing = Swing.create(session = self.session,
                name = sname,
                dtlVid = dtlVid,
                lmdata= lmdata,
                faceVid = faceVid,
                screen = screen)
        except Exception as e:
            self.logger.error(f"add_and_load_swing()  db excption {e}")
            if swing is not None:
                self.logger.error(f"swing {model_to_dict(swing)}")
            return
        self.swingloader.load_swing(swing,LoadHint.NEW)



    # Function to open a video file
    def open_file(self,file_path):
        if file_path is None or file_path == False:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")

        if not os.path.exists(file_path):
            return "OF1 no file "

        #self.logger.debug(f" file path: {file_path}")
        self.logger.debug(f"Starting AV load 1 of {file_path}")
        
        start = time.time()
        clip = av.open(file_path,mode='r',options=self.av_options)
        end = time.time()
        self.logger.debug(f"AV load 1 took {end-start} seconds")
        obj = (clip,1)
        self.clip_loaded.emit(obj)
        #self.of1w.signals.result.emit("done of1")
        


    def open_file2(self,file_path):
        if file_path is None or file_path == False:
             file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
            
        if not os.path.exists(file_path):
            return "OF1 no file "

        #self.logger.debug(f"file path2: {file_path}")
        self.logger.debug(f"Starting AV load 2 of {file_path}")
        start = time.time()
        clip = av.open(file_path,mode='r',options=self.av_options)
        end = time.time()
        self.logger.debug(f"AV load 2 took {end-start} seconds")
        obj = (clip,2)
        self.clip_loaded.emit(obj)
        #self.of1w.signals.result.emit("done of2")

    def do_open_file(self,swing,fpath,trcT,hint):
        if not os.path.exists(fpath):
            return "can't find FACE video file"
        start = time.time()
        clip = av.open(fpath,mode='r',options=self.av_options)
        end = time.time()
        self.logger.debug(f"AV load took {end-start} seconds")
        obj = (clip,swing,trcT,hint)
        self.clip_loaded.emit(obj)
    
    def open_file_worker(self,swing,trcT,hint):
        match trcT:
            case TrcT.FACE:
                #TODO:  make the threads again
                self.do_open_file(swing,swing.faceVid,trcT,hint)        
            case TrcT.DTL:
                self.do_open_file(swing,swing.dtlVid,trcT,hint)
        

    @Slot()
    def post_load_video_clip(self, obj):
        """
        this is connected via self.clip_loaded.emit(obj) 
        """
        (clip,swing,trcT,hint) = obj
        if clip is None:
            self.logger.error(f"No clip {swing.id} {trcT}")
            return
        self.logger.debug(f"load_video: {clip} type: {trcT} id: {swing.id} adding clips")
        if(trcT == TrcT.FACE):
            if self.video_playback.face_video_clip is not None:
                #self.video_playback.video_clip.close()
                None
            self.video_playback.face_video_clip = clip
        if(trcT == TrcT.DTL):
            #TODO:  rename these videoclips!!!
            if self.video_playback.dtl_video_clip is not None:
                #self.video_playback.video_clip2.close()
                None
            self.video_playback.dtl_video_clip = clip

        if hint == LoadHint.LOAD:
            self.swingloader.load_swing(swing,LoadHint.LOAD_CLIP,trcT)
        if hint == LoadHint.NEW:
            self.swingloader.load_swing(swing,LoadHint.NEW_CLIP,trcT)
        return
       
    # Function to play the video
    @Slot()
    def play(self):
        self.main_play_signal.emit()


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
                               )
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
        #else:
            #self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.running = False
            self.signals.finished.emit()  # Done
            #self.quit()
            #self.wait()
    @Slot()
    def isRunning(self):
        return self.running


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
        self.plot_widget.setMaximumHeight(300)
        self.plot_item = self.plot_widget.plot(self.x, self.y, pen={'color': 'r', 'width': 4})
        self.plot_item2 = self.plot_widget.plot(self.x, self.y, pen={'color': 'g', 'width': 1})
        #self.hip_plot_item = self.plot_widget.plot(self.x, self.y, pen={'color': 'g', 'width': 1})
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
        #self.plot_item.scene().sigMouseMoved.connect(self.mouse_moved)

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
        slen = len(self.oy)
        self.x = list(range(slen))
        self.slider.setRange(0, slen)

        #self.plot_item.setXRange(0, slen, padding=0)
        #self.plot_item2.setXRange(0, slen, padding=0)

        self.plot_item.setData(self.x, self.y, pen={'color': 'r', 'width': 2})
        self.plot_item2.setData(self.x, self.y, pen={'color': 'r', 'width': 2})
    @Slot()
    #def update_data(self, new_y_data):
    def update_data(self,df, df2 = None, df3 = None):
        if 'LWrist_Speed_filtered' in df.columns:
            self.y = df['LWrist_Speed_filtered'].to_list()
            slen = len(self.y)
            self.x = list(range(slen))
            
            self.y2 = df['LWrist_Speed'].to_list()
            pen = {'color': 'r', 'width': 1}
            self.slider.setRange(0, slen)
            
            

            self.plot_item.setData(self.x, self.y, pen={'color': 'cyan', 'width': 4})
            self.plot_item2.setData(self.x,self.y2,pen=pen)

            #self.plot_item.setXRange(0, slen, padding=0)
            #self.plot_item2.setXRange(0, slen, padding=0)
            self.plot_item.getViewBox().setXRange(0, slen)
            self.plot_item2.getViewBox().setXRange(0,slen)
        else:
            self.logger.error("update_data df not found for swing {swing.id}")

        # TODO: implement as a pipe
        #if df2 is not None and not df2.empty:
            #self.logger.debug("Got some Shoulder data! now you have to update the plot and add the ui stuff to toggle and stuff")
            #self.hip_plot_item.setData(self.x, df2['Speed'],pen={'color':'g','width':2})

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
            print(f"Selected key: {key}, files: {self.data_dict[key]}")
            self.files = self.data_dict[key]
            full_path_files = []
            for file in self.files:
                full_path_files.append(self.config.vidDir + "/" + file)
            self.files = full_path_files
                



if __name__ == "__main__":
    app = QApplication(sys.argv)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    f = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    log_window_handler = QtWindowHandler()
    log_window_handler.setFormatter(f)
    logger.addHandler(log_window_handler)
    #logger = logging.getLogger(__name__)
    #widget = SBW()
    widget = SBW(parent=None, log_window_handler=log_window_handler)
    #time.sleep(1)
    widget.show()
    #widget.show_connection_dialog(widget)
    cd = ConnectionDialog(widget)
    widget.cd = cd
    cd.show()
    sys.exit(app.exec())
