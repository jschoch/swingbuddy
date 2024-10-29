# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_SBW
from PySide6 import QtCore
#from PySide6.QtCore import QApplication, QWidget, Qt, Signal
from flask import Flask, request,jsonify
import logging

app2 = Flask(__name__)
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

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

    @app2.route('/bar')
    def ham2():
        #message = request.form['message']
        return "message"

class MyReceiver(QtCore.QObject):
    def receive_signal(self, message):
        self.ui.out_msg.setText(" god damn you ")
        print("Received signal:", message)


class SBW(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_SBW()
        self.ui.setupUi(self)
        # In your main window or other appropriate class:
        self.message_signal = MessageReceivedSignal()
        self.message_signal.messageReceived.connect(self.foo, QtCore.Qt.QueuedConnection)
        self.shared_object = shared_object
        self.shared_object.message_signal.messageReceived.connect(self.foo, QtCore.Qt.QueuedConnection)
        #receiver = MyReceiver()

        self.flask_thread = FlaskThread()
        self.ui.play_btn.clicked.connect(self.foo)

        logger.debug("from qt")
        self.flask_thread.start()

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
    widget = SBW()
    widget.show()
    sys.exit(app.exec())
