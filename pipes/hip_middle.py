from lib.swingpipe import BasePipe
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QTransform, QPen,QPainter


class HipMiddle(BasePipe):
    def __init__(self):
        super().__init__()
        # Update the configuration for this subclass
        self.update_config(
            name = "Hip Middle",
            render_on_dtl=True,
            render_static=True,
            render_tracking=True,
            render_trace=False
        )
    """
    normalize Y and X values for display in original pixel sizes 
    """
    def preprocess_df(self, df):
        rx = df['RHip_x']
        lx = df['LHip_x']
        df['HipMiddle_x'] = (rx + lx) / 2.0
        return df
    def process_static_frame(self, frame,df,idx):
        x_pos = df['HipMiddle_x'].iloc[0]
        print(f"HMX: {x_pos}")
        pen = QPen(Qt.green, 4)
        painter = QPainter(frame)
        painter.setPen(pen)
        painter.drawLine(x_pos, 0, x_pos, frame.height()) 

        return frame
    def process_tracking_frame(self, frame,df,idx):
        if  not 'HipMiddle_x' in df.columns:
            return frame
        print(".", end="")
        x_pos = df['HipMiddle_x'].iloc[idx]
        painter = QPainter(frame)
        pen = QPen(Qt.red, 2)
        painter.setPen(pen)
        painter.drawLine(x_pos, 0, x_pos, frame.height())
        painter.end()
        return frame
    def process_trace_frame(self,frame,df,idx):
        
        return frame