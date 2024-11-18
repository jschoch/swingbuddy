import sys
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget, QVBoxLayout, QPushButton

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.stacked_widget = QStackedWidget()

        # Create some widgets to add to the stacked widget
        widget1 = QWidget()
        widget1.setStyleSheet("background-color: red")

        widget2 = QWidget()
        widget2.setStyleSheet("background-color: green")

        # Add widgets to the stacked widget
        self.stacked_widget.addWidget(widget1)
        self.stacked_widget.addWidget(widget2)

        # Create buttons to switch between widgets
        button1 = QPushButton("Show Widget 1")
        button1.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        button2 = QPushButton("Show Widget 2")
        button2.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        # Create a layout for the main window
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        layout.addWidget(button1)
        layout.addWidget(button2)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())