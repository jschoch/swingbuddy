from lib.swingpipe import BasePipe
from dataa import euclidean_distance, butter_lowpass_filter
import pandas as pd

class LWristPipe(BasePipe):
    """
    normalize Y and X values for display in original pixel sizes 
    """
    def preprocess_df(self, df):
        pixels_per_inch = 0.10422944004466449
        mps_const = 0.0026474277771344782

        # Calculate speed in units per second (assuming distance is in units and time is in seconds)
        fps_120 = 1.0/120
        #convert meters per second to miles per hour
        mps_mph_const = 2.237
        
        
        

        df.at[0,'LWrist_Distance'] = None
        df.at[0,'LWrist_Speed'] = None
        df['LWrist_Distance'] = df.apply(lambda row: euclidean_distance((row['LWrist_x'], row['LWrist_y']),
            (df.iloc[row.name-1]['LWrist_x'], df.iloc[row.name-1]['LWrist_y']) 
            if row.name > 0 else None), axis=1)
        
        
        # TODO:  should lookup and load a config for stuff like this
        apply_filters = True
        cutoff=12
        fs=120

        df['LWrist_Speed'] = df['LWrist_Distance'].apply(
            #lambda x: x / (frame_time_ms * mps_const * 1e-6) 
            lambda x: (x / fps_120) * mps_const * mps_mph_const
            if x is not None else 0)  # Assuming constant time_per_frame

        if apply_filters:
            df['LWrist_Distance'] = df['LWrist_Distance'].interpolate(method='linear', limit_direction='both')
            df['LWrist_Speed'] = df['LWrist_Speed'].interpolate(method='linear', limit_direction='both')

            df['LWrist_Distance_filtered'] = butter_lowpass_filter(df['LWrist_Distance'], cutoff, fs)
            df['LWrist_Speed_filtered'] = butter_lowpass_filter(df['LWrist_Speed'], cutoff, fs)
                
        return df
    def process_static_frame(self, frame):
        return frame
    def process_tracking_frame(self, frame):
        return frame
    def process_trace_frame(self,frame):
        return frame