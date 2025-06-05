from lib.swingpipe import BasePipe
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QTransform, QPen,QPainter

class SpinePipe(BasePipe):
    """
    Show spine angle on screen
    """
    def __init__(self):
        super().__init__()
        # Update the configuration for this subclass
        self.update_config(
		    name="SpinePipe",
            enable=True,
            render_static=True,
            render_tracking=True,
            render_trace=False
        )
    def preprocess_df(self, df):
        return df
    def process_static_frame(self, frame,df,idx):
        if  not 'HipMiddle_x' in df.columns:
            return frame
        x_pos1 = df['HipMiddle_x'].iloc[idx]
        y_pos1 = df['HipMiddle_y'].iloc[idx]
        x_pos2 = df['Neck_x'].iloc[idx]
        y_pos2 = df['Neck_y'].iloc[idx]
        painter = QPainter(frame)
        pen = QPen(Qt.blue, 5)
        painter.setPen(pen)
        painter.drawLine(x_pos1, y_pos1, x_pos2, y_pos2)
        painter.end()
        return frame
    def process_tracking_frame(self, frame,df,idx):
        if  not 'HipMiddle_x' in df.columns:
            return frame
        x_pos1 = df['HipMiddle_x'].iloc[idx]
        y_pos1 = df['HipMiddle_y'].iloc[idx]
        x_pos2 = df['Neck_x'].iloc[idx]
        y_pos2 = df['Neck_y'].iloc[idx]
        painter = QPainter(frame)
        pen = QPen(Qt.red, 3)
        painter.setPen(pen)
        painter.drawLine(x_pos1, y_pos1, x_pos2, y_pos2)
        painter.end()
        return frame
    def process_trace_frame(self, frame,df,idx):
        return frame
