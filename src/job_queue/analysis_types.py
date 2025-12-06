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
        "params": {"threshold": 0.0001, "min_len": 100},
        "func": detect_cutout
    },
    "Loudness": {
        "type": "in-file",
        "params": {"loudness_threshold": -10.0, "window_s": 0.4},
        "func": get_loudness_spikes
    },
    "Speech Quality": {
        "type": "in-file",
        "params": {"mos_threshold": 2.0, "window_s": 1.0},
        "func": detect_low_mos_regions
    },
    "Overall LUFS": {
        "type": "overall",
        "params": {},
        "func": get_lufs
    },
    "Low MOS": {
    "type": "in-file",
    "display_name": "Low Audio Quality",
    "description": "Identifies portions of the audio that fall below an acceptable quality level.",
    "params": {
        "mos_threshold": {
            "default": 2.5,
            "label": "Quality Level",
            "help": "The minimum acceptable quality score before a section is flagged."
        },
        "window_s": {
            "default": 1.0,
            "label": "Evaluation Duration",
            "help": "How long the system listens during each quality assessment."
        },
        "hop_s": {
            "default": 0.5,
            "label": "Evaluation Interval",
            "help": "How frequently the system performs a new assessment as it moves through the audio."
        },
    },
    "func": detect_low_mos_regions,
    }
}