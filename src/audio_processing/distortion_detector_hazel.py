#!/usr/bin/env python3
"""
distortion_detector.py

This script loads an audio file and detects potential distortion,
including clipping and high-frequency anomalies.ls
"""

import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import argparse

def detect_clipping(audio, sr, clip_threshold=0.98, plot=False):
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
    clipped = np.abs(audio) > clip_threshold
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

    # Visualization
    if plot:
        plt.figure(figsize=(12, 5))
        librosa.display.waveshow(audio, sr=sr, alpha=0.6)
        plt.scatter(clipped_times, np.ones_like(clipped_times)*0.9, color='r', s=5, label='Clipping')
        plt.title("Distortion Detection: Clipped Samples Highlighted")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.legend()
        plt.show()

    # Summary 
    summary = {
        "sampling_rate": sr,
        "duration_sec": librosa.get_duration(y=audio, sr=sr),
        "total_clipped_samples": np.sum(clipped),
        "clip_ratio": clip_ratio,
        "distorted_regions_sec": distorted_regions[:10]  # first 10 regions
    }

    print("=== Distortion Summary ===")
    print(f"Sampling Rate: {summary['sampling_rate']} Hz")
    print(f"Duration: {summary['duration_sec']:.2f} seconds")
    print(f"Total Clipped Samples: {summary['total_clipped_samples']}")
    print(f"Clipping Detected in {summary['clip_ratio']*100:.4f}% of samples")
    print(f"Distorted Regions (first 10): {summary['distorted_regions_sec']} seconds")

    return distorted_regions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect distortion in an audio file.")
    parser.add_argument("audio_file", type=str, help="Path to the audio file (.wav recommended)")
    parser.add_argument("clip_threshold", type=float, nargs='?', default=0.98, help="Amplitude threshold for clipping detection")
    parser.add_argument("--no_plot", action="store_true", help="Do not display waveform plot")
    args = parser.parse_args()

    detect_clipping(args.audio_file, clip_threshold=args.clip_threshold, plot=not args.no_plot)
