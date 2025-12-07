from audio_processing.distortion_detection import detect_clipping, detect_cutout
from audio_processing.loudness import get_loudness_spikes, get_lufs
from audio_processing.squim_detector import detect_low_mos_regions

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
        "params": {"silence_threshold": 0.0001, "minimum_length": 100},
        "func": detect_cutout
    },
    "Loudness": {
        "type": "in-file",
        "params": {"loudness_threshold": -10.0, "window_size": 0.4},
        "func": get_loudness_spikes
    },
    "Speech Quality": {
        "type": "in-file",
        "params": {"mos_threshold": 2.0, "window_size": 1.0},
        "func": detect_low_mos_regions
    },
    "Overall LUFS": {
        "type": "overall",
        "params": {},
        "func": get_lufs
    }
}