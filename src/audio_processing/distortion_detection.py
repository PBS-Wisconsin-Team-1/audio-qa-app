import numpy as np
from scipy.fftpack import fft

def thd_ratio(data : np.array):
    n = len(data)
    fft_data = np.abs(fft(data))
    fundamental = np.max(fft_data)
    harmonics_power = np.sum(fft_data**2) - fundamental**2
    return np.sqrt(harmonics_power) / fundamental

def detect_clipping(data, bit_depth=16):
    max_val = 2**(bit_depth - 1) - 1
    min_val = -max_val - 1
    clipping = np.any(data >= max_val) or np.any(data <= min_val)
    return clipping

