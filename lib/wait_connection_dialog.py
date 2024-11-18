from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Signal

class ConnectionDialog(QDialog):
    connection_established = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Waiting for WebSocket Connection")
        self.setGeometry(100, 100, 300, 200)
        
        layout = QVBoxLayout()
        label = QLabel("Waiting for TRC data server connection...", self)
        layout.addWidget(label)
        
        container = QWidget()
        container.setLayout(layout)
        #self.setCentralWidget(container)

    def got_connection(self):
        self.accept()

    def closeEvent(self, event):
        super().closeEvent(event)
        print("WebSocket dialog closed")