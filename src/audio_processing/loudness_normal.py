import argparse
import os
from typing import List, Tuple
import numpy as np
import librosa
import soundfile as sf
import pyloudnorm as pyln


def load_audio(path: str, sr: int | None = None) -> tuple[np.ndarray, int]:
    audio, sr_ret = librosa.load(path, sr=sr, mono=True)
    return audio.astype(np.float32), sr_ret

def save_audio(path: str, audio: np.ndarray, sr: int):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    sf.write(path, audio, sr, subtype="FLOAT")

# Compute short-term loudness windows
def compute_short_term_loudness(
    audio: np.ndarray,
    sr: int,
    meter: pyln.Meter,
    window_s: float = 0.4,
    hop_s: float = 0.2,
) -> Tuple[np.ndarray, np.ndarray]:
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

# Build smoothed gain envelope from loudness spikes
def build_gain_envelope(
    short_times: np.ndarray,
    short_lufs: np.ndarray,
    tgt_lufs: float,
    global_lufs: float,
    sr: int,
    n_samples: int,
    max_boost_db: float = 6.0,
    max_cut_db: float = 12.0,
    spike_soft_limit_db: float = 5.0,
    smooth_seconds: float = 1.0,
) -> np.ndarray:
    if np.all(np.isneginf(short_lufs)):
        return np.ones(n_samples, dtype=np.float32)

    base_global_gain_db = tgt_lufs - global_lufs
    desired_lufs = np.copy(short_lufs)
    spike_threshold = global_lufs + spike_soft_limit_db

    loud_mask = desired_lufs > spike_threshold
    desired_lufs[loud_mask] = spike_threshold

    quiet_mask = desired_lufs < tgt_lufs - max_boost_db
    desired_lufs[quiet_mask] = tgt_lufs - max_boost_db

    gain_db_per_window = desired_lufs - short_lufs
    gain_db_per_window += base_global_gain_db
    gain_db_per_window = np.clip(gain_db_per_window, -max_cut_db, max_boost_db)

    sample_times = np.linspace(0, n_samples / sr, n_samples, endpoint=False)

    finite_mask = np.isfinite(gain_db_per_window)
    gain_db_clean = gain_db_per_window.copy()
    gain_db_clean[~finite_mask] = base_global_gain_db

    gain_db_samples = np.interp(sample_times, short_times, gain_db_clean)

    if smooth_seconds > 0:
        smooth_len = int(smooth_seconds * sr)
        if smooth_len > 1:
            kernel = np.ones(smooth_len, float) / smooth_len
            gain_db_samples = np.convolve(gain_db_samples, kernel, mode="same")

    return (10.0 ** (gain_db_samples / 20.0)).astype(np.float32)

# Normalize a single track to target LUFS
def normalize_track(
    audio: np.ndarray,
    sr: int,
    target_lufs: float = -24.0,
    window_s: float = 0.4,
    hop_s: float = 0.2,
) -> np.ndarray:
    meter = pyln.Meter(sr)
    if np.allclose(audio, 0.0):
        return audio

    global_lufs = meter.integrated_loudness(audio)

    short_times, short_lufs = compute_short_term_loudness(
        audio, sr, meter, window_s, hop_s
    )

    gain_env = build_gain_envelope(
        short_times,
        short_lufs,
        target_lufs,
        global_lufs,
        sr,
        len(audio),
    )

    processed = audio * gain_env
    peak = np.max(np.abs(processed)) or 1.0
    if peak > 1.0:
        processed /= peak

    return processed.astype(np.float32)

def process_files(
    input_files: List[str],
    output_dir: str | None,
    target_lufs: float,
    sr: int | None,
):
    for path in input_files:
        print(f"\n=== Processing {path} ===")
        audio, sr_ret = load_audio(path, sr=sr)
        normalized = normalize_track(audio, sr_ret, target_lufs)

        base = os.path.basename(path)
        name, ext = os.path.splitext(base)
        out_name = f"{name}_norm{ext or '.wav'}"
        out_path = (
            os.path.join(output_dir, out_name)
            if output_dir
            else os.path.join(os.path.dirname(path), out_name)
        )

        save_audio(out_path, normalized, sr_ret)
        print(f"  ➜ Saved: {out_path}")

def build_arg_parser():
    p = argparse.ArgumentParser(description="LUFS loudness normalizer with spike smoothing")
    p.add_argument("files", nargs="+")
    p.add_argument("--target", type=float, default=-24.0)
    p.add_argument("-o", "--out-dir", type=str, default=None)
    p.add_argument("--sr", type=int, default=None)
    return p

def main():
    parser = build_arg_parser()
    args = parser.parse_args()
    process_files(args.files, args.out_dir, args.target, args.sr)

if __name__ == "__main__":
    main()
