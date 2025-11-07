from audio_processing.distortion_detection import detect_clipping, detect_cutout

USER_JOB_TYPES = {
    "load_and_queue": {"audio_files": list, "detection_types": list, "detection_params": dict},
    "simulate_artifacts": {"artifacts": dict}
}

ANALYSIS_TYPES = {
    "detect_clipping": {
        "params": {"threshold": float},
        "func": detect_clipping
    },
    "detect_cutouts": {
        "params": {"threshold": float, "min_len": int},
        "func": detect_cutout
    }
}