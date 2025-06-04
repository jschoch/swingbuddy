# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout,QTextEdit
from PySide6.QtCore import Qt
from datetime import datetime
from swingdb import Swing  # Adjust the path to your models module
from trcc import QCollapsibleWidget

class SwingDataWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.hlayout = QVBoxLayout()
        self.metadata_layout = QVBoxLayout()
        self.vlayout2 = QHBoxLayout()

        self.hlayout.addLayout(self.metadata_layout)
        self.hlayout.addLayout(self.vlayout2)
        self.setLayout(self.hlayout)

        self.clear_layout()

    def set_swing_data(self, swing: 'Swing'):
        self.clear_layout()
        

        labels = {
            "ID: ": swing.id,
            "Name:": swing.name,
            "Date": swing.sdate.strftime("%Y-%m-%d"),
            "Screen": swing.screen,
            "Down the Line Video ": swing.dtlVid,
            "Face On Video ": swing.faceVid,
            "Face on TRC": len(swing.faceTrc),
            "DTL TRC": len(swing.dtlTrc),
            "TRC Video": swing.trcVid,
            "Club": swing.club,
            "Comment": swing.comment
        }

        for label_text, value in labels.items():
            label = QTextEdit(f"{label_text}\t\t\t {value}", self)
            label.setReadOnly(True)
            label.setFixedHeight(15)
            self.metadata_layout.addWidget(label)

        # Create a collapsible widget for the trc field
        face_trc_collapsible = QCollapsibleWidget("face TRC", self)
        face_trc_label = QLabel(swing.faceTrc, self)
        face_trc_collapsible.add_content(face_trc_label)
        self.vlayout2.addWidget(face_trc_collapsible)

        dtl_trc_collapsible = QCollapsibleWidget("Down the line TRC", self)
        dtl_trc_label = QLabel(swing.dtlTrc, self)
        dtl_trc_collapsible.add_content(dtl_trc_label)
        self.vlayout2.addWidget(dtl_trc_collapsible)

        ocr_collapsible = QCollapsibleWidget("Raw OCR Data", self)
        ocr_label = QLabel(swing.lmdata.raw_txt, self)
        ocr_collapsible.add_content(ocr_label)
        self.vlayout2.addWidget(ocr_collapsible)
        

    def clear_layout(self):
        while self.metadata_layout.count():
            item = self.metadata_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        while self.vlayout2.count():
            item = self.vlayout2.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
