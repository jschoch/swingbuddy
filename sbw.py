# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_SBW
from PySide6 import QtCore
#from PySide6.QtCore import QObject, Signal, QStandardItemModel, QStandardItem
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QListView
from flask import Flask, request,jsonify
import logging
from swingdb import Swing
from peewee import *
from wlog import QtWindowHandler

app2 = Flask(__name__)

db = SqliteDatabase('people.db')

class MessageReceivedSignal(QtCore.QObject):
    messageReceived = QtCore.Signal(str)

class SharedObject:
    def __init__(self):
        self.message_signal = MessageReceivedSignal()

shared_object = SharedObject()

class FlaskThread(QtCore.QThread):

    def run(self):
        global shared_object
        app2.run(host='127.0.0.1', port=5000)
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



class MyReceiver(QtCore.QObject):
    def receive_signal(self, message):
        self.ui.out_msg.setText(" god damn you ")
        print("Received signal:", message)




class SBW(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_SBW()
        self.ui.setupUi(self)


        # Setup share obj for flask messages
        self.message_signal = MessageReceivedSignal()
        self.message_signal.messageReceived.connect(self.foo, QtCore.Qt.QueuedConnection)
        self.shared_object = shared_object
        self.shared_object.message_signal.messageReceived.connect(self.foo, QtCore.Qt.QueuedConnection)


        self.flask_thread = FlaskThread()
        self.logger =  logging.getLogger("__main__")

        self.find_swings()
        self.ui.play_btn.clicked.connect(self.foo)
        self.flask_thread.start()
        db.connect()
        tables = db.get_tables()
        self.logger.debug(f" tables: {tables}")
        if "swing" in tables:
            self.logger.debug("found swing table")
            self.foo("swings")
        else:
            self.foo("no swings")
            db.create_tables([Swing])
            self.foo("made seings")
        print(f"tables: {tables}")
        self.logger.debug("end of widget init")

    def find_swings(self):
        # Create a model to hold the items
        model = QStandardItemModel()

        # Add items to the model
        items = ["Swing 1", "swing 2", "Item 3"]
        for item in items:
            model.appendRow(QStandardItem(item))

        # Set the model to the list view
        self.ui.swings_lv.setModel(model)

    @QtCore.Slot()
    def unf(self):
        print("unf")

    @QtCore.Slot(str)
    def foo(self,s):
        if isinstance(s,str):
            self.ui.out_msg.setText(s)
        else:
            self.ui.out_msg.setText("you are the worst programmer ever")
            print("shit out of luck")

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
