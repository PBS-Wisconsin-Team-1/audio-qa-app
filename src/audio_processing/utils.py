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
    def __init__(self, type: str, params: dict, result=None, start: float=None, end: float=None, in_file: bool=True):
        self.start = start
        self.end = end
        self.type = type
        self.params = params
        self.result = result
        self.in_file = in_file

    def get_details(self) -> str:
        match self.type:
            case "Cutout":
                return f'Less than {self.params["threshold"]} RMS detected for at least {self.params["min_len"]} ms'

            case "Clipping":
                return f"Clipping detected by ClipDaT algorithm"
            
            case "Loudness":
                return f'Loudness exceeded {self.params["threshold"]} LUFS'

    def __lt__(self, other: "Detection") -> bool:
        if not self.in_file and not other.in_file:
            return self.type < other.type
        if not self.in_file or not other.in_file:
            return not self.in_file
        return self.start < other.start

    def __str__(self) -> str:
        return self.to_json()

    def to_json(self) -> str:
        return json.dumps({
            'type': self.type,
            'params': self.params,
            'start': self.start,
            'end': self.end,
            'result': self.result,
            'in_file': self.in_file
        })
    
    @staticmethod
    def det_from_string(s: str) -> "Detection":
        d = json.loads(s)
        type = str(d['type'])
        params = d['params'] if d['params'] is not None else {}
        start = float(d['start']) if d['start'] is not None else None
        end = float(d['end']) if d['end'] is not None else None
        result = d['result'] if 'result' in d else None
        in_file = bool(d['in_file']) if 'in_file' in d else None
        return Detection(start=start, end=end, result=result, type=type, params=params, in_file=in_file)

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
