import os
from pathlib import Path
import math
from scipy.signal import butter, filtfilt
import pandas as pd


def euclidean_distance(point1, point2):
    if point1 is None or point2 is None:
        return None
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

# Function to apply Butterworth filter
def butter_lowpass(cutoff, fs, order=10):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5, padlen=2):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data, padlen=padlen)  # Apply filter with additional padding
    return pd.Series(y, index=data.index)

def gen_speed(data,apply_filters=True, fs=120, cutoff=12):
    calculate_constant = False
    if calculate_constant:
        a = (214.4791,974.7798)
        b = (655.811,973.405)
        ab_dist = euclidean_distance(a,b)
        print(f"the distance was: {ab_dist}")
        pixel_to_inches = 46 / ab_dist
        pixels_to_meters = 1.1684 / ab_dist
        print(f"the pixels per inch factor is: {pixel_to_inches}")
        print(f"m/p: {pixels_to_meters}")

    pixels_per_inch = 0.10422944004466449
    mps_const = 0.0026474277771344782

    #  access the first column of the dataframe and multiply it by 1000 
    data['X1'] = data.iloc[:,1] * 1000
    #  acces the second column of the dataframe and multiply it by 1000 
    data['Y1'] = data.iloc[:, 2] * -1000

    
     # Initialize Distance and Speed for the first row
    data.at[0, 'Distance'] = None  # or some default value if applicable
    data.at[0, 'Speed'] = None   # or some default value if applicable

    data['Distance'] = data.apply(lambda row: euclidean_distance((row['X1'], row['Y1']),
        (data.iloc[row.name-1]['X1'], data.iloc[row.name-1]['Y1']) 
        if row.name > 0 else None), axis=1)

    # Calculate speed in units per second (assuming distance is in units and time is in seconds)
    fps_120 = 1.0/120
    #convert meters per second to miles per hour
    mps_mph_const = 2.237
    
    data['Speed'] = data['Distance'].apply(
        #lambda x: x / (frame_time_ms * mps_const * 1e-6) 
        lambda x: (x / fps_120) * mps_const * mps_mph_const
        if x is not None else 0)  # Assuming constant time_per_frame

    # Calculate time for each frame
    #data['Time'] = data.index * frame_time_ms

    if apply_filters:
        data['Distance'] = data['Distance'].interpolate(method='linear', limit_direction='both')
        data['Speed'] = data['Speed'].interpolate(method='linear', limit_direction='both')

        data['Distance_filtered'] = butter_lowpass_filter(data['Distance'], cutoff, fs)
        data['Speed_filtered'] = butter_lowpass_filter(data['Speed'], cutoff, fs)
        
    

    return data
def pre_speed(lw,key):
    lw = lw[key]
    #lw.columns = ['t',"x","y","z"] 
    #lw = gen_speed(lw)
    print(f"{key}: {lw.head()}")
    return lw
