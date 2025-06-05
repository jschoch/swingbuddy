# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from trcqm import TrcQueueWorker

class QwStatusWidget(QWidget):
    def __init__(self,logger, queue_worker=None, parent=None):
        super().__init__(parent)
        self.queue_worker = queue_worker if queue_worker is not None else TrcQueueWorker()
        self.initUI()
        self.logger = logger

        self.queue_worker.progress_s.connect(self.update_status)

    def initUI(self):
        self.layout = QVBoxLayout()

        self.status_label = QLabel("Queue Status: Idle", self)
        self.layout.addWidget(self.status_label)

        self.setLayout(self.layout)
        self.setWindowTitle('Status Widget')

    def update_status(self, progress):
        self.status_label.setText(progress)
