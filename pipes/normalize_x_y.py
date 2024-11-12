from lib.swingpipe import BasePipe
import pandas as pd

class NXY(BasePipe):
    """
    normalize Y and X values for display in original pixel sizes 
    """
    def preprocess_df(self, df):
        #df = df.filter(regex='_y$') * -1000
        for col in df.columns:
           if col.endswith('_y'):
                df[col] *= -1000
           if col.endswith('_x'):
               df[col] *= 1000
        return df
    def process_frame(self, frame):
        return frame
    def process_perf_frame(self, frame):
        return frame