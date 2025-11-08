import numpy as np
import librosa
from scipy.fftpack import fft

def thd_ratio(data : np.array):
    n = len(data)
    fft_data = np.abs(fft(data))
    fundamental = np.max(fft_data)
    harmonics_power = np.sum(fft_data**2) - fundamental**2
    return np.sqrt(harmonics_power) / fundamental

def index_to_time(index: int, sr: int) -> float:
    """Convert a sample index to time in seconds given sample rate sr."""
    if sr <= 0:
        raise ValueError("Sample rate 'sr' must be positive")
    if index < 0:
        raise ValueError("Index must be non-negative")
    return index / float(sr)

def detect_clipping(audio, sr, threshold=0.98):
    """
    Detects clipping in an audio file.

    Parameters:
        filename (str): Path to the audio file.
        clip_threshold (float): Amplitude threshold for clipping detection.
        plot (bool): Whether to show waveform visualization.

    Returns:
        dict: Summary of distortion analysis.
    """

    # Normalize audio
    audio = audio / np.max(np.abs(audio))

    # Detect clipping
    clipped = np.abs(audio) > threshold
    clip_ratio = np.sum(clipped) / len(audio)

    # Clipped sample times 
    clipped_frames = np.where(clipped)[0]
    clipped_times = clipped_frames / sr

    # Spectral analysis (centroid) 
    spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
    frames = range(len(spectral_centroid))
    t = librosa.frames_to_time(frames, sr=sr)
    threshold = np.mean(spectral_centroid) + 2 * np.std(spectral_centroid)
    distorted_regions = t[spectral_centroid > threshold]

    return distorted_regions

def detect_cutout(audio, sr, threshold=0.001, min_len=50):
    frame_length = int((min_len * sr) / 1000)
    hop_length = frame_length // 2
    rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]
    duration_s = len(audio) / float(sr)
    intervals = rms_frame_intervals_seconds(len(rms), sr, frame_length, hop_length, duration_s=duration_s)

    # Detect frames below threshold
    silent_frames = rms < threshold

    # Group consecutive frames into regions using start/end of covered intervals
    regions = []
    start_time = None
    end_time = None
    for i, is_silent in enumerate(silent_frames):
        if is_silent:
            if start_time is None:
                start_time = intervals[i][0]
            end_time = intervals[i][1]
        elif not is_silent and start_time is not None:
            regions.append((start_time, end_time))
            start_time = None
            end_time = None
    if start_time is not None:
        end_time = intervals[-1][1]
        regions.append((start_time, end_time))
    return regions

def rms_frame_intervals_seconds(num_frames: int, sr: int, frame_length: int, hop_length: int, center: bool = True,
                                duration_s: float | None = None) -> np.ndarray:
    """Return [num_frames, 2] array with (start_s, end_s) covered by each RMS frame.

    Assumes librosa.feature.rms was called with the same frame_length, hop_length, and center.
    If duration_s is provided, intervals are clamped to [0, duration_s].
    """
    if sr <= 0:
        raise ValueError("Sample rate 'sr' must be positive")
    if num_frames < 0:
        raise ValueError("num_frames must be non-negative")
    if frame_length <= 0 or hop_length <= 0:
        raise ValueError("frame_length and hop_length must be positive")

    frames = np.arange(num_frames)
    if center:
        centers = (frames * hop_length) / float(sr)
    else:
        centers = (frames * hop_length + frame_length / 2.0) / float(sr)

    half = (frame_length / 2.0) / float(sr)
    starts = centers - half
    ends = centers + half
    if duration_s is not None:
        starts = np.clip(starts, 0.0, duration_s)
        ends = np.clip(ends, 0.0, duration_s)
    return np.stack([starts, ends], axis=1)