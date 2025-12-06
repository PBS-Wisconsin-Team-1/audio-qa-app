import torch
import torchaudio
from torchaudio.prototype import squim
from .utils import Detection

DEFAULT_SR = 48000

def load_for_squim(path: str, target_sr: int = DEFAULT_SR):
    wav, sr = torchaudio.load(path)
    if wav.shape[0] > 1:
        wav = wav.mean(dim=0, keepdim=True)
    if sr != target_sr:
        wav = torchaudio.functional.resample(wav, sr, target_sr)
        sr = target_sr
    return wav, sr

# Create squim MOS model
def get_squim_model(device=None):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = squim.SquimObjective().to(device)
    model.eval()
    return model, device

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

def detect_low_mos_regions(
    path: str,
    mos_threshold: float = 2.5,
    window_s: float = 1.0,
    hop_s: float = 0.5,
    target_sr: int = DEFAULT_SR,
    device=None,
):
    scores = sliding_mos(
        path=path,
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
