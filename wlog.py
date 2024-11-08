# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
import logging
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QWidget, QTextEdit, QPushButton, QVBoxLayout
from PySide6.QtGui import QTextCursor


class QtWindowHandler(logging.Handler):

    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.window = Window()
        self.window.show()

    def emit(self, record):
        self.window.textEdit.append(self.format(record))
        self.window.textEdit.moveCursor(QTextCursor.End)


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        # set the title
        self.setWindowTitle("Debugger")

        # setting  the geometry of window
        self.setGeometry(0, 0, 1500, 500)

        # Layout
        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)
        self.btn_debbugger = QPushButton('Start Debugger')
        self.btn_clean_debbugger = QPushButton('Clean Debugger')
        self.lbl_debugger = QTextEdit('Debbuger')

        self.vertLayout = QVBoxLayout()
        self.vertLayout .addWidget(self.textEdit)
        self.vertLayout .addWidget(self.btn_debbugger)
        self.vertLayout .addWidget(self.btn_clean_debbugger)
        self.setLayout(self.vertLayout )

        # Connect button
        self.btn_debbugger.clicked.connect(self.initialize_thread_1)
        self.btn_clean_debbugger.clicked.connect(self.CleanUi)



    def initialize_thread_1(self):
        logger.info("Starting Debugger ...")


    def CleanUi(self):
        self.textEdit.clear()

    def closeEvent(self, event):
        # Optionally you can add some confirmation logic here
        # For example:
        # reply = QMessageBox.question(self, 'Message', "Are you sure to quit?",
        #                              QMessageBox.Yes | QMessageBox.No,
        #                              QMessageBox.No)
        # if reply == QMessageBox.Yes:
        self.quit_application()
        event.accept()

    def quit_application(self):
        self.close()
