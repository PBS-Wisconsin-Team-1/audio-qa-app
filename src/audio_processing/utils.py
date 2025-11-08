import json
import inspect

def seconds_to_mmss(seconds : float):
    if seconds is None:
        return "N/A"
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

    def get_details(self) -> str:
        match self.type:
            case "Cutout":
                return f'Less than {self.params["threshold"]} RMS detected for at least {self.params["min_len"]} ms'

            case "Clipping":
                return f'Greater than {self.params["threshold"]} amplitude detected'

    def __lt__(self, other: "Detection") -> bool:
        return self.start < other.start

    def __str__(self) -> str:
        return self.to_json()

    def to_json(self) -> str:
        return json.dumps({
            'type': self.type,
            'start': self.start,
            'end': self.end,
            'params': self.params
        })
    
    @staticmethod
    def det_from_string(s: str) -> "Detection":
        d = json.loads(s)
        start = float(d['start']) if d['start'] is not None else None
        end = float(d['end']) if d['end'] is not None else None
        type = str(d['type'])
        params = d['params'] if d['params'] is not None else {}
        return Detection(start=start, end=end, type=type, params=params)

def fill_default_params(func, params):
    sig = inspect.signature(func)
    filled = {}
    for name, param in sig.parameters.items():
        if name in ['audio', 'sr']:
            continue
        if name in params:
            filled[name] = params[name]
        elif param.default is not inspect.Parameter.empty:
            filled[name] = param.default
    return filled
