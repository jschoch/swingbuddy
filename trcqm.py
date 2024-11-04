# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from PySide6.QtCore import QObject, Signal, QThread,Slot
import pandas as pd
from io import StringIO
#from util import fetch_trc
import requests
from swingdb import Config,Swing
from peewee import *

db = SqliteDatabase('swingbuddy.db')

class TrcQueueWorker(QObject):
    complete = Signal(int)
    progress = Signal(int)
    progress_s = Signal(str)
    complete_trc = Signal(object)

    def __init__(self,logger, tasks=None, parent=None):
        super().__init__(parent)
        self.tasks = tasks if tasks is not None else []
        self.current_task_index = 0
        self.is_running = False
        self.logger = logger

    @Slot(int)
    def add_task(self, task_value):
        self.tasks.append(task_value)
        self.progress.emit(task_value)
        self.logger.debug(f"Added task: {task_value}")

    def run(self):
        while self.is_running :
            if len(self.tasks) > 0:
                task_value = self.tasks.pop()
                s = f"swing TRC: swing id: {task_value} Queue Size: {len(self.tasks)} "
                self.logger.debug(s)
                self.progress_s.emit(s)

                config = Config.get_by_id(1)
                swing = Swing.get_by_id(task_value)
                url = config.poseServer + "?path="+ requests.utils.quote(swing.leftVid)
                self.logger.debug(f" url: {url}")
                response = requests.get(url)
                if response.status_code == 200:
                    #logger.debug(f"woot, got trc\n{response.text} encoding: {response.encoding}")
                    self.logger.debug(f"woot, got trc encoding: {response.encoding}")
                    #return response.text
                else:
                    return "ERROR"
                #clean = result.replace('\\r','')

                sio = StringIO(response.text)
                df = pd.read_csv(sio)

                self.logger.debug(f"df info: {df.info()}")
                #swing.trc = response.text
                #swing.save
                obj = (df,response.text,task_value)
                #self.trc_w.signals.result.emit(obj)
                self.complete_trc.emit(obj)
                self.progress.emit(self.current_task_index)
                self.logger.debug(f"pretending i'm done")
            else:
                self.progress_s.emit("Idle")
                QThread.msleep(200)

        self.logger.debug("TRC worker queue thread exited")

    def stop(self):
        self.is_running = False

