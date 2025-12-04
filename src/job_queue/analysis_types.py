from audio_processing.distortion_detection import detect_clipping, detect_cutout
from audio_processing.loudness import get_loudness_spikes, get_lufs

USER_JOB_TYPES = {
    "load_and_queue": {"audio_files": list, "detection_types": list, "detection_params": dict},
    "simulate_artifacts": {"artifacts": dict}
}

ANALYSIS_TYPES = {
    "Clipping": {
        "type": "in-file",
        "params": {},
        "func": detect_clipping
    },
    "Cutout": {
        "type": "in-file",
        "params": {"threshold": 0.001, "min_len": 50},
        "func": detect_cutout
    },
    "Loudness": {
        "type": "in-file",
        "params": {"loudness_threshold": -23.0, "window_s": 0.4},
        "func": get_loudness_spikes
    },
    "Overall LUFS": {
        "type": "overall",
        "params": {},
        "func": get_lufs
    }
}