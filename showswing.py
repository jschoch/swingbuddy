# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from datetime import datetime
from swingdb import Swing  # Adjust the path to your models module
from trcc import QCollapsibleWidget

class SwingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.clear_layout()

    def set_swing_data(self, swing: 'Swing'):
        self.clear_layout()

        labels = {
            "Name:": swing.name,
            "Date": swing.sdate.strftime("%Y-%m-%d"),
            "Screen": swing.screen,
            "Left Video ": swing.leftVid,
            "Right Video ": swing.rightVid,
            "TRC": len(swing.trc),
            "TRC Video": swing.trcVid,
            "Club": swing.club,
            "Comment": swing.comment
        }

        for label_text, value in labels.items():
            label = QLabel(f"{label_text}\t\t\t {value}", self)
            self.layout.addWidget(label)

        # Create a collapsible widget for the trc field
        trc_collapsible = QCollapsibleWidget("TRC", self)
        trc_label = QLabel(swing.trc, self)
        trc_collapsible.add_content(trc_label)
        self.layout.addWidget(trc_collapsible)

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
