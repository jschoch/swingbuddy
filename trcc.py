# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QLabel

class QCollapsibleWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        self.title_button = QPushButton(title, self)
        self.title_button.setCheckable(True)
        self.title_button.setChecked(False)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        self.title_button.toggled.connect(self.toggle_content)

        # Initially hide the scroll area
        self.scroll_area.setVisible(False)

        self.layout.addWidget(self.title_button)
        self.layout.addWidget(self.scroll_area)

    def toggle_content(self):
        if self.title_button.isChecked():
            self.scroll_area.setVisible(True)
            self.scroll_area.setWidget(self.content_widget)
        else:
            self.scroll_area.setVisible(False)
            self.scroll_area.takeWidget()

    def add_content(self, content):
        if isinstance(content, str):
            label = QLabel(content, self.content_widget)
            self.content_layout.addWidget(label)
        elif isinstance(content, QWidget):
            self.content_layout.addWidget(content)
