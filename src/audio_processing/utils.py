def seconds_to_mmss(seconds : float):
    """Convert seconds to mm:ss format"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"

class Detection:
    def __init__(self, start : float, end: float, type: str, params: dict):
        self.start = start
        self.end = end
        self.type = type
        self.params = params

    def get_details(self):
        match self.type:
            case "cutout":
                return f'Less than {self.params["threshold"]} RMS detected for at least {self.params["min_len"]} ms'

            case "clipping":
                return f'Greater than {self.params["threshold"]} amplitude detected'

    def __lt__(self, other):
        return self.start < other.start
