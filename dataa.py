import os
from pathlib import Path
import math
from scipy.signal import butter, filtfilt
import pandas as pd
pd.options.mode.copy_on_write = True


#
#
#   IS ANYTHING USING THIS?
##
#

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
