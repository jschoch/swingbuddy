from lib.swingpipe import BasePipe
import pandas as pd

class NXY(BasePipe):
    """
    normalize Y and X values for display in original pixel sizes 
    """
    def preprocess_df(self, df):
        rx = df['RHip_x']
        lx = df['LHip_x']
        df['HipMiddle_x'] = (rx + lx) / 2.0
        return df
    def process_frame(self, frame):
        return frame
    def process_perf_frame(self, frame):
        return frame