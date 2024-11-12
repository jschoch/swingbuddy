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


models = [Swing,Config,Session,LMData]

class TestVideoPlayBack(unittest.TestCase):
    def setUp(self):
        # Set up the database connection
        self.db = SqliteDatabase('swingbuddy_test.db')
        self.db.connect()
        self.db.create_tables(models)  # Replace YourModel with your actual model class

        self.app = QApplication(sys.argv)
        self.ui = QMainWindow()
        self.video_clip = av.open('c:/Files/test_swings/20241111-150119-left.mp4')
        self.video_clip2 = av.open('c:/Files/test_swings/20241111-150119-left.mp4')
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        streamHandler = logging.StreamHandler(sys.stdout)
        stE = logging.StreamHandler(sys.stderr)
        logger.addHandler(streamHandler)
        logger.addHandler(stE)
        logger.info('Hello World!')

        # Initialize VideoPlayBack instance
        self.video_playback_Ui = VideoPlayBackUi()
        self.video_playback = VideoPlayBack(self.video_playback_Ui, None)
        self.video_playback.video_clip = self.video_clip
        self.video_playback.video_clip2 = self.video_clip2

        central_widget = QWidget()
        h = QHBoxLayout()
        lbl = QLabel('Video Playback',self.ui)
        h.addWidget(lbl)
        central_widget.setLayout(h)
        self.ui.setCentralWidget(self.video_playback_Ui)
        self.video_playback.logger = logger
        self.video_playback_Ui.video_label2.setPixmap(QPixmap())
        self.video_playback_Ui.video_label1.setPixmap(QPixmap())
        self.ui.show()
        

    def tearDown(self):
        # Clean up the database and close the connection
        self.db.drop_tables(models)
        self.db.close()
        self.ui.close()
        self.app.quit()

    def test_load_frame(self):
        # Test the load_frame method
        lr = 1# or False, depending on what you want to test
        self.video_playback.load_frame(lr)
        self.video_playback.update_frame(lr)
        self.app.exec()
        #time.sleep(2)


if __name__ == '__main__':
    unittest.main()