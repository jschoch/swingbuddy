

from lib.enums import LoadHint, TrcT
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model

from vplayer import OverlayWidget, VideoPlayBackUi,VideoPlayBack
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap,QStandardItemModel, QStandardItem
import os
from util import find_swing, fetch_trc,get_pairs,load_pipes
import pandas as pd
from swingdb import Swing, Session,Config,LMData
import traceback
from io import StringIO


class SwingLoader():
    def __init__(self,widget):
        self.w = widget
        self.logger = self.w.logger
        self.w.logger.info("SwingLoader initialized")

    def load_swing(self,swing, hint,trcT=None):
        match hint:
            case LoadHint.NEW:
                self.logger.debug("Loading brand new swing")
                self.unload_swing(swing)
                self.check_swing(swing)
                self.start_screen_timer(swing)
                self.add_swing_to_view_model(swing,hint)
                self.w.ws_request_face_trc(swing)
                self.set_current_swing(swing)
                self.load_clips(swing,hint)

            case LoadHint.LOAD:
                self.logger.debug("Loading existing swing")
                self.unload_swing(swing)
                self.check_swing(swing)
                self.set_current_swing(swing)
                self.load_clips(swing,hint)
            case LoadHint.NEW_TRC:
                self.logger.debug("TRC found, reloading frames and plots")
                self.parse_trc(swing,trcT,hint)
                #self.unload_pipes(swing,trcT,hint)
                self.sl_load_pipes(swing,trcT,hint)
                self.w.main_pause_signal.emit()
                self.reload_frames(swing,trcT,hint)
                self.load_plot(swing,trcT,hint)

            case LoadHint.NEW_CLIP:
                self.logger.debug("Loading new clip")
                self.load_frames(swing,trcT,hint)
            case LoadHint.LOAD_CLIP:
                self.logger.debug("Loading existing clip")
                self.load_screen(swing,hint)
                self.parse_trc(swing,trcT,hint)
                self.sl_load_pipes(swing,trcT,hint)
                self.load_frames(swing,trcT,hint)
                self.load_plot(swing,trcT,hint)
            case _:
                self.logger.debug("ERROR unknown hint")
        None

    def start_screen_timer(self,swing):
        if self.w.config.enableScreen:
            self.w.do_screen_timer()

    def unload_swing(self,swing):
        self.logger.debug("maybe Unloading swing")
        if(self.w.current_swing is not None):
            self.logger.debug("found swing, unloading")
            if self.w.video_playback != None and self.w.video_playback.is_playing:
                self.w.main_pause_signal.emit()
                self.logger.debug("resetting swing UI")
                self.w.video_playback_Ui.video_label2.setPixmap(QPixmap())
                self.w.video_playback_Ui.video_label1.setPixmap(QPixmap())
                self.w.plot.reset_data()
                self.w.video_playback.shutdown()
                self.w.video_playback = VideoPlayBack(self.w.video_playback_Ui, self.logger)
                self.w.video_playback.logger = self.logger

                self.w.main_play_signal.connect(self.w.video_playback.play)
                self.w.main_pause_signal.connect(self.w.video_playback.pause)
                self.w.video_playback.dtldf = pd.DataFrame()
                self.w.video_playback.facedf = pd.DataFrame()
            else:
                self.logger.debug("No swing to unload")

    def unload_pipes(self, swing,trcT,hint):
        if trcT == TrcT.DTL:
            self.w.video_playback.dtldf = pd.DataFrame()
        else:
            self.w.video_playback.facedf = pd.DataFrame()
        
    def check_swing(self,swing):
        if not os.path.exists(swing.faceVid):
            self.logger.error(f"no path for {swing.faceVid}")
        elif not os.path.exists(swing.dtlVid):
            self.logger.error(f"no path for {swing.dtlVid}")
        else:
            self.logger.debug("check_swing() both paths exist")


    def set_current_swing(self,swing):
        self.logger.debug("Setting current swing")
        self.w.current_swing = swing

        self.w.ui.sw.set_swing_data(self.w.current_swing)

    def load_clips(self,swing,hint):
        #  load clip 1

        # TODO: spin up workers for this
        self.w.open_file_worker(swing,TrcT.FACE,hint)
        self.w.open_file_worker(swing,TrcT.DTL,hint)
        
        # load clip 2
        self.w.video_playback_Ui.play_button.setEnabled(True)
        self.w.video_playback_Ui.slider.setEnabled(True)
        self.w.video_playback_Ui.speed_slider.setRange(50, 200)
        self.w.video_playback_Ui.speed_slider.setValue(100)
        self.w.video_playback_Ui.speed_slider.setEnabled(True)
    
        
    def load_frames(self,swing,trcT,hint):
        self.logger.debug(f"swingloader load_frames swing {swing.id} hint{hint} trcT{trcT}")
        if(trcT == TrcT.FACE):
            self.w.video_playback.load_frame(0)
            self.logger.debug(f"queued frame loading for FACE swingid {swing.id}")
        elif(trcT == TrcT.DTL):
            self.logger.debug(f"queued frame loading for DTL swingid {swing.id}")
            self.w.video_playback.load_frame(1)
        else:
            self.logger.debug(f"can't load frames for {trcT} swingid {swing.id}")

    def reload_frames(self,swing,trcT,hint):
        self.logger.debug(f"swingloader load_frames swing {swing.id} hint{hint} trcT{trcT}")
        if(trcT == TrcT.FACE):
            self.w.video_playback.load_frame(0,True)
            self.logger.debug(f"queued frame loading for FACE swingid {swing.id}")
        elif(trcT == TrcT.DTL):
            self.logger.debug(f"queued frame loading for DTL swingid {swing.id}")
            self.w.video_playback.load_frame(1,True)
        else:
            self.logger.debug(f"can't load frames for {trcT} swingid {swing.id}")

        
    def parse_ocr(self,swing,ocr_txt):
        None
    
    def load_screen(self,swing,hint):
        image_path = swing.screen
        if image_path == "no Screen":
            self.logger.debug("no screen")

        else:
            self.logger.debug(f"Screenshot path {image_path}")
            if (os.path.exists(image_path)):
                pixmap_big = QPixmap(image_path)
                parent_size = self.w.screenlabel.parent().size()
                pixmap = pixmap_big.scaledToHeight(parent_size.height()-100,Qt.SmoothTransformation)
                self.w.video_playback_Ui.screen_label2.setPixmap(pixmap)
            else:
                self.logger.debug(f"No path for screen {image_path}")
        None
    
    def update_model(self,swing):
        self.logger.debug("updating list view model")
    
    def add_swing_to_view_model(self,swing,hint):
        i = QStandardItem(f"{swing.id} --- {swing.name}")
        i.setData(swing.id,Qt.UserRole)
        self.w.fuckyoumodel.insertRow(0,[i])
        
    def parse_trc(self,swing,trcT,hint):
        try:
            #
            if trcT == TrcT.FACE:
                if swing.faceTrc == Swing.faceTrc.default:
                    self.logger.debug("no face trc data found")
                    return

                self.w.video_playback.facedf = pd.read_csv(StringIO(swing.faceTrc))
                self.logger.debug(f"pd for DTL head {self.w.video_playback.facedf.head()}")
            elif trcT == TrcT.DTL:
                if swing.dtlTrc == Swing.dtlTrc.default:
                    self.logger.debug("no dtl trc data found")
                    return

                self.w.video_playback.dtldf = pd.read_csv(StringIO(swing.dtlTrc))
                self.logger.debug(f"pd for DTL head {self.w.video_playback.dtldf.head()}")
            else:
                self.logger.error(f"Unknown type {trcT}  {hint}")

        except Exception as e:
            self.logger.error(f"Error reading dataframe for swing {swing.id}: {e}")
            tb = traceback.format_exc()
            self.logger.error(tb)

    def sl_load_pipes(self, swing, trcT, hint):
        match hint:
            case LoadHint.NEW_CLIP:
                self.logger.debug(f"load pipes new_clip {swing.id}")
                self.do_load_pipes(swing,trcT,hint)
            case LoadHint.LOAD_CLIP:
                self.logger.debug(f"load pipes load_clip {swing.id}")
                self.do_load_pipes(swing,trcT,hint)
            case LoadHint.NEW_TRC:
                self.logger.debug(f"load pipes new_trc {swing.id}")
                self.do_load_pipes(swing,trcT,hint)
            case _:
                #self.logger.debug(f"load pipes HORROR {model_to_dict(swing)}")
                self.logger.error(f"HORROR {swing.id} {trcT} {hint}")
    
    def do_load_pipes(self,swing,trcT,hint):
        if(trcT == TrcT.FACE):
            if self.w.video_playback.facedf.empty:
                self.logger.error("empty facedf")
                return
            pipes = load_pipes()
            for pipe in pipes:
                pipe.preprocess_df(self.w.video_playback.facedf)
            self.logger.debug(f"load pipes swingid: {swing.id} hint {hint}  trcT {trcT}\n{self.w.video_playback.facedf.head()}")
        if(trcT == TrcT.DTL):
            if self.w.video_playback.dtldf.empty:
                self.logger.error(f"empty DTL DF for swing {swing.id}, hint {hint}  skipping load_pipes\n{self.w.video_playback.dtldf}")
                return
            pipes = load_pipes()
            for pipe in pipes:
                pipe.preprocess_df(self.w.video_playback.dtldf)
            self.logger.debug(f"load pipes swingid: {swing.id} hint {hint}  trcT {trcT}\n{self.w.video_playback.dtldf.head()}")

    def load_plot(self,swing,trcT,hint):
        #TODO: this shoudl be in a subclass of Pipes
        self.w.plot.update_data(self.w.video_playback.facedf)
        
    