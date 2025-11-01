from audio_processing.audio_import import AudioLoader
from audio_processing.distortion_detection import detect_clipping, detect_cutout
from audio_processing.utils import Detection, seconds_to_mmss
from typing import Type
from rq import Queue
from audio_processing.artifact_simulate import ArtifactSim


class AudioDetectionJob:
    def __init__(self, queue : Type[Queue], loader: Type[AudioLoader]):
        self.results : list[Detection] = []
        self.loader = loader
        self.queue = queue
        self.completed = {}
        self.audio = None

    def load_and_queue(self, audio_file_path: str, analyses: list[dict]):
        self.audio = self.loader.load_audio_file(audio_file_path, type="pydub")
        for analysis in analyses:
            if analysis['type'] == 'detect_clipping':
                self.completed['detect_clipping'] = False
                self.queue.enqueue(self.detect_clipping, analysis['threshold'])
            elif analysis['type'] == 'detect_cutouts':
                self.completed['detect_cutouts'] = False
                self.queue.enqueue(self.detect_cutouts, analysis['threshold'], analysis['min_len'])
        return
        
    def detect_cutouts(self, threshold, min_silence_len):
        
        results = detect_cutout(self.audio['data'], self.audio['sr'], threshold=threshold, min_silence_duration_ms=min_silence_len)

        for s, e in results:
            detection = Detection(start=s, end=e, type="cutout", params={"threshold": threshold, "min_len": min_silence_len})
            self.results.append(detection)

        self.complete('detect_cutouts')

    def detect_clipping(self, threshold):
        
        results = detect_clipping(self.audio['data'], self.audio['sr'], threshold=threshold)

        for s in results:
            detection = Detection(start=s, end=None, type="clipping", params={"threshold": threshold})
            self.results.append(detection)
        
        self.complete('detect_clipping')

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
