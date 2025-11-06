from audio_processing.audio_import import AudioLoader
from audio_processing.utils import Detection, seconds_to_mmss
from typing import Type
from rq import Queue
from audio_processing.artifact_simulate import ArtifactSim
from analysis_types import ANALYSIS_TYPES
from threading import Lock

class AudioDetectionJob:
    def __init__(self, queue : Type[Queue], loader: Type[AudioLoader]):
        self.results : list[Detection] = []
        self.loader = loader
        self.queue = queue
        self.completed = {}
        self.audio = None
        self.result_lock = Lock()

    def load_and_queue(self, audio_file_path: str, analyses: list[dict]):
        self.audio = self.loader.load_audio_file(audio_file_path)
        for analysis in analyses:
            self.completed[analysis['type']] = False
            self.queue.enqueue(self.run_detection, ANALYSIS_TYPES[analysis['type']]['func'], analysis['params'])
        return
        
    def run_detection(self, func: callable, params: dict):

        det_result = func(self.audio['data'], self.audio['sr'], **params)

        with self.result_lock:
            for s, e in det_result:
                detection = Detection(start=s, end=e, type="cutout", params=params)
                self.results.append(detection)

        self.complete('detect_cutouts')

    def complete(self, type : str):
        self.completed[type] = True
        for value in self.completed.values():
            if not value:
                return
        self.queue.enqueue(self.create_report)
    
    def create_report(self):
        print("Creating report...")
        for detection in sorted(self.results):
            print(f"Detection: {detection.type} from {seconds_to_mmss(detection.start)} to {seconds_to_mmss(detection.end)} - {detection.get_details()}")


def simulate_artifacts(loader : Type[AudioLoader], input_file: str, output_file: str, artifacts: dict, seed: int = 42):
    simulator = ArtifactSim(directory=loader.directory, artifacts=artifacts)
    simulator.distort_audio(input_file, output_file, seed=seed)
