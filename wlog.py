# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
import logging
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QWidget, QTextEdit, QPushButton, QVBoxLayout
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import QSettings,QObject, Signal, Slot, QThread

# ---
# Custom Signal Emitter for cross-thread logging
# ---
class LogEmitter(QObject):
    """
    A QObject that emits a signal with log messages.
    This is used to safely pass messages from any thread to the GUI thread.
    """
    message_logged = Signal(str)

# ---
# Logging Handler that emits signals
# ---
class QtWindowHandler(logging.Handler):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        # Create an instance of our LogEmitter.
        # This emitter doesn't have to live in the GUI thread directly,
        # but its signal will be connected to a slot that does.
        self.log_emitter = LogEmitter()
        self.window = Window()
        self.window.show()

        # Connect the emitter's signal to the textEdit's append slot.
        # Qt's signal-slot mechanism automatically handles the thread marshalling,
        # ensuring append is called on the GUI thread.
        self.log_emitter.message_logged.connect(self.window.textEdit.append)
        # Also connect to move cursor to end, as append doesn't auto-scroll often
        self.log_emitter.message_logged.connect(lambda: self.window.textEdit.moveCursor(QTextCursor.End))


    def emit(self, record):
        """
        This method is called by the logging system.
        It might be called from any thread.
        """
        msg = self.format(record)
        # Instead of directly appending, emit a signal with the formatted message.
        # The connection ensures this signal is handled on the main GUI thread.
        self.log_emitter.message_logged.emit(msg)

    def close_handler(self):
        """
        Safely removes the handler and closes the window, saving its position.
        """
        # It's good practice to ensure this is also called on the main thread
        # if there's any chance a background thread might trigger it.
        # For a simple close, it's often fine as it's typically user-initiated.
        if self in logging.getLogger(__name__).handlers:
            logging.getLogger(__name__).removeHandler(self)

        # Save the current window geometry to a setting
        settings = QSettings("schoch", "swingbuddy_debug")
        # Ensure geometry() is called on the GUI thread, which it will be if close_handler
        # is triggered by a GUI event (like the close button).
        settings.setValue("windowPosition", self.window.geometry())

        print("Closing handler")
        self.window.close()



# ---
# The GUI Window
# ---
class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        # set the title
        self.setWindowTitle("Debugger")

        # Layout and Widgets
        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)
        self.btn_debbugger = QPushButton('Start Debugger')
        self.btn_clean_debbugger = QPushButton('Clean Debugger')
        # This lbl_debugger is a QTextEdit, but it's likely meant to be a QLabel
        # based on its name. I've left it as QTextEdit as per your code.
        self.lbl_debugger = QTextEdit('Debbuger') # Consider changing to QLabel if it's just a label

        self.vertLayout = QVBoxLayout()
        self.vertLayout.addWidget(self.textEdit)
        self.vertLayout.addWidget(self.btn_debbugger)
        self.vertLayout.addWidget(self.btn_clean_debbugger)
        # If lbl_debugger is meant to be a label *for* the debugger, you might
        # place it differently or remove it if not needed as a separate widget.
        # self.vertLayout.addWidget(self.lbl_debugger) # Uncomment if you want to add this widget
        self.setLayout(self.vertLayout)

        # Connect buttons
        self.btn_debbugger.clicked.connect(self.initialize_thread_1)
        self.btn_clean_debbugger.clicked.connect(self.CleanUi)

        # Restoring window geometry
        settings = QSettings("schoch", "swingbuddy_debug")
        if settings.contains("windowPosition"):
            setting = settings.value("windowPosition")
            # QWidget.setGeometry accepts QRect directly
            self.setGeometry(setting)
            print(f"Restored settings: {setting}")
        else:
            self.setGeometry(0, 0, 1500, 500)

    @Slot() # It's good practice to mark slots with @Slot decorator
    def initialize_thread_1(self):
        """
        This method should trigger a background task (like your Flask server).
        Logging messages from that task will now safely appear in the debugger.
        """
        logger.info("Starting Debugger ... (This message should appear)")
        # Example of how you might start your Flask/SocketIO server in a separate thread:
        # from your_flask_module import create_app
        # app = create_app()
        #
        # self.server_thread = QThread() # Create a QThread
        # self.flask_worker = FlaskWorker(app) # Your Flask app wrapped in a QObject worker
        # self.flask_worker.moveToThread(self.server_thread)
        # self.server_thread.started.connect(self.flask_worker.run)
        # self.server_thread.start()
        # logger.info("Flask server thread started (example).")


    @Slot()
    def CleanUi(self):
        """Clears the text in the debugger window."""
        self.textEdit.clear()
        logger.info("Debugger cleared.") # Log the clear action

    def closeEvent(self, event):
        """Overrides the close event to ensure proper shutdown."""
        # When the window is closed, ensure the logging handler is removed and settings saved.
        # We need access to the handler instance, which is held by QtWindowHandler.
        # A more robust way might be to pass the handler instance to the Window or
        # have a main application class manage it. For now, we'll iterate.
        for handler in logging.getLogger(__name__).handlers:
            if isinstance(handler, QtWindowHandler):
                handler.close_handler()
        event.accept()

    def quit_application(self):
        """A simple method to close the window.
           closeEvent will be called automatically."""
        self.close()