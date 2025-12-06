from typing import List, Tuple
import numpy as np
import librosa
import pyloudnorm as pyln

def compute_short_term_loudness(
    audio: np.ndarray,
    sr: int,
    window_s: float = 0.4,
) -> Tuple[np.ndarray, np.ndarray]:
    
    meter = pyln.Meter(sr)

    hop_s = window_s / 2.0  # 50% overlap
    win_len = int(window_s * sr)
    hop_len = int(hop_s * sr)

    if win_len <= 0 or hop_len <= 0:
        raise ValueError("window_s and hop_s must be > 0")

    n = len(audio)
    if n < win_len:
        loud = meter.integrated_loudness(audio)
        return np.array([n / (2 * sr)], float), np.array([loud], float)

    times = []
    lufs = []
    start = 0
    while start + win_len <= n:
        end = start + win_len
        chunk = audio[start:end]
        loud = -np.inf if np.allclose(chunk, 0.0) else meter.integrated_loudness(chunk)
        center_time = (start + win_len / 2) / sr
        times.append(center_time)
        lufs.append(loud)
        start += hop_len

    return np.array(times, float), np.array(lufs, float)

# Return (start, end, max_lufs) tuples for loudness spikes above threshold [ran by job queue]
def get_loudness_spikes(
    audio: np.ndarray,
    sr: int,
    window_s: float = 0.4,
    threshold: float = -16.0
) -> List[Tuple[float, float, float]]:
    """
    Find sections of audio where loudness exceeds the specified threshold.
    
    Args:
        audio (np.ndarray): Audio signal.
        sr (int): Sample rate.
        window_s (float): Window size in seconds for loudness analysis.
        threshold (float): Loudness threshold in LUFS. Sections above this are returned.
        merge (bool): Whether to merge adjacent sections. Default True.
    
    Returns:
        List[Tuple[float, float, float]]: List of (start_time, end_time, max_lufs) tuples
                                          for each detected spike section.
    """
    merge = True

    hop_s = window_s / 2.0  # 50% overlap
    meter = pyln.Meter(sr)
    win_len = int(window_s * sr)
    hop_len = int(hop_s * sr)

    if win_len <= 0 or hop_len <= 0:
        raise ValueError("window_s and hop_s must be > 0")

    n = len(audio)
    
    # pyloudnorm requires at least 0.4 seconds for integrated loudness
    min_samples = int(0.4 * sr)
    if n < min_samples:
        return []
    
    # If audio is shorter than window, use the audio length as window
    if n < win_len:
        win_len = n
        hop_len = n  # Only one measurement

    detections = []  # List of (start_sample, end_sample, loudness)
    start_sample = 0
    
    while start_sample + win_len <= n:
        end_sample = start_sample + win_len
        chunk = audio[start_sample:end_sample]
        loud = -np.inf if np.allclose(chunk, 0.0) else meter.integrated_loudness(chunk)
        
        # Only include sections above threshold
        if loud > threshold:
            detections.append((start_sample, end_sample, loud))
        
        start_sample += hop_len

    if len(detections) == 0:
        return []
    
    if not merge:
        # Return individual windows as intervals
        return [(start / sr, end / sr, lufs) for start, end, lufs in detections]

    # Merge adjacent/overlapping sections
    merged = []
    current_start, current_end, current_max_lufs = detections[0]
    
    for start, end, lufs in detections[1:]:
        # Check if current detection overlaps or is adjacent to previous
        if start <= current_end:
            # Merge: extend end time and update max loudness
            current_end = max(current_end, end)
            current_max_lufs = max(current_max_lufs, lufs)
        else:
            # No overlap: save current section and start new one
            merged.append((current_start / sr, current_end / sr, current_max_lufs))
            current_start, current_end, current_max_lufs = start, end, lufs
    
    # Add the last section
    merged.append((current_start / sr, current_end / sr, current_max_lufs))
    
    return merged

# Get overall LUFS for entire audio file [ran by job queue]
def get_lufs(
    audio: np.ndarray,
    sr: int
) -> float:
    """
    Compute the integrated LUFS (loudness) for the entire audio signal.

    Args:
        audio (np.ndarray): Audio signal.
        sr (int): Sample rate.
        meter (pyln.Meter): Loudness meter.

    Returns:
        float: Integrated loudness in LUFS.
    """
    meter = pyln.Meter(sr)

    if audio.size == 0:
        return float('-inf')
    return meter.integrated_loudness(audio)