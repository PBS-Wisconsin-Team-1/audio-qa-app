import torch
import torchaudio
import numpy as np
from .utils import Detection
import math

DEFAULT_SR = 48000

def _compute_simple_features(wav: torch.Tensor):
    if wav.dim() == 1:
        wav = wav.unsqueeze(0)
    eps = 1e-12
    peak = wav.abs().max().item()
    rms = float(torch.sqrt(torch.mean(wav ** 2)) + eps)
    rms_db = 20.0 * math.log10(rms + eps)
    clip_thresh = 0.99
    clipped = (wav.abs() >= clip_thresh).float()
    clip_ratio = float(clipped.mean().item())
    return rms_db, peak, clip_ratio

def _compute_simple_mos(wav: torch.Tensor, sr: int) -> float:
    rms_db, peak, clip_ratio = _compute_simple_features(wav)
    rms_db_clamped = max(-60.0, min(0.0, rms_db))
    mos = 1.0 + 4.0 * (rms_db_clamped + 60.0) / 60.0
    mos -= 2.0 * min(clip_ratio * 10.0, 1.0)
    if rms_db < -50.0:
        mos -= 0.5
    mos = max(1.0, min(5.0, mos))
    return float(mos)

# Create squim MOS model
def get_squim_model():

    class SimpleMOSModel(torch.nn.Module):
        def forward(self, wav: torch.Tensor, sr: int) -> torch.Tensor:
            mos = _compute_simple_mos(wav.cpu(), sr)
            return torch.tensor(mos, dtype=torch.float32)
    model = SimpleMOSModel().to('cpu')
    model.eval()

    return model

def sliding_mos(
    audio: np.ndarray,
    sr: int,
    window_s: float = 1.0,
):
    hop_s = window_s / 2
    wav = torch.from_numpy(audio).unsqueeze(0)  # Shape: (1, samples)
    model = get_squim_model()
    wav = wav.to('cpu')

    win = int(window_s * sr)
    hop = int(hop_s * sr)

    scores = []
    with torch.inference_mode():
        pos = 0
        while pos + win <= wav.shape[-1]:
            chunk = wav[:, pos:pos + win]
            mos_val = model(chunk, sr).item()
            start_t = pos / sr
            end_t = (pos + win) / sr
            scores.append((float(start_t), float(end_t), float(mos_val)))
            pos += hop
    return scores

def detect_low_mos_regions(
    audio: np.ndarray,
    sr: int,
    mos_threshold: float = 2.0,
    window_size: float = 1.0,
):
    scores = sliding_mos(
        audio=audio,
        sr=sr,
        window_s=window_size,
    )
    detections = []
    for start_t, end_t, mos_val in scores:
        if mos_val < mos_threshold:
            detections.append((start_t, end_t, mos_val))
    return detections
