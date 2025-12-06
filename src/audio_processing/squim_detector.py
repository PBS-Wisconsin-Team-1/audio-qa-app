import math
import numpy as np
import torch
import torchaudio
from .utils import Detection

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


def get_squim_model(device=None):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    class SimpleMOSModel(torch.nn.Module):
        def forward(self, wav: torch.Tensor, sr: int) -> torch.Tensor:
            mos = _compute_simple_mos(wav.cpu(), sr)
            return torch.tensor(mos, dtype=torch.float32)

    model = SimpleMOSModel().to(device)
    model.eval()
    return model, device


def prepare_wav_from_array(audio: np.ndarray, sr: int, target_sr: int = DEFAULT_SR, device=None):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    wav = torch.from_numpy(audio.astype(np.float32)).unsqueeze(0).to(device)
    if sr != target_sr:
        wav = torchaudio.functional.resample(wav, sr, target_sr)
        sr = target_sr
    return wav, sr, device


def sliding_mos_from_array(
    audio: np.ndarray,
    sr: int,
    window_s: float = 1.0,
    hop_s: float = 0.5,
    target_sr: int = DEFAULT_SR,
    device=None,
):
    wav, sr, device = prepare_wav_from_array(audio, sr, target_sr, device)
    model, device = get_squim_model(device)
    wav = wav.to(device)

    total_len = wav.shape[-1]
    win = int(window_s * sr)
    hop = int(hop_s * sr)

    scores = []
    with torch.inference_mode():
        if total_len < win:
            mos_val = model(wav, sr).item()
            scores.append((0.0, total_len / sr, float(mos_val)))
        else:
            pos = 0
            while pos + win <= total_len:
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
    mos_threshold: float = 2.5,
    window_s: float = 1.0,
    hop_s: float = 0.5,
    target_sr: int = DEFAULT_SR,
    device=None,
):
    scores = sliding_mos_from_array(
        audio=audio,
        sr=sr,
        window_s=window_s,
        hop_s=hop_s,
        target_sr=target_sr,
        device=device,
    )

    detections = []
    for start_t, end_t, mos_val in scores:
        if mos_val < mos_threshold:
            det = Detection(
                start=start_t,
                end=end_t,
                type="LowMOS",
                params={
                    "mos": mos_val,
                    "threshold": mos_threshold,
                    "window_s": window_s,
                    "hop_s": hop_s,
                },
            )
            detections.append(det)
    return detections


def load_for_squim(path: str, target_sr: int = DEFAULT_SR):
    wav, sr = torchaudio.load(path)
    if wav.shape[0] > 1:
        wav = wav.mean(dim=0, keepdim=True)
    if sr != target_sr:
        wav = torchaudio.functional.resample(wav, sr, target_sr)
        sr = target_sr
    return wav, sr


def full_mos(path: str, target_sr: int = DEFAULT_SR, device=None) -> float:
    wav, sr = load_for_squim(path, target_sr)
    model, device = get_squim_model(device)
    wav = wav.to(device)
    with torch.inference_mode():
        mos = model(wav, sr).item()
    return float(mos)


def sliding_mos(
    path: str,
    window_s: float = 1.0,
    hop_s: float = 0.5,
    target_sr: int = DEFAULT_SR,
    device=None,
):
    wav, sr = load_for_squim(path, target_sr)
    model, device = get_squim_model(device)
    wav = wav.to(device)

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
