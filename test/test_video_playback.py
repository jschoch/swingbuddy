# test_video_playback.py

import unittest
from vplayer import OverlayWidget, VideoPlayBackUi,VideoPlayBack
from peewee import SqliteDatabase
from swingdb import Swing, Session,Config,LMData
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout,QMainWindow,QLabel
from PySide6.QtGui import QAction,QIcon,QMovie, QStandardItemModel, QStandardItem,QImage, QPixmap,QPainter,QTransform

import sys
import av
import logging
import time
from io import StringIO
import pandas as pd
from util import load_pipes


models = [Swing,Config,Session,LMData]

class TestVideoPlayBack(unittest.TestCase):
    def setupDb(self):
        self.db = SqliteDatabase('swingbuddy_test.db')
        self.db.connect()
        self.db.create_tables(models)  # Replace YourModel with your actual model class
        self.swing = Swing.get_by_id(2)
        self.logger.debug(f"swn: {self.swing.name}")


    def setupDF(self,maybe_trc):
        df = []
        try:
            df = pd.read_csv(StringIO(maybe_trc))
            pipes = load_pipes()
            for pipe in pipes:
                pipe.preprocess_df(df)
            self.logger.debug(f"df post pipes {df.head()}") 
            return df
        except Exception as e:  
            self.logger.error(f"Error reading trc data: {e}")
            return
        
    def setUp(self):
        # setup logger
        
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        streamHandler = logging.StreamHandler(sys.stdout)
        stE = logging.StreamHandler(sys.stderr)
        self.logger.addHandler(streamHandler)
        self.logger.addHandler(stE)
        self.logger.info('Hello World!')
        
        # Set up the database connection
        self.setupDb() 
        # setup qt app

        self.facedf = self.setupDF(self.swing.faceTrc)
        self.dtldf = self.setupDF(self.swing.dtlTrc)
        self.app = QApplication(sys.argv)
        self.ui = QMainWindow()
        self.video_clip = av.open(self.swing.faceVid)
        self.video_clip2 = av.open(self.swing.dtlVid)
        

        # Initialize VideoPlayBack instance
        self.video_playback_Ui = VideoPlayBackUi()
        self.video_playback = VideoPlayBack(self.video_playback_Ui, None)
        self.video_playback.facedf = self.facedf
        self.video_playback.dtldf = self.dtldf
        

        self.video_playback.video_clip = self.video_clip
        self.video_playback.video_clip2 = self.video_clip2

        central_widget = QWidget()
        h = QHBoxLayout()
        lbl = QLabel('Video Playback',self.ui)
        h.addWidget(lbl)
        central_widget.setLayout(h)
        self.ui.setCentralWidget(self.video_playback_Ui)
        self.video_playback.logger = self.logger
        self.video_playback_Ui.video_label2.setPixmap(QPixmap())
        self.video_playback_Ui.video_label1.setPixmap(QPixmap())
        self.video_playback_Ui.play_button.setEnabled(True)
        self.video_playback_Ui.slider.setEnabled(True)
        self.ui.show()
        

    def tearDown(self):
        # Clean up the database and close the connection
        #self.db.drop_tables(models)
        self.db.close()
        self.ui.close()
        self.app.quit()

    def test_load_frame(self):
        # Test the load_frame method
        lr = 1# or False, depending on what you want to test
        self.video_playback.load_frame(lr)
        self.video_playback.update_frame(lr)
        lr = 0
        self.video_playback.load_frame(lr)
        self.video_playback.update_frame(lr)
        self.app.exec()
        #time.sleep(2)


if __name__ == '__main__':
    unittest.main()