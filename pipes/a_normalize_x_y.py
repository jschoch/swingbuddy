from lib.swingpipe import BasePipe
import pandas as pd

class NXY(BasePipe):
    """
    normalize Y and X values for display in original pixel sizes 
    """
    def __init__(self):
        super().__init__()
        # Update the configuration for this subclass
        self.update_config(
            enable=True,
            render_static=False,
            render_tracking=False,
            render_trace=False
        )
    def preprocess_df(self, df):
        #df = df.filter(regex='_y$') * -1000
        for col in df.columns:
           if col.endswith('_y'):
                df[col] *= -1000
           if col.endswith('_x'):
               df[col] *= 1000
        return df
    def process_static_frame(self, frame):
        return frame
    def process_tracking_frame(self, frame):
        return frame
    def process_trace_frame(self,frame):
        return frame